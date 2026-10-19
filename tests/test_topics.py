"""src.ai.topics 选题推荐的单元测试（阶段 5.1）。

覆盖：正常多主题场景、空数据、缺失日期、无法解析日期、全部同日、
小样本、top_n 截断、排序单调性、关联新闻可溯源、关键词权重计算、
以及类型校验。全部使用本地构造的合成数据，不依赖网络与模型。
"""

import unittest
from datetime import datetime

import pandas as pd

from src.ai.topics import (
    MAX_ARTICLES_PER_TOPIC,
    build_topic_recommendations,
    keyword_mean_weights,
)
from src.analysis.clustering import cluster_articles
from src.analysis.keywords import keywords_for_corpus
from src.analysis.vectorize import combine_text_fields


def make_df() -> pd.DataFrame:
    """构造两个话题方向的合成新闻 DataFrame（日期有先后差异）。"""
    rows = []
    for i in range(3):
        rows.append(
            {
                "id": f"a{i}",
                "title": f"校园活动报道{i}",
                "content": "校园 图书馆 阅览室 氛围 校园 阅览室",
                "source": "示例甲",
                "published_at": datetime(2026, 1, i + 1),
            }
        )
    for i in range(3):
        rows.append(
            {
                "id": f"b{i}",
                "title": f"科技新品发布{i}",
                "content": "科技 公司 发布 智能 设备 科技 公司",
                "source": "示例乙",
                "published_at": datetime(2026, 1, 10),
            }
        )
    return pd.DataFrame(rows)


def make_cluster_result(df: pd.DataFrame, n_clusters: int = 2) -> dict:
    return cluster_articles(df, n_clusters=n_clusters)


def make_corpus_keywords(df: pd.DataFrame) -> pd.DataFrame:
    return keywords_for_corpus(combine_text_fields(df, ("title", "content")), top_k=10)


class TestKeywordMeanWeights(unittest.TestCase):
    def test_mean_over_positive_weights(self):
        df = pd.DataFrame(
            {
                "doc_id": [0, 0, 1, 1],
                "rank": [1, 2, 1, 2],
                "keyword": ["科技", "科技", "校园", "校园"],
                "weight": [0.4, 0.2, 0.6, 0.0],
            }
        )
        means = keyword_mean_weights(df)
        # 权重为 0 的行不参与平均（与 TF-IDF 语义一致）
        self.assertAlmostEqual(means["科技"], 0.3)
        self.assertAlmostEqual(means["校园"], 0.6)

    def test_empty_and_none(self):
        self.assertEqual(keyword_mean_weights(None), {})
        self.assertEqual(keyword_mean_weights(pd.DataFrame()), {})
        bad = pd.DataFrame({"a": [1]})
        self.assertEqual(keyword_mean_weights(bad), {})


