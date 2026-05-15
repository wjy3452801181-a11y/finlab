"""板块扫描 — 滞涨标的筛选"""

from typing import Optional
import pandas as pd

from finlab.ashare.data import login, logout, fetch_history, StockData
from finlab.core.config import get_config

# 板块和标的定义（从配置加载，默认值在 core/config.py）
def _load_categories() -> dict[str, list[tuple[str, str]]]:
    return get_config().sectors

DEFAULT_CATEGORIES = _load_categories()


def scan_sectors(
    categories: dict = None,
    end_date: str = None,
    exclude: list[str] = None,
) -> list[dict]:
    """扫描A股板块，筛选滞涨标的

    Args:
        categories: 板块定义字典，默认 DEFAULT_CATEGORIES
        end_date: 结束日期
        exclude: 排除的板块列表

    Returns:
        扫描结果列表（每项含 板块/代码/名称/最新价/今日涨幅/5日涨幅/换手/量比）
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES
    if exclude is None:
        exclude = []

    logged_in = login()
    if not logged_in:
        print("Baostock login failed")
        return []

    results = []
    try:
        for cat_name, stocks in categories.items():
            if cat_name in exclude:
                continue
            for code, name in stocks:
                sd = fetch_history(code, name, days=7, end_date=end_date)
                if sd is None:
                    continue
                result = _analyze_stock(sd, code, name, cat_name)
                if result:
                    results.append(result)
    finally:
        logout()

    return results


def _analyze_stock(sd: StockData, code: str, name: str, category: str) -> Optional[dict]:
    """分析单个标的"""
    df = sd.df
    if len(df) < 3:
        return None

    today_pct = float(df["pctChg"].iloc[-1])
    # 估算5日开盘价
    d5_open = float(df["close"].iloc[0]) / (1 + float(df["pctChg"].iloc[0]) / 100)
    d5_close = float(df["close"].iloc[-1])
    d5_pct = round((d5_close - d5_open) / d5_open * 100, 2)
    avg_turn = float(df["turn"].mean())
    latest = float(df["close"].iloc[-1])
    avg_vol = float(df["volume"].mean())
    vol_ratio = round(float(df["volume"].iloc[-1]) / avg_vol, 2) if avg_vol > 0 else 0

    return {
        "板块": category,
        "代码": code,
        "名称": name,
        "最新价": latest,
        "今日涨幅%": round(today_pct, 2),
        "5日涨幅%": d5_pct,
        "日均换手%": round(avg_turn, 2),
        "量比": vol_ratio,
    }


def print_sector_scan(results: list[dict], top_n: int = 15):
    """打印板块扫描结果"""
    if not results:
        print("无数据")
        return

    print(f"\n{'='*80}")
    print(f"A股板块扫描 — 筛选滞涨标的（今日未大涨+5日未提前抢跑）")
    print(f"{'='*80}")

    # 按板块分组打印
    seen_cats = set(r["板块"] for r in results)
    for cat in sorted(seen_cats):
        subset = [r for r in results if r["板块"] == cat]
        subset.sort(key=lambda x: x["今日涨幅%"])

        print(f"\n▶ {cat}")
        for r in subset:
            flag = ""
            if r["5日涨幅%"] >= 8:
                flag = " ← 5日已涨太多"
            elif abs(r["今日涨幅%"]) >= 3:
                flag = " ← 今日涨/跌偏大"
            print(
                f"  {r['名称']:<10} {r['最新价']:<10} "
                f"今日{r['今日涨幅%']:>+6.2f}%  "
                f"5日{r['5日涨幅%']:>+7.2f}%  "
                f"换手{r['日均换手%']:>6.2f}%  "
                f"量比{r['量比']:>5.2f}{flag}"
            )

    # 推荐
    candidates = [
        r for r in results
        if abs(r["今日涨幅%"]) < 4 and r["5日涨幅%"] < 8
    ]
    candidates.sort(key=lambda r: r["5日涨幅%"])

    print(f"\n\n{'='*80}")
    print("推荐（逻辑驱动 + 尚未明显上涨）：")
    print(f"{'='*80}")

    for r in candidates[:top_n]:
        desc = ""
        if r["5日涨幅%"] < 0:
            desc = "回调充分，绝对低吸位"
        elif r["5日涨幅%"] < 2:
            desc = "横盘滞涨，没抢跑"
        elif r["5日涨幅%"] < 5:
            desc = "温和上升，启动阶段"
        else:
            desc = "有一定涨幅但未透支"

        if r["量比"] < 0.5:
            desc += ", 量能不足"
        elif r["量比"] > 3:
            desc += ", 放量明显"

        print(
            f"  {r['名称']:<10} {r['代码']:<12} {r['最新价']:<8}  "
            f"5日{r['5日涨幅%']:>+7.2f}%  "
            f"今日{r['今日涨幅%']:>+6.2f}%  — {desc}"
        )
