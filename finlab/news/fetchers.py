"""新闻模块 — 实时快讯抓取（委托给 core.jin10 统一适配器）"""

from finlab.core.jin10 import (
    fetch_flash,  # noqa: F401 — re-export
    search_flash,  # noqa: F401 — re-export
    fetch_calendar,
    is_available as check_mcp_available,  # noqa: F401 — re-export
)


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
