"""研报模块 — 一键生成研报"""

from datetime import datetime


def generate_report(
    title: str,
    sections: list[dict],
    output_path: str = None,
) -> str:
    """生成研报并保存到 Obsidian

    Args:
        title: 研报标题
        sections: 章节列表 [{"heading": str, "content": str}, ...]
        output_path: 输出路径，默认 Obsidian 研究分析目录

    Returns:
        文件路径
    """
    ...
