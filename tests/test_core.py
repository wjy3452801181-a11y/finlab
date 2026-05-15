"""测试 core 模块基础设施"""
from datetime import datetime, timedelta
from finlab.core import BJT
from finlab.core.config import get_config
from finlab.core.models import Score, MacroEvent


class TestBJT:
    def test_offset_is_8_hours(self):
        assert BJT.utcoffset(None) == timedelta(hours=8)

    def test_bjt_now_is_reasonable(self):
        """BJT 时间应在 UTC+8 范围内"""
        bjt_now = datetime.now(BJT)
        diff = (bjt_now.utcoffset() - timedelta(hours=8)).total_seconds()
        assert abs(diff) < 1


class TestConfig:
    def test_get_config_returns_defaults(self):
        c = get_config()
        assert len(c.ticker_groups) >= 6
        assert len(c.sectors) >= 6
        assert c.report_default_days == 7
        assert c.macro_default_days == 2

    def test_config_is_singleton(self):
        a = get_config()
        b = get_config()
        assert a is b


class TestModels:
    def test_score_defaults(self):
        s = Score(value=5)
        assert s.value == 5
        assert s.direction == ""
        assert s.reason == ""

    def test_macro_event_creation(self):
        e = MacroEvent(
            time="14:30",
            country="US",
            indicator="CPI",
            actual=3.2,
            forecast=3.1,
            previous=3.0,
            score=3,
            direction="利空",
            reason="通胀高于预期",
        )
        assert e.score == 3
        assert e.direction == "利空"
        assert e.reason == "通胀高于预期"
