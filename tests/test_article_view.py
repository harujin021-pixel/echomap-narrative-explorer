"""新闻详情与相似新闻辅助模块的单元测试（标准库 unittest）。

测试 src.ui.article_view 的纯函数。所有数据均为合成构造或来自
tests/fixtures/ 下明确标记的合成夹具，不是真实新闻。
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.pipeline import run_ingestion  # noqa: E402
from src.ui.article_view import (  # noqa: E402
    article_text,
    field_or_placeholder,
    get_article_detail,
    get_similar_articles,
    should_reset_selection,
)
from src.ui.cluster_view import data_fingerprint  # noqa: E402

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_news_corpus.csv"


def _fixture_clean_df() -> pd.DataFrame:
    return run_ingestion(FIXTURE)["clean"]


class TestArticleDetail(unittest.TestCase):
    def setUp(self):
        self.df = _fixture_clean_df()

    def test_normal_detail_mapping(self):
        detail = get_article_detail(self.df, 0)
        row = self.df.iloc[0]
        self.assertEqual(detail["row_index"], 0)
        self.assertEqual(detail["title"], str(row["title"]))
        self.assertEqual(detail["source"], str(row["source"]))
        self.assertEqual(detail["content"], str(row["content"]))
        # 关键词结构
        self.assertListEqual(list(detail["keywords"].columns), ["rank", "keyword", "weight"])
        # 摘要句必须来自原文（标题+正文拼接文本）
        text = article_text(row)
        for sentence in detail["summary"]["summary"]:
            self.assertIn(sentence, text)

    def test_news_id_present(self):
        detail = get_article_detail(self.df, 0)
        self.assertEqual(str(detail["news_id"]), str(self.df.iloc[0]["id"]))

    def test_duplicate_titles_distinguished_by_row_index(self):
        dup = pd.DataFrame(
            [
                {"id": "a", "title": "相同标题", "content": "正文甲", "source": "甲报"},
                {"id": "b", "title": "相同标题", "content": "正文乙", "source": "乙报"},
            ]
        )
        d0 = get_article_detail(dup, 0)
        d1 = get_article_detail(dup, 1)
        self.assertEqual(d0["title"], d1["title"])  # 标题相同
        self.assertNotEqual(d0["row_index"], d1["row_index"])  # 行下标不同
        self.assertNotEqual(d0["content"], d1["content"])
        self.assertNotEqual(d0["news_id"], d1["news_id"])

    def test_missing_optional_fields(self):
        df = pd.DataFrame(
            [{"title": "只有标题", "content": "只有正文", "source": "某报"}]
        )
        detail = get_article_detail(df, 0)
        self.assertIsNone(detail["news_id"])
        self.assertEqual(detail["published_at"], "")
        self.assertEqual(
            field_or_placeholder(df.iloc[0], "published_at", "未知日期"), "未知日期"
        )
        self.assertEqual(
            field_or_placeholder(df.iloc[0], "author", "未知作者"), "未知作者"
        )

    def test_empty_content_and_title(self):
        df = pd.DataFrame([{"title": "", "content": "", "source": "某报"}])
        detail = get_article_detail(df, 0)
        self.assertTrue(detail["keywords"].empty)
        self.assertEqual(detail["summary"]["summary"], [])
        self.assertIn("空文本", detail["summary"]["note"])

    def test_short_single_sentence_text(self):
        df = pd.DataFrame([{"title": "", "content": "只有一句话。", "source": "某报"}])
        detail = get_article_detail(df, 0)
        self.assertEqual(len(detail["summary"]["summary"]), 1)
        self.assertIn("仅有一句", detail["summary"]["note"])

    def test_out_of_range_index(self):
        with self.assertRaises(IndexError):
            get_article_detail(self.df, len(self.df))
        with self.assertRaises(IndexError):
            get_article_detail(self.df, -1)


class TestSimilarArticles(unittest.TestCase):
    def setUp(self):
        self.df = _fixture_clean_df()

    def test_excludes_self(self):
        result = get_similar_articles(self.df, 0, top_n=5)
        query_id = str(self.df.iloc[0]["id"])
        for _, row in result.iterrows():
            self.assertNotEqual(int(row["row_index"]), 0)
            self.assertNotEqual(str(row["matched_id"]), query_id)

    def test_result_mapping_back_to_df(self):
        result = get_similar_articles(self.df, 0, top_n=5)
        self.assertGreater(len(result), 0)  # 夹具有交通双篇，必有正相似度
        for _, row in result.iterrows():
            pos = int(row["row_index"])
            self.assertGreaterEqual(pos, 0)
            self.assertEqual(str(self.df.iloc[pos]["title"]), row["title"])
            self.assertEqual(str(self.df.iloc[pos]["source"]), row["source"])
            self.assertEqual(row["published_at"], str(self.df.iloc[pos]["published_at"]))

    def test_top_n_not_exceed_available(self):
        result = get_similar_articles(self.df, 0, top_n=100)
        # 最多 len(df)-1 篇（排除自身），且只有正相似度
        self.assertLessEqual(len(result), len(self.df) - 1)
        self.assertTrue((result["similarity"] > 0).all())

    def test_no_positive_similarity_returns_empty(self):
        df = pd.DataFrame(
            [
                {"title": "苹果", "content": "苹果 香蕉 橘子", "source": "甲"},
                {"title": "量子", "content": "量子 物理 实验", "source": "乙"},
            ]
        )
        result = get_similar_articles(df, 0, top_n=5)
        self.assertTrue(result.empty)
        self.assertListEqual(list(result.columns), list(result.columns))  # 结构存在

    def test_single_row_corpus_empty(self):
        df = pd.DataFrame([{"title": "唯一", "content": "唯一一篇", "source": "甲"}])
        result = get_similar_articles(df, 0, top_n=5)
        self.assertTrue(result.empty)

    def test_empty_query_text_empty_result(self):
        df = pd.DataFrame(
            [
                {"title": "", "content": "", "source": "甲"},
                {"title": "正常", "content": "正常新闻内容", "source": "乙"},
            ]
        )
        result = get_similar_articles(df, 0, top_n=5)
        self.assertTrue(result.empty)

    def test_empty_dataframe(self):
        result = get_similar_articles(pd.DataFrame(), 0, top_n=5)
        self.assertTrue(result.empty)


class TestDatasetSwitching(unittest.TestCase):
    def test_should_reset_on_fingerprint_change(self):
        df1 = _fixture_clean_df()
        df2 = df1.iloc[:3].copy()
        fp1 = data_fingerprint(df1)
        fp2 = data_fingerprint(df2)
        self.assertTrue(should_reset_selection(fp1, fp2))
        self.assertFalse(should_reset_selection(fp1, data_fingerprint(df1.copy())))


if __name__ == "__main__":
    unittest.main(verbosity=2)
