"""数据源基础接口"""

from abc import ABC, abstractmethod
from typing import Any


class DataSource(ABC):
    """数据源抽象基类 — 所有数据提供者实现此接口"""

    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        ...

    @abstractmethod
    def available(self) -> bool:
        """检查数据源是否可用"""
        ...


class QuoteSource(DataSource):
    """行情数据源"""

    @abstractmethod
    def quote(self, symbol: str) -> dict[str, Any]:
        """获取实时报价"""
        ...


class HistoricalSource(DataSource):
    """历史数据源"""

    @abstractmethod
    def fetch(self, symbol: str, period: str, interval: str) -> Any:
        """拉取历史数据"""
        ...
