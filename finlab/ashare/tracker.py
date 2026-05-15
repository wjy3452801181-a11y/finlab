"""标的追踪 — 止损止盈检查 + 量价异常预警"""

import logging
from dataclasses import dataclass, field

from finlab.ashare.data import StockData

logger = logging.getLogger(__name__)


@dataclass
class TrackConfig:
    """标的跟踪配置"""
    code: str
    name: str
    entry: float = 0.0
    stop: float = 0.0
    target1: float = 0.0


@dataclass
class TrackResult:
    """标的跟踪结果"""
    config: TrackConfig
    data: StockData
    alerts: list[str] = field(default_factory=list)
    signal: str = "无信号"

    @property
    def status(self) -> str:
        if not self.alerts:
            return "✅ 正常"
        if self.data.close <= self.config.stop and self.config.stop > 0:
            return "❌ 触止损"
        if self.data.close >= self.config.target1 and self.config.target1 > 0:
            return "🎯 达目标"
        return "⚠️ 预警"

    @property
    def pct_to_stop(self) -> float:
        s = self.config.stop
        return (self.data.close - s) / s * 100 if s > 0 else 0

    @property
    def pct_to_target(self) -> float:
        t = self.config.target1
        return (self.data.close - t) / t * 100 if t > 0 else 0

    @property
    def pct_from_entry(self) -> float:
        e = self.config.entry
        return (self.data.close - e) / e * 100 if e > 0 else 0

    def __str__(self) -> str:
        s = self.data
        c = self.config
        out = (
            f"数据日期:{s.last['date']} | {c.name}({c.code}) | "
            f"收盘{s.close:.2f} | 开{s.last['open']:.2f} 高{s.high:.2f} 低{s.low:.2f} | "
            f"今日{s.pct:+.2f}% | "
            f"入场{c.entry}({self.pct_from_entry:+.1f}%) | "
        )
        if c.stop > 0:
            out += f"止损{c.stop:.2f}(距{self.pct_to_stop:+.1f}%) | "
        if c.target1 > 0:
            out += f"目标{c.target1:.2f}(距{self.pct_to_target:+.1f}%) | "
        out += f"量比{s.vol_ratio:.2f} | 振幅{(s.high-s.low)/s.close*100:.1f}% | {self.status}"
        if self.alerts:
            out += "\n     ⚡ " + " | ".join(self.alerts)
        return out


def _check_alerts(result: TrackResult) -> list[str]:
    """检查各项预警"""
    s = result.data
    c = result.config
    alerts = []

    # 止损
    if c.stop > 0 and s.close <= c.stop:
        alerts.append(f"收盘{s.close:.2f}已≤止损{c.stop:.2f}")
        result.signal = "止损离场"

    # 目标
    if c.target1 > 0 and s.close >= c.target1:
        alerts.append(f"收盘{s.close:.2f}已≥目标{c.target1:.2f}")
        if result.signal == "无信号":
            result.signal = "目标达成"

    # 单日大跌
    if result.prev is not None and s.pct < -3:
        alerts.append(f"今日{s.pct:+.2f}%，单日跌幅超3%")
        if result.signal == "无信号":
            result.signal = "单日大跌"

    # 量能
    vr = s.vol_ratio
    if vr < 0.5:
        alerts.append(f"缩量量比{vr:.2f}")
    elif vr > 2.5:
        alerts.append(f"放量量比{vr:.2f}")

    # 偏离MA5
    dev = (s.close - s.ma5) / s.ma5 * 100
    if abs(dev) > 5:
        alerts.append(f"偏离MA5 {dev:+.1f}%")

    # 日内振幅
    day_range = (s.high - s.low) / s.close * 100
    if day_range > 6:
        alerts.append(f"日内振幅{day_range:.1f}%")

    return alerts


def track_stocks(
    configs: list[TrackConfig],
    days: int = 10,
) -> list[TrackResult]:
    """跟踪一组A股标的

    Args:
        configs: 标的配置列表
        days: 回溯天数

    Returns:
        TrackResult 列表
    """
    from finlab.ashare.data import login, logout, fetch_history

    logged_in = login()
    if not logged_in:
        return []

    results = []
    try:
        for cfg in configs:
            sd = fetch_history(cfg.code, cfg.name, days=days)
            if sd is None:
                logger.warning("%s(%s) | 数据不足", cfg.name, cfg.code)
                continue

            result = TrackResult(config=cfg, data=sd)
            result.alerts = _check_alerts(result)
            results.append(result)
            logger.info(str(result))
    finally:
        logout()

    return results


def print_summary(results: list[TrackResult]):
    """打印综合评估"""
    if not results:
        return

    print("\n" + "=" * 60)
    print("【综合评估】")

    triggered = [r for r in results if r.status == "❌ 触止损"]
    reached = [r for r in results if r.status == "🎯 达目标"]
    warnings = [r for r in results if r.status == "⚠️ 预警"]

    if triggered:
        for r in triggered:
            print(f"  ❌ {r.config.name} 触止损！当前{r.data.close:.2f}")
    if reached:
        for r in reached:
            print(f"  🎯 {r.config.name} 达目标！当前{r.data.close:.2f}")
    if warnings:
        for r in warnings:
            print(f"  ⚠️  {r.config.name}: {' | '.join(r.alerts)}")
    if not triggered and not reached and not warnings:
        print("  ✅ 正常，无特殊信号")
