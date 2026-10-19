import base64
import json
import os
import secrets
import time
import httpx
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_typed_data
from fastmcp import FastMCP
from web3 import Web3

load_dotenv()

mcp = FastMCP("Institutional-Market-Levels-x402")
BASE_URL = "https://agent-paywall.onrender.com"


def call_x402_endpoint(path: str, payload: dict) -> dict:
    priv_key = os.getenv("BUYER_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
    if not priv_key:
        return {"error": "Set BUYER_PRIVATE_KEY in your environment to auto-pay x402 endpoints."}

    account = Account.from_key(priv_key.strip())
    url = f"{BASE_URL}{path}"
    client = httpx.Client(timeout=30.0)

    # Step 1: Request challenge
    res = client.post(url, json=payload)
    if res.status_code != 402:
        return res.json()

    terms = res.json()["accepts"][0]
    amount = int(terms["maxAmountRequired"])
    pay_to = terms["payTo"]
    asset = terms["asset"]
    network = terms.get("network", "base")

    # Step 2: Sign gasless EIP-3009 transfer on Base Mainnet (Chain ID 8453)
    chain_id = 8453 if network == "base" else 84532
    domain_name = "USD Coin" if network == "base" else "USDC"

    now = int(time.time())
    valid_after = now - 60
    valid_before = now + int(terms.get("maxTimeoutSeconds", 300))
    nonce = "0x" + secrets.token_hex(32)

    structured_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        },
        "primaryType": "TransferWithAuthorization",
        "domain": {
            "name": domain_name,
            "version": "2",
            "chainId": chain_id,
            "verifyingContract": Web3.to_checksum_address(asset),
        },
        "message": {
            "from": Web3.to_checksum_address(account.address),
            "to": Web3.to_checksum_address(pay_to),
            "value": amount,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": nonce,
        },
    }

    signed = account.sign_message(encode_typed_data(full_message=structured_data))
    sig_hex = signed.signature.hex()
    if not sig_hex.startswith("0x"):
        sig_hex = "0x" + sig_hex

    x_payment = base64.b64encode(
        json.dumps(
            {
                "x402Version": 1,
                "scheme": "exact",
                "network": network,
                "payload": {
                    "signature": sig_hex,
                    "authorization": {
                        "from": Web3.to_checksum_address(account.address),
                        "to": Web3.to_checksum_address(pay_to),
                        "value": str(amount),
                        "validAfter": str(valid_after),
                        "validBefore": str(valid_before),
                        "nonce": nonce,
                    },
                },
            }
        ).encode()
    ).decode()

    # Step 3: Settle and return data
    paid_res = client.post(url, json=payload, headers={"X-PAYMENT": x_payment})
    return paid_res.json()


@mcp.tool()
def get_institutional_levels(symbol: str = "BTCUSDT", interval: str = "1h") -> dict:
    """Fetches live Swing High/Low, Equilibrium, OTE, and Fair Value Gaps ($0.005 USDC)."""
    return call_x402_endpoint("/v1/calculate-levels", {"symbol": symbol, "interval": interval})


@mcp.tool()
def scan_multi_timeframe_confluence(symbol: str = "BTCUSDT") -> dict:
    """Scans 15m, 1h, and 4h institutional confluence, ATR stops, and FVGs ($0.05 USDC)."""
    return call_x402_endpoint("/v1/alpha-confluence", {"symbol": symbol})


@mcp.tool()
def audit_trading_strategy(code: str) -> dict:
    """Audits PineScript or Python strategy code for repainting and lookahead bias ($0.01 USDC)."""
    return call_x402_endpoint("/v1/audit-code", {"code": code})


if __name__ == "__main__":
    mcp.run()
