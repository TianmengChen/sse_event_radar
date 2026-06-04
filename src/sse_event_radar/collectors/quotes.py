import math
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from loguru import logger

from sse_event_radar.network import get_requests_proxies


EASTMONEY_SINGLE_QUOTE_HOSTS = [
    "https://push2.eastmoney.com/api/qt/stock/get",
    "https://82.push2.eastmoney.com/api/qt/stock/get",
    "https://83.push2.eastmoney.com/api/qt/stock/get",
    "https://84.push2.eastmoney.com/api/qt/stock/get",
]


def eastmoney_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://quote.eastmoney.com/",
        "Connection": "close",
    }


def request_json_with_retry(
    hosts: list[str],
    params: dict[str, Any],
    page_label: str,
    timeout: int = 30,
) -> dict:
    last_exc: Exception | None = None

    for url in hosts:
        try:
            with requests.Session() as session:
                session.trust_env = False

                response = session.get(
                    url,
                    params=params,
                    headers=eastmoney_headers(),
                    proxies=get_requests_proxies(),
                    timeout=timeout,
                )

                response.raise_for_status()
                return response.json()

        except Exception as exc:
            last_exc = exc
            logger.warning(f"Eastmoney request {page_label} failed on {url}: {exc}")
            time.sleep(1.0)

    raise RuntimeError(f"All Eastmoney hosts failed for {page_label}: {last_exc}")


def to_float(value: Any) -> float | None:
    if value in ("-", "", None):
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    try:
        result = float(value)
    except Exception:
        return None

    if math.isnan(result) or math.isinf(result):
        return None

    return result


def eastmoney_price_value(value: Any) -> float | None:
    result = to_float(value)

    if result is None:
        return None

    # Eastmoney single quote sometimes returns price * 100.
    if abs(result) > 1000:
        return result / 100

    return result


def is_etf_code(code: str) -> bool:
    return code.startswith(
        (
            "510",
            "511",
            "512",
            "513",
            "515",
            "516",
            "517",
            "518",
            "588",
            "589",
        )
    )


def fetch_single_quote(code: str) -> dict:
    """
    Fetch one Shanghai stock/ETF quote by code.

    This is the only quote function needed for watchlist mode.
    """
    code = str(code).zfill(6)
    secid = f"1.{code}"  # 1.xxxxxx means Shanghai in Eastmoney secid format.

    params = {
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "secid": secid,
        "fields": "f43,f57,f58,f169,f170,f47,f48,f168,f46,f44,f45,f60",
    }

    payload = request_json_with_retry(
        hosts=EASTMONEY_SINGLE_QUOTE_HOSTS,
        params=params,
        page_label=f"single quote {code}",
    )

    if payload.get("rc") != 0:
        raise RuntimeError(f"Eastmoney single quote API error for {code}: {payload}")

    data = payload.get("data") or {}
    security_type = "etf" if is_etf_code(code) else "stock"

    return {
        "code": code,
        "name": data.get("f58") or data.get("f57"),
        "price": eastmoney_price_value(data.get("f43")),
        "pct_chg": to_float(data.get("f170")),
        "volume": to_float(data.get("f47")),
        "amount": to_float(data.get("f48")),
        "turnover": to_float(data.get("f168")),
        "speed": None,
        "pct_5min": None,
        "security_type": security_type,
        "source": "eastmoney_single_quote",
        "fetched_at": datetime.utcnow().isoformat(),
    }