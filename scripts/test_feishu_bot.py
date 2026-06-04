from sse_event_radar.alerts.models import Alert, RelatedStock
from sse_event_radar.alerts.service import AlertService
from sse_event_radar.logging import setup_logging
from sse_event_radar.network import configure_proxy


def main() -> None:
    setup_logging()
    configure_proxy()

    alert = Alert(
        level="INFO",
        title="飞书 Bot 通知通道测试",
        summary="这是一条来自 SSE Event Radar 的飞书测试消息。如果你在飞书群里收到，说明飞书通知通道已经打通。",
        direction="neutral",
        event_type="system_test",
        time_horizon="none",
        confidence=1.0,
        source="local_test",
        related_stocks=[
            RelatedStock(
                code="600000",
                name="浦发银行",
                reason="测试用示例股票，不代表任何投资建议。",
                relevance_score=0.1,
            )
        ],
        risk_flags=[
            "这是一条测试消息。",
            "不构成投资建议。",
            "不会触发自动交易。",
        ],
    )

    ok = AlertService().send_alert(alert)
    print("send result:", ok)


if __name__ == "__main__":
    main()