from datetime import datetime

import akshare as ak
import pandas as pd

from sse_event_radar.collectors.base import BaseCollector


SSE_A_PREFIXES = ("600", "601", "603", "605", "688", "689")


class AnnouncementCollector(BaseCollector):
    source_name = "akshare_stock_notice_report"

    def __init__(self, symbol: str = "全部", date: str | None = None):
        self.symbol = symbol
        self.date = date or datetime.now().strftime("%Y%m%d")

    def collect(self) -> pd.DataFrame:
        df = ak.stock_notice_report(symbol=self.symbol, date=self.date)

        column_map = {
            "代码": "code",
            "名称": "name",
            "公告标题": "title",
            "公告类型": "ann_type",
            "公告日期": "ann_date",
            "网址": "url",
        }

        df = df.rename(columns=column_map)

        required = ["code", "title"]
        for col in required:
            if col not in df.columns:
                raise RuntimeError(f"Unexpected columns from AKShare stock_notice_report: {df.columns}")

        for col in ["name", "ann_type", "ann_date", "url"]:
            if col not in df.columns:
                df[col] = None

        df["code"] = df["code"].astype(str).str.zfill(6)
        df = df[df["code"].str.startswith(SSE_A_PREFIXES)].copy()
        df["source"] = self.source_name
        df["fetched_at"] = datetime.utcnow().isoformat()

        return df[["code", "name", "title", "ann_type", "ann_date", "url", "source", "fetched_at"]]