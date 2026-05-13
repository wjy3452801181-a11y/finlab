from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class MacroEvent:
    """宏观事件数据模型"""
    time: str
    country: str
    indicator: str
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    impact: str = ""  # 利多/利空/中性
    score: int = 5  # 1-10评分


@dataclass
class MarketSnapshot:
    """市场快照"""
    symbol: str
    price: float
    change_pct: float
    volume: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AnalysisResult:
    """分析结果基类"""
    title: str
    timestamp: datetime = field(default_factory=datetime.now)
    summary: str = ""
    risk_level: str = "中性"  # 乐观/中性/谨慎
    tags: list[str] = field(default_factory=list)
