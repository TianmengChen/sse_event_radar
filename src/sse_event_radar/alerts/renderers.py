from sse_event_radar.alerts.models import Alert


def render_alert_markdown(alert: Alert) -> str:
    lines: list[str] = []

    lines.append(f"# 【{alert.level} 级预警｜{alert.market}】")
    lines.append("")
    lines.append(f"**事件类型**：{alert.event_type}")
    lines.append(f"**方向**：{alert.direction}")
    lines.append(f"**时效**：{alert.time_horizon}")

    if alert.confidence is not None:
        lines.append(f"**可信度**：{alert.confidence:.2f}")

    lines.append("")
    lines.append("## 摘要")
    lines.append(alert.summary)

    if alert.related_stocks:
        lines.append("")
        lines.append("## 相关标的")
        for idx, stock in enumerate(alert.related_stocks, start=1):
            score = ""
            if stock.relevance_score is not None:
                score = f"｜相关性 {stock.relevance_score:.2f}"

            name = stock.name or ""
            reason = stock.reason or "暂无说明"

            lines.append(f"{idx}. **{stock.code} {name}**{score}")
            lines.append(f"   - {reason}")

    if alert.risk_flags:
        lines.append("")
        lines.append("## 风险提示")
        for flag in alert.risk_flags:
            lines.append(f"- {flag}")

    if alert.source:
        lines.append("")
        lines.append(f"**来源**：{alert.source}")

    if alert.source_url:
        lines.append("")
        lines.append(f"[查看原文]({alert.source_url})")

    lines.append("")
    lines.append("---")
    lines.append("本消息仅作事件监测和研究辅助，不构成投资建议，不自动触发交易。")

    return "\n".join(lines)


def render_alert_title(alert: Alert) -> str:
    return f"【{alert.level}级预警】{alert.title}"