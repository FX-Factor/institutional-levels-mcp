# Institutional Levels & Trading Strategy Auditor (x402 MCP Server)

Plug-and-play Model Context Protocol (MCP) server providing autonomous AI assistants with live institutional crypto/gold market structure analysis and static strategy security auditing on Base Mainnet via the x402 payment standard.

## Tools Included

- **`get_institutional_levels`** ($0.005 USDC): Fetches live OHLC candlesticks for any crypto/gold pair (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `PAXGUSDT`) and computes Swing High/Low, Equilibrium, and Fair Value Gaps (FVGs).
- **`scan_multi_timeframe_confluence`** ($0.050 USDC): Simultaneously analyzes 15m, 1h, and 4h structural alignment, ATR stop-loss volatility sizing, and institutional discount zones.
- **`audit_trading_strategy`** ($0.010 USDC): Static security scanner for PineScript and Python trading scripts to catch repainting bugs, lookahead leaks, and missing risk parameters.

---

## Quick Setup

### 1. Install Dependencies

Clone this repository and install the required Python packages:

```bash
git clone [https://github.com/FX-Factor/institutional-levels-mcp.git](https://github.com/FX-Factor/institutional-levels-mcp.git)
cd institutional-levels-mcp
pip install fastmcp httpx web3 eth-account python-dotenv
