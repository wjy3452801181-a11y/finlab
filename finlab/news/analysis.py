"""新闻模块 — 金融事件影响分析框架"""

from finlab.news.fetchers import search_flash, format_flash_item


# 事件分类 + 与评分规则的映射
EVENT_CATEGORIES = {
    "通胀": ["PPI", "CPI", "PCE", "核心CPI", "核心PCE", "居民消费价格", "生产者价格"],
    "就业": ["NFP", "非农", "失业", "初请", "JOLTS", "ADP", "就业人口"],
    "增长": ["GDP", "零售", "工业产出", "制造业", "耐用品", "消费者信心"],
    "货币政策": ["FOMC", "利率", "降息", "加息", "鲍威尔", "美联储", "央行"],
    "地缘/贸易": ["关税", "制裁", "谈判", "协议", "冲突", "战争", "停火"],
    "行业/公司": ["财报", "营收", "净利润", "订单", "产能"],
}

# 评分默认规则（通胀越高越利多BTC，越高越利空A股等要看上下文）
DEFAULT_SCORE_MAP = {
    "通胀": ("利空", "紧缩预期强化"),
    "就业": ("中性", "劳动力市场韧性"),
    "增长": ("利多", "经济韧性强劲"),
    "货币政策": ("多空分歧", "取决于具体决策方向"),
    "地缘/贸易": ("利空", "不确定性上升"),
    "行业/公司": ("中性", "需结合个股基本面"),
}


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
