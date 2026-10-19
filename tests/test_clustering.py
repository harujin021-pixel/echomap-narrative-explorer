"""主题聚类模块的单元测试（标准库 unittest）。

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
from src.analysis.clustering import RESULT_COLUMNS, cluster_articles  # noqa: E402

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_news_corpus.csv"


class TestClustering(unittest.TestCase):
    def setUp(self):
        self.df = load_csv(FIXTURE)

    def test_basic_clustering(self):
        result = cluster_articles(self.df, n_clusters=2, random_state=42)
        labels = result["labels"]
        self.assertEqual(list(labels.columns), RESULT_COLUMNS)
        self.assertEqual(len(labels), len(self.df))
        self.assertEqual(result["n_clusters"], 2)
        self.assertEqual(labels["cluster"].nunique(), 2)
        self.assertEqual(labels["news_id"].tolist(), self.df["id"].tolist())
        self.assertTrue(all(isinstance(v, list) for v in result["cluster_keywords"].values()))

    def test_n_clusters_too_large_is_clamped(self):
        result = cluster_articles(self.df, n_clusters=99, random_state=42)
        self.assertEqual(result["n_clusters"], len(self.df))
        self.assertIn("超过有效文档数", result["note"])

    def test_reproducibility_same_seed(self):
        first = cluster_articles(self.df, n_clusters=3, random_state=7)["labels"]["cluster"].tolist()
        second = cluster_articles(self.df, n_clusters=3, random_state=7)["labels"]["cluster"].tolist()
        self.assertEqual(first, second)

    def test_single_document(self):
        one = self.df.head(1)
        result = cluster_articles(one, n_clusters=3)
        self.assertEqual(result["n_clusters"], 1)
        self.assertEqual(result["labels"]["cluster"].tolist(), [0])
        self.assertTrue(result["note"])

    def test_empty_texts(self):
        df = pd.DataFrame(
            {"title": ["", "   "], "content": ["", ""], "source": ["a", "b"]}
        )
        result = cluster_articles(df, n_clusters=2)
        self.assertEqual(result["n_clusters"], 0)
        self.assertEqual(result["clustered_documents"], 0)
        self.assertTrue(result["note"])
        self.assertTrue((result["labels"]["cluster"] == -1).all())

    def test_invalid_n_clusters(self):
        with self.assertRaises(ValueError):
            cluster_articles(self.df, n_clusters=0)

    def test_small_sample_warning(self):
        result = cluster_articles(self.df.head(4), n_clusters=2, random_state=42)
        self.assertIn("较少", result["note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
