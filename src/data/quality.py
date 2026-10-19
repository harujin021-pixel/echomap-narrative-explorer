"""数据质量报告模块（src.data.quality）。

阶段 1 功能：根据 DataFrame 计算真实的数据质量指标，并导出可读的 Markdown 报告。
所有数字均来自输入数据本身，不做任何虚构或估算。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.data.loader import REQUIRED_COLUMNS
from src.data.cleaning import DATE_COL

# 需要统计文本长度的列
TEXT_LENGTH_COLS = ("title", "content")


def _is_blank(series: pd.Series) -> pd.Series:
    """判断每个单元格是否为空（NaN 或去空白后为空字符串）。"""
    return series.isna() | (series.astype(str).str.strip() == "")


def build_quality_report(df: pd.DataFrame, name: str = "dataset") -> dict:
    """计算数据质量指标，返回可 JSON 序列化的字典。"""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("build_quality_report 需要 pandas.DataFrame")

    total_rows = int(len(df))

    report: dict = {
        "name": name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rows": total_rows,
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_by_column": {},
        "missing_ratio_by_column": {},
        "missing_required_columns": {},
        "text_length_stats": {},
        "date_summary": None,
    }

    # 各列缺失情况
    for col in df.columns:
        blank = _is_blank(df[col])
        count = int(blank.sum())
        report["missing_by_column"][col] = count
        report["missing_ratio_by_column"][col] = (
            round(count / total_rows, 4) if total_rows else 0.0
        )

    # 必需列缺失情况
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            report["missing_required_columns"][col] = int(_is_blank(df[col]).sum())

    # 文本长度统计（按字符数）
    for col in TEXT_LENGTH_COLS:
        if col in df.columns:
            lengths = df[col].astype(str).str.len()
            report["text_length_stats"][col] = {
                "min": int(lengths.min()) if total_rows else 0,
                "max": int(lengths.max()) if total_rows else 0,
                "mean": round(float(lengths.mean()), 2) if total_rows else 0.0,
            }

    # 日期摘要（区分「缺失/空」与「非空但无法解析」）
    if DATE_COL in df.columns:
        raw_series = df[DATE_COL]
        blank_mask = _is_blank(raw_series)
        if pd.api.types.is_datetime64_any_dtype(raw_series):
            parsed = raw_series
        else:
            parsed = pd.to_datetime(raw_series, format="mixed", errors="coerce")
        valid = parsed.dropna()
        report["date_summary"] = {
            "missing": int(blank_mask.sum()),
            "valid": int(valid.shape[0]),
            "invalid": int((~blank_mask & parsed.isna()).sum()),
            "min": valid.min().isoformat() if not valid.empty else None,
            "max": valid.max().isoformat() if not valid.empty else None,
        }

    return report


def report_to_markdown(report: dict) -> str:
    """把质量报告字典格式化为 Markdown 文本。"""
    lines: list[str] = []
    lines.append(f"## 数据集：{report['name']}")
    lines.append("")
    lines.append(f"- 生成时间：{report['generated_at']}")
    lines.append(f"- 行数：{report['rows']}，列数：{report['columns']}")
    lines.append(f"- 完全重复行数：{report['duplicate_rows']}")
    lines.append("")

    lines.append("### 各列缺失（空值）情况")
    lines.append("")
    lines.append("| 列名 | 缺失数 | 缺失比例 |")
    lines.append("| --- | --- | --- |")
    for col in report["column_names"]:
        lines.append(
            f"| {col} | {report['missing_by_column'][col]} "
            f"| {report['missing_ratio_by_column'][col]:.2%} |"
        )
    lines.append("")

    lines.append("### 必需列缺失")
    lines.append("")
    if report["missing_required_columns"]:
        for col, count in report["missing_required_columns"].items():
            lines.append(f"- {col}：{count}")
    else:
        lines.append("- （无相关列）")
    lines.append("")

    lines.append("### 文本长度统计（字符数）")
    lines.append("")
    if report["text_length_stats"]:
        lines.append("| 列名 | 最短 | 最长 | 平均 |")
        lines.append("| --- | --- | --- | --- |")
        for col, stats in report["text_length_stats"].items():
            lines.append(
                f"| {col} | {stats['min']} | {stats['max']} | {stats['mean']} |"
            )
    else:
        lines.append("- （无相关列）")
    lines.append("")

    lines.append("### 日期字段摘要")
    lines.append("")
    ds = report["date_summary"]
    if ds is None:
        lines.append("- （无日期列）")
    else:
        lines.append(f"- 缺失（空）：{ds['missing']}")
        lines.append(f"- 可解析：{ds['valid']}")
        lines.append(f"- 无效：{ds['invalid']}")
        lines.append(f"- 最早：{ds['min']}")
        lines.append(f"- 最晚：{ds['max']}")
    lines.append("")

    return "\n".join(lines)


def save_report(report: dict, path: str | Path) -> Path:
    """把质量报告以 Markdown 写入 path（自动创建父目录），返回写入路径。"""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_to_markdown(report), encoding="utf-8")
    return out_path
