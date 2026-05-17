"""A股模块 — 标的追踪、板块扫描、板块轮动"""

from finlab.ashare.data import login, logout, fetch_history, StockData
from finlab.ashare.tracker import TrackConfig, TrackResult, track_stocks, print_summary
from finlab.ashare.screener import scan_sectors, print_sector_scan, DEFAULT_CATEGORIES
from finlab.ashare.chief import SectorChief

__all__ = [
    "login", "logout", "fetch_history", "StockData",
    "TrackConfig", "TrackResult", "track_stocks", "print_summary",
    "scan_sectors", "print_sector_scan", "DEFAULT_CATEGORIES",
    "SectorChief",
]
