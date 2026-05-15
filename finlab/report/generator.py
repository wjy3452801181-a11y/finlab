"""研报模块 — 研报完整生成器

组装四大章节 + 行情数据 + 快讯，输出 Markdown 文件并归档到 Obsidian。
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from finlab.core import BJT
from finlab.core.config import get_config
from finlab.report.fetchers import (
    fetch_yfinance_batch,
    fetch_report_quotes,
    default_date_range,
    TICKER_GROUPS,
    calc_weekly_change,
)
from finlab.report.sections import (
    generate_intro,
    generate_data_section,
    generate_policy_section,
    generate_topic_section,
    generate_investment_section,
)

OBSIDIAN_DIR = get_config().obsidian_dir


def generate_report(
    title: str = "",
    date_range: tuple = None,
    tickers: list[str] = None,
    topic_title: str = "",
    topic_desc: str = "",
    topic_analysis: str = "",
    outlook: str = "",
    risks: str = "",
    output_dir: str = None,
    use_jin10_quotes: bool = True,
) -> str:
    """生成完整研报

    Args:
        title: 研报标题（默认自动生成）
        date_range: (start_date, end_date)，默认最近7天
        tickers: 标的列表，默认全部分组
        topic_title: 专题分析标题
        topic_desc: 专题事件描述
        topic_analysis: 专题深度分析
        outlook: 市场展望
        risks: 风险提示
        output_dir: 输出目录（默认 Obsidian 研究分析）
        use_jin10_quotes: 是否拉取金十行情快照

    Returns:
        文件绝对路径
    """
    # 默认参数
    if date_range:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_date_range()

    if not tickers:
        tickers = []
        for group_tickers in TICKER_GROUPS.values():
            tickers.extend(group_tickers)

    if not title:
        title = (
            f"全市场周报 — "
            f"{start_date.strftime('%m/%d')} ~ {end_date.strftime('%m/%d')}"
        )

    period_start = start_date.strftime("%Y-%m-%d")
    period_end = end_date.strftime("%Y-%m-%d")

    print(f"📡 拉取 Yahoo Finance 行情 ({len(tickers)} 个标的)...")
    yf_results = fetch_yfinance_batch(tickers, start_date, end_date)
    print(f"✅ {len(yf_results)}/{len(tickers)} 个标的取到数据")

    quotes = {}
    if use_jin10_quotes:
        print("📡 拉取金十MCP行情快照...")
        try:
            quotes = fetch_report_quotes()
            valid = sum(1 for v in quotes.values() if v is not None)
            print(f"✅ {valid}/{len(quotes)} 个行情取到数据")
        except Exception as e:
            print(f"⚠️ 金十行情失败: {e}")
            quotes = {}

    # 组装研报
    print("📝 生成研报内容...")
    sections = []

    # 导语
    sections.append(generate_intro(title, period_start, period_end))

    # 第一章：数据更新
    sections.append(generate_data_section(yf_results, quotes, period_start, period_end))

    # 第二章：政策与新闻
    sections.append(generate_policy_section())

    # 第三章：专题分析
    sections.append(generate_topic_section(
        title=topic_title,
        description=topic_desc,
        analysis=topic_analysis,
    ))

    # 第四章：投资观点
    sections.append(generate_investment_section(
        outlook=outlook,
        risks=risks,
    ))

    # 尾注
    sections.append("---")
    sections.append("*免责声明：本研报由 AI 辅助生成，仅供参考，不构成投资建议。*")
    sections.append("")

    content = "\n".join(sections)

    # 输出
    output_path = output_dir or OBSIDIAN_DIR
    os.makedirs(output_path, exist_ok=True)

    filename_slug = title.replace(" ", "_").replace("/", "_").replace(":", "_")
    filepath = os.path.join(output_path, f"{filename_slug}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 研报已保存: {filepath}")
    return filepath


def quick_report(
    title: str = "",
    topic_title: str = "",
    topic_desc: str = "",
    outlook: str = "",
    risks: str = "",
) -> str:
    """快速生成一份研报（默认最近7天 + 全标的数据）"""
    return generate_report(
        title=title,
        topic_title=topic_title,
        topic_desc=topic_desc,
        outlook=outlook,
        risks=risks,
    )
