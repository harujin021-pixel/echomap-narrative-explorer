"""数据可追溯性（Data Provenance）模块的单元测试（标准库 unittest）。

测试 src.ui.provenance 的纯函数。所有数据均为合成构造或来自
tests/fixtures/ 下明确标记的合成夹具，不是真实新闻。
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.pipeline import run_ingestion  # noqa: E402
from src.ui.provenance import (  # noqa: E402
    CLEANING_STEPS,
    PROVENANCE_KEYS,
    build_provenance,
    dataset_tag,
    date_range,
    format_imported_at,
)

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_news_corpus.csv"


class TestFormatImportedAt(unittest.TestCase):
    def test_formats_datetime(self):
        dt = datetime(2026, 10, 17, 19, 30, 5)
        self.assertEqual(format_imported_at(dt), "2026-10-17 19:30:05")

    def test_none_states_session_limitation(self):
        msg = format_imported_at(None)
        self.assertIn("未知", msg)
        self.assertIn("刷新", msg)  # 必须如实说明会话限制


class TestDateRange(unittest.TestCase):
    def test_valid_dates(self):
        df = pd.DataFrame({"published_at": ["2024-01-03", "2024-01-01", None]})
        self.assertEqual(date_range(df), ("2024-01-01", "2024-01-03"))

    def test_missing_column(self):
        self.assertEqual(date_range(pd.DataFrame({"title": ["a"]})), ("不可用", "不可用"))

    def test_all_invalid_dates(self):
        df = pd.DataFrame({"published_at": ["不是日期", ""]})
        self.assertEqual(date_range(df), ("不可用", "不可用"))

    def test_empty_dataframe(self):
        self.assertEqual(date_range(pd.DataFrame()), ("不可用", "不可用"))


class TestBuildProvenance(unittest.TestCase):
    def setUp(self):
        self.result = run_ingestion(FIXTURE)

    def test_normal_synthetic_dataset(self):
        prov = build_provenance(
            self.result, "合成测试数据", "synthetic_news_corpus.csv",
            datetime(2026, 10, 17, 10, 0, 0),
        )
        # 全部键齐全
        for key in PROVENANCE_KEYS:
            self.assertIn(key, prov)
        # 行数与实际结果一致（夹具 6 行原始、第 5 行 source 为空被清洗删除）
        self.assertEqual(prov["raw_rows"], 6)
        self.assertEqual(prov["clean_rows"], 5)
        # 日期范围来自实际数据
        self.assertEqual(prov["date_min"], "2024-05-01")
        self.assertEqual(prov["date_max"], "2024-05-06")
        # 指纹为 16 位十六进制
        self.assertEqual(len(prov["fingerprint"]), 16)
        int(prov["fingerprint"], 16)  # 可解析为十六进制
        # 导入时间已格式化
        self.assertEqual(prov["imported_at"], "2026-10-17 10:00:00")
        self.assertIn("合成测试数据", prov["source_label"])
        self.assertEqual(prov["cleaning_steps"], CLEANING_STEPS)

    def test_user_upload_label(self):
        prov = build_provenance(
            self.result, "用户上传数据", "my_real_news.csv", datetime.now()
        )
        self.assertIn("用户上传数据", prov["source_label"])
        self.assertIn("my_real_news.csv", prov["dataset_name"])
        self.assertNotIn("合成", prov["dataset_name"])

    def test_missing_filename_and_time_placeholders(self):
        prov = build_provenance(self.result, "用户上传数据", None, None)
        self.assertEqual(prov["dataset_name"], "未知文件")
        self.assertIn("未知", prov["imported_at"])

    def test_unknown_label_not_invented(self):
        prov = build_provenance(self.result, None, "x.csv", None)
        self.assertEqual(prov["source_label"], "未知来源")

    def test_dataset_switch_changes_fingerprint(self):
        full = build_provenance(self.result, "用户上传数据", "a.csv", None)
        subset_result = {"raw": self.result["raw"], "clean": self.result["clean"].iloc[:3]}
        sub = build_provenance(subset_result, "用户上传数据", "b.csv", None)
        self.assertNotEqual(full["fingerprint"], sub["fingerprint"])
        self.assertEqual(sub["clean_rows"], 3)

    def test_empty_dataframe_safe(self):
        result = {"raw": pd.DataFrame(), "clean": pd.DataFrame()}
        prov = build_provenance(result, "用户上传数据", "empty.csv", None)
        self.assertEqual(prov["raw_rows"], 0)
        self.assertEqual(prov["clean_rows"], 0)
        self.assertEqual(prov["fingerprint"], "无数据")
        self.assertEqual(prov["date_min"], "不可用")

    def test_malformed_result_safe(self):
        prov = build_provenance({}, None, None, None)
        self.assertEqual(prov["raw_rows"], "未知")
        self.assertEqual(prov["clean_rows"], 0)  # 非 DataFrame 归一为空 df
        self.assertIn("未知", prov["imported_at"])

    def test_missing_date_column(self):
        result = {
            "raw": pd.DataFrame([{"title": "t", "content": "c", "source": "s"}]),
            "clean": pd.DataFrame([{"title": "t", "content": "c", "source": "s"}]),
        }
        prov = build_provenance(result, "用户上传数据", "nodate.csv", None)
        self.assertEqual(prov["date_min"], "不可用")
        self.assertEqual(prov["date_max"], "不可用")


class TestDatasetTag(unittest.TestCase):
    def test_tag_format(self):
        prov = {"source_label": "合成测试数据", "fingerprint": "abcdef1234567890"}
        tag = dataset_tag(prov)
        self.assertIn("合成测试数据", tag)
        self.assertIn("abcdef1234567890", tag)  # 完整指纹出现在标识中

    def test_tag_missing_keys_safe(self):
        tag = dataset_tag({})
        self.assertIn("未知来源", tag)


if __name__ == "__main__":
    unittest.main(verbosity=2)
