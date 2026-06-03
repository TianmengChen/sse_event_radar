import math
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from loguru import logger

from sse_event_radar.collectors.base import BaseCollector
from sse_event_radar.network import get_requests_proxies


class SSEQuoteCollector(BaseCollector):
    source_name = "eastmoney_push2_sse_spot"

    def __init__(
        self,
        page_size: int = 100,
        sleep_seconds: float = 0.05,
        max_pages: int | None = None,
    ):
        self.page_size = page_size
        self.sleep_seconds = sleep_seconds
        self.max_pages = max_pages

    @staticmethod
    def _clean_value(value: Any):
        if value in ("-", "", None):
            return None
        return value

    def _fetch_page(self, page: int) -> dict:
        url = "https://82.push2.eastmoney.com/api/qt/clist/get"

        params = {
            "pn": page,
            "pz": self.page_size,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": "f12",
            # Shanghai main board + STAR Market
            "fs": "m:1 t:2,m:1 t:23",
            # Keep fields minimal to reduce proxy/protocol issues
            "fields": "f12,f14,f2,f3,f5,f6,f8,f22",
        }

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://quote.eastmoney.com/",
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            proxies=get_requests_proxies(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def collect(self) -> pd.DataFrame:
        first = self._fetch_page(1)

        if first.get("rc") != 0:
            raise RuntimeError(f"Eastmoney API error: {first}")

        data = first.get("data") or {}
        total = int(data.get("total") or 0)
        diff = data.get("diff") or []

        if total <= 0:
            return pd.DataFrame(
                columns=[
                    "code",
                    "name",
                    "price",
                    "pct_chg",
                    "volume",
                    "amount",
                    "turnover",
                    "speed",
                    "pct_5min",
                    "source",
                    "fetched_at",
                ]
            )

        total_pages = math.ceil(total / self.page_size)

        if self.max_pages is not None:
            total_pages = min(total_pages, self.max_pages)

        rows = list(diff)

        logger.info(f"Eastmoney total={total}, page_size={self.page_size}, pages={total_pages}")

        for page in range(2, total_pages + 1):
            time.sleep(self.sleep_seconds)
            page_data = self._fetch_page(page)
            if page_data.get("rc") != 0:
                logger.warning(f"Skip page {page}, rc={page_data.get('rc')}")
                continue

            page_diff = (page_data.get("data") or {}).get("diff") or []
            rows.extend(page_diff)

        now = datetime.utcnow().isoformat()

        normalized = []
        for item in rows:
            normalized.append(
                {
                    "code": str(item.get("f12", "")).zfill(6),
                    "name": item.get("f14"),
                    "price": self._clean_value(item.get("f2")),
                    "pct_chg": self._clean_value(item.get("f3")),
                    "volume": self._clean_value(item.get("f5")),
                    "amount": self._clean_value(item.get("f6")),
                    "turnover": self._clean_value(item.get("f8")),
                    "speed": self._clean_value(item.get("f22")),
                    "pct_5min": None,
                    "source": self.source_name,
                    "fetched_at": now,
                }
            )

        df = pd.DataFrame(normalized)
        df = df.drop_duplicates("code")
        return df