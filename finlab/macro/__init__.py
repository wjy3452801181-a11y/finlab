"""宏观数据模块 — 数据抓取、评分、报告生成"""

from finlab.macro.fetchers import (
    fetch_economic_calendar,
    filter_high_impact_events,
    fetch_forexlive_news,
    WATCHED_EVENTS,
)
from finlab.macro.director import MacroDirector

__all__ = [
    "fetch_economic_calendar",
    "filter_high_impact_events",
    "fetch_forexlive_news",
    "MacroDirector",
    "WATCHED_EVENTS",
]
