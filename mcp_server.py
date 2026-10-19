import os
import sys
import time
import secrets
import json
import base64
import httpx
from typing import Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

load_dotenv()

# Initialize MCP Server
mcp = FastMCP("Institutional Market Structure & Auditor")

API_BASE_URL = os.getenv("API_BASE_URL", "https://agent-paywall.onrender.com")
BUYER_PRIVATE_KEY = os.getenv("BUYER_PRIVATE_KEY")


def get_buyer_account() -> Optional[Account]:
    if not BUYER_PRIVATE_KEY:
        return None
    key = BUYER_PRIVATE_KEY.strip().strip('"').strip("'")
    if not key.startswith("0x"):
        key = "0x" + key
    try:
        return Account.from_key(key)
    except Exception:
        return None


def execute_x402_call(endpoint_path: str, payload: dict) -> dict:
    """Executes an automated x402 payment flow against the Render microservice."""
    buyer_account = get_buyer_account()
    if not buyer_account:
        return {
            "error": "BUYER_PRIVATE_KEY is missing or invalid in environment. Configure your Base wallet private key."
        }

    target_url = f"{API_BASE_URL.rstrip('/')}{endpoint_path}"

    with httpx.Client(timeout=45.0) as client:
        # 1. Probe for 402 challenge
        probe = client.post(target_url, json=payload)
        if probe.status_code == 200:
            return probe.json()

        if probe.status_code != 402:
            return {
                "error": f"API returned unexpected HTTP {probe.status_code}",
                "detail": probe.text
            }

        challenge = probe.json()
        accepts = challenge.get("accepts", [{}])[0]

        pay_to = accepts.get("payTo")
        amount = int(accepts.get("maxAmountRequired", "5000"))
        token_address = accepts.get("asset", "0x833589fCD6eDb6E08f4c7C32D4f71b54bda02913")
        extra = accepts.get("extra", {})

        domain_name = extra.get("name", "USD Coin")
        domain_version = extra.get("version", "2")
        chain_id = 8453  # Base Mainnet

        # 2. Sign EIP-3009 TransferWithAuthorization
        valid_after = int(time.time()) - 60
        valid_before = int(time.time()) + 300
        nonce = "0x" + secrets.token_hex(32)

        typed_data = {
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
                "version": domain_version,
                "chainId": chain_id,
                "verifyingContract": Web3.to_checksum_address(token_address),
            },
            "message": {
                "from": Web3.to_checksum_address(buyer_account.address),
                "to": Web3.to_checksum_address(pay_to),
                "value": amount,
                "validAfter": valid_after,
                "validBefore": valid_before,
                "nonce": nonce,
            },
        }

        signable = encode_typed_data(full_message=typed_data)
        signed = buyer_account.sign_message(signable)
        sig_hex = signed.signature.hex()
        if not sig_hex.startswith("0x"):
            sig_hex = "0x" + sig_hex

        payment_payload = {
            "x402Version": 1,
            "scheme": "exact",
            "network": "base",
            "payload": {
                "signature": sig_hex,
                "authorization": {
                    "from": Web3.to_checksum_address(buyer_account.address),
                    "to": Web3.to_checksum_address(pay_to),
                    "value": str(amount),
                    "validAfter": str(valid_after),
                    "validBefore": str(valid_before),
                    "nonce": nonce,
                    "v": signed.v,
                    "r": Web3.to_hex(signed.r),
                    "s": Web3.to_hex(signed.s),
                }
            }
        }

        x_payment_header = base64.b64encode(json.dumps(payment_payload).encode()).decode()

        # 3. Submit payment header and fetch payload
        response = client.post(
            target_url,
            json=payload,
            headers={"X-PAYMENT": x_payment_header}
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": f"Payment settlement failed with HTTP {response.status_code}",
            "response": response.text
        }


@mcp.tool()
def get_institutional_levels(symbol: str = "BTCUSDT", timeframe: str = "1h") -> dict:
    """Fetch live crypto/gold institutional levels (Swing High, Swing Low, Equilibrium, FVGs) for $0.005 USDC."""
    return execute_x402_call("/v1/calculate-levels", {"symbol": symbol, "timeframe": timeframe})


@mcp.tool()
def scan_multi_timeframe_confluence(symbol: str = "BTCUSDT") -> dict:
    """Multi-timeframe 15m/1h structure scan, ATR volatility stop sizing, and discount regime for $0.050 USDC."""
    return execute_x402_call("/v1/alpha-confluence", {"symbol": symbol})


@mcp.tool()
def audit_trading_strategy(code: str, language: str = "python") -> dict:
    """Static security and repainting audit for PineScript or Python algorithmic strategies for $0.010 USDC."""
    return execute_x402_call("/v1/audit-code", {"code": code, "language": language})


if __name__ == "__main__":
    mcp.run()
