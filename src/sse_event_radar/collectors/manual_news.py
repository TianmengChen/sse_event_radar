import hashlib
from datetime import datetime

from sse_event_radar.models.news import NewsItem


class ManualNewsCollector:
    def collect_from_text(
        self,
        text: str,
        title: str | None = None,
        source: str = "manual",
        url: str | None = None,
    ) -> NewsItem:
        text = text.strip()
        title = title or text[:80]

        raw_id = f"{source}|{title}|{text}|{url or ''}"
        item_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()

        return NewsItem(
            id=item_id,
            source=source,
            source_type="manual_input",
            title=title,
            content=text,
            url=url,
            published_at=datetime.now(),
            raw={"input_text": text},
        )