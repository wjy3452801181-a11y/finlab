"""宏观事件评分 — 委托给 core.scoring 统一引擎"""

from finlab.core.models import MacroEvent, Score
from finlab.core.scoring import score_event


def calc_impact_score(event_name: str, actual: str, forecast: str, previous: str) -> int:
    """计算宏观事件的多空影响评分（委托给统一引擎）

    Returns:
        评分 1-10
    """
    return score_event(event_name, actual, forecast, previous).value


def format_score(score: int) -> str:
    """将评分格式化为可读的带emoji字符串"""
    return Score(value=score).as_label()


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

    s = score_event(event_name, actual, forecast, previous)

    return MacroEvent(
        time=time_part,
        country=event.get("Country", ""),
        indicator=event_name,
        actual=float(actual) if actual not in ("-", "") else None,
        forecast=float(forecast) if forecast not in ("-", "") else None,
        previous=float(previous) if previous not in ("-", "") else None,
        score=s.value,
        direction=s.direction,
        reason=s.reason,
    )
