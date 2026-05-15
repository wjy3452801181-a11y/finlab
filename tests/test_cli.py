"""CLI 测试 — 每个命令的 happy path + 参数解析

使用 Typer CliRunner，网络/数据依赖全部 mock。
mock 路径指向源模块（cli.py 的 import 在命令函数体内）。
"""

from typer.testing import CliRunner
from unittest import mock

from finlab.cli import app

runner = CliRunner()


class TestRootCommands:
    def test_no_args_shows_help(self):
        # no_args_is_help=True → Typer raises SystemExit(2), CliRunner catches it
        result = runner.invoke(app, [])
        assert result.exit_code == 2

    def test_help_flag(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "macro" in result.stdout
        assert "ashare" in result.stdout
        assert "news" in result.stdout
        assert "report" in result.stdout

    def test_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "finlab v" in result.stdout

    def test_about(self):
        result = runner.invoke(app, ["about"])
        assert result.exit_code == 0
        assert "三角色" in result.stdout
        assert "评分体系" in result.stdout


class TestMacroCommands:
    def test_macro_default(self):
        with mock.patch("finlab.macro.report.generate_macro_report") as m:
            m.return_value = "=== 宏观报告 ==="
            result = runner.invoke(app, ["macro"])
            assert result.exit_code == 0
            m.assert_called_once_with(country="us", days_ahead=2)

    def test_macro_with_country_and_days(self):
        with mock.patch("finlab.macro.report.generate_macro_report") as m:
            m.return_value = "=== CN 宏观 ==="
            result = runner.invoke(app, ["macro", "--country", "cn", "--days", "5"])
            assert result.exit_code == 0
            m.assert_called_once_with(country="cn", days_ahead=5)

    def test_macro_summary_mode(self):
        with mock.patch("finlab.macro.report.generate_macro_summary") as m:
            m.return_value = "【宏观预览】"
            result = runner.invoke(app, ["macro", "--summary"])
            assert result.exit_code == 0
            m.assert_called_once_with(country="us")

    def test_macro_short_flags(self):
        with mock.patch("finlab.macro.report.generate_macro_report"):
            with mock.patch("finlab.macro.report.generate_macro_summary") as m2:
                m2.return_value = ""
                result = runner.invoke(app, ["macro", "-c", "jp", "-d", "1", "-s"])
                assert result.exit_code == 0
                m2.assert_called_once_with(country="jp")


class TestNewsCommands:
    def test_flash_default(self):
        with mock.patch("finlab.news.fetchers.fetch_flash") as m:
            m.return_value = [{"time": "14:30:00", "content": "test"}]
            result = runner.invoke(app, ["news", "flash"])
            assert result.exit_code == 0
            m.assert_called_once_with(hours=2)

    def test_flash_custom_hours(self):
        with mock.patch("finlab.news.fetchers.fetch_flash") as m:
            m.return_value = []
            result = runner.invoke(app, ["news", "flash", "--hours", "6"])
            assert result.exit_code == 0
            m.assert_called_once_with(hours=6)

    def test_flash_empty(self):
        with mock.patch("finlab.news.fetchers.fetch_flash") as m:
            m.return_value = []
            result = runner.invoke(app, ["news", "flash"])
            assert result.exit_code == 0
            assert "无快讯" in result.stdout or "📭" in result.stdout

    def test_analyze(self):
        with mock.patch("finlab.news.analysis.analyze_event") as m:
            m.return_value = "📊 事件分析：CPI超预期..."
            result = runner.invoke(app, ["news", "analyze", "CPI数据超预期"])
            assert result.exit_code == 0
            m.assert_called_once_with("CPI数据超预期")

    def test_brief(self):
        with mock.patch("finlab.news.brief.build_flash_brief") as m:
            m.return_value = "📰 快讯简报"
            result = runner.invoke(app, ["news", "brief"])
            assert result.exit_code == 0

    def test_calendar(self):
        with mock.patch("finlab.news.brief.build_calendar_brief") as m:
            m.return_value = "📅 财经日历"
            result = runner.invoke(app, ["news", "calendar"])
            assert result.exit_code == 0

    def test_search(self):
        with mock.patch("finlab.news.fetchers.search_flash") as m:
            m.return_value = [{"time": "14:30", "content": "tariff news"}]
            result = runner.invoke(app, ["news", "search", "tariff"])
            assert result.exit_code == 0
            m.assert_called_once_with("tariff")

    def test_search_no_results(self):
        with mock.patch("finlab.news.fetchers.search_flash") as m:
            m.return_value = []
            result = runner.invoke(app, ["news", "search", "xyznotexist"])
            assert result.exit_code == 0


class TestReportCommands:
    def test_generate(self):
        with mock.patch("finlab.report.generator.generate_report") as m:
            m.return_value = "/tmp/test_report.md"
            result = runner.invoke(app, ["report", "generate", "--title", "周报"])
            assert result.exit_code == 0
            assert "已保存" in result.stdout or "test_report" in result.stdout

    def test_generate_with_all_params(self):
        with mock.patch("finlab.report.generator.generate_report") as m:
            m.return_value = "/tmp/full.md"
            result = runner.invoke(
                app,
                [
                    "report", "generate",
                    "--title", "专题",
                    "--topic", "CPI分析",
                    "--desc", "CPI超预期",
                    "--outlook", "谨慎看多",
                    "--risks", "关税风险",
                ],
            )
            assert result.exit_code == 0
            m.assert_called_once_with(
                title="专题",
                topic_title="CPI分析",
                topic_desc="CPI超预期",
                outlook="谨慎看多",
                risks="关税风险",
            )

    def test_quick(self):
        with mock.patch("finlab.report.generator.quick_report") as m:
            m.return_value = "/tmp/quick.md"
            result = runner.invoke(app, ["report", "quick", "--title", "快速"])
            assert result.exit_code == 0
            m.assert_called_once_with(title="快速")

    def test_data(self):
        with mock.patch("finlab.report.sections.generate_data_section") as m_sec:
            m_sec.return_value = "## 一、数据更新..."
            with mock.patch("finlab.report.fetchers.fetch_yfinance_batch") as yf:
                yf.return_value = {}
                with mock.patch("finlab.report.fetchers.fetch_report_quotes") as q:
                    q.return_value = {}
                    result = runner.invoke(app, ["report", "data"])
                    assert result.exit_code == 0


class TestAshareCommands:
    def test_track_default(self):
        with mock.patch("finlab.ashare.tracker.track_stocks") as m:
            m.return_value = []
            result = runner.invoke(app, ["ashare", "track"])
            # track_stocks 内部调用 baostock login，被 mock 后返回空列表
            assert result.exit_code == 0

    def test_track_with_days(self):
        with mock.patch("finlab.ashare.tracker.track_stocks") as m:
            m.return_value = []
            result = runner.invoke(app, ["ashare", "track", "--days", "20"])
            assert result.exit_code == 0

    def test_scan_default(self):
        with mock.patch("finlab.ashare.screener.scan_sectors") as m:
            m.return_value = [{"板块": "芯片", "代码": "sh.688981", "名称": "中芯国际",
                               "最新价": 50.0, "今日涨幅%": 1.5, "5日涨幅%": 3.0,
                               "日均换手%": 2.0, "量比": 1.2}]
            result = runner.invoke(app, ["ashare", "scan"])
            assert result.exit_code == 0

    def test_scan_with_exclude(self):
        with mock.patch("finlab.ashare.screener.scan_sectors") as m:
            m.return_value = []
            result = runner.invoke(app, ["ashare", "scan", "--exclude", "金融,消费"])
            m.assert_called_once_with(exclude=["金融", "消费"])
            assert result.exit_code == 0


class TestHelpOutputs:
    """确保每个子命令组都有 help"""

    def test_macro_help(self):
        result = runner.invoke(app, ["macro", "--help"])
        assert result.exit_code == 0

    def test_ashare_help(self):
        result = runner.invoke(app, ["ashare", "--help"])
        assert result.exit_code == 0

    def test_news_help(self):
        result = runner.invoke(app, ["news", "--help"])
        assert result.exit_code == 0

    def test_report_help(self):
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
