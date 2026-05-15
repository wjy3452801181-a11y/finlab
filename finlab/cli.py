"""CLI 入口"""

import logging
import typer
from rich.console import Console

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

app = typer.Typer(
    name="finlab",
    help="开源个人投行研究工具链",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def callback():
    """finlab: 你的开源投行研究室"""
    pass


@app.command()
def version():
    """显示版本号"""
    from finlab import __version__
    console.print(f"finlab v{__version__}")


@app.command()
def about():
    """显示项目简介：版本、数据源、架构、评分体系"""
    from finlab import __version__
    from rich.panel import Panel
    from rich.table import Table

    console.print(f"[bold cyan]finlab v{__version__}[/bold cyan] — [bold]你的开源投行研究室[/bold]")
    console.print()

    console.print("[bold]三角色研究框架 / Three-role Research Framework[/bold]")
    roles = Table(show_header=True, header_style="bold")
    roles.add_column("角色", width=14)
    roles.add_column("对标投行", width=18)
    roles.add_column("负责", width=50)
    roles.add_row("宏观总监", "高盛 + 瑞银 + 花旗", "全球宏观、利率、美元、大类资产配置")
    roles.add_row("行业首席", "摩根士丹利 + 中金 + 野村", "行业赛道、A股港股、板块轮动")
    roles.add_row("交易执行官", "摩根大通 + 伯恩斯坦 + 美银", "入场时机、止损止盈、反共识Alpha")
    console.print(roles)
    console.print()

    console.print("[bold]数据源 / Data Sources[/bold]")
    sources = Table(show_header=True, header_style="bold")
    sources.add_column("数据源", width=16)
    sources.add_column("类型", width=16)
    sources.add_column("覆盖范围", width=50)
    sources.add_row("Baostock", "A股历史行情", "日线/分钟线")
    sources.add_row("yfinance", "全球行情", "美股/加密/外汇/商品")
    sources.add_row("Jin10 (MCP)", "实时快讯+财经日历", "宏观数据/突发事件")
    sources.add_row("金十数据", "行情快照", "指数/商品/外汇")
    console.print(sources)
    console.print()

    console.print("[bold]评分体系 / Scoring System[/bold]")
    scores = Table(show_header=True, header_style="bold")
    scores.add_column("评分", width=8, justify="center")
    scores.add_column("含义")
    scores.add_row("8-10", "🚀 Strongly Bullish / 强烈利多")
    scores.add_row("6-7", "✅ Bullish / 利好")
    scores.add_row("4-5", "⚖️ Neutral / 中性")
    scores.add_row("2-3", "🔴 Bearish / 利空")
    scores.add_row("1", "⚠️ Strongly Bearish / 强烈利空")
    console.print(scores)
    console.print()

    console.print("[bold]架构 / Architecture[/bold]")
    arch = Panel(
        "finlab/\n"
        "├── finlab/\n"
        "│   ├── cli.py           CLI 入口\n"
        "│   ├── core/            数据模型 + 数据源抽象层\n"
        "│   ├── macro/           宏观模块\n"
        "│   ├── ashare/          A股模块\n"
        "│   ├── crypto/          加密模块\n"
        "│   ├── news/            新闻模块\n"
        "│   └── report/          研报模块\n"
        "├── tests/\n"
        "├── data/\n"
        "└── docs/",
        title="Project Structure",
        border_style="dim"
    )
    console.print(arch)


@app.command()
def macro(
    country: str = typer.Option("us", "--country", "-c", help="国家代码 (us, cn, jp, etc.)"),
    days: int = typer.Option(2, "--days", "-d", help="向前看几天"),
    summary: bool = typer.Option(False, "--summary", "-s", help="精简模式（适合推送）"),
):
    """宏观数据拉取与评分"""
    from finlab.macro.report import generate_macro_report, generate_macro_summary

    with console.status("[bold yellow]📊 抓取宏观数据..."):
        if summary:
            text = generate_macro_summary(country=country)
        else:
            text = generate_macro_report(country=country, days_ahead=days)
    console.print(text)


# ── ashare ──────────────────────────────────────────────
ashare_app = typer.Typer(help="A股板块扫描与个股分析")
app.add_typer(ashare_app, name="ashare")


@ashare_app.command(name="track")
def ashare_track(
    days: int = typer.Option(10, "--days", "-d", help="回溯交易日数"),
    custom: str = typer.Option(None, "--custom", help='JSON自定义标的: {"sz.000063": {"name":"中兴通讯","entry":38.09,"stop":36.50,"target1":39.50}}'),
):
    """跟踪持仓标的：止损止盈检查 + 量价预警"""
    from finlab.ashare.tracker import TrackConfig, track_stocks, print_summary

    if custom:
        import json
        raw = json.loads(custom)
        configs = [
            TrackConfig(code=code, name=info["name"], entry=info.get("entry", 0),
                        stop=info.get("stop", 0), target1=info.get("target1", 0))
            for code, info in raw.items()
        ]
    else:
        configs = [
            TrackConfig("sz.000063", "中兴通讯", entry=38.09, stop=36.50, target1=39.50),
            TrackConfig("sh.600547", "山东黄金", entry=34.83, stop=33.50, target1=36.50),
            TrackConfig("sh.600150", "中国船舶", entry=40.50, stop=38.50, target1=43.00),
        ]

    with console.status("[bold green]🇨🇳 拉取A股数据..."):
        results = track_stocks(configs, days=days)

    if results:
        print_summary(results)


@ashare_app.command(name="scan")
def ashare_scan(
    exclude: str = typer.Option(None, "--exclude", help="排除板块（逗号分隔）"),
):
    """板块扫描：寻找滞涨标的"""
    from finlab.ashare.screener import scan_sectors, print_sector_scan

    exclude_list = [e.strip() for e in exclude.split(",")] if exclude else []

    with console.status("[bold green]🇨🇳 扫描A股板块..."):
        results = scan_sectors(exclude=exclude_list)

    if results:
        print_sector_scan(results)


# ── news ────────────────────────────────────────────────
news_app = typer.Typer(help="实时快讯与事件分析")
app.add_typer(news_app, name="news")


@news_app.command(name="flash")
def news_flash(hours: int = typer.Option(2, "--hours", "-h", help="最近几小时")):
    """获取金十实时快讯"""
    from finlab.news.fetchers import fetch_flash, format_flash_item

    with console.status("[bold yellow]📰 获取快讯..."):
        items = fetch_flash(hours=hours)

    if not items:
        console.print(f"[yellow]📭 最近{hours}小时无快讯[/yellow]")
        return

    console.print(f"[bold]📰 最近{hours}小时快讯 ({len(items)}条)[/bold]")
    console.print()
    for item in items:
        line = format_flash_item(item)
        console.print(f"  {line[:100]}")
    console.print()
    console.print(f"[dim]—— {len(items)}条快讯 ——[/dim]")


@news_app.command(name="analyze")
def news_analyze(title: str = typer.Argument(..., help="事件标题")):
    """分析金融事件影响"""
    from finlab.news.analysis import analyze_event
    from rich.panel import Panel

    with console.status(f"[bold yellow]🔍 分析: {title[:40]}..."):
        result = analyze_event(title)

    console.print(Panel(result, title_align="left", border_style="cyan"))


@news_app.command(name="brief")
def news_brief():
    """生成当前时段新闻简报（表格格式）"""
    from finlab.news.brief import build_flash_brief

    with console.status("[bold yellow]📰 生成简报..."):
        text = build_flash_brief()

    console.print(text)


@news_app.command(name="search")
def news_search(keyword: str = typer.Argument(..., help="搜索关键词")):
    """搜索金十快讯"""
    from finlab.news.fetchers import search_flash, format_flash_item

    with console.status(f"[bold yellow]🔍 搜索: {keyword}..."):
        items = search_flash(keyword)

    if not items:
        console.print(f"[yellow]未找到 \"{keyword}\" 相关快讯[/yellow]")
        return

    console.print(f"[bold]🔍 \"{keyword}\" 搜索结果 ({len(items)}条)[/bold]")
    console.print()
    for item in items[:10]:
        line = format_flash_item(item)
        console.print(f"  {line}")
    if len(items) > 10:
        console.print(f"\n[dim]... 还有{len(items)-10}条[/dim]")


@news_app.command(name="calendar")
def news_calendar():
    """显示本周财经日历"""
    from finlab.news.brief import build_calendar_brief

    with console.status("[bold yellow]📅 获取财经日历..."):
        text = build_calendar_brief()

    console.print(text)


# ── report ──────────────────────────────────────────────
report_app = typer.Typer(help="一键生成研报")
app.add_typer(report_app, name="report")


@report_app.command(name="generate")
def report_generate(
    title: str = typer.Option("", "--title", "-t", help="研报标题"),
    topic: str = typer.Option("", "--topic", help="专题标题"),
    desc: str = typer.Option("", "--desc", help="事件描述"),
    outlook: str = typer.Option("", "--outlook", help="市场展望"),
    risks: str = typer.Option("", "--risks", help="风险提示"),
):
    """生成研报并保存到Obsidian"""
    from finlab.report.generator import generate_report

    with console.status("[bold cyan]📄 生成研报中..."):
        filepath = generate_report(
            title=title or "",
            topic_title=topic or "",
            topic_desc=desc or "",
            outlook=outlook or "",
            risks=risks or "",
        )

    console.print(f"\n[green]✅ 研报已保存[/green]")
    console.print(f"[dim]{filepath}[/dim]")


@report_app.command(name="quick")
def report_quick(
    title: str = typer.Option("", "--title", "-t", help="研报标题"),
):
    """快速生成研报（默认最近7天 + 全标的）"""
    from finlab.report.generator import quick_report

    with console.status("[bold cyan]📄 快速研报生成中..."):
        filepath = quick_report(title=title or "")

    console.print(f"\n[green]✅ 研报已保存[/green]")
    console.print(f"[dim]{filepath}[/dim]")


@report_app.command(name="data")
def report_data():
    """仅生成数据章节（行情表格）"""
    from finlab.report.fetchers import (
        fetch_yfinance_batch, fetch_report_quotes,
        TICKER_GROUPS, default_date_range,
    )
    from finlab.report.sections import generate_data_section

    start, end = default_date_range()
    tickers = []
    for gt in TICKER_GROUPS.values():
        tickers.extend(gt)

    with console.status("[bold cyan]📡 拉取行情数据..."):
        yf_data = fetch_yfinance_batch(tickers, start, end)
        quotes = fetch_report_quotes()

    text = generate_data_section(
        yf_data, quotes,
        start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
    )
    console.print(text)


if __name__ == "__main__":
    app()