class TestBuildTopicRecommendations(unittest.TestCase):
    def setUp(self):
        self.df = make_df()
        self.cluster_result = make_cluster_result(self.df)
        self.corpus_kw = make_corpus_keywords(self.df)

    def test_type_validation(self):
        with self.assertRaises(TypeError):
            build_topic_recommendations("not a df", self.cluster_result)
        with self.assertRaises(TypeError):
            build_topic_recommendations(self.df, "not a dict")
        with self.assertRaises(ValueError):
            build_topic_recommendations(self.df, self.cluster_result, top_n=0)

    def test_basic_structure(self):
        rec = build_topic_recommendations(
            self.df, self.cluster_result, self.corpus_kw, top_n=5
        )
        self.assertIn("recommendations", rec)
        self.assertTrue(rec["recommendations"])
        self.assertLessEqual(len(rec["recommendations"]), 5)
        self.assertEqual(rec["clustered_documents"], 6)
        for item in rec["recommendations"]:
            self.assertIsInstance(item["keywords"], list)
            self.assertTrue(item["keywords"])
            self.assertGreaterEqual(item["count"], 1)
            self.assertTrue(0.0 <= item["factor_share"] <= 1.0)
            self.assertTrue(0.0 <= item["score"] <= 1.0)
            self.assertIsInstance(item["articles"], list)

    def test_scores_sorted_descending(self):
        rec = build_topic_recommendations(
            self.df, self.cluster_result, self.corpus_kw, top_n=5
        )
        scores = [item["score"] for item in rec["recommendations"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_top_n_limit(self):
        rec = build_topic_recommendations(
            self.df, self.cluster_result, self.corpus_kw, top_n=1
        )
        self.assertEqual(len(rec["recommendations"]), 1)

    def test_articles_traceable(self):
        rec = build_topic_recommendations(
            self.df, self.cluster_result, self.corpus_kw, top_n=5
        )
        for item in rec["recommendations"]:
            self.assertLessEqual(len(item["articles"]), MAX_ARTICLES_PER_TOPIC)
            for article in item["articles"]:
                row_index = article["row_index"]
                self.assertTrue(0 <= row_index < len(self.df))
                self.assertEqual(
                    article["title"], str(self.df.iloc[row_index]["title"])
                )
                if article["date"] is not None:
                    self.assertRegex(article["date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_recency_factor_prefers_latest_topic(self):
        rec = build_topic_recommendations(
            self.df, self.cluster_result, self.corpus_kw, top_n=5
        )
        by_kw = {}
        for item in rec["recommendations"]:
            for kw in item["keywords"]:
                by_kw.setdefault(kw, item)
        campus = by_kw.get("校园")
        tech = by_kw.get("科技")
        self.assertIsNotNone(campus)
        self.assertIsNotNone(tech)
        self.assertIsNotNone(campus["factor_recency"])
        self.assertIsNotNone(tech["factor_recency"])
        # "科技"主题包含全数据集最晚日期（2026-01-10），新近度应为 1.0
        self.assertAlmostEqual(tech["factor_recency"], 1.0)
        self.assertLess(campus["factor_recency"], tech["factor_recency"])

    def test_missing_date_column(self):
        df = self.df.drop(columns=["published_at"])
        rec = build_topic_recommendations(
            df, make_cluster_result(df), make_corpus_keywords(df), top_n=5
        )
        self.assertTrue(rec["no_dates"])
        for item in rec["recommendations"]:
            self.assertIsNone(item["factor_recency"])

    def test_unparseable_dates(self):
        df = self.df.copy()
        df["published_at"] = "not-a-date"
        rec = build_topic_recommendations(
            df, make_cluster_result(df), make_corpus_keywords(df), top_n=5
        )
        self.assertTrue(rec["no_dates"])

    def test_all_same_date(self):
        df = self.df.copy()
        df["published_at"] = datetime(2026, 1, 5)
        rec = build_topic_recommendations(
            df, make_cluster_result(df), make_corpus_keywords(df), top_n=5
        )
        self.assertFalse(rec["no_dates"])
        for item in rec["recommendations"]:
            # 全数据集同一天：各主题同等新近，因子为 1.0 而不是不可用
            self.assertAlmostEqual(item["factor_recency"], 1.0)

    def test_keyword_factor_unavailable_without_corpus_keywords(self):
        rec = build_topic_recommendations(self.df, self.cluster_result, None, top_n=5)
        self.assertFalse(rec["kw_factor_available"])
        for item in rec["recommendations"]:
            self.assertIsNone(item["factor_kw"])

    def test_empty_dataframe(self):
        empty = pd.DataFrame(columns=["id", "title", "content", "source", "published_at"])
        rec = build_topic_recommendations(empty, make_cluster_result(empty), None)
        self.assertEqual(rec["recommendations"], [])
        self.assertEqual(rec["clustered_documents"], 0)

    def test_small_sample_flag(self):
        small = self.df.head(2).copy()
        rec = build_topic_recommendations(
            small, make_cluster_result(small, n_clusters=1), make_corpus_keywords(small)
        )
        self.assertTrue(rec["small_sample"])

    def test_single_cluster(self):
        rec = build_topic_recommendations(
            self.df, make_cluster_result(self.df, n_clusters=1), self.corpus_kw, top_n=5
        )
        self.assertEqual(len(rec["recommendations"]), 1)


if __name__ == "__main__":
    unittest.main()
