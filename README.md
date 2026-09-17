# Crypto Pulse — Real-Time Market Anomaly Radar

A self-hosted pipeline that ingests live crypto prices, learns a rolling
statistical baseline per asset, flags anomalies in real time, and streams
everything to a live dashboard.

## Problem statement

Retail-facing price trackers show *what* the price is right now, but not
*whether that's unusual*. Crypto Pulse ingests live price data for a basket
of assets, computes a rolling statistical baseline per asset, flags
statistically significant deviations as they happen, and pushes live
updates plus anomaly events to a dashboard over WebSocket.

## Architecture

```
Data sources -> Ingestion layer -> Storage layer -> Analytics layer -> API layer (REST + WebSocket) -> Live dashboard
```

- **Ingestion**: scheduled, async polling of a public crypto price API
- **Storage**: PostgreSQL (raw ticks, aggregated bars, computed metrics)
- **Analytics**: rolling mean/stddev, z-score anomaly detection, short-horizon forecasting
- **API**: FastAPI — REST for historical queries, WebSocket for live pushes
- **Dashboard**: live-updating charts consuming the WebSocket feed

## Phase roadmap

| Phase | Name                                    | Status         |
|-------|------------------------------------------|----------------|
| 0     | Project setup + git workflow             | In progress    |
| 1     | Ingestion (live price fetching)          | Not started    |
| 2     | Storage layer (Postgres + models)        | Not started    |
| 3     | Analytics layer (stats + anomalies)      | Not started    |
| 4     | REST API                                 | Not started    |
| 5     | WebSocket + live dashboard               | Not started    |
| 6     | Forecasting (stretch)                    | Not started    |
| 7     | Docker, tests, CI, deploy                | Not started    |

We build one phase at a time and don't start the next until both
contributors understand and have reviewed the current one.

## Team & workflow

- Every phase splits into two sub-tasks, one per person, each built on its
  own branch and merged into `main` via a reviewed pull request.
- Branch naming: `<yourname>/phase<N>-<short-description>`, e.g.
  `arjun/phase1-fetcher`.
- Full git command reference and first-time setup: see
  [`docs/GIT_GUIDE.md`](docs/GIT_GUIDE.md).
- First-time contributor? See [`CONTRIBUTORS.md`](CONTRIBUTORS.md) for your
  practice exercise before touching real code.

## Getting started

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`requirements.txt` starts empty — dependencies are added phase by phase, as
each one is actually needed.

## Project structure

```
crypto-pulse/
├── app/
│   ├── ingestion/    # Phase 1
│   ├── storage/      # Phase 2
│   ├── analytics/    # Phase 3
│   ├── api/          # Phase 4 + 5
│   └── dashboard/    # Phase 5
├── tests/
└── docs/
    └── GIT_GUIDE.md
```
