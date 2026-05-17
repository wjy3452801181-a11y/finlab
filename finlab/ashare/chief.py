"""行业首席 — 数据注入 + 多视角渲染

三角色研究框架第二角色：SectorChief 接收预拉取的 StockData，
从三个维度渲染A股分析，供 CLI 直接输出。
"""

from finlab.ashare.data import StockData
from finlab.ashare.tracker import TrackConfig, TrackResult


class SectorChief:
    """行业首席 — 数据注入 + 多视角渲染"""

    def __init__(
        self,
        stock_data: dict[str, StockData],
        categories: dict[str, list[tuple[str, str]]],
    ) -> None:
        self.stock_data = stock_data
        self.categories = categories

    # ── 板块扫描 ─────────────────────────────────────────

    def render_sector_scan(self, exclude: list[str] | None = None, top_n: int = 15) -> str:
        """板块扫描 — 筛选滞涨标的"""
        exclude = exclude or []
        results: list[dict] = []

        for cat_name, stocks in self.categories.items():
            if cat_name in exclude:
                continue
            for code, name in stocks:
                sd = self.stock_data.get(code)
                if sd is None:
                    continue
                result = self._analyze_stock(sd, code, name, cat_name)
                if result:
                    results.append(result)

        return self._format_sector_scan(results, top_n)

    @staticmethod
    def _analyze_stock(sd: StockData, code: str, name: str, category: str) -> dict | None:
        """分析单个标的"""
        df = sd.df
        if len(df) < 3:
            return None

        today_pct = float(df["pctChg"].iloc[-1])
        d5_open = float(df["close"].iloc[0]) / (1 + float(df["pctChg"].iloc[0]) / 100)
        d5_close = float(df["close"].iloc[-1])
        d5_pct = round((d5_close - d5_open) / d5_open * 100, 2)
        avg_turn = float(df["turn"].mean())
        latest = float(df["close"].iloc[-1])
        avg_vol = float(df["volume"].mean())
        vol_ratio = round(float(df["volume"].iloc[-1]) / avg_vol, 2) if avg_vol > 0 else 0

        return {
            "板块": category,
            "代码": code,
            "名称": name,
            "最新价": latest,
            "今日涨幅%": round(today_pct, 2),
            "5日涨幅%": d5_pct,
            "日均换手%": round(avg_turn, 2),
            "量比": vol_ratio,
        }

    @staticmethod
    def _format_sector_scan(results: list[dict], top_n: int = 15) -> str:
        """格式化板块扫描结果"""
        if not results:
            return "无数据"

        lines = []
        lines.append(f"{'=' * 80}")
        lines.append("A股板块扫描 — 筛选滞涨标的（今日未大涨+5日未提前抢跑）")
        lines.append(f"{'=' * 80}")

        seen_cats = sorted(set(r["板块"] for r in results))
        for cat in seen_cats:
            subset = [r for r in results if r["板块"] == cat]
            subset.sort(key=lambda x: x["今日涨幅%"])

            lines.append(f"\n▶ {cat}")
            for r in subset:
                flag = ""
                if r["5日涨幅%"] >= 8:
                    flag = " ← 5日已涨太多"
                elif abs(r["今日涨幅%"]) >= 3:
                    flag = " ← 今日涨/跌偏大"
                lines.append(
                    f"  {r['名称']:<10} {r['最新价']:<10} "
                    f"今日{r['今日涨幅%']:>+6.2f}%  "
                    f"5日{r['5日涨幅%']:>+7.2f}%  "
                    f"换手{r['日均换手%']:>6.2f}%  "
                    f"量比{r['量比']:>5.2f}{flag}"
                )

        # 推荐
        candidates = [
            r for r in results
            if abs(r["今日涨幅%"]) < 4 and r["5日涨幅%"] < 8
        ]
        candidates.sort(key=lambda r: r["5日涨幅%"])

        lines.append(f"\n\n{'=' * 80}")
        lines.append("推荐（逻辑驱动 + 尚未明显上涨）：")
        lines.append(f"{'=' * 80}")

        for r in candidates[:top_n]:
            desc = ""
            if r["5日涨幅%"] < 0:
                desc = "回调充分，绝对低吸位"
            elif r["5日涨幅%"] < 2:
                desc = "横盘滞涨，没抢跑"
            elif r["5日涨幅%"] < 5:
                desc = "温和上升，启动阶段"
            else:
                desc = "有一定涨幅但未透支"

            if r["量比"] < 0.5:
                desc += ", 量能不足"
            elif r["量比"] > 3:
                desc += ", 放量明显"

            lines.append(
                f"  {r['名称']:<10} {r['代码']:<12} {r['最新价']:<8}  "
                f"5日{r['5日涨幅%']:>+7.2f}%  "
                f"今日{r['今日涨幅%']:>+6.2f}%  — {desc}"
            )

        return "\n".join(lines)

    # ── 持仓追踪 ─────────────────────────────────────────

    def render_tracking(self, configs: list[TrackConfig]) -> str:
        """持仓追踪 — 止损止盈 + 量价预警"""
        results: list[TrackResult] = []

        for cfg in configs:
            sd = self.stock_data.get(cfg.code)
            if sd is None:
                continue
            result = TrackResult(config=cfg, data=sd)
            result.alerts = self._check_alerts(result)
            results.append(result)

        return self._format_tracking(results)

    @staticmethod
    def _check_alerts(result: TrackResult) -> list[str]:
        """检查各项预警"""
        s = result.data
        c = result.config
        alerts = []

        if c.stop > 0 and s.close <= c.stop:
            alerts.append(f"收盘{s.close:.2f}已≤止损{c.stop:.2f}")
            result.signal = "止损离场"

        if c.target1 > 0 and s.close >= c.target1:
            alerts.append(f"收盘{s.close:.2f}已≥目标{c.target1:.2f}")
            if result.signal == "无信号":
                result.signal = "目标达成"

        if result.data.prev is not None and s.pct < -3:
            alerts.append(f"今日{s.pct:+.2f}%，单日跌幅超3%")
            if result.signal == "无信号":
                result.signal = "单日大跌"

        vr = s.vol_ratio
        if vr < 0.5:
            alerts.append(f"缩量量比{vr:.2f}")
        elif vr > 2.5:
            alerts.append(f"放量量比{vr:.2f}")

        dev = (s.close - s.ma5) / s.ma5 * 100
        if abs(dev) > 5:
            alerts.append(f"偏离MA5 {dev:+.1f}%")

        day_range = (s.high - s.low) / s.close * 100
        if day_range > 6:
            alerts.append(f"日内振幅{day_range:.1f}%")

        return alerts

    @staticmethod
    def _format_tracking(results: list[TrackResult]) -> str:
        """格式化持仓追踪结果"""
        if not results:
            return "无追踪数据"

        lines = []
        for r in results:
            lines.append(str(r))

        lines.append("")
        lines.append("=" * 60)
        lines.append("【综合评估】")

        triggered = [r for r in results if r.status == "❌ 触止损"]
        reached = [r for r in results if r.status == "🎯 达目标"]
        warnings = [r for r in results if r.status == "⚠️ 预警"]

        if triggered:
            for r in triggered:
                lines.append(f"  ❌ {r.config.name} 触止损！当前{r.data.close:.2f}")
        if reached:
            for r in reached:
                lines.append(f"  🎯 {r.config.name} 达目标！当前{r.data.close:.2f}")
        if warnings:
            for r in warnings:
                lines.append(f"  ⚠️  {r.config.name}: {' | '.join(r.alerts)}")
        if not triggered and not reached and not warnings:
            lines.append("  ✅ 正常，无特殊信号")

        return "\n".join(lines)

    # ── 板块轮动 ─────────────────────────────────────────

    def render_sector_rotation(self) -> str:
        """板块轮动 — 按板块综合评分排名"""
        sector_scores: list[dict] = []

        for cat_name, stocks in self.categories.items():
            metrics = self._calc_sector_metrics(stocks)
            if metrics is None:
                continue
            scores = self._score_sector(metrics)
            scores["板块"] = cat_name
            sector_scores.append(scores)

        sector_scores.sort(key=lambda x: x["综合分"], reverse=True)

        return self._format_rotation(sector_scores)

    def _calc_sector_metrics(self, stocks: list[tuple[str, str]]) -> dict | None:
        """计算板块聚合指标"""
        d5_pcts = []
        vol_ratios = []
        turns = []
        today_pcts = []

        for code, _name in stocks:
            sd = self.stock_data.get(code)
            if sd is None or len(sd.df) < 3:
                continue
            df = sd.df
            today_pct = float(df["pctChg"].iloc[-1])
            d5_open = float(df["close"].iloc[0]) / (1 + float(df["pctChg"].iloc[0]) / 100)
            d5_close = float(df["close"].iloc[-1])
            d5_pct = (d5_close - d5_open) / d5_open * 100
            avg_vol = float(df["volume"].mean())
            vol_ratio = float(df["volume"].iloc[-1]) / avg_vol if avg_vol > 0 else 0
            avg_turn = float(df["turn"].mean())

            d5_pcts.append(d5_pct)
            vol_ratios.append(vol_ratio)
            turns.append(avg_turn)
            today_pcts.append(today_pct)

        if not d5_pcts:
            return None

        n = len(d5_pcts)
        return {
            "n_stocks": n,
            "avg_d5_pct": sum(d5_pcts) / n,
            "avg_vol_ratio": sum(vol_ratios) / n,
            "avg_turn": sum(turns) / n,
            "breadth": sum(1 for p in today_pcts if p > 0) / n,
        }

    @staticmethod
    def _score_sector(metrics: dict) -> dict:
        """按四维度评分（1-10）"""

        # 动量 40% — 5日均涨幅，线性映射 (0→5, 5%+→10)
        d5 = metrics["avg_d5_pct"]
        momentum = min(max(d5 * 1.0 + 5, 1), 10)

        # 量能 30% — 均量比，>1.5=强势
        vr = metrics["avg_vol_ratio"]
        volume_score = min(max(vr * 3.0 + 3, 1), 10)

        # 活跃度 20% — 均换手，>3%=高流动性
        tr = metrics["avg_turn"]
        activity = min(max(tr * 1.5 + 3, 1), 10)

        # 宽度 10% — 上涨占比，线性映射
        br = metrics["breadth"]
        breadth = min(max(br * 8 + 1, 1), 10)

        composite = round(
            momentum * 0.4 + volume_score * 0.3 + activity * 0.2 + breadth * 0.1, 1
        )

        return {
            "动量分": round(momentum, 1),
            "量能分": round(volume_score, 1),
            "活跃分": round(activity, 1),
            "宽度分": round(breadth, 1),
            "综合分": composite,
            "个股数": metrics["n_stocks"],
            "均5日涨幅": round(metrics["avg_d5_pct"], 2),
            "均量比": round(metrics["avg_vol_ratio"], 2),
            "均换手": round(metrics["avg_turn"], 2),
            "上涨占比": round(metrics["breadth"] * 100),
        }

    @staticmethod
    def _format_rotation(sector_scores: list[dict]) -> str:
        """格式化板块轮动输出"""
        if not sector_scores:
            return "无板块数据"

        lines = []
        lines.append(f"{'=' * 80}")
        lines.append("板块轮动评分 — 综合排名")
        lines.append(f"{'=' * 80}")
        lines.append("")

        # 表头
        header = (
            f"{'排名':<6}{'板块':<12}{'综合分':<8}{'动量(40%)':<10}"
            f"{'量能(30%)':<10}{'活跃(20%)':<10}{'宽度(10%)':<10}"
            f"{'均5日涨幅':<10}{'均量比':<8}{'均换手':<8}{'上涨占比':<8}"
        )
        lines.append(header)
        lines.append("-" * len(header))

        for i, s in enumerate(sector_scores, 1):
            rank = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i:>2}")
            lines.append(
                f"{rank:<6}{s['板块']:<12}{s['综合分']:<8}"
                f"{s['动量分']:<10}{s['量能分']:<10}{s['活跃分']:<10}{s['宽度分']:<10}"
                f"{s['均5日涨幅']:>+8.2f}%  {s['均量比']:<8.2f}"
                f"{s['均换手']:<8.2f}{s['上涨占比']:>4}%"
            )

        lines.append("")
        lines.append("评分逻辑：")
        lines.append("  动量(40%) — 板块5日均涨幅，正值=强势")
        lines.append("  量能(30%) — 板块均量比，>1.5=资金流入")
        lines.append("  活跃(20%) — 板块均换手，流动性指标")
        lines.append("  宽度(10%) — 上涨个股占比，板块一致性")
        lines.append("  综合分 = 动量×0.4 + 量能×0.3 + 活跃×0.2 + 宽度×0.1")

        return "\n".join(lines)
