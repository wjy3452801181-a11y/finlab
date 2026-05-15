from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Score:
    """统一评分结果"""
    value: int            # 1-10
    direction: str = ""   # "利多" | "利空" | "中性"
    reason: str = ""      # 人类可读理由

    def as_label(self) -> str:
        """格式化评分标签"""
        if self.value >= 8:
            return f"{self.value}/10 🚀 强烈利多"
        elif self.value >= 6:
            return f"{self.value}/10 ✅ 利好"
        elif self.value >= 4:
            return f"{self.value}/10 ⚖️ 中性"
        elif self.value >= 2:
            return f"{self.value}/10 🔴 利空"
        else:
            return f"{self.value}/10 ⚠️ 强烈利空"


@dataclass
class MacroEvent:
    """宏观事件数据模型"""
    time: str
    country: str
    indicator: str
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    score: int = 5  # 1-10评分
    direction: str = ""  # 利多/利空/中性
    reason: str = ""     # 评分理由


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
