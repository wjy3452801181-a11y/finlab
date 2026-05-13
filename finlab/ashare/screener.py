"""板块扫描 — 滞涨标的筛选"""

from typing import Optional
import pandas as pd

from finlab.ashare.data import login, logout, fetch_history, StockData

# 板块和标的定义
DEFAULT_CATEGORIES = {
    "算力/AI": [
        ("sh.600941", "中国移动"), ("sh.600050", "中国联通"), ("sh.601728", "中国电信"),
        ("sz.000938", "紫光股份"), ("sh.600498", "烽火通信"), ("sz.000063", "中兴通讯"),
        ("sz.002230", "科大讯飞"), ("sh.600570", "恒生电子"),
    ],
    "芯片": [
        ("sh.688981", "中芯国际"), ("sz.002371", "北方华创"), ("sh.603501", "韦尔股份"),
        ("sz.300661", "圣邦股份"), ("sh.603986", "兆易创新"), ("sz.002049", "紫光国微"),
        ("sz.300782", "卓胜微"), ("sz.002185", "华天科技"),
    ],
    "消费电子": [
        ("sz.002475", "立讯精密"), ("sz.002241", "歌尔股份"), ("sh.603160", "汇顶科技"),
        ("sz.002600", "领益智造"), ("sh.600745", "闻泰科技"),
    ],
    "新能源": [
        ("sz.002459", "晶澳科技"), ("sz.300274", "阳光电源"), ("sh.688599", "天合光能"),
        ("sh.601012", "隆基绿能"), ("sz.300750", "宁德时代"), ("sh.600438", "通威股份"),
    ],
    "军工": [
        ("sh.600760", "中航沈飞"), ("sh.600893", "航发动力"), ("sz.000768", "中航西飞"),
        ("sz.002179", "中航光电"), ("sh.600150", "中国船舶"), ("sh.600879", "航天电子"),
    ],
    "金融": [
        ("sh.600036", "招商银行"), ("sh.601318", "中国平安"), ("sh.600030", "中信证券"),
        ("sh.601939", "建设银行"),
    ],
    "消费": [
        ("sh.600519", "贵州茅台"), ("sz.000568", "泸州老窖"), ("sh.600809", "山西汾酒"),
        ("sz.000858", "五粮液"), ("sh.600887", "伊利股份"), ("sh.600276", "恒瑞医药"),
    ],
    "金属资源": [
        ("sh.600547", "山东黄金"), ("sh.600489", "中金黄金"), ("sh.601899", "紫金矿业"),
        ("sz.000831", "中国稀土"), ("sh.600010", "包钢股份"),
    ],
}


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
