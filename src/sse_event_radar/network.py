import os

from loguru import logger

from sse_event_radar.config import settings


def configure_proxy() -> None:
    """
    Configure process-level proxy environment variables.

    AKShare internally uses requests, and requests reads proxy settings from
    environment variables by default.
    """
    if not settings.proxy_enabled:
        logger.info("Proxy disabled.")
        return

    if not settings.proxy_url:
        raise RuntimeError("PROXY_ENABLED=true but PROXY_URL is empty.")

    proxy_url = settings.proxy_url.strip()

    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url

    os.environ["no_proxy"] = settings.no_proxy
    os.environ["NO_PROXY"] = settings.no_proxy

    logger.info(f"Proxy enabled: {proxy_url}")
    logger.info(f"NO_PROXY={settings.no_proxy}")


def get_requests_proxies() -> dict[str, str] | None:
    """
    Explicit requests proxy dict.

    This is useful when a third-party function does not behave well with
    environment proxy variables.
    """
    if not settings.proxy_enabled:
        return None

    if not settings.proxy_url:
        return None

    proxy_url = settings.proxy_url.strip()
    return {
        "http": proxy_url,
        "https": proxy_url,
    }