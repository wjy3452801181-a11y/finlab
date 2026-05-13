"""宏观数据抓取器 — 各国宏观经济指标"""

import httpx
from typing import Any

TE_API_URL = "https://api.tradingeconomics.com/calendar"

# 关注的宏观事件关键词
WATCHED_EVENTS = [
    "PPI", "CPI", "PCE", "GDP", "NFP", "FOMC", "ISM", "Retail Sales",
    "Consumer Sentiment", "Initial Jobless", "Durable Goods",
    "Factory Orders", "Industrial Production", "Housing Starts",
    "New Home Sales", "Existing Home Sales", "Conference Board",
    "Beige Book", "Nonfarm Payrolls", "Employment", "Unemployment",
]


def fetch_economic_calendar(
    country: str = "us",
    days_ahead: int = 2,
    api_key: str = "guest:guest",
    timeout: float = 15.0,
) -> list[dict[str, Any]]:
    """从 TradingEconomics 获取经济日历数据

    Args:
        country: 国家代码（us, cn, jp 等）
        days_ahead: 向前看几天
        api_key: TradingEconomics API key
        timeout: 超时秒数

    Returns:
        事件列表，每个事件包含 Date/Event/Actual/Forecast/Previous/Importance
    """
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    end = (datetime.datetime.now() + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    url = f"{TE_API_URL}?country={country}&d1={today}&d2={end}&format=json&c={api_key}"

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return [{"error": f"获取经济日历失败: {e}"}]


def filter_high_impact_events(events: list[dict], min_importance: int = 2) -> list[dict]:
    """筛选高重要性事件

    Args:
        events: 事件列表
        min_importance: 最低重要性（3=极高, 2=高, 1=中）

    Returns:
        筛选后的事件列表
    """
    import re
    result = []
    for e in events:
        if "error" in e:
            continue
        imp = e.get("Importance", 1)
        name = e.get("Event", "")
        # 高重要性或匹配关注关键词
        if imp >= min_importance or any(
            w.lower() in name.lower() for w in WATCHED_EVENTS
        ):
            result.append(e)
    return result


def fetch_forexlive_news(limit: int = 20, timeout: float = 10.0) -> list[dict]:
    """从 ForexLive RSS 获取最新宏观新闻

    Returns:
        新闻条目列表 [{title, pubdate}]
    """
    import re
    url = "https://www.forexlive.com/feed/news"
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        items = []
        for item in re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)[:limit]:
            title = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            pubdate = re.findall(r'<pubDate>(.*?)</pubDate>', item)
            title = title[0] if title else ""
            if title:
                items.append({"title": title.strip(), "pubdate": pubdate[0] if pubdate else ""})
        return items
    except Exception:
        return []
