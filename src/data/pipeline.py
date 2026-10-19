"""数据流程串联模块（src.data.pipeline）。

阶段 1 功能：把「CSV 导入 -> 清洗前质量报告 -> 清洗 -> 清洗后质量报告 -> 写报告」
串成一个可复用的调用入口。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.loader import load_csv
from src.data.cleaning import clean_news_data
from src.data.quality import build_quality_report, report_to_markdown


def run_ingestion(
    input_path: str | Path,
    report_path: str | Path | None = None,
    dataset_name: str | None = None,
) -> dict:
    """执行完整的导入与质量检查流程。

    参数:
        input_path: 输入 CSV 文件路径。
        report_path: 可选，Markdown 报告输出路径；为 None 时不写文件。
        dataset_name: 可选，报告中的数据集名称；默认取文件名。

    返回:
        dict，包含：
            raw          清洗前的 DataFrame
            clean        清洗后的 DataFrame
            raw_report   清洗前的质量报告（dict）
            clean_report 清洗后的质量报告（dict）
            report_path  实际写入的报告路径（未写入则为 None）
    """
    source = Path(input_path)
    base_name = dataset_name or source.stem

    raw_df = load_csv(source)
    raw_report = build_quality_report(raw_df, name=f"{base_name}（清洗前）")

    clean_df = clean_news_data(raw_df)
    clean_report = build_quality_report(clean_df, name=f"{base_name}（清洗后）")

    written: Path | None = None
    if report_path is not None:
        markdown = (
            "# EchoMap 数据质量报告\n\n"
            + report_to_markdown(raw_report)
            + "\n"
            + report_to_markdown(clean_report)
        )
        out_path = Path(report_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        written = out_path

    return {
        "raw": raw_df,
        "clean": clean_df,
        "raw_report": raw_report,
        "clean_report": clean_report,
        "report_path": written,
    }
