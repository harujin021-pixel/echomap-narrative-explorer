"""数据导入适配层（src.ui.data_io）。

阶段 3.1 功能：把 Streamlit 上传的文件对象适配到现有 run_ingestion() 路径接口，
并提供合成示例数据的加载入口。

设计原则：
    - 复用 src.data.pipeline.run_ingestion，不重复实现导入/清洗/质量报告逻辑。
    - 上传文件写入系统临时目录，处理完成后（无论成功或失败）立即清理。
    - 调用 run_ingestion 时不指定 report_path，因此不会写入或覆盖任何报告文件。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from src.data.loader import DataValidationError
from src.data.pipeline import run_ingestion

# 项目根目录（src/ui/data_io.py 的上两级）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_news_corpus.csv"


def _extract_bytes(uploaded_file: Any) -> bytes:
    """从类文件对象中读取字节，兼容 Streamlit UploadedFile 与 io.BytesIO。"""
    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue()
    if hasattr(uploaded_file, "read"):
        return uploaded_file.read()
    raise TypeError("uploaded_file 需要是类文件对象（支持 getvalue 或 read）")


def load_uploaded_csv(uploaded_file: Any) -> dict:
    """处理 Streamlit 上传的 CSV 文件，返回 run_ingestion 的结果字典。

    流程：
        1. 读取上传文件字节。
        2. 写入系统临时目录的临时 .csv 文件。
        3. 调用 run_ingestion（不写报告文件）。
        4. 在 finally 中删除临时文件。

    返回:
        与 run_ingestion 一致的 dict：
        {raw, clean, raw_report, clean_report, report_path}
        其中 report_path 恒为 None（本函数不写报告）。

    异常:
        DataValidationError: 缺少必需列或编码无法识别（由 load_csv 抛出，原样传递）。
        ValueError: 清洗时缺少必需列（由 clean_news_data 抛出，原样传递）。
        Exception: 其他未预期异常原样传递，由调用方决定如何提示用户。
    """
    data = _extract_bytes(uploaded_file)

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, encoding=None
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(data)

        # 不指定 report_path，避免写入或覆盖任何报告文件
        return run_ingestion(tmp_path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except OSError:
                # 临时文件删除失败不影响数据结果，但不应掩盖原始异常
                pass


def load_synthetic_demo() -> dict:
    """加载内置合成示例数据，返回 run_ingestion 的结果字典。

    使用 tests/fixtures/synthetic_news_corpus.csv（明确标记为合成测试数据）。
    同样不写报告文件。

    异常:
        FileNotFoundError: 夹具文件不存在。
        DataValidationError: 夹具格式不符合规范（理论上不应发生）。
    """
    if not SYNTHETIC_FIXTURE.is_file():
        raise FileNotFoundError(f"合成示例数据不存在: {SYNTHETIC_FIXTURE}")
    return run_ingestion(SYNTHETIC_FIXTURE)
