"""测试统一评分引擎"""
import pytest
from finlab.core.scoring import score_event
from finlab.core.models import Score


class TestScoreEvent:
    """评分引擎核心行为"""

    # ── 通胀指标 ──────────────────────────────────────

    def test_cpi_above_forecast_bearish(self):
        s = score_event("CPI", "3.5", "3.2", "3.1")
        assert s.value == 3
        assert s.direction == "利空"
        assert "紧缩" in s.reason

    def test_cpi_below_forecast_bullish(self):
        s = score_event("CPI", "2.8", "3.2", "3.1")
        assert s.value == 7
        assert s.direction == "利多"
        assert "宽松" in s.reason

    def test_ppi_above_forecast_bearish(self):
        s = score_event("PPI", "4.0", "3.5", "3.4")
        assert s.value == 3
        assert s.direction == "利空"

    def test_pce_match_forecast_neutral(self):
        s = score_event("核心PCE", "2.5", "2.5", "2.4")
        assert s.value == 5
        assert s.direction == "中性"

    # ── 增长指标 ──────────────────────────────────────

    def test_gdp_above_forecast_bullish(self):
        s = score_event("GDP", "3.5", "3.0", "2.8")
        assert s.value == 7
        assert s.direction == "利多"
        assert "韧性" in s.reason

    def test_gdp_below_forecast_bearish(self):
        s = score_event("GDP", "1.5", "2.5", "2.3")
        assert s.value == 3
        assert s.direction == "利空"

    def test_retail_sales_above_bullish(self):
        s = score_event("Retail Sales", "1.2", "0.5", "0.3")
        assert s.value == 7
        assert s.direction == "利多"

    # ── 就业指标 ──────────────────────────────────────

    def test_nfp_slightly_above_neutral(self):
        s = score_event("Nonfarm Payrolls", "200", "180", "170")
        assert s.value == 5
        assert s.direction == "中性"
        assert "略超" in s.reason

    def test_nfp_above_forecast_neutral(self):
        s = score_event("NFP", "220", "180", "170")
        assert s.value == 5
        assert s.direction == "中性"
        assert "略超" in s.reason

    def test_nfp_below_hawkish(self):
        s = score_event("非农", "150", "200", "190")
        assert s.value == 6
        assert s.direction == "利好"

    # ── 失业指标 ──────────────────────────────────────

    def test_unemployment_above_bearish(self):
        s = score_event("Unemployment Rate", "5.5", "4.5", "4.4")
        assert s.value == 3
        assert s.direction == "利空"

    def test_jobless_claims_below_bullish(self):
        s = score_event("Initial Jobless", "200", "250", "240")
        assert s.value == 7
        assert s.direction == "利多"

    # ── 其他 / 默认 ───────────────────────────────────

    def test_housing_above_bullish(self):
        s = score_event("Housing Starts", "1.6", "1.4", "1.3")
        assert s.value == 7
        assert s.direction == "利多"

    def test_unknown_indicator_defaults_bullish_on_surprise_up(self):
        s = score_event("Trade Balance", "-50", "-60", "-55")
        assert s.value == 7
        assert s.direction == "利多"

    # ── 边界情况 ──────────────────────────────────────

    def test_missing_actual_returns_neutral(self):
        s = score_event("CPI", "", "3.0", "2.9")
        assert s.value == 5
        assert s.direction == "中性"

    def test_missing_forecast_returns_neutral(self):
        s = score_event("CPI", "3.0", "-", "2.9")
        assert s.value == 5
        assert s.direction == "中性"

    def test_dash_values_treated_as_missing(self):
        s = score_event("GDP", "-", "-", "2.0")
        assert s.value == 5

    def test_percent_signs_stripped(self):
        s = score_event("CPI YoY", "3.2%", "3.1%", "3.0%")
        assert s.value == 3  # above forecast = bearish

    def test_unparseable_values_returns_neutral(self):
        s = score_event("CPI", "N/A", "3.0", "2.9")
        assert s.value == 5

    def test_score_clamped_to_1_10_range(self):
        # All scores should be within [1, 10]
        for name in ["CPI", "GDP", "NFP", "Unemployment", "Housing Starts"]:
            s = score_event(name, "5.0", "1.0", "1.0")
            assert 1 <= s.value <= 10


class TestScoreModel:
    def test_as_label_bullish(self):
        assert "🚀" in Score(value=8).as_label()
        assert "✅" in Score(value=7).as_label()

    def test_as_label_neutral(self):
        assert "⚖️" in Score(value=5).as_label()
        assert "⚖️" in Score(value=4).as_label()

    def test_as_label_bearish(self):
        assert "🔴" in Score(value=3).as_label()
        assert "⚠️" in Score(value=1).as_label()
