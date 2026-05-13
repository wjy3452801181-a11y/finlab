"""CLI 入口"""

import typer
from rich.console import Console

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
def news_flash(hours: int = typer.Option(1, "--hours", "-h", help="最近几小时")):
    """获取金十实时快讯"""
    console.print("[magenta]📰 news flash — TODO: 接入金十MCP[/magenta]")


@news_app.command(name="analyze")
def news_analyze(title: str = typer.Argument(..., help="事件标题")):
    """分析金融事件影响"""
    console.print("[magenta]📰 news analyze — TODO: 调用事件分析框架[/magenta]")


@news_app.command(name="brief")
def news_brief():
    """生成当前时段新闻简报"""
    console.print("[magenta]📰 news brief — TODO: 简报生成[/magenta]")


# ── crypto ──────────────────────────────────────────────
crypto_app = typer.Typer(help="加密市场多因子分析")
app.add_typer(crypto_app, name="crypto")


@crypto_app.command(name="quote")
def crypto_quote():
    """BTC实时行情"""
    console.print("[blue]₿ crypto — TODO: OKX行情接入[/blue]")


# ── report ──────────────────────────────────────────────
report_app = typer.Typer(help="一键生成研报")
app.add_typer(report_app, name="report")


@report_app.command(name="generate")
def report_generate():
    """生成研报并保存到Obsidian"""
    console.print("[cyan]📄 report — TODO: 研报生成[/cyan]")


if __name__ == "__main__":
    app()
