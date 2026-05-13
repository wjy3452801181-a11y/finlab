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
def macro():
    """宏观数据拉取与评分"""
    console.print("[yellow]📊 macro 模块开发中[/yellow]")


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
