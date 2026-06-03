# SSE Event Radar

上证市场事件雷达 / 短线预警助手。

当前阶段：**MVP 数据采集层**。

本项目用于监测上证市场相关的：

- 实时行情
- 公司公告
- 政策 / 新闻事件
- 个股 / 板块异动

系统只做事件监测、风险提示、观察池生成，不做自动下单，也不提供确定性买卖建议。

---

## 1. Project Goal

SSE Event Radar is a local-first A-share event monitoring project focused on the Shanghai Stock Exchange market.

The first-stage goal is to build a stable data collector based on AKShare, then gradually add:

- announcement classification
- event extraction
- stock mapping
- volume / price anomaly detection
- alert ranking
- notification delivery
- optional LLM-based event explanation

The system is designed as a decision-support tool, not an automated trading bot.

---

## 2. Current Stack

- Python 3.10+
- AKShare
- Pandas
- FastAPI
- SQLite
- SQLAlchemy
- APScheduler
- Loguru

Later stages may add:

- Redis
- PostgreSQL
- React / Vite dashboard
- Telegram / WeChat notification
- local LLM via Ollama / vLLM
- OpenAI-compatible API for event reasoning

---

## 3. Project Layout

```text
sse-event-radar/
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── pyproject.toml
├── data/
│   ├── db/
│   ├── processed/
│   └── raw/
├── docs/
├── logs/
├── scripts/
│   └── smoke_test_akshare.py
├── src/
│   └── sse_event_radar/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── app.py
│       ├── collectors/
│       │   ├── __init__.py
│       │   ├── announcements.py
│       │   ├── base.py
│       │   ├── quotes.py
│       │   └── stock_master.py
│       ├── config.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── session.py
│       ├── logging.py
│       ├── notifiers/
│       ├── processors/
│       └── services/
└── tests/
    └── test_imports.py
```

---

## 4. Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

Create local environment file:

```bash
cp .env.example .env
```

---

## 5. Smoke Test

Run AKShare collector smoke test:

```bash
python scripts/smoke_test_akshare.py
```

Or use Makefile:

```bash
make smoke
```

Expected output files:

```text
data/raw/stock_master_sample.csv
data/raw/sse_quotes_sample.csv
data/raw/announcements_sample.csv
```

---

## 6. Run API

Start FastAPI development server:

```bash
uvicorn sse_event_radar.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Or:

```bash
make api
```

Check health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "sse-event-radar"
}
```

API docs:

```text
http://127.0.0.1:8000/docs
```

---

## 7. Current Collectors

### StockMasterCollector

Source:

```text
AKShare stock_info_a_code_name
```

Purpose:

- collect A-share stock code and name
- filter Shanghai-listed stocks
- classify main board and STAR Market by code prefix

Current SSE prefixes:

```text
600 / 601 / 603 / 605 / 688 / 689
```

---

### SSEQuoteCollector

Source:

```text
AKShare stock_sh_a_spot_em
```

Purpose:

- collect Shanghai A-share real-time quote snapshot
- normalize fields such as price, percentage change, volume, amount, turnover, speed, 5-minute change

---

### AnnouncementCollector

Source:

```text
AKShare stock_notice_report
```

Purpose:

- collect recent A-share announcement records
- filter Shanghai-listed stocks
- normalize announcement title, stock code, date, type and URL

---

## 8. Development Commands

Install dependencies:

```bash
make install
```

Create local `.env`:

```bash
make dev
```

Run tests:

```bash
make test
```

Run lint:

```bash
make lint
```

Format code:

```bash
make format
```

Run AKShare smoke test:

```bash
make smoke
```

Start API:

```bash
make api
```

---

## 9. Roadmap

### Phase 1: Data Collector

- [x] Initialize repo
- [x] Add AKShare dependency
- [x] Add stock master collector
- [x] Add quote collector
- [x] Add announcement collector
- [x] Add smoke test
- [x] Add FastAPI health endpoint
- [ ] Save collector results into SQLite
- [ ] Add collector scheduler
- [ ] Add raw data persistence
- [ ] Add deduplication

### Phase 2: Event Processing

- [ ] Announcement keyword classification
- [ ] Positive / negative / neutral event tags
- [ ] Risk keyword detection
- [ ] Stock-event mapping
- [ ] Market confirmation using quote data

### Phase 3: Alert System

- [ ] Alert score
- [ ] A / B / C alert levels
- [ ] Watchlist generation
- [ ] Telegram notification
- [ ] WeChat / email notification

### Phase 4: LLM Integration

- [ ] Structured event extraction
- [ ] Announcement summarization
- [ ] Risk explanation
- [ ] Local model support
- [ ] OpenAI-compatible API support

### Phase 5: Dashboard

- [ ] Watchlist page
- [ ] Alert history page
- [ ] Announcement monitor
- [ ] Market anomaly view
- [ ] Backtest result view

---

## 10. Safety Notes

This project is for research and decision support only.

It does not:

- execute trades automatically
- provide guaranteed trading signals
- provide financial advice
- promise profit
- replace human decision-making

The recommended workflow is:

```text
collect data
    ↓
detect event
    ↓
score alert
    ↓
send warning
    ↓
human review
    ↓
manual decision
```

---

## 11. License

To be decided.