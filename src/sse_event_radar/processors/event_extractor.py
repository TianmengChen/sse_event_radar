from pydantic import BaseModel, Field

from sse_event_radar.models.news import NewsItem


class IntegratedEvent(BaseModel):
    title: str
    summary: str
    event_type: str = "unknown"
    direction_hint: str = "uncertain"
    affected_industries: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    mentioned_companies: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    source: str | None = None
    source_url: str | None = None


class SimpleEventExtractor:
    """
    Temporary rule-based event extractor.

    Later this class can be replaced by a local LLM-based extractor.
    """

    INDUSTRY_KEYWORDS = {
        "半导体": ["半导体", "芯片", "集成电路", "晶圆", "光刻", "刻蚀", "先进制程"],
        "半导体设备": ["半导体设备", "刻蚀设备", "光刻机", "设备国产化"],
        "半导体材料": ["光刻胶", "硅片", "靶材", "电子气体", "材料国产化"],
        "AI": ["人工智能", "AI", "大模型", "算力", "GPU", "服务器"],
        "新能源": ["新能源", "光伏", "储能", "锂电", "电池"],
        "军工": ["军工", "国防", "航空发动机", "导弹", "无人机"],
        "银行": ["银行", "降息", "利率", "信贷", "地产融资"],
    }

    POSITIVE_WORDS = [
        "支持",
        "利好",
        "鼓励",
        "补贴",
        "国产替代",
        "突破",
        "增长",
        "预增",
        "中标",
        "重大合同",
    ]

    NEGATIVE_WORDS = [
        "处罚",
        "立案",
        "监管",
        "减持",
        "亏损",
        "预减",
        "风险",
        "下滑",
    ]

    def extract(self, news: NewsItem) -> IntegratedEvent:
        text = f"{news.title}\n{news.content or ''}"

        affected_industries: list[str] = []
        keywords: list[str] = []

        for industry, kws in self.INDUSTRY_KEYWORDS.items():
            matched = [kw for kw in kws if kw in text]
            if matched:
                affected_industries.append(industry)
                keywords.extend(matched)

        positive_hits = [kw for kw in self.POSITIVE_WORDS if kw in text]
        negative_hits = [kw for kw in self.NEGATIVE_WORDS if kw in text]

        if negative_hits:
            direction = "negative"
        elif positive_hits:
            direction = "positive"
        else:
            direction = "uncertain"

        if "政策" in text or "发布" in text or "支持" in text:
            event_type = "policy_or_news"
        elif "公告" in text:
            event_type = "company_announcement"
        else:
            event_type = "news_event"

        summary = news.content or news.title

        return IntegratedEvent(
            title=news.title,
            summary=summary[:500],
            event_type=event_type,
            direction_hint=direction,
            affected_industries=sorted(set(affected_industries)),
            keywords=sorted(set(keywords + positive_hits + negative_hits)),
            mentioned_companies=[],
            confidence=0.6 if affected_industries else 0.4,
            source=news.source,
            source_url=news.url,
        )