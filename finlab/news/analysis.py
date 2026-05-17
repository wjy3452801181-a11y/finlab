"""新闻模块 — 金融事件影响分析框架"""

from finlab.core.jin10 import search_flash, format_flash_item
from finlab.core.vocabulary import event_categories, default_score_map


# 事件分类 + 与评分规则的映射（从 vocabulary 派生）
EVENT_CATEGORIES = event_categories()
DEFAULT_SCORE_MAP = default_score_map()


def classify_event(title: str) -> list[str]:
    """分类金融事件

    Args:
        title: 事件标题

    Returns:
        事件所属分类列表
    """
    matched = []
    for category, keywords in EVENT_CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in title.lower():
                matched.append(category)
                break
    return matched or ["其他"]


def analyze_event(title: str, content: str = "") -> str:
    """分析金融事件影响

    Returns:
        分析结果文本
    """
    # 根据标题搜索相关快讯
    related_flash = search_flash(title.split(" ")[0] if title else "", max_items=5)

    # 分类
    categories = classify_event(title)
    cat_str = "、".join(categories)

    # 判断影响
    impact_dirs = []
    for cat in categories:
        if cat in DEFAULT_SCORE_MAP:
            direction, reason = DEFAULT_SCORE_MAP[cat]
            impact_dirs.append(f"  {cat}: {direction}（{reason}）")
        else:
            impact_dirs.append(f"  {cat}: 待评估")

    cat_impact = "\n".join(impact_dirs)

    # 构建分析报告
    lines = []
    lines.append(f"📊 事件分析：{title[:80]}")
    lines.append(f"  分类：{cat_str}")
    lines.append("")
    lines.append("  【影响路径】")
    lines.append(cat_impact)
    lines.append("")

    # 相关快讯
    if related_flash:
        lines.append(f"  【相关快讯 ({len(related_flash)}条)】")
        for item in related_flash[:5]:
            lines.append(f"  {format_flash_item(item)[:100]}")
    else:
        lines.append("  【相关快讯】暂无匹配")

    if content:
        lines.append("")
        lines.append(f"  【详情摘要】{content[:200]}")

    return "\n".join(lines)
