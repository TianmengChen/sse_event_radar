from dataclasses import dataclass
from typing import Literal

import pandas as pd

from sse_event_radar.alerts.models import Alert, RelatedStock


SignalAction = Literal["BUY_SETUP", "WATCH", "AVOID", "RISK"]


@dataclass
class BuySignalResult:
    action: SignalAction
    level: str
    reason: str
    risk_flags: list[str]
    confidence: float


class BuySignalRuleProcessor:
    def __init__(
        self,
        min_pct_chg: float = 1.0,
        max_pct_chg_main: float = 6.0,
        max_pct_chg_star: float = 12.0,
        max_pct_chg_etf: float = 5.0,
        min_amount: float = 100_000_000,
    ):
        self.min_pct_chg = min_pct_chg
        self.max_pct_chg_main = max_pct_chg_main
        self.max_pct_chg_star = max_pct_chg_star
        self.max_pct_chg_etf = max_pct_chg_etf
        self.min_amount = min_amount

    def evaluate_quote(self, quote: dict) -> BuySignalResult:
        code = str(quote.get("code", "")).zfill(6)
        name = quote.get("name") or ""

        pct_chg = self._to_float(quote.get("pct_chg"))
        amount = self._to_float(quote.get("amount"))
        price = self._to_float(quote.get("price"))
        speed = self._to_float(quote.get("speed"))

        is_star = code.startswith(("688", "689"))
        is_etf = code.startswith(("510", "511", "512", "513", "515", "516", "517", "518", "588"))

        if is_etf:
            max_pct_chg = self.max_pct_chg_etf
            near_limit_threshold = 8.0
        elif is_star:
            max_pct_chg = self.max_pct_chg_star
            near_limit_threshold = 15.0
        else:
            max_pct_chg = self.max_pct_chg_main
            near_limit_threshold = 8.0

        risk_flags = []

        if pct_chg is None:
            return BuySignalResult(
                action="WATCH",
                level="INFO",
                reason=f"{code} {name} 缺少涨跌幅数据。",
                risk_flags=["数据不完整。"],
                confidence=0.2,
            )

        if amount is None:
            amount = 0

        if pct_chg >= near_limit_threshold:
            return BuySignalResult(
                action="AVOID",
                level="RISK",
                reason=f"{code} {name} 涨幅 {pct_chg:.2f}%，接近涨停/高位，不适合追。",
                risk_flags=["追高风险", "可能买入位置过高"],
                confidence=0.75,
            )

        if amount < self.min_amount:
            return BuySignalResult(
                action="WATCH",
                level="C",
                reason=f"{code} {name} 成交额不足，暂不触发买入候选。",
                risk_flags=["流动性不足"],
                confidence=0.45,
            )

        if pct_chg < self.min_pct_chg:
            return BuySignalResult(
                action="WATCH",
                level="INFO",
                reason=f"{code} {name} 涨幅不足，暂未出现强势信号。",
                risk_flags=[],
                confidence=0.35,
            )

        if pct_chg > max_pct_chg:
            return BuySignalResult(
                action="AVOID",
                level="C",
                reason=f"{code} {name} 今日涨幅 {pct_chg:.2f}% 已偏高，等待回落或次日确认。",
                risk_flags=["短线追高风险"],
                confidence=0.65,
            )

        if speed is not None and speed < -1:
            return BuySignalResult(
                action="WATCH",
                level="C",
                reason=f"{code} {name} 当前涨速转弱，暂不触发买入候选。",
                risk_flags=["盘中动能转弱"],
                confidence=0.5,
            )

        return BuySignalResult(
            action="BUY_SETUP",
            level="B",
            reason=(
                f"{code} {name} 出现买入候选：涨幅 {pct_chg:.2f}%，"
                f"成交额约 {amount / 100000000:.2f} 亿，未进入明显追高区间。"
            ),
            risk_flags=[
                "这只是买入候选，不是自动买入指令。",
                "需要人工确认大盘环境、板块强度和分时走势。",
            ],
            confidence=0.65,
        )

    def build_alert(self, quote: dict, result: BuySignalResult) -> Alert | None:
        if result.action != "BUY_SETUP":
            return None

        code = str(quote.get("code", "")).zfill(6)
        name = quote.get("name") or ""
        pct_chg = self._to_float(quote.get("pct_chg"))
        price = self._to_float(quote.get("price"))
        amount = self._to_float(quote.get("amount"))

        summary = result.reason

        if price is not None:
            summary += f"\n当前价格：{price}"

        if pct_chg is not None:
            summary += f"\n当前涨幅：{pct_chg:.2f}%"

        if amount is not None:
            summary += f"\n当前成交额：{amount / 100000000:.2f} 亿"

        return Alert(
            level=result.level,
            title=f"{code} {name} 出现买入候选",
            summary=summary,
            direction="positive",
            market="SSE",
            event_type="buy_signal",
            time_horizon="intraday / 1-3 trading days",
            source="quote_rule",
            related_stocks=[
                RelatedStock(
                    code=code,
                    name=name,
                    reason=result.reason,
                    relevance_score=result.confidence,
                )
            ],
            risk_flags=result.risk_flags,
            confidence=result.confidence,
        )

    @staticmethod
    def _to_float(value):
        if value in (None, "", "-"):
            return None
        try:
            return float(value)
        except Exception:
            return None