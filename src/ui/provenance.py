"""数据可追溯性（Data Provenance）辅助模块（src.ui.provenance）。

阶段 4.1 功能：把当前会话中成功导入的数据集整理为一份「数据档案」，
使界面上的分析结果可以追溯到具体的数据来源、导入时间与数据指纹。

设计原则：
    - 全部为纯函数，不依赖 Streamlit，便于单元测试。
    - 所有字段均来自实际传入的 ingestion_result / session_state 值，
      缺失时显示明确的「未知 / 不可用」占位，不编造。
    - 导入时间仅保存在 Streamlit 会话内，刷新或重新载入后会重置——
      本模块只如实格式化，不宣称实现了持久化审计日志。
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.ui.cluster_view import data_fingerprint

DATE_COL = "published_at"

# 清洗步骤摘要：与 src/data/cleaning.py 的 clean_news_data 步骤一一对应（固定文案）
CLEANING_STEPS = (
    "1. 所有文本列去除 HTML 标签、还原 HTML 实体（如 &nbsp;），并去除首尾空白；"
    "2. published_at 解析为日期（失败记为缺失，不删行）；"
    "3. 删除 title / content / source 任一为空的行；"
    "4. 删除完全重复的行；"
    "5. 重置索引。"
)

# 英文版清洗步骤摘要（与 CLEANING_STEPS 一一对应，仅展示语言不同）
CLEANING_STEPS_EN = (
    "1. strip HTML tags, unescape HTML entities (e.g. &nbsp;), and strip "
    "leading/trailing whitespace from all text columns; "
    "2. parse published_at as dates (failures recorded as missing; rows kept); "
    "3. drop rows where any of title / content / source is empty; "
    "4. drop fully duplicated rows; "
    "5. reset the index."
)

PROVENANCE_KEYS = (
    "source_label",
    "dataset_name",
    "imported_at",
    "raw_rows",
    "clean_rows",
    "date_min",
    "date_max",
    "fingerprint",
    "cleaning_steps",
)


def format_imported_at(imported_at: datetime | None, lang: str = "zh") -> str:
    """把导入时间格式化为可读文本；None 时如实说明会话内未知。"""
    if imported_at is None:
        if lang == "en":
            return "unknown (not recorded in this session; resets after page refresh)"
        return "未知（本会话内未记录；刷新页面后重置）"
    return imported_at.strftime("%Y-%m-%d %H:%M:%S")


def date_range(clean_df: pd.DataFrame, lang: str = "zh") -> tuple[str, str]:
    """从清洗后数据提取可解析的发布日期范围。

    日期列缺失、全为空/NaT 时返回占位词（zh "不可用" / en "unavailable"），
    不编造日期。
    """
    unavailable = "unavailable" if lang == "en" else "不可用"
    if not isinstance(clean_df, pd.DataFrame) or DATE_COL not in clean_df.columns:
        return (unavailable, unavailable)
    dates = pd.to_datetime(clean_df[DATE_COL], errors="coerce").dropna()
    if dates.empty:
        return (unavailable, unavailable)
    return (dates.min().strftime("%Y-%m-%d"), dates.max().strftime("%Y-%m-%d"))


def build_provenance(
    result: dict,
    source_label: str | None,
    filename: str | None,
    imported_at: datetime | None,
    fingerprint: str | None = None,
    lang: str = "zh",
) -> dict:
    """整理当前数据集的元信息档案。

    参数:
        result: run_ingestion / load_uploaded_csv / load_synthetic_demo 返回的 dict
                （含 raw / clean）。
        source_label: session_state 中的数据来源标记（"合成测试数据" /
                      "用户上传数据"），缺失时如实标注未知。
        filename: 数据集文件名，缺失时使用「未知文件」占位。
        imported_at: 本会话内的导入时间（可为 None）。
        fingerprint: 数据指纹；为 None 时从 clean DataFrame 实时计算。
        lang: 展示语言（"zh" 默认 / "en"），仅影响占位词与清洗步骤文案。

    返回:
        含 PROVENANCE_KEYS 中全部字段的 dict；空数据或异常输入时不抛异常，
        相应字段标注「无数据 / 不可用 / 未知」（en: no data / unavailable /
        unknown）。
    """
    # 展示层占位词：仅随 lang 变化，默认中文与既有行为/测试完全一致
    if lang == "en":
        unknown, unknown_file = "unknown", "unknown file"
        unknown_source, no_data, unavailable = "unknown source", "no data", "unavailable"
        cleaning_steps = CLEANING_STEPS_EN
    else:
        unknown, unknown_file = "未知", "未知文件"
        unknown_source, no_data, unavailable = "未知来源", "无数据", "不可用"
        cleaning_steps = CLEANING_STEPS

    raw_df = result.get("raw") if isinstance(result, dict) else None
    clean_df = result.get("clean") if isinstance(result, dict) else None

    if not isinstance(clean_df, pd.DataFrame):
        clean_df = pd.DataFrame()
    if not isinstance(raw_df, pd.DataFrame):
        raw_rows: int | str = unknown
    else:
        raw_rows = len(raw_df)

    clean_rows = len(clean_df) if isinstance(clean_df, pd.DataFrame) else unknown

    if fingerprint is None:
        try:
            fingerprint = data_fingerprint(clean_df) if not clean_df.empty else no_data
        except Exception:
            fingerprint = unavailable

    d_min, d_max = date_range(clean_df, lang=lang)

    return {
        "source_label": source_label if source_label else unknown_source,
        "dataset_name": filename if filename else unknown_file,
        "imported_at": format_imported_at(imported_at, lang=lang),
        "raw_rows": raw_rows,
        "clean_rows": clean_rows,
        "date_min": d_min,
        "date_max": d_max,
        "fingerprint": fingerprint,
        "cleaning_steps": cleaning_steps,
    }


def dataset_tag(provenance: dict, lang: str = "zh") -> str:
    """生成分析结果区块顶部的数据集标识文案（一行）。"""
    if lang == "en":
        label = provenance.get("source_label", "unknown source")
        fp = provenance.get("fingerprint", "unavailable")
        return f"Dataset: {label} · fingerprint {fp}"
    label = provenance.get("source_label", "未知来源")
    fp = provenance.get("fingerprint", "不可用")
    return f"数据集：{label} · 指纹 {fp}"
