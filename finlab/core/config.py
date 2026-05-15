"""配置模块 — 用户级配置管理

读取 ~/.config/finlab/config.toml，未配置项使用内置默认值。
"""

import os
import sys
from pathlib import Path
from typing import Optional


# ── 默认值 ──────────────────────────────────────────────

def _default_ticker_groups() -> dict[str, list[str]]:
    return {
        "大盘指数ETF": ["SPY", "QQQ"],
        "美股行业ETF": ["XLK", "XLE", "XLF", "XLI", "XLV", "XLY", "XLI", "XLU", "XLB"],
        "科技AI": ["NVDA", "GOOGL", "MSFT", "AMD", "INTC", "SMH"],
        "大宗商品": ["GLD", "USO", "SLV"],
        "债券/外汇": ["TLT", "UUP"],
        "中国": ["FXI", "KWEB"],
        "加密": ["BTC-USD", "ETH-USD"],
    }


def _default_sectors() -> dict[str, list[tuple[str, str]]]:
    return {
        "算力/AI": [
            ("sh.600941", "中国移动"), ("sh.600050", "中国联通"), ("sh.601728", "中国电信"),
            ("sz.000938", "紫光股份"), ("sh.600498", "烽火通信"), ("sz.000063", "中兴通讯"),
            ("sz.002230", "科大讯飞"), ("sh.600570", "恒生电子"),
        ],
        "芯片": [
            ("sh.688981", "中芯国际"), ("sz.002371", "北方华创"), ("sh.603501", "韦尔股份"),
            ("sz.300661", "圣邦股份"), ("sh.603986", "兆易创新"), ("sz.002049", "紫光国微"),
            ("sz.300782", "卓胜微"), ("sz.002185", "华天科技"),
        ],
        "消费电子": [
            ("sz.002475", "立讯精密"), ("sz.002241", "歌尔股份"), ("sh.603160", "汇顶科技"),
            ("sz.002600", "领益智造"), ("sh.600745", "闻泰科技"),
        ],
        "新能源": [
            ("sz.002459", "晶澳科技"), ("sz.300274", "阳光电源"), ("sh.688599", "天合光能"),
            ("sh.601012", "隆基绿能"), ("sz.300750", "宁德时代"), ("sh.600438", "通威股份"),
        ],
        "军工": [
            ("sh.600760", "中航沈飞"), ("sh.600893", "航发动力"), ("sz.000768", "中航西飞"),
            ("sz.002179", "中航光电"), ("sh.600150", "中国船舶"), ("sh.600879", "航天电子"),
        ],
        "金融": [
            ("sh.600036", "招商银行"), ("sh.601318", "中国平安"), ("sh.600030", "中信证券"),
            ("sh.601939", "建设银行"),
        ],
        "消费": [
            ("sh.600519", "贵州茅台"), ("sz.000568", "泸州老窖"), ("sh.600809", "山西汾酒"),
            ("sz.000858", "五粮液"), ("sh.600887", "伊利股份"), ("sh.600276", "恒瑞医药"),
        ],
        "金属资源": [
            ("sh.600547", "山东黄金"), ("sh.600489", "中金黄金"), ("sh.601899", "紫金矿业"),
            ("sz.000831", "中国稀土"), ("sh.600010", "包钢股份"),
        ],
    }


_DEFAULT_OBSIDIAN_DIR = os.path.expanduser("~/Documents/Obsidian Vault/研究分析")


# ── 配置对象 ────────────────────────────────────────────

class Config:
    """finlab 全局配置"""

    def __init__(self, data: dict = None):
        d = data or {}
        self.obsidian_dir: str = d.get("obsidian_dir", _DEFAULT_OBSIDIAN_DIR)
        self.ticker_groups: dict[str, list[str]] = d.get("ticker_groups", _default_ticker_groups())
        self.sectors: dict[str, list[tuple[str, str]]] = d.get("sectors", _default_sectors())
        self.report_default_days: int = d.get("report_default_days", 7)
        self.macro_default_days: int = d.get("macro_default_days", 2)


# ── 加载 ────────────────────────────────────────────────

_config: Optional[Config] = None


def _find_config_path() -> Optional[Path]:
    """查找配置文件"""
    # 1. 环境变量
    env_path = os.environ.get("FINLAB_CONFIG")
    if env_path:
        p = Path(env_path)
        return p if p.exists() else None

    # 2. XDG 标准路径
    xdg = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    path = Path(xdg) / "finlab" / "config.toml"
    if path.exists():
        return path

    # 3. 项目根目录
    path = Path(__file__).parent.parent.parent / "config.toml"
    if path.exists():
        return path

    return None


def _read_toml(path: Path) -> dict:
    """解析 TOML 配置文件"""
    if sys.version_info >= (3, 11):
        import tomllib
        return tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        import tomli
        return tomli.loads(path.read_text(encoding="utf-8"))


def get_config() -> Config:
    """获取全局配置（单例，首次调用时加载）"""
    global _config
    if _config is not None:
        return _config

    data = {}
    path = _find_config_path()
    if path:
        try:
            raw = _read_toml(path)
            # 展平 TOML section
            for section in ("report", "macro", "ashare"):
                if section in raw:
                    data.update(raw[section])
            if "ticker_groups" in raw:
                data["ticker_groups"] = raw["ticker_groups"]
            if "sectors" in raw:
                data["sectors"] = raw["sectors"]
            if "obsidian_dir" in raw:
                data["obsidian_dir"] = raw["obsidian_dir"]
        except Exception:
            pass  # 解析失败 → 用默认值

    _config = Config(data)
    return _config


def reload_config() -> Config:
    """强制重新加载配置"""
    global _config
    _config = None
    return get_config()
