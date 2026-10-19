"""数据清洗模块（src.data.cleaning）。

阶段 1 功能：对导入的新闻 DataFrame 做可解释的基础清洗。
清洗规则固定、透明，便于初学者理解与维护。
"""

from __future__ import annotations

import re
from html import unescape

import pandas as pd

from src.data.loader import REQUIRED_COLUMNS

# 日期字段：解析失败会记为 NaT（缺失日期），但**不会**因此删除该行
DATE_COL = "published_at"

# 常见 HTML 标签（如 <p style="text-indent:2em">）：抓取网页正文时常混入，
# 不剥离会被 TF-IDF 当作高频“关键词”，产生按排版格式而非内容聚类的伪主题
_HTML_TAG_RE = re.compile(r"<[^>]*>")


def _strip_html(text: str) -> str:
    """去除 HTML 标签、还原 HTML 实体（&nbsp; 等），并把不换行空格归一为空格。"""
    return unescape(_HTML_TAG_RE.sub("", text)).replace("\xa0", " ")


def clean_news_data(df: pd.DataFrame) -> pd.DataFrame:
    """清洗新闻数据，返回新的 DataFrame（不修改传入对象）。

    清洗步骤：
        1. 所有文本列去除 HTML 标签、还原 HTML 实体（如 &nbsp;），并去除首尾空白。
        2. 将 published_at 解析为日期（无法解析的记为 NaT）。
        3. 删除任一必需列（title/content/source）为空的行。
        4. 删除完全重复的行。
        5. 重置索引。

    参数:
        df: 由 loader.load_csv 读入的 DataFrame。

    返回:
        清洗后的新 DataFrame。
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("clean_news_data 需要 pandas.DataFrame")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"清洗前缺少必需列: {missing}")

    cleaned = df.copy()

    # 1. 文本列去除 HTML 标签/实体 + 首尾空白
    for col in cleaned.columns:
        cleaned[col] = cleaned[col].astype(str).map(_strip_html).str.strip()

    # 2. 日期解析（解析失败 -> NaT）
    if DATE_COL in cleaned.columns:
        cleaned[DATE_COL] = pd.to_datetime(
            cleaned[DATE_COL], format="mixed", errors="coerce"
        )

    # 3. 删除必需列为空的行
    for col in REQUIRED_COLUMNS:
        cleaned = cleaned[cleaned[col] != ""]

    # 4. 删除完全重复的行
    cleaned = cleaned.drop_duplicates()

    # 5. 重置索引
    return cleaned.reset_index(drop=True)
