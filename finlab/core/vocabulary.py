"""统一关键词注册表 — 宏观指标的多维分类单一数据源

所有模块从此查询，不再各自维护关键词列表。
增删改一处生效，覆盖评分/分类/简报/过滤全部场景。
"""

from dataclasses import dataclass
from collections import defaultdict


@dataclass
class _Indicator:
    """单个宏观指标的多维属性"""
    canonical: str               # 规范名
    aliases: tuple[str, ...]     # 所有搜索别名（英文 + 中文）
    scoring_category: str | None # → core/scoring._RULES 分类
    scoring_surprise_up: str | None  # "利多"/"利空"/"中性"
    event_category: str | None   # → news/analysis.EVENT_CATEGORIES
    brief_category: str | None   # → news/brief._guess_category


# ── 统一注册表 ──────────────────────────────────────────
_REGISTRY: list[_Indicator] = [
    # ── 通胀 ──
    _Indicator("CPI", ("CPI", "消费者物价指数", "居民消费价格"),
               "通胀", "利空", "通胀", "宏观"),
    _Indicator("PPI", ("PPI", "生产者价格指数", "生产者价格"),
               "通胀", "利空", "通胀", "宏观"),
    _Indicator("PCE", ("PCE", "核心PCE", "个人消费支出"),
               "通胀", "利空", "通胀", "宏观"),
    _Indicator("核心CPI", ("核心CPI", "核心居民消费价格"),
               "通胀", "利空", "通胀", "宏观"),

    # ── 就业 ──
    _Indicator("NFP", ("NFP", "非农", "Nonfarm Payrolls", "非农就业", "非农就业人口", "就业人口"),
               "就业", "中性", "就业", "宏观"),
    _Indicator("ADP", ("ADP", "ADP就业"),
               "就业", "中性", "就业", "宏观"),
    _Indicator("JOLTS", ("JOLTS", "JOLTS职位空缺"),
               "就业", "中性", "就业", "宏观"),
    _Indicator("Employment", ("Employment", "就业"),
               "就业", "中性", "就业", "宏观"),

    # ── 失业 ──
    _Indicator("Unemployment", ("Unemployment", "Unemployment Rate", "失业", "失业率", "失业金"),
               "失业", "利空", "就业", "宏观"),
    _Indicator("Initial Jobless", ("Initial Jobless", "Initial Jobless Claims", "初请", "初请失业金"),
               "失业", "利空", "就业", "宏观"),

    # ── 增长 ──
    _Indicator("GDP", ("GDP", "国内生产总值"),
               "增长", "利多", "增长", "宏观"),
    _Indicator("Retail Sales", ("Retail Sales", "零售", "零售销售"),
               "增长", "利多", "增长", "宏观"),
    _Indicator("Industrial Production", ("Industrial Production", "工业产出", "工业生产"),
               "增长", "利多", "增长", "宏观"),
    _Indicator("Durable Goods", ("Durable Goods", "耐用品", "耐用品订单"),
               "增长", "利多", "增长", "宏观"),
    _Indicator("Factory Orders", ("Factory Orders", "工厂订单", "制造业订单"),
               "增长", "利多", "增长", "宏观"),
    _Indicator("ISM", ("ISM", "ISM制造业", "ISM服务业", "PMI"),
               "增长", "利多", "增长", "宏观"),
    _Indicator("Consumer Sentiment", ("Consumer Sentiment", "消费者信心", "消费者信心指数", "密歇根消费者信心"),
               "增长", "利多", "增长", "宏观"),
    _Indicator("Conference Board", ("Conference Board", "Conference Board Consumer Confidence", "谘商会", "谘商会消费者信心"),
               "增长", "利多", "增长", "宏观"),

    # ── 地产 / 信心 ──
    _Indicator("Housing Starts", ("Housing Starts", "Housing", "新屋开工"),
               "地产/信心", "利多", "增长", "宏观"),
    _Indicator("New Home Sales", ("New Home Sales", "Home Sales", "成屋销售", "新屋销售", "Existing Home Sales", "Sentiment"),
               "地产/信心", "利多", "增长", "宏观"),
    _Indicator("营建许可", ("Building Permits", "营建许可"),
               "地产/信心", "利多", "增长", "宏观"),

    # ── 货币 / 央行 ──
    _Indicator("FOMC", ("FOMC", "美联储", "美联储利率决议", "Federal Reserve", "联邦公开市场委员会",
                        "鲍威尔", "Powell", "加息", "降息", "利率决议", "利率", "央行"),
               None, None, "货币政策", "央行动态"),
    _Indicator("Beige Book", ("Beige Book", "褐皮书"),
               None, None, "货币政策", "央行动态"),

    # ── 地缘 / 贸易 ──
    _Indicator("贸易帐", ("关税", "贸易帐", "贸易", "制裁", "谈判", "协议", "冲突", "战争", "停火"),
               None, None, "地缘/贸易", "地缘"),

    # ── 行业 / 公司（不在 REGISTRY 作为单体指标，而是分类关键词）──
    _Indicator("行业/公司", ("财报", "营收", "净利润", "订单", "产能", "芯片", "新能源", "汽车", "医药", "AI", "算力",
                           "利润", "并购", "上市"),
               None, None, "行业/公司", "行业"),
]


