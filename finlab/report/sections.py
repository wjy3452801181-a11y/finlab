"""研报模块 — 四大章节生成器

研报结构：
1. 数据更新 — 行业/市场核心指标、周涨跌、产销量/库存等
2. 政策与新闻 — 国家-地方-行业协会/公司公告分层
3. 专题分析 — 事件描述→原因拆解→影响传导→未来预判
4. 投资观点 — 具体标的建议+风险提示
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

BJT = timezone(timedelta(hours=8))


def generate_data_section(
    yf_results: dict[str, dict[str, dict]],
    quote_snapshot: dict[str, Optional[float]],
    period_start: str,
    period_end: str,
) -> str:
    """生成第一章：数据更新

    Args:
        yf_results: yfinance 批量结果
        quote_snapshot: 金十MCP行情快照
        period_start: 周期起始日期
        period_end: 周期结束日期

    Returns:
        Markdown 章节内容
    """
    from finlab.report.fetchers import (
        TICKER_GROUPS,
        calc_weekly_change,
        format_yfinance_table,
    )

    lines = []
    lines.append(f"## 一、数据更新（{period_start} ~ {period_end}）")
    lines.append("")

    # 行情快照
    if quote_snapshot:
        valid = {k: v for k, v in quote_snapshot.items() if v is not None}
        if valid:
            lines.append("### 实时行情快照")
            lines.append(f"| {'品种':<10} | {'最新价':<12} |")
            lines.append(f"|{'-'*12}|{'-'*14}|")
            for name, price in valid.items():
                lines.append(f"| {name:<10} | {price:<12} |")
            lines.append("")

    # 按分组输出表格
    # 把 yf_results 按分组归类
    ticker_to_group = {}
    for group, tickers in TICKER_GROUPS.items():
        for t in tickers:
            ticker_to_group[t] = group

    grouped = {}
    for ticker, data in yf_results.items():
        group = ticker_to_group.get(ticker, "其他")
        if group not in grouped:
            grouped[group] = {}
        grouped[group][ticker] = data

    for group_name in ["大盘指数ETF", "美股行业ETF", "科技AI", "大宗商品", "债券/外汇", "中国", "加密"]:
        if group_name in grouped:
            lines.append(format_yfinance_table(grouped[group_name], group_name))
            lines.append("")

    return "\n".join(lines)


def generate_policy_section(flash_items: list[dict] = None) -> str:
    """生成第二章：政策与新闻

    Args:
        flash_items: 金十快讯列表（可选）

    Returns:
        Markdown 章节内容
    """
    lines = []
    lines.append("## 二、政策与新闻")
    lines.append("")

    if not flash_items:
        lines.append("> 待补充 — 请通过 `finlab report fetch-news` 获取本周快讯")
        lines.append("")
        return "\n".join(lines)

    # 按日期分组
    from collections import defaultdict
    by_date: dict[str, list[dict]] = defaultdict(list)
    for item in flash_items:
        time_str = item.get("time", "")
        dt = time_str[:10] if len(time_str) >= 10 else time_str[:8]
        by_date[dt].append(item)

    for date_str in sorted(by_date.keys(), reverse=True):
        lines.append(f"### {date_str}")
        for item in by_date[date_str]:
            t = item.get("time", "")
            content = item.get("content", "") or item.get("title", "")
            lines.append(f"- [{t}] {content[:150]}")
        lines.append("")

    return "\n".join(lines)


def generate_topic_section(title: str, description: str, analysis: str = "") -> str:
    """生成第三章：专题分析

    Args:
        title: 专题标题
        description: 事件描述
        analysis: 分析内容（原因/影响/预判）

    Returns:
        Markdown 章节内容
    """
    lines = []
    lines.append("## 三、专题分析")
    lines.append("")

    if title:
        lines.append(f"### {title}")
        lines.append("")

    lines.append("**事件描述**")
    lines.append(description)
    lines.append("")

    if analysis:
        lines.append("**原因拆解**")
        lines.append(analysis)
        lines.append("")

        # 影响传导
        lines.append("**影响传导**")
        lines.append("> 待补充 — 需结合具体事件分析对宏观/行业/市场的影响路径")
        lines.append("")

        lines.append("**未来预判**")
        lines.append("> 待补充 — 需跟踪事件后续发展")
        lines.append("")
    else:
        lines.append("*分析部分待补充*")
        lines.append("")

    return "\n".join(lines)


def generate_investment_section(outlook: str = "", risks: str = "") -> str:
    """生成第四章：投资观点

    Args:
        outlook: 市场展望
        risks: 风险提示

    Returns:
        Markdown 章节内容
    """
    lines = []
    lines.append("## 四、投资观点")
    lines.append("")

    lines.append("### 核心观点")
    if outlook:
        lines.append(outlook)
    else:
        lines.append("> 待补充 — 请结合数据更新和政策新闻做综合判断")
    lines.append("")

    lines.append("### 具体建议")
    lines.append("> 待补充 — 推荐标的、仓位、止损止盈建议")
    lines.append("")

    lines.append("### 风险提示")
    if risks:
        lines.append(risks)
    else:
        lines.append("> 待补充 — 本周主要风险事件和不确定性")
    lines.append("")

    return "\n".join(lines)


def generate_intro(title: str, period_start: str, period_end: str) -> str:
    """生成研报导语"""
    now = datetime.now(BJT).strftime("%Y-%m-%d %H:%M")
    lines = [
        "---",
        f"title: {title}",
        f"date: {now}",
        f"period: {period_start} ~ {period_end}",
        "tags: [研报, 周报, 市场分析]",
        "---",
        "",
        f"# {title}",
        "",
        f"**报告周期**：{period_start} ~ {period_end}",
        f"**生成时间**：{now} BJT",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)
