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


@app.command()
def ashare():
    """A股板块扫描与个股分析"""
    console.print("[green]🇨🇳 ashare 模块开发中[/green]")


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
