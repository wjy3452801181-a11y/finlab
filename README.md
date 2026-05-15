# FinLab

> **Your Open-Source Personal Investment Research Lab** — Macro, A-Shares, Crypto, News & Reports — all in one CLI toolchain.
>
> One person, one research department. Three roles, one framework.
>
> **你的开源个人投行研究室** — 宏观、A股、加密、新闻、研报一站式分析工具链。
> 一个人就是一个研究部门。三个角色，一套框架。

---

## 背景 / Background

**中文：** FinLab 源于一个真实需求：个人交易者需要像投行研究部一样系统化地分析市场，但 Bloomberg Terminal 太贵、Excel 太散、普通工具又不够深。于是我们把一套跑通了半年多的个人研究框架开源出来。

**English:** FinLab was born from a real need: individual traders need systematic market analysis like an investment bank's research department — but Bloomberg Terminal is too expensive, Excel is too fragmented, and off-the-shelf tools aren't deep enough. So we open-sourced a personal research framework that has been running in production for over six months.

### 三角色研究框架 / Three-role Research Framework

| Role | Focus |
|------|-------|
| **宏观总监 / Macro Director** (GS+UBS+Citi) | Global macro, rates, USD, asset allocation |
| **行业首席 / Sector Chief** (MS+CICC+NRI) | Sector rotation, China assets, Asian FX |
| **交易执行官 / Trade Executor** (JPM+Bernstein+BofA) | Entry timing, stop-loss, contrarian alpha |

---

## 快速开始 / Quick Start

```bash
pip install finlab

# 查看可用命令 / See available commands
finlab --help

# 模块预览 / Preview modules
finlab macro
finlab ashare
| finlab news
finlab news
finlab report
```

---

## 模块 / Modules

| Module | Functionality | Status |
|--------|--------------|--------|
| `finlab macro` | Macro data fetching + scoring system (PPI/CPI/NFP/Unemployment) | ✅ 完成 / Done |
| `finlab ashare` | A-share sector scan + stock screening + trend analysis | ✅ 完成 / Done |
| `finlab news` | Real-time flash news + financial event analysis + briefs | ✅ 完成 / Done |
| `finlab report` | One-click 4-layer weekly report generation → Obsidian | ✅ 完成 / Done |

### 评分体系 / Scoring System

| Score | Label |
|-------|-------|
| 8-10 | 🚀 Strongly Bullish / 强烈利多 |
| 6-7 | ✅ Bullish / 利好 |
| 4-5 | ⚖️ Neutral / 中性 |
| 2-3 | 🔴 Bearish / 利空 |
| 1 | ⚠️ Strongly Bearish / 强烈利空 |

### 报告四层结构 / Four-Layer Report Structure

1. **Data Update / 数据更新** — Core indicators, charts, anomalies
2. **Policy & News / 政策与新闻** — Layered: macro → industry → company
3. **Thematic Analysis / 专题分析** — Event → cause → transmission → forecast
4. **Investment View / 投资观点** — Specific picks + risk warnings

---

## 架构 / Architecture

```
finlab/
├── finlab/
│   ├── cli.py          # Typer CLI 入口 / Entry point
│   ├── core/           # 数据模型 + 数据源抽象层
│   │   ├── models.py   # Dataclasses (MacroEvent, AShareSignal, etc.)
│   │   └── sources.py  # DataSource ABC + 插件化
│   ├── macro/          # 宏观模块 / Macro module
│   ├── ashare/         # A股模块 / A-share module
│   ├── news/           # 新闻模块 / News module
│   └── report/         # 研报模块 / Report module
├── tests/
├── data/
└── docs/
```

### 数据源 / Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| Baostock | A-share historical | Daily/minute kline |
| yfinance | Global market | US stocks, crypto, FX, commodities |
| Jin10 (MCP) | Real-time flash + calendar | Macro data, breaking events |
| 金十数据 / Jin10 Markets | Market snapshot | Indices, commodities, FX |

---

## 开发 / Development

```bash
git clone https://github.com/wjy3452801181-a11y/finlab.git
cd finlab
pip install -e ".[all]"

# 运行测试 / Run tests
pytest tests/

# 代码检查 / Lint
ruff check finlab/
```

---

## 贡献 / Contributing

Feedback is welcome — bugs, feature requests, documentation improvements, or naming complaints.

- **提 Issue / Open an Issue** — [github.com/wjy3452801181-a11y/finlab/issues](https://github.com/wjy3452801181-a11y/finlab/issues)
- **PR** — Fork, code, and submit a PR

Discussions about data source integrations, new modules, or technical architecture are also welcome in Issues.

---

## 许可 / License

MIT © 2026 [ray wang](https://github.com/wjy3452801181-a11y)
