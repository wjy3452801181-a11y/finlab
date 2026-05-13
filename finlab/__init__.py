"""finlab — 开源个人投行研究工具链"""

from importlib.metadata import version

try:
    __version__ = version("finlab")
except Exception:
    __version__ = "0.1.0"
