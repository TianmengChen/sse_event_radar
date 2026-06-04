import base64
import hashlib
import hmac
import time

import requests
from loguru import logger

from sse_event_radar.config import settings
from sse_event_radar.network import get_requests_proxies
from sse_event_radar.notifiers.base import BaseNotifier


class FeishuBotNotifier(BaseNotifier):
    """
    Feishu custom bot notifier.

    It sends alert messages to a Feishu group chat via custom bot webhook.

    Supports:
    - text message
    - post/rich-text message
    - optional signature verification
    """

    def __init__(
        self,
        webhook: str | None = None,
        secret: str | None = None,
    ):
        self.webhook = webhook or settings.feishu_bot_webhook
        self.secret = secret or settings.feishu_bot_secret

        if not self.webhook:
            raise RuntimeError("FEISHU_BOT_WEBHOOK is empty.")

    def send_text(self, title: str, text: str) -> bool:
        content = f"{title}\n\n{text}"

        payload = {
            "msg_type": "text",
            "content": {
                "text": content,
            },
        }

        self._add_signature(payload)
        return self._post(payload)

    def send_markdown(self, title: str, markdown: str) -> bool:
        # 飞书自定义机器人不直接用 Markdown 字段；
        # 这里先用 text 发送，保证第一版简单稳定。
        content = f"{title}\n\n{markdown}"

        payload = {
            "msg_type": "text",
            "content": {
                "text": content,
            },
        }

        self._add_signature(payload)
        return self._post(payload)

    def _add_signature(self, payload: dict) -> None:
        if not self.secret:
            return

        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self.secret}"

        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        sign = base64.b64encode(hmac_code).decode("utf-8")

        payload["timestamp"] = timestamp
        payload["sign"] = sign

    def _post(self, payload: dict) -> bool:
        try:
            response = requests.post(
                self.webhook,
                json=payload,
                proxies=get_requests_proxies(),
                timeout=20,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("StatusCode") == 0 or data.get("code") == 0:
                logger.success("Feishu bot message sent.")
                return True

            logger.error(f"Feishu bot send failed: {data}")
            return False

        except Exception as exc:
            logger.exception(f"Feishu bot send error: {exc}")
            return False