"""交易执行官 — 数据注入 + 信号生成 + 风险管理

三角色研究框架第三角色：TradeExecutor 接收预拉取的 OHLCV 数据，
从三个维度渲染交易分析，供 CLI 直接输出。
"""

import pandas as pd
import numpy as np


class TradeExecutor:
    """交易执行官 — 数据注入 + 多视角渲染"""

    def __init__(
        self,
        price_data: dict[str, pd.DataFrame],
        watchlist: list[dict] | None = None,
    ) -> None:
        """
        Args:
            price_data: {symbol: OHLCV DataFrame} — 预拉取数据
            watchlist: [{"symbol": "AAPL", "entry": 150.0, "stop": 145.0, "target": 160.0}, ...]
        """
        self.price_data = price_data
        self.watchlist = watchlist or []

    # ── 入场信号 ──────────────────────────────────────────

    def render_signal(self, symbol: str | None = None) -> str:
        """入场信号综合评分 — 趋势/动量/量价/波动四维评分"""
        if symbol:
            if symbol not in self.price_data:
                return f"无 {symbol} 数据"
            results = {symbol: self._score_symbol(symbol, self.price_data[symbol])}
        else:
            results = {
                sym: self._score_symbol(sym, df)
                for sym, df in self.price_data.items()
            }
            results = {k: v for k, v in results.items() if v is not None}

        return self._format_signals(results)

    def _score_symbol(self, symbol: str, df: pd.DataFrame) -> dict | None:
        """对单个标的四维评分"""
        if len(df) < 26:
            return None

        close = df["close"].values.astype(float)
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        volume = df["volume"].values.astype(float)

        # ── 趋势 35%: EMA 排列 + ADX ──
        ema9 = self._ema(close, 9)
        ema21 = self._ema(close, 21)
        ema55 = self._ema(close, 55)

        # EMA 排列评分
        alignment = 0
        if ema9[-1] > ema21[-1] > ema55[-1]:
            alignment = 3  # 多头排列
        elif ema9[-1] < ema21[-1] < ema55[-1]:
            alignment = -3  # 空头排列
        elif ema9[-1] > ema21[-1]:
            alignment = 1  # 短期偏多

        # ADX
        adx = self._adx(high, low, close, 14)
        adx_now = float(adx[-1]) if not np.isnan(adx[-1]) else 20.0
        trend_strength = min(adx_now / 25, 2.5)  # 0-2.5

        trend_raw = 5 + alignment * 0.8 + trend_strength
        trend_score = round(float(max(1, min(10, trend_raw))), 1)

        # ── 动量 30%: RSI + MACD ──
        rsi = self._rsi(close, 14)
        rsi_now = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0

        # RSI: 30-70 为健康区间，过高/过低扣分
        if 40 <= rsi_now <= 65:
            rsi_sub = 7 + (rsi_now - 40) / 25 * 3  # 7-10
        elif 30 <= rsi_now < 40:
            rsi_sub = 4 + (rsi_now - 30) / 10 * 3  # 4-7 超卖反弹
        elif 65 < rsi_now <= 80:
            rsi_sub = 7 - (rsi_now - 65) / 15 * 3  # 4-7 超买
        elif rsi_now > 80:
            rsi_sub = 2
        else:
            rsi_sub = 3

        macd_line, signal_line, histogram = self._macd(close)
        hist_now = histogram[-1]
        hist_prev = histogram[-2] if len(histogram) > 1 else 0
        macd_sub = 5 + (1.5 if hist_now > 0 else -1.5)
        if hist_now > hist_prev:
            macd_sub += 1  # 动能加速
        elif hist_now < hist_prev:
            macd_sub -= 0.5
        macd_sub = max(1, min(10, macd_sub))

        momentum_raw = rsi_sub * 0.55 + macd_sub * 0.45
        momentum_score = round(float(max(1, min(10, momentum_raw))), 1)

        # ── 量价 20%: 量比 + 价量背离 ──
        avg_vol_20 = np.mean(volume[-26:-1]) if len(volume) > 25 else np.mean(volume[:-1])
        vol_ratio = volume[-1] / avg_vol_20 if avg_vol_20 > 0 else 1.0

        if 1.0 <= vol_ratio <= 2.0:
            vol_sub = 6 + vol_ratio  # 温和放量最佳
        elif 0.6 <= vol_ratio < 1.0:
            vol_sub = 4 + vol_ratio * 2  # 缩量
        elif vol_ratio > 2.0:
            vol_sub = 7  # 过度放量
        else:
            vol_sub = 3

        # 价量关系: 上涨+放量=好，下跌+放量=差
        price_chg = (close[-1] - close[-2]) / close[-2] if close[-2] > 0 else 0
        if price_chg > 0 and vol_ratio > 1.0:
            vol_sub += 1
        elif price_chg < 0 and vol_ratio > 1.0:
            vol_sub -= 1.5
        vol_sub = max(1, min(10, float(vol_sub)))

        volume_score = round(float(vol_sub), 1)

        # ── 波动 15%: ATR + 布林带 ──
        atr = self._atr(high, low, close, 14)
        atr_pct = atr[-1] / close[-1] * 100 if close[-1] > 0 else 2

        # ATR: 2-4% 适中
        if 1.5 <= atr_pct <= 4:
            atr_sub = 7
        elif atr_pct < 1.5:
            atr_sub = 5
        else:
            atr_sub = 8 - atr_pct * 0.5

        # 布林带位置
        bb_mid = self._ema(close, 20)[-1]
        bb_std = np.std(close[-20:])
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        bb_width = (bb_upper - bb_lower) / bb_mid if bb_mid > 0 else 0

        # 在带宽适中时，接近下轨=机会
        bb_position = (close[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper > bb_lower else 0.5
        if 0.1 <= bb_position <= 0.35:
            bb_sub = 8  # 接近下轨，潜在反弹
        elif 0.35 < bb_position <= 0.65:
            bb_sub = 6  # 中枢
        elif 0.65 < bb_position <= 0.85:
            bb_sub = 5  # 接近上轨
        elif bb_position > 0.85:
            bb_sub = 3  # 超买
        else:
            bb_sub = 4  # 超卖

        # 带宽极窄→即将突破
        if bb_width < 0.05:
            bb_sub = min(bb_sub + 1, 10)

        volatility_raw = atr_sub * 0.5 + bb_sub * 0.5
        volatility_score = round(float(max(1, min(10, volatility_raw))), 1)

        # ── 综合 ──
        composite = round(float(
            trend_score * 0.35 + momentum_score * 0.30
            + volume_score * 0.20 + volatility_score * 0.15
        ), 1)

        return {
            "symbol": symbol,
            "综合分": composite,
            "趋势分(35%)": trend_score,
            "动量分(30%)": momentum_score,
            "量价分(20%)": volume_score,
            "波动分(15%)": volatility_score,
            "最新价": round(float(close[-1]), 2),
            "涨跌幅%": round(float(price_chg) * 100, 2),
            "RSI": round(rsi_now, 1),
            "量比": round(float(vol_ratio), 2),
            "ATR%": round(float(atr_pct), 2),
            "ADX": round(adx_now, 1),
        }

    @staticmethod
    def _format_signals(results: dict[str, dict]) -> str:
        """格式化信号评分"""
        if not results:
            return "无有效数据（需至少26个交易日）"

        scored = sorted(results.values(), key=lambda x: x["综合分"], reverse=True)

        lines = [f"{'=' * 80}"]
        lines.append("交易信号评分 — 趋势/动量/量价/波动四维综合")
        lines.append(f"{'=' * 80}")
        lines.append("")

        header = (
            f"{'排名':<6}{'标的':<12}{'综合':<8}{'趋势(35%)':<10}"
            f"{'动量(30%)':<10}{'量价(20%)':<10}{'波动(15%)':<10}"
            f"{'价格':<10}{'涨跌':<8}{'RSI':<8}{'量比':<8}{'ATR%':<8}"
        )
        lines.append(header)
        lines.append("-" * len(header))

        for i, s in enumerate(scored, 1):
            label = TradeExecutor._score_label(s["综合分"])
            rank = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i:>2}")
            lines.append(
                f"{rank:<6}{s['symbol']:<12}{s['综合分']:<8}"
                f"{s['趋势分(35%)']:<10}{s['动量分(30%)']:<10}"
                f"{s['量价分(20%)']:<10}{s['波动分(15%)']:<10}"
                f"{s['最新价']:<10.2f}{s['涨跌幅%']:>+7.2f}%"
                f"{s['RSI']:<8.1f}{s['量比']:<8.2f}{s['ATR%']:<8.2f}  {label}"
            )

        lines.append("")
        lines.append("评分维度：")
        lines.append("  趋势(35%) — EMA排列(9/21/55) + ADX趋势强度")
        lines.append("  动量(30%) — RSI区间 + MACD柱方向/加速度")
        lines.append("  量价(20%) — 量比 + 价量共振/背离")
        lines.append("  波动(15%) — ATR波动率 + 布林带位置")
        lines.append("")
        lines.append("信号解读：")
        lines.append("  8-10  🚀 强烈看多 — 趋势/动量/量价共振")
        lines.append("  6-7   ✅ 看多 — 多数维度支持")
        lines.append("  4-5   ⚖️ 中性 — 信号分歧，等待确认")
        lines.append("  2-3   🔴 看空 — 多数维度偏弱")
        lines.append("  1     ⚠️ 强烈看空 — 共振下行")

        return "\n".join(lines)

    @staticmethod
    def _score_label(score: float) -> str:
        if score >= 8:
            return "🚀强烈看多"
        elif score >= 6:
            return "✅看多"
        elif score >= 4:
            return "⚖️中性"
        elif score >= 2:
            return "🔴看空"
        else:
            return "⚠️强烈看空"

    # ── 风险管理 ──────────────────────────────────────────

    def render_risk_check(self) -> str:
        """持仓风险管理 — 止损止盈状态检查"""
        checks: list[dict] = []

        for pos in self.watchlist:
            sym = pos["symbol"]
            df = self.price_data.get(sym)
            if df is None or len(df) < 2:
                continue
            checks.append(self._check_position(pos, df))

        return self._format_risk_checks(checks)

    def _check_position(self, pos: dict, df: pd.DataFrame) -> dict:
        """检查单个持仓"""
        close = df["close"].values.astype(float)
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)

        price = float(close[-1])
        entry = pos.get("entry", 0)
        stop = pos.get("stop", 0)
        target = pos.get("target", 0)
        pct_from_entry = (price - entry) / entry * 100 if entry > 0 else 0

        # 动态止损建议（ATR trailing）
        atr = self._atr(high, low, close, 14)[-1]
        trailing_stop = price - atr * 1.5
        hard_stop = entry * 0.93  # 硬止损 -7%

        alerts = []
        action = "持仓"

        if stop > 0 and price <= stop:
            alerts.append(f"触止损{stop:.2f}")
            action = "❌ 止损离场"
        if target > 0 and price >= target:
            alerts.append(f"达目标{target:.2f}")
            action = "🎯 止盈离场"
        if pct_from_entry <= -5:
            alerts.append(f"距入场{pct_from_entry:+.1f}%")
            action = "⚠️ 浮亏警戒"
        if entry > 0 and price >= entry * 1.15:
            alerts.append(f"浮盈{pct_from_entry:+.1f}%")
            if action == "持仓":
                action = "🟢 盈利运行"

        # 建议新止损
        suggested_stop = round(max(trailing_stop, hard_stop), 2) if entry > 0 else 0

        return {
            "symbol": pos["symbol"],
            "name": pos.get("name", pos["symbol"]),
            "price": price,
            "entry": entry,
            "stop": stop,
            "target": target,
            "pct_from_entry": round(pct_from_entry, 1),
            "action": action,
            "alerts": alerts,
            "suggested_stop": suggested_stop,
            "atr": round(atr, 2),
        }

    @staticmethod
    def _format_risk_checks(checks: list[dict]) -> str:
        """格式化风险检查"""
        if not checks:
            return "无持仓数据"

        lines = [f"{'=' * 80}"]
        lines.append("持仓风险管理 — 止损止盈状态")
        lines.append(f"{'=' * 80}")
        lines.append("")

        for c in checks:
            lines.append(f"▶ {c['name']} ({c['symbol']})")
            lines.append(f"  当前价: {c['price']:.2f}")
            if c["entry"] > 0:
                lines.append(
                    f"  入场: {c['entry']:.2f}  |  "
                    f"距入场 {c['pct_from_entry']:+.1f}%  |  "
                    f"状态: {c['action']}"
                )
            if c["stop"] > 0:
                lines.append(f"  原止损: {c['stop']:.2f}")
            if c["target"] > 0:
                lines.append(f"  原目标: {c['target']:.2f}")
            if c["suggested_stop"] > 0:
                lines.append(f"  建议新止损: {c['suggested_stop']:.2f} (ATR动态)")
            if c["alerts"]:
                for a in c["alerts"]:
                    lines.append(f"  ⚡ {a}")
            lines.append(f"  ATR(14): {c['atr']:.2f}")
            lines.append("")

        return "\n".join(lines)

    # ── 反共识 Alpha ─────────────────────────────────────

    def render_anti_consensus(self) -> str:
        """反共识 Alpha — 独立于趋势/动量的反向维度"""
        signals: list[dict] = []

        for sym, df in self.price_data.items():
            if len(df) < 26:
                continue
            alpha = self._calc_alpha(sym, df)
            if alpha:
                signals.append(alpha)

        signals.sort(key=lambda x: x["alpha_score"], reverse=True)

        return self._format_alpha(signals)

    def _calc_alpha(self, symbol: str, df: pd.DataFrame) -> dict | None:
        """计算反共识 Alpha 信号"""
        close = df["close"].values.astype(float)
        volume = df["volume"].values.astype(float)

        # 1. 恐慌指数: 连续下跌天数 + 跌幅
        down_days = 0
        for i in range(len(close) - 1, 0, -1):
            if close[i] < close[i - 1]:
                down_days += 1
            else:
                break
        drop_pct = (close[-1] - close[-down_days]) / close[-down_days] * 100 if down_days > 0 else 0

        # 连续下跌+跌幅适中 = 恐慌抛售机会
        if down_days >= 3 and -8 <= drop_pct <= -2:
            panic = 8
        elif down_days >= 2 and drop_pct <= -1:
            panic = 6
        elif down_days >= 4 and drop_pct < -8:
            panic = 4  # 恐慌过度，可能继续跌
        else:
            panic = 5

        # 2. 缩量止跌: 成交量萎缩+跌幅收窄
        avg_vol_5 = np.mean(volume[-6:-1])
        avg_vol_20 = np.mean(volume[-21:-1])
        vol_contract = avg_vol_5 / avg_vol_20 if avg_vol_20 > 0 else 1

        last_chg = (close[-1] - close[-2]) / close[-2] * 100 if close[-2] > 0 else 0
        prev_chg = (close[-2] - close[-3]) / close[-3] * 100 if close[-3] > 0 else 0

        # 缩量+跌幅收窄 = 止跌信号
        if vol_contract < 0.8 and last_chg > prev_chg and last_chg > -1:
            exhaustion = 8
        elif vol_contract < 0.9 and last_chg > prev_chg:
            exhaustion = 6
        elif vol_contract > 1.5 and last_chg < -1:
            exhaustion = 3  # 放量下跌
        else:
            exhaustion = 5

        # 3. 波动压缩: 布林带收窄 = 即将突破
        bb_mid = self._ema(close, 20)[-1]
        bb_std = np.std(close[-20:])
        bb_width = (4 * bb_std) / bb_mid if bb_mid > 0 else 0

        if bb_width < 0.04:
            squeeze = 8  # 极度压缩
        elif bb_width < 0.06:
            squeeze = 7
        elif bb_width < 0.08:
            squeeze = 6
        elif bb_width > 0.20:
            squeeze = 3  # 过度扩张
        else:
            squeeze = 5

        # 4. 相对强弱背离: 价格新低但 RSI 未新低
        rsi = self._rsi(close, 14)
        low_5 = np.argmin(close[-5:])
        rsi_5 = rsi[-5:]

        divergence = 5
        if low_5 > 0:
            rsi_now = rsi[-1]
            if close[-1] <= close[-5:].min() and rsi_now > rsi_5.min() + 3:
                divergence = 8  #  bullish divergence

        # 综合 Alpha（等权）
        alpha = round(panic * 0.30 + exhaustion * 0.25 + squeeze * 0.25 + divergence * 0.20, 1)

        signals = []
        if panic >= 7:
            signals.append("恐慌抛售")
        if exhaustion >= 7:
            signals.append("缩量止跌")
        if squeeze >= 7:
            signals.append("波动压缩·即将突破")
        if divergence >= 7:
            signals.append("RSI底背离")

        return {
            "symbol": symbol,
            "alpha_score": alpha,
            "panic": panic,
            "exhaustion": exhaustion,
            "squeeze": squeeze,
            "divergence": divergence,
            "signals": signals,
            "price": round(float(close[-1]), 2),
        }

    @staticmethod
    def _format_alpha(signals: list[dict]) -> str:
        """格式化反共识 Alpha"""
        if not signals:
            return "无有效数据"

        lines = [f"{'=' * 80}"]
        lines.append("反共识 Alpha — 独立维度信号（恐慌/止跌/压缩/背离）")
        lines.append(f"{'=' * 80}")
        lines.append("")

        header = (
            f"{'标的':<12}{'Alpha':<8}{'恐慌抛售':<10}{'缩量止跌':<10}"
            f"{'波动压缩':<10}{'RSI背离':<10}{'价格':<10}{'信号'}"
        )
        lines.append(header)
        lines.append("-" * len(header))

        for s in signals:
            if s["alpha_score"] >= 7:
                label = "🟢 Alpha"
            elif s["alpha_score"] >= 5.5:
                label = "🟡 关注"
            else:
                label = "⚪ 无信号"

            signal_text = " · ".join(s["signals"]) if s["signals"] else "—"
            lines.append(
                f"{s['symbol']:<12}{s['alpha_score']:<8}"
                f"{s['panic']:<10}{s['exhaustion']:<10}"
                f"{s['squeeze']:<10}{s['divergence']:<10}"
                f"{s['price']:<10.2f}{signal_text[:30]}  {label}"
            )

        lines.append("")
        lines.append("Alpha 维度说明：")
        lines.append("  恐慌抛售 — 连跌天数+跌幅，恐慌=逆向机会（30%）")
        lines.append("  缩量止跌 — 量缩+跌幅收窄，卖方衰竭（25%）")
        lines.append("  波动压缩 — 布林带收窄，突破前兆（25%）")
        lines.append("  RSI背离  — 价格新低RSI未新低，底部信号（20%）")
        lines.append("")
        lines.append("  Alpha≥7  🟢 独立于趋势的做多信号（反共识）")
        lines.append("  Alpha5.5-7 🟡 值得关注")
        lines.append("  Alpha<5.5 ⚪ 无特殊信号")

        return "\n".join(lines)

    # ── 技术指标（纯函数）────────────────────────────────

    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """指数移动平均"""
        result = np.full_like(data, np.nan, dtype=float)
        if len(data) < period:
            return result
        k = 2 / (period + 1)
        result[period - 1] = np.mean(data[:period])
        for i in range(period, len(data)):
            result[i] = data[i] * k + result[i - 1] * (1 - k)
        return result

    @staticmethod
    def _rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
        """RSI"""
        result = np.full_like(close, np.nan, dtype=float)
        if len(close) < period + 1:
            return result
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])
        for i in range(period, len(close)):
            avg_gain = (avg_gain * (period - 1) + gain[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + loss[i - 1]) / period
            if avg_loss == 0:
                result[i] = 100
            else:
                result[i] = 100 - 100 / (1 + avg_gain / avg_loss)
        return result

    @staticmethod
    def _macd(close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD — 返回 (macd_line, signal_line, histogram)"""
        ema_fast = TradeExecutor._ema(close, fast)
        ema_slow = TradeExecutor._ema(close, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TradeExecutor._ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """ATR"""
        result = np.full_like(close, np.nan, dtype=float)
        if len(close) < period + 1:
            return result
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1]),
            ),
        )
        result[period] = np.mean(tr[:period])
        for i in range(period + 1, len(close)):
            result[i] = (result[i - 1] * (period - 1) + tr[i - 1]) / period
        return result

    @staticmethod
    def _adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """ADX"""
        result = np.full_like(close, np.nan, dtype=float)
        if len(close) < period * 2:
            return result
        up_move = high[1:] - high[:-1]
        down_move = low[:-1] - low[1:]
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1]),
            ),
        )

        atr_arr = np.full_like(close, np.nan, dtype=float)
        atr_arr[period] = np.mean(tr[:period])
        for i in range(period + 1, len(close)):
            atr_arr[i] = (atr_arr[i - 1] * (period - 1) + tr[i - 1]) / period

        plus_di = np.full_like(close, np.nan, dtype=float)
        minus_di = np.full_like(close, np.nan, dtype=float)
        plus_dm_smooth = np.mean(plus_dm[:period])
        minus_dm_smooth = np.mean(minus_dm[:period])

        for i in range(period, len(close) - 1):
            plus_dm_smooth = (plus_dm_smooth * (period - 1) + plus_dm[i]) / period
            minus_dm_smooth = (minus_dm_smooth * (period - 1) + minus_dm[i]) / period
            atr_val = atr_arr[i + 1]
            if atr_val > 0:
                plus_di[i + 1] = plus_dm_smooth / atr_val * 100
                minus_di[i + 1] = minus_dm_smooth / atr_val * 100

        dx = np.full_like(close, np.nan, dtype=float)
        for i in range(period, len(close)):
            pdi = plus_di[i]
            mdi = minus_di[i]
            if not np.isnan(pdi) and not np.isnan(mdi) and (pdi + mdi) > 0:
                dx[i] = abs(pdi - mdi) / (pdi + mdi) * 100

        # Smooth DX to ADX
        valid_dx = dx[~np.isnan(dx)]
        if len(valid_dx) >= period:
            result[period * 2 - 1] = np.mean(valid_dx[:period])
            for i in range(period * 2, len(close)):
                if not np.isnan(dx[i - 1]):
                    result[i] = (result[i - 1] * (period - 1) + dx[i - 1]) / period
        return result

