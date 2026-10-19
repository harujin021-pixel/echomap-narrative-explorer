"""数据概览统计与图表辅助模块（src.ui.overview）。

阶段 3.2.1 功能：基于清洗后的 DataFrame 计算数据概览指标，
并提供 matplotlib 图表构造（含中文字体检测与降级）。

设计原则：
    - 全部为纯函数，不依赖 Streamlit，便于单元测试。
    - 所有数值均来自输入 DataFrame，不硬编码。
    - 空数据、缺失日期、单一来源等边界返回安全的空结构，不抛异常。
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # 无界面后端，仅用于构造 Figure

import matplotlib.pyplot as plt
from matplotlib import font_manager

import pandas as pd

DATE_COL = "published_at"
REQUIRED_TEXT_COLS = ("title", "content", "source")

# 常见 Windows 中文字体候选（按优先级）
_CJK_FONT_CANDIDATES = ("Microsoft YaHei", "SimHei", "SimSun", "KaiTi", "DengXian")


def compute_overview_stats(clean_df: pd.DataFrame) -> dict:
    """计算数据概览指标，全部来自 clean_df 本身。

    返回 dict：
        rows: 记录数
        n_sources: 不同来源数（按非空 source 计）
        date_min / date_max: 可解析日期的最早/最晚（ISO 字符串或 None）
        valid_dates: 可解析日期数量
        completeness: {字段: 非空数量}（仅统计存在的必需字段）
        content_length: {min, max, mean, median}（正文字符数；无数据时为 None）
    """
    stats: dict = {
        "rows": 0,
        "n_sources": 0,
        "date_min": None,
        "date_max": None,
        "valid_dates": 0,
        "completeness": {},
        "content_length": None,
    }
    if not isinstance(clean_df, pd.DataFrame) or clean_df.empty:
        return stats

    stats["rows"] = int(len(clean_df))

    # 来源数量（去空白后非空）
    if "source" in clean_df.columns:
        sources = clean_df["source"].astype(str).str.strip()
        stats["n_sources"] = int(sources[sources != ""].nunique())

    # 日期范围（仅用可解析日期）
    if DATE_COL in clean_df.columns:
        series = clean_df[DATE_COL]
        if pd.api.types.is_datetime64_any_dtype(series):
            parsed = series
        else:
            parsed = pd.to_datetime(series, format="mixed", errors="coerce")
        valid = parsed.dropna()
        stats["valid_dates"] = int(len(valid))
        if not valid.empty:
            stats["date_min"] = valid.min().date().isoformat()
            stats["date_max"] = valid.max().date().isoformat()

    # 必需字段完整性（非空计数）
    for col in REQUIRED_TEXT_COLS:
        if col in clean_df.columns:
            non_empty = clean_df[col].astype(str).str.strip() != ""
            stats["completeness"][col] = int(non_empty.sum())

    # 正文长度统计（按字符数）
    if "content" in clean_df.columns:
        lengths = clean_df["content"].astype(str).str.len()
        stats["content_length"] = {
            "min": int(lengths.min()),
            "max": int(lengths.max()),
            "mean": round(float(lengths.mean()), 2),
            "median": round(float(lengths.median()), 2),
        }

    return stats


def source_distribution(clean_df: pd.DataFrame) -> pd.Series:
    """返回各来源的文章数量（Series，index=来源，按数量降序）。

    空数据或无 source 列时返回空 Series。
    """
    if not isinstance(clean_df, pd.DataFrame) or clean_df.empty:
        return pd.Series(dtype=int)
    if "source" not in clean_df.columns:
        return pd.Series(dtype=int)
    sources = clean_df["source"].astype(str).str.strip()
    sources = sources[sources != ""]
    if sources.empty:
        return pd.Series(dtype=int)
    return sources.value_counts()


def date_distribution(clean_df: pd.DataFrame) -> pd.Series:
    """返回按日发布文章数量（Series，index=日期字符串，升序）。

    只统计可解析的日期；空数据或无可解析日期时返回空 Series。
    """
    if not isinstance(clean_df, pd.DataFrame) or clean_df.empty:
        return pd.Series(dtype=int)
    if DATE_COL not in clean_df.columns:
        return pd.Series(dtype=int)
    series = clean_df[DATE_COL]
    if pd.api.types.is_datetime64_any_dtype(series):
        parsed = series
    else:
        parsed = pd.to_datetime(series, format="mixed", errors="coerce")
    valid = parsed.dropna()
    if valid.empty:
        return pd.Series(dtype=int)
    return valid.dt.date.value_counts().sort_index()


def find_cjk_font() -> str | None:
    """检测系统中可用的中文字体，返回字体名；找不到时返回 None。"""
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in _CJK_FONT_CANDIDATES:
        if name in available:
            return name
    return None


def make_bar_chart(
    series: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    font_name: str | None = None,
) -> "plt.Figure | None":
    """用 matplotlib 构造柱状图 Figure。

    font_name 为 None 时不设置中文字体（调用方应改用降级方案）。
    空 series 返回 None（调用方应显示空状态提示）。
    """
    if series is None or series.empty:
        return None
    if font_name is None:
        return None

    plt.rcParams["font.sans-serif"] = [font_name]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar([str(i) for i in series.index], series.values)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig
