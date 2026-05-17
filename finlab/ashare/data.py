"""A股数据模块 — Baostock 封装"""

from typing import Optional
import pandas as pd
import baostock as bs

__all__ = [
    "login", "logout",
    "fetch_history",
    "StockData",
]


class StockData:
    """A股标的日线数据容器"""

    def __init__(self, code: str, name: str, df: pd.DataFrame):
        self.code = code
        self.name = name
        self.df = df

    @property
    def last(self) -> pd.Series:
        return self.df.iloc[-1]

    @property
    def prev(self) -> Optional[pd.Series]:
        return self.df.iloc[-2] if len(self.df) > 1 else None

    @property
    def close(self) -> float:
        return float(self.last["close"])

    @property
    def pct(self) -> float:
        return float(self.last["pctChg"])

    @property
    def volume(self) -> float:
        return float(self.last["volume"])

    @property
    def turnover(self) -> float:
        return float(self.last["turn"])

    @property
    def high(self) -> float:
        return float(self.last["high"])

    @property
    def low(self) -> float:
        return float(self.last["low"])

    @property
    def ma5(self) -> float:
        return float(self.df["close"].tail(5).mean())

    @property
    def avg_vol_5(self) -> float:
        return float(self.df["volume"].tail(5).mean())

    @property
    def vol_ratio(self) -> float:
        avg = self.avg_vol_5
        return self.volume / avg if avg > 0 else 1.0


def login() -> bool:
    """登录 Baostock"""
    lg = bs.login()
    return lg.error_code == "0"


def logout():
    """登出 Baostock"""
    bs.logout()


def fetch_history(
    code: str,
    name: str = "",
    days: int = 10,
    end_date: Optional[str] = None,
    adjust: str = "3",
) -> Optional[StockData]:
    """获取A股历史日线数据

    Args:
        code: 股票代码 (如 "sz.000063")
        name: 股票名称
        days: 需要的交易日数（实际多拉一些以跳过周末）
        end_date: 结束日期，默认今天
        adjust: 复权方式（3=前复权）

    Returns:
        StockData 对象，或 None（数据不足时）
    """
    from datetime import datetime, timedelta

    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    start_dt = datetime.now() - timedelta(days=days + 14)
    start_date = start_dt.strftime("%Y-%m-%d")

    rs = bs.query_history_k_data_plus(
        code,
        "date,open,high,low,close,volume,amount,turn,pctChg",
        start_date=start_date, end_date=end_date,
        frequency="d", adjustflag=adjust,
    )

    rows = []
    while rs.next():
        rows.append(rs.get_row_data())

    if len(rows) < 2:
        return None

    df = pd.DataFrame(rows, columns=[
        "date", "open", "high", "low", "close",
        "volume", "amount", "turn", "pctChg",
    ])
    for c in ["open", "high", "low", "close", "volume", "amount", "turn", "pctChg"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return StockData(code, name, df)


# ── HistoricalSource 适配器 ─────────────────────────────

class BaostockAdapter:
    """Baostock 历史数据适配器 — 提供 A 股历史日线数据"""

    def name(self) -> str:
        return "baostock"

    def available(self) -> bool:
        return login()

    def fetch(self, symbol: str, start: str, end: str) -> Optional["StockData"]:
        """拉取历史日线（封装 login/logout）"""
        logged_in = login()
        if not logged_in:
            return None
        try:
            return fetch_history(symbol, name="", end_date=end)
        finally:
            logout()
