"""新闻模块 — 快讯简报生成"""

from datetime import datetime, timedelta
from typing import Optional

from finlab.core import BJT
from finlab.news.fetchers import (
    fetch_flash,
    fetch_calendar,
    fetch_high_impact_calendar,
    search_flash,
    format_flash_item,
    format_calendar_item,
    check_mcp_available,
)
from finlab.news.analysis import analyze_event


def build_flash_brief(hours: int = 2, max_items: int = 20) -> str:
    """生成最近 N 小时的快讯简报（表格格式）

    Args:
        hours: 最近几小时
        max_items: 最大条目数

    Returns:
        格式化的简报文本
    """
    if not check_mcp_available():
        return "❌ 金十MCP客户端不可用，无法获取快讯"

    items = fetch_flash(hours=hours, max_items=max_items)
    if not items:
        return f"📭 最近{hours}小时无快讯"

    now = datetime.now(BJT)
    header = (
        f"📰 快讯简报 — {now.strftime('%Y-%m-%d %H:%M')}  BJT\n"
        f"{'='*56}\n"
    )

    # 表格格式
    table_lines = []
    table_lines.append(f"| {'时间':<8} | {'分类':<10} | {'内容':<50} |")
    table_lines.append(f"|{'-'*10}|{'-'*12}|{'-'*52}|")

    # 按时间排序（降序，最新在前）
    sorted_items = sorted(items, key=lambda x: x.get("time", ""), reverse=True)

    for item in sorted_items:
        t = item.get("time", "")
        content = item.get("content", "") or item.get("title", "")
        category = _guess_category(content)

        # 截断长内容
        disp = content[:48] + ".." if len(content) > 48 else content.ljust(50)

        table_lines.append(f"| {t[:8]:<8} | {category[:10]:<10} | {disp:<50} |")

    # 提取关键事件
    high_impact = _extract_high_impact(sorted_items)

    result = header + "\n".join(table_lines)

    if high_impact:
        result += "\n\n【重点关注】\n"
        for item in high_impact:
            result += f"  ⚡ {item}\n"

    result += f"\n{'='*56}"
    return result


def build_calendar_brief(days: int = 7) -> str:
    """生成财经日历简报

    Args:
        days: 覆盖天数（实际按自然周）

    Returns:
        格式化的日历简报
    """
    if not check_mcp_available():
        return "❌ 金十MCP客户端不可用，无法获取日历"

    cal = fetch_calendar()
    if not cal:
        return "📭 本周无财经日历事件"

    now = datetime.now(BJT)
    header = (
        f"📅 财经日历 — {now.strftime('%Y-%m-%d')} BJT\n"
        f"{'='*56}\n"
    )

    # 按日期分组
    high_impact = fetch_high_impact_calendar(4)  # 4-5星
    medium = [e for e in cal if e not in high_impact and int(e.get("star", 0)) >= 2]

    result = header

    if high_impact:
        result += "\n【🔴 高重要性】\n"
        for item in high_impact[:5]:
            result += f"  {format_calendar_item(item)}\n"

    if medium:
        result += "\n【🟡 中等重要性】\n"
        for item in medium[:8]:
            result += f"  {format_calendar_item(item)}\n"

    result += f"\n{'='*56}"
    return result


def build_search_brief(keyword: str) -> str:
    """生成关键词搜索简报

    Args:
        keyword: 搜索关键词

    Returns:
        格式化搜索结果
    """
    if not check_mcp_available():
        return "❌ 金十MCP客户端不可用，无法搜索"

    items = search_flash(keyword)
    if not items:
        return f"🔍 未找到 \"{keyword}\" 相关快讯"

    result = f"🔍 \"{keyword}\" 搜索结果 ({len(items)}条)\n"
    result += f"{'='*56}\n"

    # 分析
    try:
        analysis = analyze_event(keyword)
        result += f"{analysis}\n\n"
    except Exception:
        pass

    for item in items[:10]:
        result += f"  {format_flash_item(item)}\n"

    result += f"{'='*56}"
    return result


def _guess_category(content: str) -> str:
    """根据内容猜测快讯分类"""
    content_lower = content.lower()
    cat_map = [
        ("行情", any(x in content_lower for x in ["上涨", "下跌", "涨幅", "跌幅", "收盘", "开盘"])),
        ("宏观", any(x in content_lower for x in ["CPI", "PPI", "GDP", "PMI", "就业", "失业", "通胀"])),
        ("央行动态", any(x in content_lower for x in ["美联储", "加息", "降息", "利率", "央行"])),
        ("地缘", any(x in content_lower for x in ["关税", "制裁", "谈判", "冲突", "战争"])),
        ("行业", any(x in content_lower for x in ["芯片", "新能源", "汽车", "医药", "AI", "算力"])),
        ("公司", any(x in content_lower for x in ["财报", "营收", "利润", "并购", "上市"])),
    ]
    for name, match in cat_map:
        if match:
            return name
    return "综合"


def _extract_high_impact(items: list[dict]) -> list[str]:
    """从快讯中提取高影响力事件"""
    highlights = []
    for item in items:
        content = item.get("content", "") or item.get("title", "")
        # 匹配重要关键词
        trigger_words = [
            "突发", "紧急", "重大", "央行", "加息", "降息", "利率决议",
            "CPI", "PPI", "非农", "FOMC", "关税", "制裁",
        ]
        if any(w in content for w in trigger_words):
            highlights.append(format_flash_item(item))
    return highlights[:5]
