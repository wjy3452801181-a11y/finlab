"""统一评分引擎 — 宏观事件 → 1-10 多空评分

合并自 macro/scoring.py 和 news/analysis.py 的评分逻辑。
所有模块通过此唯一入口打分，保证规则一致。
"""

from finlab.core.models import Score


def _classify(event_name: str) -> tuple[str, str] | None:
    """根据事件名匹配指标分类，返回 (surprise_up_direction, category_label) 或 None"""
    from finlab.core.vocabulary import _match
    matched = _match(event_name)
    if matched and matched.scoring_category and matched.scoring_surprise_up:
        return matched.scoring_surprise_up, matched.scoring_category
    return None


def _clean_value(raw: str) -> float | None:
    """清洗数值字符串：去 %/M/K/逗号"""
    if not raw or raw in ("-", ""):
        return None
    try:
        return float(raw.strip("%").strip("M").strip("K").replace(",", ""))
    except (ValueError, TypeError):
        return None


def score_event(
    event_name: str,
    actual: str = "",
    forecast: str = "",
    previous: str = "",
) -> Score:
    """计算宏观事件多空影响评分（1-10）

    唯一入口。所有模块（macro / news / report）通过此函数打分。

    评分规则：
      - 通胀指标（PPI/CPI/PCE）：高于预期 → 利空（加息预期），低于 → 利多
      - 增长指标（GDP/零售/工业产出等）：高于预期 → 利多，低于 → 利空
      - 就业指标（NFP/非农等）：略超预期 → 中性(~5)，大幅超预期(>0.3) → 利空
      - 失业指标：高于预期 → 利空，低于 → 利多
      - 其他：高于预期 → 利多（默认）

    Returns:
        Score(value=1-10, direction, reason)
    """
    a = _clean_value(actual)
    f = _clean_value(forecast)

    if a is None or f is None:
        return Score(value=5, direction="中性", reason="暂无对比数据")

    surprise = a - f
    rule = _classify(event_name)

    if rule is None:
        # 未匹配 → 默认规则：高于预期利多
        category = "其他"
        if surprise > 0:
            return Score(
                value=7, direction="利多",
                reason=f"实际{a}高于预期{f}(+{surprise:+.2f})，经济韧性强劲"
            )
        elif surprise < 0:
            return Score(
                value=3, direction="利空",
                reason=f"实际{a}低于预期{f}({surprise:+.2f})，经济承压"
            )
        else:
            return Score(value=5, direction="中性", reason=f"实际{a}符合预期{f}")

    direction_up, category = rule

    if category == "通胀":
        if surprise > 0:
            return Score(
                value=3, direction="利空",
                reason=f"{category}高于预期{surprise:+.2f}，紧缩预期强化"
            )
        elif surprise < 0:
            return Score(
                value=7, direction="利多",
                reason=f"{category}低于预期{surprise:+.2f}，宽松预期强化"
            )
        else:
            return Score(value=5, direction="中性", reason=f"{category}符合预期")

    if category == "增长":
        if surprise > 0:
            return Score(
                value=7, direction="利多",
                reason=f"{category}强于预期{surprise:+.2f}，经济韧性好"
            )
        elif surprise < 0:
            return Score(
                value=3, direction="利空",
                reason=f"{category}弱于预期{surprise:+.2f}，经济承压"
            )
        else:
            return Score(value=5, direction="中性", reason=f"{category}符合预期")

    if category == "就业":
        if surprise > 0:
            return Score(
                value=5, direction="中性",
                reason=f"就业略超预期{surprise:+.2f}，影响有限"
            )
        elif surprise < 0:
            return Score(
                value=6, direction="利好",
                reason=f"就业低于预期{surprise:+.2f}，降息预期升温"
            )
        else:
            return Score(value=5, direction="中性", reason="就业符合预期")

    if category == "失业":
        if surprise > 0:
            return Score(
                value=3, direction="利空",
                reason=f"失业高于预期{surprise:+.2f}"
            )
        elif surprise < 0:
            return Score(
                value=7, direction="利多",
                reason=f"失业低于预期{surprise:+.2f}"
            )
        else:
            return Score(value=5, direction="中性", reason="失业符合预期")

    # 地产/信心 等 → 高于预期利多
    if surprise > 0:
        return Score(
            value=7, direction="利多",
            reason=f"{category}高于预期{surprise:+.2f}"
        )
    elif surprise < 0:
        return Score(
            value=3, direction="利空",
            reason=f"{category}低于预期{surprise:+.2f}"
        )
    else:
        return Score(value=5, direction="中性", reason=f"{category}符合预期")
