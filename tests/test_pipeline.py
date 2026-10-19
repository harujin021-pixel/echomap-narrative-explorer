"""导入->清洗->质量报告 完整流程的单元测试（标准库 unittest）。"""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.pipeline import run_ingestion  # noqa: E402

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_sample_news.csv"


class TestPipeline(unittest.TestCase):
    def test_run_ingestion_with_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "reports" / "quality.md"
            result = run_ingestion(
                FIXTURE, report_path=report_path, dataset_name="synthetic_sample"
            )
            self.assertEqual(len(result["raw"]), 5)
            self.assertEqual(len(result["clean"]), 2)
            self.assertTrue(report_path.is_file())
            self.assertIsNotNone(result["report_path"])
            text = report_path.read_text(encoding="utf-8")
            self.assertIn("清洗前", text)
            self.assertIn("清洗后", text)

    def test_run_ingestion_without_report(self):
        result = run_ingestion(FIXTURE)
        self.assertIsNone(result["report_path"])
        self.assertEqual(result["raw_report"]["rows"], 5)
        self.assertEqual(result["clean_report"]["rows"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
