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
    def _mock_director(self, full_text="=== 宏观报告 ===", summary_text="【宏观预览】"):
        """构建 MacroDirector mock 及其依赖的 fetcher mock"""
        mock_director = mock.MagicMock()
        mock_director.render_full_report.return_value = full_text
        mock_director.render_summary.return_value = summary_text
        return mock_director

    def test_macro_default(self):
        with mock.patch("finlab.macro.fetchers.fetch_economic_calendar") as m_cal, \
             mock.patch("finlab.macro.fetchers.fetch_forexlive_news") as m_news, \
             mock.patch("finlab.core.jin10.fetch_flash") as m_flash, \
             mock.patch("finlab.macro.director.MacroDirector") as m_director_cls:
            m_cal.return_value = []
            m_news.return_value = []
            m_flash.return_value = []
            mock_inst = self._mock_director()
            m_director_cls.return_value = mock_inst

            result = runner.invoke(app, ["macro"])
            assert result.exit_code == 0
            m_cal.assert_called_once_with(country="us", days_ahead=2)
            m_director_cls.assert_called_once_with(events=[], news=[], flashes=[])
            mock_inst.render_full_report.assert_called_once_with(country="us")

    def test_macro_with_country_and_days(self):
        with mock.patch("finlab.macro.fetchers.fetch_economic_calendar") as m_cal, \
             mock.patch("finlab.macro.fetchers.fetch_forexlive_news") as m_news, \
             mock.patch("finlab.core.jin10.fetch_flash") as m_flash, \
             mock.patch("finlab.macro.director.MacroDirector") as m_director_cls:
            m_cal.return_value = []
            m_news.return_value = []
            m_flash.return_value = []
            mock_inst = self._mock_director(full_text="=== CN 宏观 ===")
            m_director_cls.return_value = mock_inst

            result = runner.invoke(app, ["macro", "--country", "cn", "--days", "5"])
            assert result.exit_code == 0
            m_cal.assert_called_once_with(country="cn", days_ahead=5)

    def test_macro_summary_mode(self):
        with mock.patch("finlab.macro.fetchers.fetch_economic_calendar") as m_cal, \
             mock.patch("finlab.macro.fetchers.fetch_forexlive_news") as m_news, \
             mock.patch("finlab.core.jin10.fetch_flash") as m_flash, \
             mock.patch("finlab.macro.director.MacroDirector") as m_director_cls:
            m_cal.return_value = []
            m_news.return_value = []
            m_flash.return_value = []
            mock_inst = self._mock_director(summary_text="【宏观预览】")
            m_director_cls.return_value = mock_inst

            result = runner.invoke(app, ["macro", "--summary"])
            assert result.exit_code == 0
            m_cal.assert_called_once_with(country="us", days_ahead=2)
            mock_inst.render_summary.assert_called_once_with(country="us")
            mock_inst.render_full_report.assert_not_called()

    def test_macro_short_flags(self):
        with mock.patch("finlab.macro.fetchers.fetch_economic_calendar") as m_cal, \
             mock.patch("finlab.macro.fetchers.fetch_forexlive_news") as m_news, \
             mock.patch("finlab.core.jin10.fetch_flash") as m_flash, \
             mock.patch("finlab.macro.director.MacroDirector") as m_director_cls:
            m_cal.return_value = []
            m_news.return_value = []
            m_flash.return_value = []
            mock_inst = self._mock_director(summary_text="")
            m_director_cls.return_value = mock_inst

            result = runner.invoke(app, ["macro", "-c", "jp", "-d", "1", "-s"])
            assert result.exit_code == 0
            m_cal.assert_called_once_with(country="jp", days_ahead=1)
            mock_inst.render_summary.assert_called_once_with(country="jp")


class TestNewsCommands:
    def test_flash_default(self):
        with mock.patch("finlab.core.jin10.fetch_flash") as m:
            m.return_value = [{"time": "14:30:00", "content": "test"}]
            result = runner.invoke(app, ["news", "flash"])
            assert result.exit_code == 0
            m.assert_called_once_with(hours=2)

    def test_flash_custom_hours(self):
        with mock.patch("finlab.core.jin10.fetch_flash") as m:
            m.return_value = []
            result = runner.invoke(app, ["news", "flash", "--hours", "6"])
            assert result.exit_code == 0
            m.assert_called_once_with(hours=6)

    def test_flash_empty(self):
        with mock.patch("finlab.core.jin10.fetch_flash") as m:
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
        with mock.patch("finlab.core.jin10.search_flash") as m:
            m.return_value = [{"time": "14:30", "content": "tariff news"}]
            result = runner.invoke(app, ["news", "search", "tariff"])
            assert result.exit_code == 0
            m.assert_called_once_with("tariff")

    def test_search_no_results(self):
        with mock.patch("finlab.core.jin10.search_flash") as m:
            m.return_value = []
            result = runner.invoke(app, ["news", "search", "xyznotexist"])
            assert result.exit_code == 0


