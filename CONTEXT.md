# FinLab 领域词汇

> 由 /improve-codebase-architecture 生成，2026-05-15。
> 所有架构讨论使用此文件定义的术语，避免命名漂移。

## 模块地图

```
cli.py          CLI 入口（Typer），只做路由注册和渲染，不包含业务逻辑
core/           跨模块共享的基础设施
  _time.py      BJT 时区常量（零依赖）
  models.py     数据模型（Score, MacroEvent, MarketSnapshot, AnalysisResult）
  sources.py    数据源抽象（QuoteSource, HistoricalSource ABC）
  scoring.py    统一评分引擎 — 唯一入口 score_event()
  jin10.py      金十 MCP 适配器（单例客户端 + QuoteSource 适配器）
  config.py     用户配置管理（~/.config/finlab/config.toml）
macro/          宏观模块 — 经济日历拉取、评分、报告生成
  fetchers.py   经济日历 + ForexLive 新闻（TradingEconomics API）
  scoring.py    向后兼容包装层 → 委托给 core.scoring
  report.py     宏观简报 / 摘要生成器
ashare/         A股模块 — 数据、追踪、板块扫描
  data.py       Baostock 封装 + HistoricalSource 适配器
  tracker.py    持仓追踪（止损/止盈/量价预警）
  screener.py   板块扫描（滞涨标的筛选）
news/           新闻模块 — 快讯、分析、简报
  fetchers.py   格式化函数（委托 core.jin10 获取数据）
  analysis.py   金融事件文本分类 + 影响分析
  brief.py      快讯简报 / 日历简报 / 搜索简报生成
report/         研报模块 — 四层结构周报生成
  fetchers.py   Yahoo Finance 批量行情 + 金十行情快照
  sections.py   四大章节生成器（数据/政策/专题/观点）
  generator.py  完整研报组装 + Obsidian 输出
```

## 核心概念

**评分引擎 (Scoring Engine)**
单一模块 `core/scoring.py`，所有宏观事件打分通过 `score_event()` 入口。
- 输入：事件名 + 实际/预期/前值
- 输出：`Score(value=1-10, direction, reason)`
- 指标分类规则表集中维护在 `_RULES`

**数据源适配器 (Data Source Adapter)**
每个外部数据源通过适配器满足 `core/sources.py` 的接口。
- `Jin10QuoteAdapter` → `QuoteSource`（金十实时报价）
- `BaostockAdapter` → `HistoricalSource`（A股历史日线）
- 两个适配器 = 真实缝，可用于测试替身注入

**三角色研究框架**
| 角色 | 对标投行 | 负责 |
|------|---------|------|
| 宏观总监 | GS+UBS+Citi | 全球宏观、利率、美元、大类资产 |
| 行业首席 | MS+CICC+NRI | 行业赛道、A股港股、板块轮动 |
| 交易执行官 | JPM+Bernstein+BofA | 入场时机、止损止盈、反共识Alpha |

**评分体系**
| 分值 | 含义 |
|------|------|
| 8-10 | 强烈利多 |
| 6-7 | 利好 |
| 4-5 | 中性 |
| 2-3 | 利空 |
| 1 | 强烈利空 |

**研报四层结构**
1. 数据更新 — 核心指标、图表、异常
2. 政策与新闻 — 宏观→行业→公司分层
3. 专题分析 — 事件→原因→传导→预判
4. 投资观点 — 具体标的建议 + 风险提示

## 设计决策

### 为什么就业指标没有「大幅超预期」阈值
就业数据（NFP 等）的原始格式不统一（万/千/百万），无法用一个固定的 surprise 绝对值判断「大幅」。
当前采用保守策略：就业高于预期 → 中性(5分)，低于预期 → 利好(6分)。
未来如有可靠的数据标准化层，可重新引入幅度判断。

### 为什么评分引擎放在 core/ 而非独立模块
评分被 macro/ 和 news/ 两个模块共享。放在 core/ 避免循环导入，且符合「跨模块共享的基础设施」定位。

### 为什么 BJT 放在 _time.py 而非 core/__init__.py
core/__init__.py 导入 core.jin10，core.jin10 需要 BJT。
如果 BJT 定义在 core/__init__.py，会形成循环导入。
_time.py 是零依赖模块，解决此问题。

## 数据源

| 数据源 | 适配器 | 覆盖范围 |
|--------|--------|---------|
| Baostock | BaostockAdapter | A股日线/分钟线 |
| yfinance | （直接调用） | 美股/加密/外汇/商品 |
| 金十 MCP | Jin10QuoteAdapter | 实时快讯+财经日历+行情快照 |
| TradingEconomics | （macro/fetchers.py） | 全球经济日历 |
| ForexLive | （macro/fetchers.py） | 宏观新闻 RSS |
