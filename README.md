# AI Trading Analysis — Trading With Sasiya

Full-stack educational crypto market-analysis starter: Next.js + React + TypeScript + Tailwind + Lightweight Charts frontend, FastAPI analysis backend, Binance public REST/WebSocket market data, optional CoinMarketCap market-cap rankings, and Binance USD-M Futures positioning statistics.

## Run locally

Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend (second terminal):
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Open http://localhost:3000.

Set `CMC_API_KEY` in `backend/.env` for CoinMarketCap ranking/market-cap enrichment. Never expose it in frontend code. Configure `NEXT_PUBLIC_API_BASE_URL` for deployment.

## API
- GET /health
- GET /api/markets?quote=USDT&limit=500
- GET /api/market/{symbol}
- GET /api/klines/{symbol}?interval=1h&limit=500
- GET /api/analyze/{symbol}?interval=1h
- GET /api/positioning/{symbol}

Supported analysis intervals: 15m, 1h, 4h, 1d, 1w.

## Important
This is a rule-based educational analysis and paper-trading platform, not a hosted generative AI model or a guarantee of profitable signals. It does not execute real orders or connect to exchange accounts. SMC/ICT, order-block and liquidity labels are simplified OHLCV-derived proxies, not verified institutional order flow. Entry/SL/TP are hypothetical study levels; unclear conditions return NO TRADE.

Binance public APIs can be rate-limited or regionally unavailable. CoinMarketCap enrichment requires an API key; otherwise rank/market cap are unavailable. Symbol matching can be ambiguous. This starter does not include accounts, PostgreSQL/Redis, historical backtesting storage, or production rate limiting. Add HTTPS, monitoring, rate limiting, and infrastructure before public deployment.