class TestReportCommands:
    @staticmethod
    def _macro_director_mocks():
        """Mock 构建 MacroDirector 所需的 4 个依赖"""
        return (
            mock.patch("finlab.macro.fetchers.fetch_economic_calendar", return_value=[]),
            mock.patch("finlab.macro.fetchers.fetch_forexlive_news", return_value=[]),
            mock.patch("finlab.core.jin10.fetch_flash", return_value=[]),
            mock.patch("finlab.macro.director.MacroDirector"),
        )

    def test_generate(self):
        m1, m2, m3, m4 = self._macro_director_mocks()
        with m1, m2, m3, m4, \
             mock.patch("finlab.report.generator.generate_report") as m:
            m.return_value = "/tmp/test_report.md"
            result = runner.invoke(app, ["report", "generate", "--title", "周报"])
            assert result.exit_code == 0
            assert "已保存" in result.stdout or "test_report" in result.stdout

    def test_generate_with_all_params(self):
        m1, m2, m3, m4 = self._macro_director_mocks()
        with m1, m2, m3, m4, \
             mock.patch("finlab.report.generator.generate_report") as m:
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
                macro_source=mock.ANY,
            )

    def test_quick(self):
        m1, m2, m3, m4 = self._macro_director_mocks()
        with m1, m2, m3, m4, \
             mock.patch("finlab.report.generator.quick_report") as m:
            m.return_value = "/tmp/quick.md"
            result = runner.invoke(app, ["report", "quick", "--title", "快速"])
            assert result.exit_code == 0
            m.assert_called_once_with(title="快速", macro_source=mock.ANY)

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
    @staticmethod
    def _mock_stock_data():
        """构建一个 mock StockData，满足 SectorChief 最低要求"""
        import pandas as pd
        sd = mock.MagicMock()
        sd.df = pd.DataFrame([
            {"close": 38.0, "pctChg": 0.5, "volume": 1e7, "turn": 2.0},
            {"close": 38.2, "pctChg": 0.8, "volume": 1.1e7, "turn": 2.1},
            {"close": 38.5, "pctChg": 1.2, "volume": 1.2e7, "turn": 2.3},
            {"close": 38.3, "pctChg": -0.5, "volume": 9e6, "turn": 1.8},
        ])
        return sd

    def test_track_default(self):
        mock_sd = self._mock_stock_data()
        with mock.patch("finlab.ashare.data.login", return_value=True), \
             mock.patch("finlab.ashare.data.logout"), \
             mock.patch("finlab.ashare.data.fetch_history", return_value=mock_sd), \
             mock.patch("finlab.ashare.chief.SectorChief") as m_chief:
            mock_inst = mock.MagicMock()
            mock_inst.render_tracking.return_value = "追踪结果"
            m_chief.return_value = mock_inst
            result = runner.invoke(app, ["ashare", "track"])
            assert result.exit_code == 0
            mock_inst.render_tracking.assert_called_once()

    def test_track_with_days(self):
        mock_sd = self._mock_stock_data()
        with mock.patch("finlab.ashare.data.login", return_value=True), \
             mock.patch("finlab.ashare.data.logout"), \
             mock.patch("finlab.ashare.data.fetch_history", return_value=mock_sd), \
             mock.patch("finlab.ashare.chief.SectorChief") as m_chief:
            mock_inst = mock.MagicMock()
            mock_inst.render_tracking.return_value = "追踪结果"
            m_chief.return_value = mock_inst
            result = runner.invoke(app, ["ashare", "track", "--days", "20"])
            assert result.exit_code == 0

    def test_scan_default(self):
        mock_sd = self._mock_stock_data()
        with mock.patch("finlab.ashare.data.login", return_value=True), \
             mock.patch("finlab.ashare.data.logout"), \
             mock.patch("finlab.ashare.data.fetch_history", return_value=mock_sd), \
             mock.patch("finlab.ashare.chief.SectorChief") as m_chief:
            mock_inst = mock.MagicMock()
            mock_inst.render_sector_scan.return_value = "板块扫描结果"
            m_chief.return_value = mock_inst
            result = runner.invoke(app, ["ashare", "scan"])
            assert result.exit_code == 0
            mock_inst.render_sector_scan.assert_called_once()

    def test_scan_with_exclude(self):
        mock_sd = self._mock_stock_data()
        with mock.patch("finlab.ashare.data.login", return_value=True), \
             mock.patch("finlab.ashare.data.logout"), \
             mock.patch("finlab.ashare.data.fetch_history", return_value=mock_sd), \
             mock.patch("finlab.ashare.chief.SectorChief") as m_chief:
            mock_inst = mock.MagicMock()
            mock_inst.render_sector_scan.return_value = "板块扫描结果"
            m_chief.return_value = mock_inst
            result = runner.invoke(app, ["ashare", "scan", "--exclude", "金融,消费"])
            mock_inst.render_sector_scan.assert_called_once_with(exclude=["金融", "消费"])
            assert result.exit_code == 0

    def test_rotation(self):
        mock_sd = self._mock_stock_data()
        with mock.patch("finlab.ashare.data.login", return_value=True), \
             mock.patch("finlab.ashare.data.logout"), \
             mock.patch("finlab.ashare.data.fetch_history", return_value=mock_sd), \
             mock.patch("finlab.ashare.chief.SectorChief") as m_chief:
            mock_inst = mock.MagicMock()
            mock_inst.render_sector_rotation.return_value = "板块轮动评分"
            m_chief.return_value = mock_inst
            result = runner.invoke(app, ["ashare", "rotation"])
            assert result.exit_code == 0
            mock_inst.render_sector_rotation.assert_called_once()


