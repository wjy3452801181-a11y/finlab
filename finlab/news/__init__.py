"""新闻模块 — 实时快讯、事件分析、简报生成"""

from finlab.news.fetchers import fetch_jin10_flash
from finlab.news.analysis import analyze_event
from finlab.news.brief import generate_brief

__all__ = [
    "fetch_jin10_flash",
    "analyze_event",
    "generate_brief",
]
