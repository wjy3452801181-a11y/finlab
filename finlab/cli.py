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


@app.command()
def crypto():
    """加密市场多因子分析"""
    console.print("[blue]₿ crypto 模块开发中[/blue]")


@app.command()
def news():
    """实时快讯与事件分析"""
    console.print("[magenta]📰 news 模块开发中[/magenta]")


@app.command()
def report():
    """一键生成研报"""
    console.print("[cyan]📄 report 模块开发中[/cyan]")


if __name__ == "__main__":
    app()
