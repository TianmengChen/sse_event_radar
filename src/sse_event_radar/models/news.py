import hashlib
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


NewsSourceType = Literal[
    "manual_input",
    "official_policy",
    "company_announcement",
    "finance_news",
    "industry_news",
]


class NewsItem(BaseModel):
    id: str
    source: str = "manual"
    source_type: NewsSourceType = "manual_input"

    title: str
    content: str | None = None
    url: str | None = None

    published_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=datetime.now)

    raw: dict = Field(default_factory=dict)


def make_news_item_from_text(
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