"""数据质量报告模块的单元测试（标准库 unittest）。"""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_csv  # noqa: E402
from src.data.cleaning import clean_news_data  # noqa: E402
from src.data.quality import (  # noqa: E402
    build_quality_report,
    report_to_markdown,
    save_report,
)

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_sample_news.csv"


class TestQualityReport(unittest.TestCase):
    def setUp(self):
        self.raw = load_csv(FIXTURE)

    def test_raw_counts(self):
        report = build_quality_report(self.raw, name="raw")
        self.assertEqual(report["rows"], 5)
        self.assertEqual(report["duplicate_rows"], 1)
        self.assertEqual(report["missing_by_column"]["content"], 1)
        self.assertEqual(report["missing_by_column"]["title"], 1)
        self.assertEqual(report["missing_required_columns"]["content"], 1)

    def test_date_summary(self):
        report = build_quality_report(self.raw)
        ds = report["date_summary"]
        self.assertEqual(ds["missing"], 1)   # 第 5 行日期为空
        self.assertEqual(ds["valid"], 2)     # 第 1、4 行
        self.assertEqual(ds["invalid"], 2)   # 第 2、3 行日期非法
        self.assertEqual(ds["min"], "2024-05-01T00:00:00")

    def test_clean_counts(self):
        clean = clean_news_data(self.raw)
        report = build_quality_report(clean)
        self.assertEqual(report["rows"], 2)
        self.assertEqual(report["duplicate_rows"], 0)
        self.assertEqual(report["missing_by_column"]["content"], 0)

    def test_markdown_contains_real_numbers(self):
        report = build_quality_report(self.raw, name="sample")
        md = report_to_markdown(report)
        self.assertIn("数据集：sample", md)
        self.assertIn("行数：5", md)

    def test_save_report_creates_file(self):
        report = build_quality_report(self.raw, name="sample")
        with tempfile.TemporaryDirectory() as tmp:
            path = save_report(report, Path(tmp) / "sub" / "quality.md")
            self.assertTrue(path.is_file())
            self.assertIn("数据集：sample", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
