"""数据模板文件（data/templates/news_dataset_template.csv）的单元测试。

验证模板与现有导入/清洗接口兼容，且示例记录明确标记为合成数据。
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from src.data.cleaning import clean_news_data  # noqa: E402
from src.data.loader import OPTIONAL_COLUMNS, REQUIRED_COLUMNS, load_csv  # noqa: E402
from src.data.pipeline import run_ingestion  # noqa: E402

TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "news_dataset_template.csv"


class TestNewsDatasetTemplate(unittest.TestCase):
    def test_template_file_exists(self):
        self.assertTrue(TEMPLATE_PATH.is_file(), f"模板文件不存在: {TEMPLATE_PATH}")

    def test_template_columns_compatible_with_loader(self):
        """模板列名必须包含导入代码要求的全部必需列。"""
        df = load_csv(TEMPLATE_PATH)
        for col in REQUIRED_COLUMNS:
            self.assertIn(col, df.columns)
        # 演示可选字段写法：可选列也应出现（模板定位就是字段示例）
        for col in OPTIONAL_COLUMNS:
            self.assertIn(col, df.columns)

    def test_template_loads_and_cleans_without_loss(self):
        """3 条示例必需字段齐全，清洗后应全部保留（0 删除、0 重复）。"""
        df = load_csv(TEMPLATE_PATH)
        self.assertEqual(len(df), 3)
        cleaned = clean_news_data(df)
        self.assertEqual(len(cleaned), 3)
        # 日期解析成功（ISO 格式）
        self.assertEqual(cleaned["published_at"].notna().sum(), 3)
        self.assertEqual(cleaned["published_at"].min().strftime("%Y-%m-%d"), "2024-03-01")
        self.assertEqual(cleaned["published_at"].max().strftime("%Y-%m-%d"), "2024-03-03")

    def test_template_end_to_end_ingestion(self):
        """run_ingestion 全流程可处理模板（与第 8 节文档声明一致）。"""
        result = run_ingestion(TEMPLATE_PATH)
        self.assertEqual(len(result["raw"]), 3)
        self.assertEqual(len(result["clean"]), 3)
        self.assertEqual(result["raw_report"]["duplicate_rows"], 0)

    def test_template_records_marked_as_synthetic(self):
        """示例记录必须明确标记为合成数据，不伪装成真实新闻。"""
        df = load_csv(TEMPLATE_PATH)
        self.assertIn("data_source", df.columns)
        self.assertTrue((df["data_source"] == "synthetic_template").all())
        # 标题带「合成示例：」前缀，正文不含任何真实媒体报道暗示
        for title in df["title"]:
            self.assertIn("合成示例", str(title))


if __name__ == "__main__":
    unittest.main(verbosity=2)
