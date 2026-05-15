"""新闻模块 — 实时快讯抓取（金十MCP封装）"""

import sys
import os
from typing import Optional
from datetime import datetime, timezone, timedelta

# 导入金十MCP客户端
_JIN10_PATH = os.path.expanduser("~/.hermes/scripts")
if _JIN10_PATH not in sys.path:
    sys.path.insert(0, _JIN10_PATH)

try:
    from jin10_mcp_client import Jin10MCP, MCPError
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


# 时区
BJT = timezone(timedelta(hours=8))


def _ensure_client() -> Jin10MCP:
    """获取已初始化的 Jin10MCP 客户端"""
    if not _MCP_AVAILABLE:
        raise RuntimeError("jin10_mcp_client.py 未找到，请检查 ~/.hermes/scripts/ 路径")
    client = Jin10MCP()
    client.initialize()
    return client


def fetch_flash(hours: int = 1, max_items: int = 30) -> list[dict]:
    """获取最近 N 小时的金十快讯

    Args:
        hours: 最近几小时
        max_items: 最大返回条数

    Returns:
        [{time, content, ...}]
    """
    client = _ensure_client()
    data = client.list_flash()
    if not data:
        return []

    items = data.get("items", [])
    if not items:
        return []

    # 按时间过滤（金十快讯 time 为 "HH:MM:SS" 格式）
    now = datetime.now(BJT)
    cutoff = now - timedelta(hours=hours)

    filtered = []
    for item in items:
        time_str = item.get("time", "")
        if not time_str:
            continue
        try:
            # time 格式 "HH:MM:SS"，拼到当天日期
            item_dt = datetime.strptime(time_str, "%H:%M:%S").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=BJT
            )
            # 跨日处理：如果当前是凌晨但快讯是昨晚的
            if item_dt > now:
                item_dt -= timedelta(days=1)
            if item_dt >= cutoff:
                filtered.append(item)
        except ValueError:
            filtered.append(item)

    return filtered[:max_items]


def search_flash(keyword: str, max_items: int = 20) -> list[dict]:
    """搜索快讯

    Args:
        keyword: 关键词
        max_items: 最大返回条数

    Returns:
        [{time, content, ...}]
    """
    client = _ensure_client()
    items = client.search_flash(keyword)
    if not items:
        return []
    return items[:max_items]


def fetch_calendar() -> list[dict]:
    """获取本周财经日历

    Returns:
        [{pub_time, title, star, previous, consensus, actual, affect_txt, ...}]
    """
    client = _ensure_client()
    data = client.list_calendar()
    return data or []


def fetch_high_impact_calendar(min_star: int = 3) -> list[dict]:
    """获取高重要性财经事件

    Args:
        min_star: 最小星级（金十日历星级范围 1-5）

    Returns:
        高重要性事件列表
    """
    cal = fetch_calendar()
    return [e for e in cal if int(e.get("star", 0)) >= min_star]


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


def check_mcp_available() -> bool:
    """检查金十MCP是否可用"""
    if not _MCP_AVAILABLE:
        return False
    try:
        client = _ensure_client()
        return True
    except Exception:
        return False
