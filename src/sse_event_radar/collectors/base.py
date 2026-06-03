from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseCollector(ABC):
    source_name: str

    @abstractmethod
    def collect(self) -> pd.DataFrame:
        raise NotImplementedError

    @staticmethod
    def safe_get(row: dict[str, Any], key: str, default=None):
        value = row.get(key, default)
        if pd.isna(value):
            return default
        return value