# ── 查询函数 ────────────────────────────────────────────

def _all_entries() -> list[_Indicator]:
    return _REGISTRY


def _match(event_name: str) -> _Indicator | None:
    """根据事件名匹配注册表中的指标（最长别名优先）"""
    best = None
    best_len = 0
    for indicator in _REGISTRY:
        for alias in indicator.aliases:
            if alias.lower() in event_name.lower():
                if len(alias) > best_len:
                    best = indicator
                    best_len = len(alias)
    return best


# ── 导出给 core/scoring.py ─────────────────────────────

def scoring_rules() -> list[tuple[tuple[str, ...], str, str]]:
    """返回 _RULES 格式：[(keywords_tuple, surprise_up_direction, category)]"""
    result = []
    # 聚合：同一 (scoring_category, scoring_surprise_up) 组合的关键词合并
    groups: dict[tuple[str | None, str | None], list[str]] = defaultdict(list)
    for ind in _REGISTRY:
        key = (ind.scoring_category, ind.scoring_surprise_up)
        groups[key].extend(ind.aliases)

    for (cat, direction), aliases in groups.items():
        if cat is None or direction is None:
            continue
        result.append((tuple(aliases), direction, cat))
    return result


# ── 导出给 news/analysis.py ────────────────────────────

def event_categories() -> dict[str, list[str]]:
    """返回 EVENT_CATEGORIES 格式：{category: [keywords]}"""
    groups: dict[str, list[str]] = defaultdict(list)
    for ind in _REGISTRY:
        if ind.event_category:
            groups[ind.event_category].extend(ind.aliases)
    return dict(groups)


def default_score_map() -> dict[str, tuple[str, str]]:
    """返回 DEFAULT_SCORE_MAP 格式：{category: (direction, reason)}"""
    return {
        "通胀": ("利空", "紧缩预期强化"),
        "就业": ("中性", "劳动力市场韧性"),
        "增长": ("利多", "经济韧性强劲"),
        "货币政策": ("多空分歧", "取决于具体决策方向"),
        "地缘/贸易": ("利空", "不确定性上升"),
        "行业/公司": ("中性", "需结合个股基本面"),
    }


# ── 导出给 news/brief.py ───────────────────────────────

def brief_categories() -> list[tuple[str, list[str]]]:
    """返回 _guess_category 格式：[(category, [keywords])]"""
    groups: dict[str, list[str]] = defaultdict(list)
    for ind in _REGISTRY:
        if ind.brief_category:
            groups[ind.brief_category].extend(ind.aliases)

    # 加上行情和公司（不在 REGISTRY 中作为指标，但是简报分类需要）
    groups["行情"].extend(["上涨", "下跌", "涨幅", "跌幅", "收盘", "开盘"])
    groups["公司"].append("上市")

    return list(groups.items())


# ── 导出给 macro/fetchers.py + macro/director.py ───────

def watched_keywords() -> list[str]:
    """返回 WATCHED_EVENTS 格式（英文关键词列表，用于 TradingEconomics 和 ForexLive）"""
    # 只取有 scoring 分类的指标（真正有经济影响的），所有别名合并
    result = []
    for ind in _REGISTRY:
        if ind.scoring_category is not None:
            result.extend(ind.aliases)
    return result


def cn_match_keywords() -> list[str]:
    """返回中文快讯匹配关键词（所有别名）"""
    result = []
    for ind in _REGISTRY:
        result.extend(ind.aliases)
    return result


# ── 导出给 news/brief._extract_high_impact ──────────────

def flash_trigger_words() -> list[str]:
    """快讯高影响触发词"""
    return [
        "突发", "紧急", "重大", "央行", "加息", "降息", "利率决议",
        "CPI", "PPI", "非农", "FOMC", "关税", "制裁",
    ]
