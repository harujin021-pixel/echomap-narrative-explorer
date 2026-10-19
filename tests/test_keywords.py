"""关键词提取模块的单元测试（标准库 unittest）。"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.keywords import (  # noqa: E402
    CORPUS_COLUMNS,
    DOCUMENT_COLUMNS,
    extract_keywords,
    keywords_for_corpus,
    keywords_for_document,
)

TEXT = "地铁新线路今日开通，早高峰通勤时间缩短。交通部门表示将增加班次并优化换乘。"


class TestKeywords(unittest.TestCase):
    def test_document_keywords_structure(self):
        df = keywords_for_document(TEXT, top_k=5)
        self.assertEqual(list(df.columns), DOCUMENT_COLUMNS)
        self.assertGreater(len(df), 0)
        self.assertLessEqual(len(df), 5)
        # 权重按降序
        self.assertTrue((df["weight"].diff().dropna() <= 0).all())

    def test_document_empty_and_missing(self):
        for value in ["", "   ", None, 12]:
            df = keywords_for_document(value, top_k=5)
            self.assertTrue(df.empty, f"输入 {value!r} 应返回空结果")

    def test_document_all_stopwords_filtered(self):
        df = keywords_for_document("的 了 和 是 ！？", top_k=5)
        self.assertTrue(df.empty)

    def test_keywords_no_single_char(self):
        # 关键词结果中不得出现单字（单个汉字/字母/数字）
        df = keywords_for_document(TEXT, top_k=20)
        if not df.empty:
            self.assertTrue(
                (df["keyword"].str.len() >= 2).all(),
                f"关键词中出现单字: {df['keyword'].tolist()}",
            )

    def test_keywords_no_sensitive_words(self):
        # 敏感词不得出现在关键词结果中（过滤发生在预处理层）
        df = keywords_for_document("废物 回收 地铁新线路今日开通。", top_k=10)
        if not df.empty:
            self.assertNotIn("废物", df["keyword"].tolist())

    def test_keywords_no_pure_numbers(self):
        # 关键词结果中不得出现纯数字（日期、编号类噪声）
        df = keywords_for_document(
            "地铁新线路今日开通，首日客流约 2026 万人次，10 月 17 日数据。", top_k=20
        )
        if not df.empty:
            self.assertTrue(
                df["keyword"].str.contains(r"[A-Za-z\u4e00-\u9fff]").all(),
                f"关键词中出现纯数字: {df['keyword'].tolist()}",
            )

    def test_corpus_keywords_structure(self):
        texts = ["地铁开通 交通 通勤", "空气质量 环保 监测", "机器学习 算法 实验室"]
        df = keywords_for_corpus(texts, top_k=3)
        self.assertEqual(list(df.columns), CORPUS_COLUMNS)
        self.assertEqual(set(df["doc_id"]), {0, 1, 2})

    def test_corpus_single_document(self):
        df = keywords_for_corpus([TEXT], top_k=3)
        self.assertEqual(set(df["doc_id"]), {0})

    def test_corpus_all_empty(self):
        df = keywords_for_corpus(["", "   "], top_k=3)
        self.assertTrue(df.empty)

    def test_extract_keywords_dispatch(self):
        single = extract_keywords(TEXT, top_k=3)
        self.assertEqual(list(single.columns), DOCUMENT_COLUMNS)
        corpus = extract_keywords([TEXT, TEXT], top_k=3)
        self.assertIn("doc_id", corpus.columns)

    def test_top_k_configuration(self):
        df = keywords_for_document(TEXT, top_k=2)
        self.assertLessEqual(len(df), 2)

    def test_invalid_top_k(self):
        with self.assertRaises(ValueError):
            keywords_for_document(TEXT, top_k=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
