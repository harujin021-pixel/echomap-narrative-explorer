"""数据导入适配层的单元测试（标准库 unittest）。

测试 src.ui.data_io 的 load_uploaded_csv 与 load_synthetic_demo。
所有测试数据均为合成构造，不涉及真实新闻。
"""

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import DataValidationError  # noqa: E402
from src.ui.data_io import load_synthetic_demo, load_uploaded_csv  # noqa: E402

# 合成的有效 CSV（包含必需列 title/content/source）
VALID_CSV = (
    "id,title,content,source\n"
    "1,标题一,正文一,来源甲\n"
    "2,标题二,正文二,来源乙\n"
)

# 缺少必需列 title 的 CSV
MISSING_COLUMN_CSV = "id,content,source\n1,正文一,来源甲\n"


class TestLoadUploadedCsv(unittest.TestCase):
    def test_normal_upload_returns_run_ingestion_structure(self):
        uploaded = io.BytesIO(VALID_CSV.encode("utf-8"))
        result = load_uploaded_csv(uploaded)
        # 返回结构与 run_ingestion 一致
        self.assertIn("raw", result)
        self.assertIn("clean", result)
        self.assertIn("raw_report", result)
        self.assertIn("clean_report", result)
        self.assertIn("report_path", result)
        # 未指定 report_path，不应写入报告
        self.assertIsNone(result["report_path"])
        self.assertEqual(len(result["raw"]), 2)
        self.assertEqual(len(result["clean"]), 2)

    def test_missing_required_column_raises(self):
        uploaded = io.BytesIO(MISSING_COLUMN_CSV.encode("utf-8"))
        with self.assertRaises(DataValidationError):
            load_uploaded_csv(uploaded)

    def test_empty_file_raises(self):
        # 空字节内容无法被 pandas 解析
        uploaded = io.BytesIO(b"")
        with self.assertRaises(Exception):
            load_uploaded_csv(uploaded)

    def test_temp_file_cleaned_up_on_success(self):
        created_paths: list[Path] = []
        real_named_temp = tempfile.NamedTemporaryFile

        def tracking_named_temp(*args, **kwargs):
            tmp = real_named_temp(*args, **kwargs)
            created_paths.append(Path(tmp.name))
            return tmp

        uploaded = io.BytesIO(VALID_CSV.encode("utf-8"))
        with patch("src.ui.data_io.tempfile.NamedTemporaryFile", tracking_named_temp):
            load_uploaded_csv(uploaded)

        self.assertEqual(len(created_paths), 1)
        self.assertFalse(created_paths[0].exists(), "成功路径下临时文件应被删除")

    def test_temp_file_cleaned_up_on_failure(self):
        created_paths: list[Path] = []
        real_named_temp = tempfile.NamedTemporaryFile

        def tracking_named_temp(*args, **kwargs):
            tmp = real_named_temp(*args, **kwargs)
            created_paths.append(Path(tmp.name))
            return tmp

        uploaded = io.BytesIO(MISSING_COLUMN_CSV.encode("utf-8"))
        with patch("src.ui.data_io.tempfile.NamedTemporaryFile", tracking_named_temp):
            with self.assertRaises(DataValidationError):
                load_uploaded_csv(uploaded)

        self.assertEqual(len(created_paths), 1)
        self.assertFalse(created_paths[0].exists(), "失败路径下临时文件也应被删除")

    def test_no_report_file_written(self):
        # 在临时目录中预先放一个报告文件，验证加载后未被覆盖
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "quality.md"
            report_path.write_text("原有报告内容", encoding="utf-8")
            original_mtime = report_path.stat().st_mtime

            uploaded = io.BytesIO(VALID_CSV.encode("utf-8"))
            # load_uploaded_csv 内部不指定 report_path，不会写入任何报告
            load_uploaded_csv(uploaded)

            self.assertTrue(report_path.is_file())
            self.assertEqual(
                report_path.read_text(encoding="utf-8"),
                "原有报告内容",
                "已有报告文件不应被覆盖",
            )
            self.assertEqual(report_path.stat().st_mtime, original_mtime)


class TestLoadSyntheticDemo(unittest.TestCase):
    def test_synthetic_demo_loads_successfully(self):
        result = load_synthetic_demo()
        self.assertIsNotNone(result)
        self.assertEqual(len(result["raw"]), 6)
        # 夹具中 1 行 source 为空，清洗后应剩 5 行
        self.assertEqual(len(result["clean"]), 5)
        self.assertIsNone(result["report_path"])
        self.assertEqual(result["clean_report"]["rows"], 5)
        self.assertEqual(result["clean_report"]["missing_required_columns"]["source"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
