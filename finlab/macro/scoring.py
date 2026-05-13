"""宏观事件评分系统"""

from finlab.core.models import MacroEvent


def calc_impact_score(event_name: str, actual: str, forecast: str, previous: str) -> int:
    """计算宏观事件的多空影响评分

    Score range: 1-10
     8-10 🚀 强烈利多
     6-7  ✅ 利好
     4-5  ⚖️ 中性
     2-3  🔴 利空
     1    ⚠️ 强烈利空

    Args:
        event_name: 事件名称（如 "CPI", "PPI", "NFP"）
        actual: 实际值
        forecast: 预期值
        previous: 前值

    Returns:
        评分 1-10
    """
    score = 5
    try:
        if actual and forecast:
            actual_val = float(actual.strip("%").strip("M").strip("K"))
            forecast_val = float(forecast.strip("%").strip("M").strip("K"))
            surprise = actual_val - forecast_val

            if any(x in event_name for x in ["PPI", "CPI", "PCE"]):
                # 通胀指标：高于预期 = 利空（加息预期）
                score = 3 if surprise > 0 else 7
            elif any(x in event_name for x in ["GDP", "Retail Sales"]):
                # 增长指标：高于预期 = 利多
                score = 7 if surprise > 0 else 3
            elif any(x in event_name for x in ["NFP", "Payrolls", "Employment"]):
                # 就业：略高于预期 = 中性偏多，大幅超预期 = 利空（加息）
                score = 5 if surprise > 0 else 6
            elif "Jobless" in event_name or "Unemployment" in event_name:
                # 失业：高于预期 = 利空
                score = 7 if surprise > 0 else 3
            elif any(x in event_name for x in ["Housing", "Home Sales", "Sentiment"]):
                score = 7 if surprise > 0 else 3
            else:
                score = 7 if surprise > 0 else 3
    except (ValueError, TypeError):
        score = 5

    return max(1, min(10, score))


def format_score(score: int) -> str:
    """将评分格式化为可读的带emoji字符串"""
    if score >= 8:
        return f"{score}/10 🚀 强烈利多"
    elif score >= 6:
        return f"{score}/10 ✅ 利好"
    elif score >= 4:
        return f"{score}/10 ⚖️ 中性"
    elif score >= 2:
        return f"{score}/10 🔴 利空"
    else:
        return f"{score}/10 ⚠️ 强烈利空"


def event_to_macro_event(event: dict) -> MacroEvent:
    """将API返回的原始事件字典转换为 MacroEvent 数据模型"""
    import datetime
    raw_date = event.get("Date", "")
    if "T" in raw_date:
        time_part = raw_date.split("T")[1][:5]
    else:
        time_part = "全天"

    event_name = event.get("Event", "N/A")
    actual = str(event.get("Actual", "-"))
    forecast = str(event.get("Forecast", "-"))
    previous = str(event.get("Previous", "-"))

    score = calc_impact_score(event_name, actual, forecast, previous)

    # 判断多空方向
    if score >= 6:
        impact = "利多"
    elif score <= 3:
        impact = "利空"
    else:
        impact = "中性"

    return MacroEvent(
        time=time_part,
        country=event.get("Country", ""),
        indicator=event_name,
        actual=float(actual) if actual not in ("-", "") else None,
        forecast=float(forecast) if forecast not in ("-", "") else None,
        previous=float(previous) if previous not in ("-", "") else None,
        impact=impact,
        score=score,
    )
