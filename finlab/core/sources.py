"""数据源基础接口 + 内置适配器

每个数据源通过适配器满足这些接口，调用者依赖接口而非具体实现。
两个适配器 = 真实的缝（可用于测试替身注入）。
"""

from abc import ABC, abstractmethod
from typing import Optional, Any


class QuoteSource(ABC):
    """行情数据源 — 提供实时报价"""

    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        ...

    @abstractmethod
    def available(self) -> bool:
        """数据源是否可用"""
        ...

    @abstractmethod
    def quote(self, symbol: str) -> Optional[float]:
        """获取实时报价，失败返回 None"""
        ...


class HistoricalSource(ABC):
    """历史数据源 — 提供日线历史行情"""

    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        ...

    @abstractmethod
    def available(self) -> bool:
        """数据源是否可用"""
        ...

    @abstractmethod
    def fetch(self, symbol: str, start: str, end: str) -> Any:
        """拉取历史日线数据，返回 StockData 或 DataFrame 或 None"""
        ...
