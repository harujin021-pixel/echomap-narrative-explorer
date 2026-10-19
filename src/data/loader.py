"""CSV 导入模块（src.data.loader）。

阶段 1 功能：从 CSV 文件读取新闻数据，并做最小结构校验。
本模块**不包含**任何 AI 分析、可视化或界面功能。

数据规范（最小字段）：
    必需列：title（标题）、content（正文）、source（来源媒体）
    可选列：id、author、published_at、url
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# —— 规范列名 ——
TITLE_COL = "title"
CONTENT_COL = "content"
SOURCE_COL = "source"

REQUIRED_COLUMNS = (TITLE_COL, CONTENT_COL, SOURCE_COL)
OPTIONAL_COLUMNS = ("id", "author", "published_at", "url")

# 读取 CSV 时依次尝试的编码（中文新闻数据常见 utf-8-sig / utf-8 / gbk）
CANDIDATE_ENCODINGS = ("utf-8-sig", "utf-8", "gbk")


class DataValidationError(ValueError):
    """输入数据不符合规范时抛出。"""


def find_csv_files(raw_dir: str | Path) -> list[Path]:
    """列出 raw_dir 目录下（含子目录）的所有 .csv 文件，按路径名排序。"""
    directory = Path(raw_dir)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob("*.csv") if p.is_file())


def load_csv(path: str | Path, encoding: str | None = None) -> pd.DataFrame:
    """读取一个 CSV 文件并校验必需列。

    参数:
        path: CSV 文件路径。
        encoding: 指定编码；为 None 时依次尝试 CANDIDATE_ENCODINGS。

    返回:
        pandas.DataFrame（所有列按字符串读取，空单元格为 ""）。

    异常:
        FileNotFoundError: 文件不存在。
        DataValidationError: 所有候选编码都无法解码，或缺少必需列。
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"找不到 CSV 文件: {file_path}")

    encodings: tuple[str, ...] = (encoding,) if encoding else CANDIDATE_ENCODINGS
    last_error: Exception | None = None
    df: pd.DataFrame | None = None

    for enc in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=enc,
                dtype=str,
                keep_default_na=False,
            )
            break
        except UnicodeDecodeError as exc:  # 换下一个候选编码
            last_error = exc

    if df is None:
        raise DataValidationError(
            f"无法用候选编码 {encodings} 解码文件 {file_path}：{last_error}"
        )

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataValidationError(
            f"CSV 文件缺少必需列 {missing}；当前列：{list(df.columns)}"
        )

    return df
