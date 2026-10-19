"""i18n 双语界面文案模块测试（标准库 unittest）。

覆盖：
    - en/zh 键集合一致性与占位符一致性
    - t() 取值、格式化与回退顺序
    - app 辅助函数与 provenance 模块的英文输出（lang="en"）
    - 默认中文行为不回归（与 test_app_helpers.py / test_provenance.py 互补）

所有数据均为合成构造或来自 tests/fixtures/ 下明确标记的合成夹具，不是真实新闻。
"""

import string
import sys
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.app import _friendly_error, sidebar_data_status  # noqa: E402
from src.data.loader import DataValidationError  # noqa: E402
from src.data.pipeline import run_ingestion  # noqa: E402
from src.ui.i18n import DEFAULT_LANG, STRINGS, SUPPORTED_LANGS, t  # noqa: E402
from src.ui.provenance import (  # noqa: E402
    build_provenance,
    dataset_tag,
    date_range,
    format_imported_at,
)

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_news_corpus.csv"


def _placeholders(text: str) -> set[str]:
    """提取格式串中的 {placeholder} 名称集合。"""
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}


class TestKeyParity(unittest.TestCase):
    def test_supported_langs(self):
        self.assertEqual(set(SUPPORTED_LANGS), {"en", "zh"})

    def test_default_lang_is_en(self):
        # 英文授课项目评审场景：默认语言必须为 English
        self.assertEqual(DEFAULT_LANG, "en")

    def test_en_zh_key_sets_identical(self):
        en_keys = set(STRINGS["en"])
        zh_keys = set(STRINGS["zh"])
        self.assertEqual(
            en_keys,
            zh_keys,
            msg=f"only in en: {sorted(en_keys - zh_keys)}; "
            f"only in zh: {sorted(zh_keys - en_keys)}",
        )

    def test_no_empty_strings(self):
        for lang in SUPPORTED_LANGS:
            for key, value in STRINGS[lang].items():
                self.assertTrue(value.strip(), msg=f"{lang}:{key} is empty")

    def test_placeholder_sets_match_across_langs(self):
        for key in STRINGS["en"]:
            en_fields = _placeholders(STRINGS["en"][key])
            zh_fields = _placeholders(STRINGS["zh"][key])
            self.assertEqual(en_fields, zh_fields, msg=f"placeholder mismatch: {key}")


class TestT(unittest.TestCase):
    def test_en_value(self):
        self.assertEqual(t("sb_import_btn", "en"), "Import")

    def test_zh_value(self):
        self.assertEqual(t("sb_import_btn", "zh"), "开始导入")

    def test_default_uses_default_lang(self):
        self.assertEqual(t("sb_import_btn"), STRINGS[DEFAULT_LANG]["sb_import_btn"])

    def test_unknown_lang_falls_back_to_default(self):
        self.assertEqual(
            t("sb_import_btn", "fr"), STRINGS[DEFAULT_LANG]["sb_import_btn"]
        )

    def test_unknown_key_returns_key(self):
        self.assertEqual(t("no_such_key", "en"), "no_such_key")

    def test_format_kwargs_en(self):
        self.assertEqual(
            t("status_user", "en", name="a.csv"),
            "Current data: user-uploaded data (a.csv)",
        )

    def test_format_kwargs_zh(self):
        self.assertEqual(
            t("status_user", "zh", name="a.csv"), "当前数据：用户上传数据（a.csv）"
        )


