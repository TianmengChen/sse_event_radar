from fastapi import FastAPI

from sse_event_radar.db.session import init_db
from sse_event_radar.logging import setup_logging

setup_logging()
init_db()

app = FastAPI(title="SSE Event Radar", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "sse-event-radar"}


@app.get("/")
def root():
    return {
        "message": "SSE Event Radar API",
        "stage": "MVP data collector",
        "docs": "/docs",
    }
