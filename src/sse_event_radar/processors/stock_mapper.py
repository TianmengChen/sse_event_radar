from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from sse_event_radar.processors.event_extractor import IntegratedEvent


class StockCandidate(BaseModel):
    code: str
    name: str
    security_type: str = "stock"
    match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_terms: list[str] = Field(default_factory=list)
    reason: str = ""


class StockMapper:
    def __init__(self, knowledge_path: str = "config/stock_knowledge.yaml"):
        self.knowledge_path = Path(knowledge_path)
        self.stocks = self._load_stocks()

    def map_event_to_candidates(
        self,
        event: IntegratedEvent,
        top_n: int = 8,
        min_score: float = 0.15,
    ) -> list[StockCandidate]:
        event_terms = set(event.affected_industries + event.keywords)
        if not event_terms:
            return []

        candidates: list[StockCandidate] = []

        for stock in self.stocks:
            stock_terms = set(stock.get("industries", []) + stock.get("concepts", []))
            matched = sorted(event_terms.intersection(stock_terms))

            if not matched:
                continue

            # Simple score: matched terms / event terms, capped.
            score = min(len(matched) / max(len(event_terms), 1), 1.0)

            if score < min_score:
                continue

            code = str(stock["code"]).zfill(6)
            name = stock["name"]
            security_type = stock.get("type", "stock")

            candidates.append(
                StockCandidate(
                    code=code,
                    name=name,
                    security_type=security_type,
                    match_score=score,
                    matched_terms=matched,
                    reason=f"匹配事件关键词/行业：{', '.join(matched)}",
                )
            )

        candidates.sort(key=lambda x: x.match_score, reverse=True)
        return candidates[:top_n]

    def _load_stocks(self) -> list[dict]:
        if not self.knowledge_path.exists():
            raise FileNotFoundError(f"Stock knowledge file not found: {self.knowledge_path}")

        data = yaml.safe_load(self.knowledge_path.read_text(encoding="utf-8")) or {}
        return data.get("stocks", [])