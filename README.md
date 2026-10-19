# Institutional Levels & Strategy Auditor (x402 MCP Server)

Plug-and-play Model Context Protocol (MCP) server providing autonomous AI assistants with live institutional crypto/gold market structure analysis and static strategy security auditing on Base Mainnet via the x402 payment standard.

## Tools Included

- **`get_institutional_levels`** ($0.005 USDC): Fetches live OHLC candlesticks for crypto/gold pairs (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `PAXGUSDT`) and computes Swing High/Low, Equilibrium, and Fair Value Gaps (FVGs).
- **`scan_multi_timeframe_confluence`** ($0.050 USDC): Simultaneously analyzes 15m, 1h, and 4h structural alignment, ATR stop-loss sizing, and institutional discount zones.
- **`audit_trading_strategy`** ($0.010 USDC): Static security scanner for PineScript and Python trading scripts to catch repainting bugs, lookahead leaks, and missing risk parameters.

---

## Quick Setup

### 1. Install Dependencies

Clone this repository and install the required Python packages:

```bash
git clone [https://github.com/FX-Factor/institutional-levels-mcp.git](https://github.com/FX-Factor/institutional-levels-mcp.git)
cd institutional-levels-mcp
pip install fastmcp httpx web3 eth-account python-dotenv
```

### 2. Configuration for AI Clients (Claude Desktop, Cursor, Windsurf)

Add this entry to your client configuration file (e.g. `claude_desktop_config.json` or Cursor MCP settings):

```json
{
  "mcpServers": {
    "market-levels": {
      "command": "python",
      "args": ["C:/path/to/institutional-levels-mcp/mcp_server.py"],
      "env": {
        "BUYER_PRIVATE_KEY": "YOUR_BASE_WALLET_PRIVATE_KEY"
      }
    }
  }
}
```

*Note: The wallet configured under `BUYER_PRIVATE_KEY` only needs a small balance of Base USDC ($0.10–$1.00). Payments settle gaslessly on-chain via EIP-3009 transfer authorizations.*

---

## License

MIT License. Free for open-source AI agent integration.
