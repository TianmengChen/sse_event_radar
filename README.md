# SSE Event Radar

上证市场事件雷达 / 短线预警助手。

当前阶段：**MVP 数据采集层 + 通知模块基础版**。

本项目用于监测上证市场相关的：

- 实时行情
- 公司公告
- 政策 / 新闻事件
- 个股 / 板块异动
- 事件预警推送

系统只做事件监测、风险提示、观察池生成，不做自动下单，也不提供确定性买卖建议。

---

## 1. Project Goal

SSE Event Radar is a local-first A-share event monitoring project focused on the Shanghai Stock Exchange market.

The first-stage goal is to build a stable data collector based on AKShare / Eastmoney-compatible public data sources, then gradually add:

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
- Requests
- Server 酱 Turbo notification

Later stages may add:

- Redis
- PostgreSQL
- React / Vite dashboard
- Telegram notification
- PushPlus / WxPusher notification
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
│   ├── smoke_test_akshare.py
│   └── test_serverchan.py
├── src/
│   └── sse_event_radar/
│       ├── __init__.py
│       ├── alerts/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── renderers.py
│       │   └── service.py
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
│       ├── network.py
│       ├── notifiers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── serverchan.py
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

## 5. Environment Configuration

Edit `.env`.

Example without proxy:

```env
APP_NAME=sse-event-radar
APP_ENV=dev
LOG_LEVEL=INFO

DATA_DIR=./data
DATABASE_URL=sqlite:///./data/db/sse_event_radar.sqlite3

QUOTE_POLL_SECONDS=60
ANNOUNCEMENT_POLL_MINUTES=5
STOCK_MASTER_REFRESH_HOUR=17

AKSHARE_RATE_LIMIT_SECONDS=3

PROXY_ENABLED=false
PROXY_URL=
NO_PROXY=localhost,127.0.0.1,::1

ENABLE_SERVERCHAN=false
SERVERCHAN_SENDKEY=

ENABLE_LLM=false
OPENAI_API_KEY=
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

Example with proxy:

```env
PROXY_ENABLED=true
PROXY_URL=http://your-proxy-host:your-proxy-port
NO_PROXY=localhost,127.0.0.1,::1
```

When `PROXY_ENABLED=false`, the project should not use a proxy.  
When `PROXY_ENABLED=true`, collectors and notifiers will use `PROXY_URL`.

---

## 6. Smoke Test

Run collector smoke test:

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

## 7. Run API

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

## 8. Current Collectors

### StockMasterCollector

Current source:

```text
Eastmoney push2 SSE quote endpoint
```

Purpose:

- collect Shanghai-listed stock code and name
- avoid unrelated BSE data requests
- classify main board and STAR Market by code prefix

Current SSE prefixes:

```text
600 / 601 / 603 / 605 / 688 / 689
```

---

### SSEQuoteCollector

Current source:

```text
Eastmoney push2 SSE quote endpoint
```

Purpose:

- collect Shanghai A-share quote snapshot
- normalize fields such as price, percentage change, volume, amount, turnover and speed
- support smaller page size and `max_pages` for smoke tests

---

### AnnouncementCollector

Current source:

```text
AKShare stock_notice_report
```

Purpose:

- collect recent A-share announcement records
- filter Shanghai-listed stocks
- normalize announcement title, stock code, date, type and URL

---

## 9. Notification: Server 酱 Turbo

First version uses Server 酱 Turbo for personal WeChat notification.

### 9.1 Configure Server 酱

Set the following variables in `.env`:

```env
ENABLE_SERVERCHAN=true
SERVERCHAN_SENDKEY=your_sendkey_here
```

`SERVERCHAN_SENDKEY` is your personal Server 酱 SendKey.  
Do not commit `.env`.

### 9.2 Test Server 酱

Run:

```bash
python scripts/test_serverchan.py
```

If configured correctly, your bound WeChat account should receive a test notification.

### 9.3 Current notification flow

```text
Alert
  ↓
render_alert_markdown()
  ↓
AlertService
  ↓
ServerChanNotifier
  ↓
Server 酱 API
  ↓
personal WeChat notification
```

### 9.4 Important note

Server 酱 first version sends messages to the WeChat account bound to the SendKey.

It does not directly send messages to arbitrary WeChat friends.

For multi-user delivery, each user should have their own channel binding, or the project should later implement a user-channel mapping system.

---

## 10. Development Commands

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

Run collector smoke test:

```bash
make smoke
```

Start API:

```bash
make api
```

---

## 11. Roadmap

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

### Phase 2: Alert and Notification

- [x] Add Alert model
- [x] Add Markdown alert renderer
- [x] Add AlertService
- [x] Add ServerChanNotifier
- [x] Add Server 酱 test script
- [ ] Add alert history table
- [ ] Add alert deduplication
- [ ] Add notification rate limit

### Phase 3: Event Processing

- [ ] Announcement keyword classification
- [ ] Positive / negative / neutral event tags
- [ ] Risk keyword detection
- [ ] Stock-event mapping
- [ ] Market confirmation using quote data

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

## 12. Safety Notes

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

## 13. License

To be decided.