class TestAppHelpersBilingual(unittest.TestCase):
    """app.py 辅助函数：lang="en" 输出英文；默认中文行为不回归。"""

    def test_sidebar_status_en_synthetic(self):
        msg = sidebar_data_status("合成测试数据", "synthetic_news_corpus.csv", lang="en")
        self.assertIn("synthetic test data", msg)
        self.assertIn("not real news", msg)

    def test_sidebar_status_en_user_upload(self):
        msg = sidebar_data_status("用户上传数据", "my_news.csv", lang="en")
        self.assertIn("user-uploaded data", msg)
        self.assertIn("my_news.csv", msg)
        self.assertNotIn("synthetic", msg)  # 用户数据不得被标为合成

    def test_sidebar_status_en_none(self):
        self.assertIn("no data imported", sidebar_data_status(None, None, lang="en"))

    def test_sidebar_status_default_zh_unchanged(self):
        msg = sidebar_data_status("合成测试数据", "x.csv")
        self.assertIn("合成测试数据", msg)
        self.assertIn("非真实新闻", msg)

    def test_friendly_error_en_missing_cols(self):
        exc = DataValidationError("CSV 文件缺少必需列 ['title']")
        msg = _friendly_error(exc, lang="en")
        self.assertIn("missing required columns", msg)

    def test_friendly_error_en_encoding(self):
        exc = DataValidationError("无法用候选编码解码文件")
        self.assertIn("encoding", _friendly_error(exc, lang="en"))

    def test_friendly_error_en_generic(self):
        msg = _friendly_error(RuntimeError("boom"), lang="en")
        self.assertIn("Import failed", msg)
        self.assertIn("boom", msg)

    def test_friendly_error_default_zh_unchanged(self):
        exc = DataValidationError("CSV 文件缺少必需列 ['title']")
        self.assertIn("缺少必需列", _friendly_error(exc))


class TestProvenanceBilingual(unittest.TestCase):
    """provenance 模块：lang="en" 英文占位；默认中文行为不回归。"""

    def setUp(self):
        self.result = run_ingestion(FIXTURE)

    def test_format_imported_at_none_en(self):
        msg = format_imported_at(None, lang="en")
        self.assertIn("unknown", msg)
        self.assertIn("session", msg)  # 必须如实说明会话限制

    def test_format_imported_at_default_zh_unchanged(self):
        msg = format_imported_at(None)
        self.assertIn("未知", msg)
        self.assertIn("刷新", msg)

    def test_date_range_unavailable_en(self):
        df = pd.DataFrame({"title": ["a"]})
        self.assertEqual(date_range(df, lang="en"), ("unavailable", "unavailable"))

    def test_date_range_default_zh_unchanged(self):
        df = pd.DataFrame({"title": ["a"]})
        self.assertEqual(date_range(df), ("不可用", "不可用"))

    def test_build_provenance_en_normal(self):
        prov = build_provenance(
            self.result,
            "synthetic test data",
            "synthetic_news_corpus.csv",
            datetime(2026, 10, 17, 10, 0, 0),
            lang="en",
        )
        self.assertEqual(prov["raw_rows"], 6)
        self.assertEqual(prov["clean_rows"], 5)
        self.assertEqual(prov["date_min"], "2024-05-01")
        self.assertEqual(prov["date_max"], "2024-05-06")
        self.assertIn("whitespace", prov["cleaning_steps"])  # 英文清洗步骤

    def test_build_provenance_en_placeholders(self):
        prov = build_provenance(
            {"raw": pd.DataFrame(), "clean": pd.DataFrame()}, None, None, None, lang="en"
        )
        self.assertEqual(prov["source_label"], "unknown source")
        self.assertEqual(prov["dataset_name"], "unknown file")
        self.assertEqual(prov["fingerprint"], "no data")
        self.assertEqual(prov["date_min"], "unavailable")
        self.assertIn("unknown", prov["imported_at"])

    def test_build_provenance_default_zh_unchanged(self):
        prov = build_provenance(self.result, "合成测试数据", "x.csv", None)
        self.assertIn("未知", prov["imported_at"])
        self.assertIn("合成测试数据", prov["source_label"])

    def test_dataset_tag_en(self):
        prov = {"source_label": "synthetic test data", "fingerprint": "abcdef1234567890"}
        tag = dataset_tag(prov, lang="en")
        self.assertIn("Dataset:", tag)
        self.assertIn("fingerprint", tag)
        self.assertIn("abcdef1234567890", tag)  # 完整指纹出现在标识中

    def test_dataset_tag_default_zh_unchanged(self):
        tag = dataset_tag({"source_label": "合成测试数据", "fingerprint": "abc"})
        self.assertIn("数据集", tag)
        self.assertIn("指纹", tag)


if __name__ == "__main__":
    unittest.main(verbosity=2)
