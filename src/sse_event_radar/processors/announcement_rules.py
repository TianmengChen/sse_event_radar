from typing import Any

import pandas as pd

from sse_event_radar.alerts.models import Alert, RelatedStock


POSITIVE_KEYWORDS = [
    "业绩预增",
    "预增",
    "扭亏",
    "中标",
    "重大合同",
    "合同",
    "订单",
    "回购",
    "增持",
    "战略合作",
]

NEGATIVE_KEYWORDS = [
    "业绩预减",
    "预减",
    "亏损",
    "减持",
    "监管函",
    "问询函",
    "立案",
    "处罚",
    "诉讼",
    "仲裁",
    "资产减值",
    "风险提示",
    "异常波动",
]

IMPORTANT_KEYWORDS = [
    "重大",
    "中标",
    "合同",
    "回购",
    "增持",
    "减持",
    "重组",
    "并购",
    "业绩预告",
    "业绩快报",
    "风险提示",
    "监管函",
    "问询函",
]


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


class AnnouncementRuleProcessor:
    def process_dataframe(self, df: pd.DataFrame) -> list[Alert]:
        alerts: list[Alert] = []

        for _, row in df.iterrows():
            alert = self.process_row(row.to_dict())
            if alert is not None:
                alerts.append(alert)

        return alerts

    def process_row(self, row: dict[str, Any]) -> Alert | None:
        code = safe_str(row.get("code"))
        name = safe_str(row.get("name"))
        title = safe_str(row.get("title"))
        ann_type = safe_str(row.get("ann_type"))
        ann_date = safe_str(row.get("ann_date"))
        url = safe_str(row.get("url"))

        if not title:
            return None

        matched_positive = [kw for kw in POSITIVE_KEYWORDS if kw in title]
        matched_negative = [kw for kw in NEGATIVE_KEYWORDS if kw in title]
        matched_important = [kw for kw in IMPORTANT_KEYWORDS if kw in title]

        if not matched_positive and not matched_negative and not matched_important:
            return None

        if matched_negative:
            level = "RISK"
            direction = "negative"
            confidence = 0.75
            risk_flags = [f"命中风险关键词：{', '.join(matched_negative)}"]
        elif matched_positive:
            level = "B"
            direction = "positive"
            confidence = 0.70
            risk_flags = ["规则初筛为潜在利好，仍需人工阅读公告原文确认。"]
        else:
            level = "C"
            direction = "uncertain"
            confidence = 0.55
            risk_flags = ["命中重要公告关键词，但方向不确定，需要人工确认。"]

        if direction == "positive" and any(kw in title for kw in ["重大", "中标", "业绩预增", "回购"]):
            level = "A"

        if any(kw in title for kw in ["减持", "立案", "处罚", "监管函"]):
            level = "RISK"

        summary = f"{code} {name} 发布公告：{title}"

        if ann_type:
            summary += f"\n公告类型：{ann_type}"

        if ann_date:
            summary += f"\n公告日期：{ann_date}"

        related_stocks = []
        if code:
            related_stocks.append(
                RelatedStock(
                    code=code,
                    name=name or None,
                    reason="公告直接关联该上市公司。",
                    relevance_score=1.0,
                )
            )

        return Alert(
            level=level,
            title=title,
            summary=summary,
            direction=direction,
            market="SSE",
            event_type="announcement",
            time_horizon="1-5 trading days",
            source="AKShare announcement",
            source_url=url or None,
            related_stocks=related_stocks,
            risk_flags=risk_flags,
            confidence=confidence,
        )