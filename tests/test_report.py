"""测试研报模块 — 数据注入缝"""
import os
import tempfile
from unittest import mock
from datetime import date, timedelta

from finlab.report.generator import generate_report


class TestReportSeam:
    """verifies generate_report accepts pre-fetched data"""

    def test_inject_yf_results_skips_fetch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            injected = {
                "SPY": {
                    "2026-05-10": {"open": 600.0, "high": 605.0, "low": 598.0, "close": 603.0, "volume": 1000000},
                    "2026-05-11": {"open": 603.0, "high": 608.0, "low": 601.0, "close": 607.0, "volume": 1100000},
                }
            }
            filepath = generate_report(
                title="Inject Test",
                date_range=(date(2026, 5, 10), date(2026, 5, 15)),
                yf_results=injected,
                quotes={},
                use_jin10_quotes=False,
                output_dir=tmpdir,
            )
            assert os.path.exists(filepath)
            content = open(filepath).read()
            assert "Inject Test" in content
            assert "SPY" in content

    def test_inject_quotes_skips_fetch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            injected = {"SPY": {"2026-05-10": {"open": 600.0, "high": 605.0, "low": 598.0, "close": 603.0, "volume": 1000000}}}
            quotes = {"上证": 3300.0, "黄金": 2650.0}
            filepath = generate_report(
                title="Quotes Inject",
                date_range=(date(2026, 5, 10), date(2026, 5, 15)),
                yf_results=injected,
                quotes=quotes,
                use_jin10_quotes=False,
                output_dir=tmpdir,
            )
            assert os.path.exists(filepath)
            content = open(filepath).read()
            assert "3300" in content
            assert "2650" in content
