"""研报模块 — 数据获取（Yahoo Finance + 金十MCP行情）"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional

from finlab.core import BJT
from finlab.core.config import get_config

logger = logging.getLogger(__name__)

# 研报默认覆盖的标的分组 (Yahoo Finance tickers)
# 延迟加载，避免 import 时读取磁盘配置
_TICKER_GROUPS_CACHE: dict[str, list[str]] | None = None


def get_ticker_groups() -> dict[str, list[str]]:
    global _TICKER_GROUPS_CACHE
    if _TICKER_GROUPS_CACHE is None:
        _TICKER_GROUPS_CACHE = get_config().ticker_groups
    return _TICKER_GROUPS_CACHE


def fetch_yfinance_batch(
    tickers: list[str],
    start: date,
    end: date,
    timeout: int = 30,
) -> dict[str, dict]:
    """批量获取 Yahoo Finance 历史行情

    Args:
        tickers: 标的列表
        start: 开始日期
        end: 结束日期
        timeout: 超时秒数

    Returns:
        {ticker: {date: {open, high, low, close, volume}}}
    """
    import yfinance as yf

    results = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(start=start, end=end, auto_adjust=True, timeout=timeout)
            if hist.empty:
                continue

            data = {}
            for idx, row in hist.iterrows():
                ds = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx.date())
                data[ds] = {
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                }
            results[ticker] = data
        except Exception:
            logger.warning("yfinance 获取失败: %s", ticker)
            continue
    return results


def calc_weekly_change(data: dict[str, dict]) -> Optional[float]:
    """计算周涨跌幅(百分比)

    Args:
        data: {date_str: {close: float, ...}}

    Returns:
        百分比涨跌幅，无数据返回 None
    """
    dates = sorted(data.keys())
    if len(dates) < 2:
        return None
    first_close = data[dates[0]]["close"]
    last_close = data[dates[-1]]["close"]
    if first_close == 0:
        return None
    return round((last_close - first_close) / first_close * 100, 2)


def fetch_report_quotes() -> dict[str, Optional[float]]:
    """获取当前行情快照（通过金十MCP统一适配器）

    Returns:
        {品种代码: 最新价}
    """
    from finlab.core.jin10 import fetch_quotes

    return fetch_quotes({
        "上证": "000001",
        "深证": "399001",
        "创业板": "399006",
        "黄金": "XAUUSD",
        "原油": "USOIL",
        "欧元": "EURUSD",
        "美元指数": "USDX",
    })


def default_date_range() -> tuple[date, date]:
    """返回默认研报周期：最近7天"""
    today = datetime.now(BJT).date()
    return today - timedelta(days=7), today


def format_yfinance_table(
    results: dict[str, dict],
    group_key: str = "",
) -> str:
    """将 yfinance 数据格式化为表格字符串"""
    lines = []
    if group_key:
        lines.append(f"### {group_key}")
    lines.append(f"| {'标的':<12} | {'周涨跌幅':<12} | {'最新价':<12} | {'最高':<12} | {'最低':<12} |")
    lines.append(f"|{'-'*14}|{'-'*14}|{'-'*14}|{'-'*14}|{'-'*14}|")

    for ticker, data in results.items():
        change = calc_weekly_change(data)
        dates = sorted(data.keys())
        last_close = data[dates[-1]]["close"] if dates else "-"
        high = max(d["high"] for d in data.values()) if data else "-"
        low = min(d["low"] for d in data.values()) if data else "-"
        change_str = f"{change:+.2f}%" if change is not None else "-"
        lines.append(
            f"| {ticker:<12} | {change_str:<12} | {last_close:<12} | {high:<12} | {low:<12} |"
        )
    return "\n".join(lines)
