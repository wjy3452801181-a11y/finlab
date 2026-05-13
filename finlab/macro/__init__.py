"""宏观数据模块 — 数据抓取、评分、报告生成"""

from finlab.macro.fetchers import (
    fetch_economic_calendar,
    filter_high_impact_events,
    fetch_forexlive_news,
    WATCHED_EVENTS,
)
from finlab.macro.scoring import (
    calc_impact_score,
    format_score,
    event_to_macro_event,
)
from finlab.macro.report import (
    generate_macro_report,
    generate_macro_summary,
)

__all__ = [
    "fetch_economic_calendar",
    "filter_high_impact_events",
    "fetch_forexlive_news",
    "calc_impact_score",
    "format_score",
    "event_to_macro_event",
    "generate_macro_report",
    "generate_macro_summary",
    "WATCHED_EVENTS",
]
