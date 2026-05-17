"""宏观总监 — 数据注入 + 多视角渲染

三角色研究框架第一角色：MacroDirector 接收已拉取的经济日历和新闻数据，
从四个维度渲染宏观分析，供 report 模块嵌入或 CLI 直接输出。
"""

import datetime

from finlab.macro.fetchers import filter_high_impact_events, WATCHED_EVENTS
from finlab.core.scoring import score_event
from finlab.core.models import MacroEvent
from finlab.core.vocabulary import cn_match_keywords


class MacroDirector:
    """宏观总监 — 数据注入 + 多视角渲染"""

    def __init__(
        self,
        events: list[dict],
        news: list[dict],
        flashes: list[dict] | None = None,
    ) -> None:
        self.events = events
        self.news = news
        self.flashes = flashes or []
        self._high_impact: list[dict] | None = None

    @property
    def high_impact(self) -> list[dict]:
        if self._high_impact is None:
            if self.events and "error" not in self.events[0]:
                self._high_impact = filter_high_impact_events(self.events)
            else:
                self._high_impact = []
        return self._high_impact

    # ── 章节子段渲染 ──

    def render_calendar_section(self, country: str = "us") -> str:
        """第一章：财经日历 — 近期重要事件一览"""
        lines = ["## 一、财经日历"]
        lines.append("")

        if not self.high_impact:
            lines.append("> ⚠️ 经济日历数据暂不可用")
            return "\n".join(lines)

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # Group events by date
        by_date: dict[str, list[dict]] = {}
        for e in self.high_impact:
            d = str(e.get("Date", ""))[:10]
            by_date.setdefault(d, []).append(e)

        imp_label = {3: "🔴极高", 2: "🟠高", 1: "🟡中", 0: "⚪低"}

        for date_str in sorted(by_date.keys()):
            label = "📅 今日" if date_str == today_str else f"📅 {date_str}"
            lines.append(f"### {label}")
            for e in by_date[date_str]:
                me = MacroEvent.from_dict(e)
                imp = e.get("Importance", 1)
                lines.append(
                    f"- {imp_label.get(imp, '⚪低')} **{me.indicator}**"
                    f"  ⏰ {me.time}  |  预期 {me.forecast}  |  前值 {me.previous}"
                )
            lines.append("")

        return "\n".join(lines)

    def render_events_section(self, country: str = "us") -> str:
        """第二章：今日数据 — 实际值 vs 预期，含评分"""
        lines = ["## 二、今日数据"]
        lines.append("")

        if not self.high_impact:
            lines.append("> ⚠️ 今日无高影响事件数据")
            return "\n".join(lines)

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        today_events = [e for e in self.high_impact if str(e.get("Date", ""))[:10] == today_str]

        if not today_events:
            lines.append("> 今日无重要经济数据发布")
            return "\n".join(lines)

        for e in today_events:
            event_name = e.get("Event", "N/A")
            actual = e.get("Actual", "-")
            forecast = e.get("Forecast", "-")
            previous = e.get("Previous", "-")
            s = score_event(event_name, actual, forecast, previous)
            me = MacroEvent.from_dict(e)

            lines.append(f"### {me.indicator}")
            lines.append(f"- ⏰ 发布时间：{me.time}")
            lines.append(f"- 📊 实际值：**{actual}**  |  预期：{forecast}  |  前值：{previous}")
            lines.append(f"- 📈 影响评分：{s.as_label()}")
            if me.reason:
                lines.append(f"- 💬 解读：{me.reason}")
            lines.append("")

        return "\n".join(lines)

    def render_impact_section(self, country: str = "us") -> str:
        """第三章：综合影响评估 — 总体方向与关键主题"""
        lines = ["## 三、综合影响评估"]
        lines.append("")

        if not self.high_impact:
            lines.append("> ⚠️ 无足够数据评估宏观影响")
            return "\n".join(lines)

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        today_events = [e for e in self.high_impact if str(e.get("Date", ""))[:10] == today_str]

        # Score today's events
        scores: list[int] = []
        directions: list[str] = []
        for e in today_events:
            event_name = e.get("Event", "N/A")
            actual = str(e.get("Actual", "-"))
            forecast = str(e.get("Forecast", "-"))
            previous = str(e.get("Previous", "-"))
            s = score_event(event_name, actual, forecast, previous)
            scores.append(s.value)
            # Determine direction from score
            if s.value >= 8:
                directions.append("strong_bullish")
            elif s.value >= 6:
                directions.append("bullish")
            elif s.value >= 4:
                directions.append("neutral")
            elif s.value >= 2:
                directions.append("bearish")
            else:
                directions.append("strong_bearish")

        # Aggregate
        if scores:
            avg_score = sum(scores) / len(scores)
            bullish = sum(1 for d in directions if d in ("bullish", "strong_bullish"))
            bearish = sum(1 for d in directions if d in ("bearish", "strong_bearish"))
            neutral = sum(1 for d in directions if d == "neutral")

            lines.append(f"**今日评分汇总**（{len(scores)} 项指标）")
            lines.append(f"- 平均评分：{avg_score:.1f} / 10")
            lines.append(f"- 利多指标：{bullish} 项  |  利空指标：{bearish} 项  |  中性：{neutral} 项")

            if bullish > bearish:
                lines.append("- 总体方向：✅ **偏多** — 多数指标指向经济韧性")
            elif bearish > bullish:
                lines.append("- 总体方向：🔴 **偏空** — 多数指标低于预期")
            else:
                lines.append("- 总体方向：⚖️ **中性** — 多空信号均衡")
        else:
            lines.append("今日无评分数据，等待明日数据更新。")

        lines.append("")

        # Tomorrow preview
        tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_events = [e for e in self.high_impact if str(e.get("Date", ""))[:10] == tomorrow_str]
        if tomorrow_events:
            lines.append(f"**明日关注**（{len(tomorrow_events)} 项）")
            for e in tomorrow_events[:5]:
                me = MacroEvent.from_dict(e)
                lines.append(f"- {me.indicator}  ⏰ {me.time}  |  预期 {me.forecast}")
            lines.append("")

        return "\n".join(lines)

    def render_risk_section(self, country: str = "us") -> str:
        """第四章：风险提示 — 新闻驱动风险 + 事件集中度"""
        lines = ["## 四、风险提示"]
        lines.append("")

        # ForexLive macro news
        macro_news = [
            n for n in self.news
            if any(e.lower() in n.get("title", "").lower() for e in WATCHED_EVENTS)
        ]
        if macro_news:
            lines.append("### 📰 ForexLive 宏观新闻")
            for n in macro_news[:5]:
                lines.append(f"- {n['title'][:120]}")
            lines.append("")

        # JIN10 real-time flashes
        if self.flashes:
            all_keywords = cn_match_keywords()
            macro_flashes = [
                f for f in self.flashes
                if any(
                    kw.lower() in (f.get("content", "") or f.get("title", "")).lower()
                    for kw in all_keywords
                )
            ]
            if macro_flashes:
                lines.append(f"### 📡 金十实时快讯（{len(macro_flashes)} 条）")
                for fh in macro_flashes[:8]:
                    t_raw = fh.get("time", "")
                    # Handle both ISO 8601 and HH:MM:SS formats
                    if "T" in t_raw:
                        t = t_raw.split("T")[1][:5] if "T" in t_raw else t_raw[:5]
                    else:
                        t = t_raw[:5]
                    content = fh.get("content", "") or fh.get("title", "")
                    lines.append(f"- [{t}] {content[:120]}")
                lines.append("")
        elif macro_news:
            pass  # At least one risk source is present
        else:
            lines.append("> 暂无宏观新闻风险信号")
            lines.append("")

        # Event concentration risk
        if self.high_impact:
            now = datetime.datetime.now()
            tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            tomorrow_events = [e for e in self.high_impact if str(e.get("Date", ""))[:10] == tomorrow_str]
            if len(tomorrow_events) >= 4:
                lines.append("### ⚡ 事件集中度预警")
                lines.append(f"> 明日有 **{len(tomorrow_events)}** 项高影响事件密集发布，波动率可能放大。")
                lines.append("> 建议：控制仓位，避免在数据发布前后追涨杀跌。")
                lines.append("")

        return "\n".join(lines)

    # ── CLI 便利方法 ──

    def render_full_report(self, country: str = "us") -> str:
        """生成完整宏观简报（替换原 generate_macro_report）"""
        now = datetime.datetime.now()
        sections = [
            f"{'=' * 56}",
            f"  📊 宏观数据快讯 — {now.strftime('%Y-%m-%d %H:%M')} 北京时间",
            f"{'=' * 56}",
            "",
            self.render_calendar_section(country),
            self.render_events_section(country),
            self.render_impact_section(country),
            self.render_risk_section(country),
            "=" * 56,
        ]
        return "\n".join(sections)

    def render_summary(self, country: str = "us") -> str:
        """生成精简版宏观摘要（替换原 generate_macro_summary）"""
        now = datetime.datetime.now()
        lines = [f"【🌍 宏观预览】{now.strftime('%m/%d %H:%M')}"]

        if self.high_impact:
            today_str = now.strftime("%Y-%m-%d")
            today_e = [e for e in self.high_impact if str(e.get("Date", ""))[:10] == today_str]
            if today_e:
                for e in today_e[:5]:
                    me = MacroEvent.from_dict(e)
                    lines.append(
                        f"  {me.indicator} | {me.time} | 预期{me.forecast}"
                        f" | {me.direction}({me.score}/10)"
                    )

            tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            tom_e = [e for e in self.high_impact if str(e.get("Date", ""))[:10] == tomorrow_str]
            if tom_e:
                lines.append("  --- 明日 ---")
                for e in tom_e[:5]:
                    me = MacroEvent.from_dict(e)
                    lines.append(f"  {me.indicator} | {me.time} | 预期{me.forecast}")
        else:
            lines.append("  ⚠️ 数据暂不可用")

        return "\n".join(lines)
