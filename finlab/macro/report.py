"""宏观数据报告生成器"""

import datetime
from typing import Optional

from finlab.core.models import MacroEvent, MarketSnapshot
from finlab.macro.fetchers import (
    fetch_economic_calendar,
    filter_high_impact_events,
    fetch_forexlive_news,
    WATCHED_EVENTS,
)
from finlab.macro.scoring import (
    calc_impact_score,
    format_score,
    event_to_macro_event,
)


def generate_macro_report(
    country: str = "us",
    days_ahead: int = 2,
    api_key: str = "guest:guest",
    include_news: bool = True,
) -> str:
    """生成宏观数据简报

    Args:
        country: 国家代码
        days_ahead: 向前看几天
        api_key: TradingEconomics API key
        include_news: 是否包含ForexLive新闻

    Returns:
        格式化的宏观简报文本
    """
    now = datetime.datetime.now()
    lines = []
    lines.append("=" * 56)
    lines.append(f"  📊 宏观数据快讯 — {now.strftime('%Y-%m-%d %H:%M')} 北京时间")
    lines.append("=" * 56)

    # 获取事件
    events = fetch_economic_calendar(country=country, days_ahead=days_ahead, api_key=api_key)
    if events and "error" not in events[0]:
        high_impact = filter_high_impact_events(events)
        today_str = now.strftime("%Y-%m-%d")

        today_events = [e for e in high_impact if str(e.get("Date", "")).startswith(today_str)]
        if today_events:
            lines.append(f"\n  📅 今日 {country.upper()} 数据 ({len(today_events)}项)")
            for e in today_events:
                imp = e.get("Importance", 1)
                imp_label = {3: "🔴极高", 2: "🟠高", 1: "🟡中"}.get(imp, "⚪低")
                event_name = e.get("Event", "N/A")
                actual = e.get("Actual", "-")
                forecast = e.get("Forecast", "-")
                previous = e.get("Previous", "-")
                score = calc_impact_score(event_name, actual, forecast, previous)
                me = event_to_macro_event(e)
                time_part = me.time
                lines.append(f"\n    ⏰ {time_part} {imp_label} {event_name}")
                lines.append(f"      实际: {actual} | 预期: {forecast} | 前值: {previous}")
                lines.append(f"      影响: {format_score(score)}")

        # 明日事件
        tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_events = [e for e in high_impact if str(e.get("Date", "")).startswith(tomorrow_str)]
        if tomorrow_events:
            lines.append(f"\n  📅 明日 {country.upper()} 数据 ({len(tomorrow_events)}项)")
            for e in tomorrow_events:
                imp = e.get("Importance", 1)
                imp_label = {3: "🔴极高", 2: "🟠高", 1: "🟡中"}.get(imp, "⚪低")
                event_name = e.get("Event", "N/A")
                forecast = e.get("Forecast", "-")
                previous = e.get("Previous", "-")
                me = event_to_macro_event(e)
                lines.append(f"\n    {imp_label} {event_name}")
                lines.append(f"      预期: {forecast} | 前值: {previous}")
    else:
        lines.append(f"\n  ⚠️ 经济日历数据不可用 (API限制)")
        lines.append(f"     尝试直接访问 TradingEconomics 或使用其他数据源")

    # 新闻
    if include_news:
        news = fetch_forexlive_news()
        macro_news = [
            n for n in news
            if any(e.lower() in n.get("title", "").lower() for e in WATCHED_EVENTS)
        ]
        if macro_news:
            lines.append(f"\n  📰 宏观相关新闻 ({len(macro_news)}条)")
            for n in macro_news[:5]:
                lines.append(f"    • {n['title'][:120]}")

    lines.append("\n" + "=" * 56)
    return "\n".join(lines)


def generate_macro_summary(country: str = "us") -> str:
    """生成精简版宏观摘要（适合推送）"""
    now = datetime.datetime.now()
    events = fetch_economic_calendar(country=country)
    lines = []
    lines.append(f"【🌍 宏观预览】{now.strftime('%m/%d %H:%M')}")

    if events and "error" not in events[0]:
        today_str = now.strftime("%Y-%m-%d")
        today_e = [e for e in filter_high_impact_events(events) if str(e.get("Date", "")).startswith(today_str)]
        if today_e:
            for e in today_e[:5]:
                me = event_to_macro_event(e)
                lines.append(f"  {me.indicator} | {me.time} | 预期{me.forecast} | {me.impact}({me.score}/10)")

        tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tom_e = [e for e in filter_high_impact_events(events) if str(e.get("Date", "")).startswith(tomorrow_str)]
        if tom_e:
            lines.append(f"  --- 明日 ---")
            for e in tom_e[:5]:
                me = event_to_macro_event(e)
                lines.append(f"  {me.indicator} | {me.time} | 预期{me.forecast}")
    else:
        lines.append("  ⚠️ 数据暂不可用")

    return "\n".join(lines)
