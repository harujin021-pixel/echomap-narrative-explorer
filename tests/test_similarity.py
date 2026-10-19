"""文章相似度模块的单元测试（标准库 unittest）。

使用的 CSV 是**明确标记的合成测试数据**，不代表真实新闻语料。
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_csv  # noqa: E402
from src.analysis.similarity import (  # noqa: E402
    RESULT_COLUMNS,
    compute_similarity_matrix,
    find_similar_articles,
)

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_news_corpus.csv"


class TestSimilarity(unittest.TestCase):
    def setUp(self):
        self.df = load_csv(FIXTURE)

    def test_returns_results_and_excludes_self(self):
        res = find_similar_articles(self.df, query_index=0, top_n=3)
        self.assertEqual(list(res.columns), RESULT_COLUMNS)
        self.assertGreater(len(res), 0)
        query_id = res["query_id"].iloc[0]
        self.assertNotIn(query_id, res["matched_id"].tolist(), "不应把查询文章自身作为匹配项")

    def test_query_by_id(self):
        res = find_similar_articles(self.df, query_id="1", top_n=2)
        self.assertEqual(res["query_id"].iloc[0], "1")

    def test_similarity_sorted_descending(self):
        res = find_similar_articles(self.df, query_index=0, top_n=3)
        self.assertTrue((res["similarity"].diff().dropna() <= 0).all())

    def test_single_document_returns_empty(self):
        res = find_similar_articles(self.df.head(1), query_index=0, top_n=3)
        self.assertTrue(res.empty)

    def test_empty_texts_return_empty(self):
        df = pd.DataFrame(
            {"id": ["1", "2"], "title": ["", ""], "content": ["", ""], "source": ["a", "b"]}
        )
        res = find_similar_articles(df, query_index=0)
        self.assertTrue(res.empty)

    def test_query_id_not_found(self):
        with self.assertRaises(KeyError):
            find_similar_articles(self.df, query_id="不存在的id")

    def test_requires_query_argument(self):
        with self.assertRaises(ValueError):
            find_similar_articles(self.df)

    def test_top_n_is_clamped_by_corpus_size(self):
        res = find_similar_articles(self.df, query_index=0, top_n=999)
        self.assertLessEqual(len(res), len(self.df) - 1)

    def test_compute_similarity_matrix_symmetric(self):
        texts = ["地铁 交通 通勤", "交通 通勤 公交", ""]
        matrix, sims, processed = compute_similarity_matrix(texts)
        self.assertIsNotNone(sims)
        self.assertEqual(sims.shape, (3, 3))
        self.assertAlmostEqual(sims[0][1], sims[1][0], places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