class TestTradeCommands:
    """交易命令测试 — mock TradeExecutor + yfinance"""

    def test_signal_default(self):
        with mock.patch("finlab.cli._fetch_yfinance_batch") as m_fetch, \
             mock.patch("finlab.trade.executor.TradeExecutor") as m_exec:
            m_fetch.return_value = {"AAPL": mock.MagicMock()}
            mock_inst = mock.MagicMock()
            mock_inst.render_signal.return_value = "交易信号"
            m_exec.return_value = mock_inst
            result = runner.invoke(app, ["trade", "signal"])
            assert result.exit_code == 0
            mock_inst.render_signal.assert_called_once_with(symbol=None)

    def test_signal_with_symbol(self):
        with mock.patch("finlab.cli._fetch_yfinance_batch") as m_fetch, \
             mock.patch("finlab.trade.executor.TradeExecutor") as m_exec:
            m_fetch.return_value = {"NVDA": mock.MagicMock()}
            mock_inst = mock.MagicMock()
            mock_inst.render_signal.return_value = "NVDA信号"
            m_exec.return_value = mock_inst
            result = runner.invoke(app, ["trade", "signal", "--symbol", "NVDA"])
            assert result.exit_code == 0
            mock_inst.render_signal.assert_called_once_with(symbol="NVDA")

    def test_monitor_default(self):
        with mock.patch("finlab.cli._fetch_yfinance_batch") as m_fetch, \
             mock.patch("finlab.trade.executor.TradeExecutor") as m_exec:
            m_fetch.return_value = {"NVDA": mock.MagicMock(), "QQQ": mock.MagicMock()}
            mock_inst = mock.MagicMock()
            mock_inst.render_risk_check.return_value = "风险检查"
            m_exec.return_value = mock_inst
            result = runner.invoke(app, ["trade", "monitor"])
            assert result.exit_code == 0
            mock_inst.render_risk_check.assert_called_once()

    def test_alpha(self):
        with mock.patch("finlab.cli._fetch_yfinance_batch") as m_fetch, \
             mock.patch("finlab.trade.executor.TradeExecutor") as m_exec:
            m_fetch.return_value = {"SPY": mock.MagicMock()}
            mock_inst = mock.MagicMock()
            mock_inst.render_anti_consensus.return_value = "Alpha信号"
            m_exec.return_value = mock_inst
            result = runner.invoke(app, ["trade", "alpha"])
            assert result.exit_code == 0
            mock_inst.render_anti_consensus.assert_called_once()


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

    def test_trade_help(self):
        result = runner.invoke(app, ["trade", "--help"])
        assert result.exit_code == 0

    def test_report_help(self):
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
