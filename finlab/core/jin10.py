"""金十数据适配器 — 统一的 Jin10MCP 客户端管理

所有模块通过此模块访问金十数据，不再各自初始化客户端。
"""

import sys
import os
from typing import Optional
from datetime import datetime, timedelta

from finlab.core._time import BJT

_JIN10_PATH = os.path.expanduser("~/.hermes/scripts")
if _JIN10_PATH not in sys.path:
    sys.path.insert(0, _JIN10_PATH)

try:
    from jin10_mcp_client import Jin10MCP, MCPError
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    Jin10MCP = None  # type: ignore
    MCPError = Exception  # type: ignore


_client: Optional["Jin10MCP"] = None


def get_client() -> "Jin10MCP":
    """获取已初始化的 Jin10MCP 客户端（单例）"""
    global _client
    if not _MCP_AVAILABLE:
        raise RuntimeError("jin10_mcp_client.py 未找到，请检查 ~/.hermes/scripts/ 路径")
    if _client is None:
        _client = Jin10MCP()
        _client.initialize()
    return _client


def is_available() -> bool:
    """检查金十 MCP 是否可用"""
    if not _MCP_AVAILABLE:
        return False
    try:
        get_client()
        return True
    except Exception:
        return False


def fetch_flash(hours: int = 1, max_items: int = 30) -> list[dict]:
    """获取最近 N 小时的金十快讯"""
    client = get_client()
    data = client.list_flash()
    if not data:
        return []

    items = data.get("items", [])
    if not items:
        return []

    now = datetime.now(BJT)
    cutoff = now - timedelta(hours=hours)

    filtered = []
    for item in items:
        time_str = item.get("time", "")
        if not time_str:
            continue
        try:
            item_dt = datetime.strptime(time_str, "%H:%M:%S").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=BJT
            )
            if item_dt > now:
                item_dt -= timedelta(days=1)
            if item_dt >= cutoff:
                filtered.append(item)
        except ValueError:
            filtered.append(item)

    return filtered[:max_items]


def search_flash(keyword: str, max_items: int = 20) -> list[dict]:
    """搜索快讯"""
    client = get_client()
    items = client.search_flash(keyword)
    return items[:max_items] if items else []


def fetch_calendar() -> list[dict]:
    """获取本周财经日历"""
    client = get_client()
    data = client.list_calendar()
    return data or []


def fetch_quotes(codes: dict[str, str]) -> dict[str, Optional[float]]:
    """批量获取实时行情报价

    Args:
        codes: {名称: 品种代码}，如 {"上证": "000001", "黄金": "XAUUSD"}

    Returns:
        {名称: 最新价}，获取失败则为 None
    """
    client = get_client()
    result = {}
    for name, code in codes.items():
        try:
            q = client.get_quote(code)
            if q:
                result[name] = float(q.get("close", 0))
            else:
                result[name] = None
        except Exception:
            result[name] = None
    return result


# ── 格式化 ─────────────────────────────────────────────

def format_flash_item(item: dict) -> str:
    """格式化单条快讯"""
    t = item.get("time", "")
    content = item.get("content", "") or item.get("title", "")
    return f"[{t}] {content}"


def format_calendar_item(item: dict) -> str:
    """格式化单条日历事件"""
    star = "⭐" * min(int(item.get("star", 0)), 3)
    pub = item.get("pub_time", "")
    title = item.get("title", "")
    prev = item.get("previous", "-")
    cons = item.get("consensus", "-")
    actual = item.get("actual", "-")
    affect = item.get("affect_txt", "")
    tag = f" [{affect}]" if affect else ""
    return f"[{pub}] {star} {title}{tag}\n    前值:{prev} 预期:{cons} 实际:{actual}"


# ── QuoteSource 适配器 ──────────────────────────────────

class Jin10QuoteAdapter:
    """金十行情适配器 — 提供实时报价查询"""

    def name(self) -> str:
        return "jin10"

    def available(self) -> bool:
        return is_available()

    def quote(self, symbol: str) -> Optional[float]:
        try:
            client = get_client()
            q = client.get_quote(symbol)
            if q:
                return float(q.get("close", 0))
            return None
        except Exception:
            return None
