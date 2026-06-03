import requests
from loguru import logger

from sse_event_radar.config import settings
from sse_event_radar.network import get_requests_proxies
from sse_event_radar.notifiers.base import BaseNotifier


class ServerChanNotifier(BaseNotifier):
    """
    Server 酱 Turbo notifier.

    API:
        POST https://sctapi.ftqq.com/<SENDKEY>.send

    Payload:
        title: message title
        desp: markdown/text body
    """

    def __init__(self, sendkey: str | None = None):
        self.sendkey = sendkey or settings.serverchan_sendkey

        if not self.sendkey:
            raise RuntimeError("SERVERCHAN_SENDKEY is empty.")

        self.api_url = f"https://sctapi.ftqq.com/{self.sendkey}.send"

    def send_text(self, title: str, text: str) -> bool:
        return self._send(title=title, desp=text)

    def send_markdown(self, title: str, markdown: str) -> bool:
        return self._send(title=title, desp=markdown)

    def _send(self, title: str, desp: str) -> bool:
        payload = {
            "title": title,
            "desp": desp,
        }

        try:
            response = requests.post(
                self.api_url,
                data=payload,
                proxies=get_requests_proxies(),
                timeout=20,
            )
            response.raise_for_status()

            data = response.json()

            # Server 酱不同版本/通道返回字段可能略有差异，这里做兼容。
            ok = (
                data.get("code") == 0
                or data.get("errno") == 0
                or data.get("message") in {"SUCCESS", "success", "ok"}
            )

            if not ok:
                logger.error(f"ServerChan send failed: {data}")
                return False

            logger.success("ServerChan message sent.")
            return True

        except Exception as exc:
            logger.exception(f"ServerChan send error: {exc}")
            return False