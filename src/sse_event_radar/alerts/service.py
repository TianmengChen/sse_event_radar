from loguru import logger

from sse_event_radar.alerts.models import Alert
from sse_event_radar.alerts.renderers import render_alert_markdown, render_alert_title
from sse_event_radar.config import settings
from sse_event_radar.notifiers.base import BaseNotifier
from sse_event_radar.notifiers.serverchan import ServerChanNotifier
from sse_event_radar.notifiers.feishu_bot import FeishuBotNotifier


class AlertService:
    def __init__(self, notifiers: list[BaseNotifier] | None = None):
        if notifiers is not None:
            self.notifiers = notifiers
        else:
            self.notifiers = self._build_default_notifiers()

    def _build_default_notifiers(self) -> list[BaseNotifier]:
        notifiers: list[BaseNotifier] = []

        if settings.enable_serverchan:
            notifiers.append(ServerChanNotifier())

        if settings.enable_feishu_bot:
            notifiers.append(FeishuBotNotifier())
            
        return notifiers

    def send_alert(self, alert: Alert) -> bool:
        if not self.notifiers:
            logger.warning("No notifier enabled. Alert will not be sent.")
            return False

        title = render_alert_title(alert)
        markdown = render_alert_markdown(alert)

        results = []
        for notifier in self.notifiers:
            ok = notifier.send_markdown(title=title, markdown=markdown)
            results.append(ok)

        return any(results)