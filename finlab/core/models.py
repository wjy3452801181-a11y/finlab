from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any
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

    @classmethod
    def from_dict(cls, event: dict[str, Any]) -> MacroEvent:
        """从 TradingEconomics API 原始字典构建（替代原 event_to_macro_event）"""
        from finlab.core.scoring import score_event

        raw_date = event.get("Date", "")
        if "T" in raw_date:
            time_part = raw_date.split("T")[1][:5]
        else:
            time_part = "全天"

        event_name = event.get("Event", "N/A")
        actual = str(event.get("Actual", "-"))
        forecast = str(event.get("Forecast", "-"))
        previous = str(event.get("Previous", "-"))

        s = score_event(event_name, actual, forecast, previous)

        return cls(
            time=time_part,
            country=event.get("Country", ""),
            indicator=event_name,
            actual=float(actual) if actual not in ("-", "") else None,
            forecast=float(forecast) if forecast not in ("-", "") else None,
            previous=float(previous) if previous not in ("-", "") else None,
            score=s.value,
            direction=s.direction,
            reason=s.reason,
        )


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
