"""主题聚类界面辅助模块的单元测试（标准库 unittest）。

测试 src.ui.cluster_view 的纯函数，覆盖正常多主题、空数据、
有效文本不足、聚类数超界、映射正确性及数据指纹。
所有数据均为合成构造。
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.cluster_view import (  # noqa: E402
    articles_in_cluster,
    cluster_summary,
    compute_clusters,
    data_fingerprint,
    unclustered_count,
    wordlists_fingerprint,
)


class TestWordlistsFingerprint(unittest.TestCase):
    def test_stable_and_formatted(self):
        fp1 = wordlists_fingerprint()
        fp2 = wordlists_fingerprint()
        self.assertEqual(fp1, fp2)
        self.assertRegex(fp1, r"^[0-9a-f]{12}$")


def _make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(
            df["published_at"], format="mixed", errors="coerce"
        )
    return df


MULTI_TOPIC_ROWS = [
    {"id": 1, "title": "地铁新线路开通", "content": "城市交通迎来新线路开通，有效缓解高峰时段拥堵。交通部门表示，此举将改善市区交通状况。", "source": "甲报", "published_at": "2024-05-01"},
    {"id": 2, "title": "公交专用道调整", "content": "交通部门公布公交线路优化方案，涉及高峰时段专用道调整，提升通勤效率。", "source": "乙报", "published_at": "2024-05-02"},
    {"id": 3, "title": "空气质量改善", "content": "监测数据显示城市空气质量持续改善，多项污染物浓度同比下降。", "source": "甲报", "published_at": "2024-05-03"},
    {"id": 4, "title": "河流水质治理", "content": "环保部门推进河流水质治理工程，预计明年水质将达标。", "source": "丙报", "published_at": "2024-05-04"},
    {"id": 5, "title": "高校人工智能实验室", "content": "某高校成立人工智能实验室，专注机器学习算法研究。", "source": "乙报", "published_at": "2024-05-05"},
    {"id": 6, "title": "开源社区大会", "content": "开源软件社区举办年度大会，探讨大模型协作与生态。", "source": "丁报", "published_at": "2024-05-06"},
]

FEW_ROWS = [
    {"id": 1, "title": "唯一有效新闻", "content": "新闻正文内容", "source": "甲报", "published_at": "2024-05-01"},
    {"id": 2, "title": "", "content": "", "source": "乙报", "published_at": "2024-05-02"},
]

EMPTY_ROWS = [
    {"id": 1, "title": "", "content": "", "source": "", "published_at": ""},
]


class TestDataFingerprint(unittest.TestCase):
    def test_same_df_same_fingerprint(self):
        df = _make_df(MULTI_TOPIC_ROWS)
        self.assertEqual(data_fingerprint(df), data_fingerprint(df))

    def test_different_df_different_fingerprint(self):
        fp1 = data_fingerprint(_make_df(MULTI_TOPIC_ROWS))
        fp2 = data_fingerprint(_make_df(MULTI_TOPIC_ROWS[:3]))
        self.assertNotEqual(fp1, fp2)

    def test_content_change_changes_fingerprint(self):
        df1 = _make_df(MULTI_TOPIC_ROWS)
        rows = [dict(r, title=r["title"] + "x") for r in MULTI_TOPIC_ROWS]
        df2 = _make_df(rows)
        self.assertNotEqual(data_fingerprint(df1), data_fingerprint(df2))


class TestComputeClustersNormal(unittest.TestCase):
    def test_multi_topic_structure(self):
        result = compute_clusters(_make_df(MULTI_TOPIC_ROWS), n_clusters=3)
        self.assertIn("labels", result)
        self.assertIn("cluster_keywords", result)
        self.assertIn("n_clusters", result)
        self.assertIn("clustered_documents", result)
        self.assertIn("note", result)

    def test_summary_counts_and_keywords(self):
        result = compute_clusters(_make_df(MULTI_TOPIC_ROWS), n_clusters=3)
        summary = cluster_summary(result)
        total = result["clustered_documents"]
        self.assertGreater(len(summary), 0)
        count_sum = sum(s["count"] for s in summary)
        self.assertEqual(count_sum, total)
        for s in summary:
            self.assertGreaterEqual(s["ratio"], 0)
            self.assertLessEqual(s["ratio"], 1)
            self.assertIsInstance(s["keywords"], list)

    def test_articles_in_cluster_mapping(self):
        result = compute_clusters(_make_df(MULTI_TOPIC_ROWS), n_clusters=3)
        summary = cluster_summary(result)
        if not summary:
            self.skipTest("聚类结果为空，跳过映射测试")
        cluster_id = summary[0]["cluster"]
        articles = articles_in_cluster(result, cluster_id)
        self.assertGreater(len(articles), 0)
        # 标题确实来自原始数据
        all_titles = set(r["title"] for r in MULTI_TOPIC_ROWS)
        for title in articles["title"]:
            self.assertIn(title, all_titles)


class TestBoundaryConditions(unittest.TestCase):
    def test_empty_dataframe(self):
        result = compute_clusters(_make_df(EMPTY_ROWS), n_clusters=3)
        self.assertEqual(result["n_clusters"], 0)
        self.assertEqual(result["clustered_documents"], 0)
        self.assertTrue(cluster_summary(result) == [])

    def test_few_valid_documents(self):
        result = compute_clusters(_make_df(FEW_ROWS), n_clusters=3)
        # 1 篇有效，< 2，统一标记为 0
        self.assertEqual(result["n_clusters"], 1)
        self.assertIn("有效文本不足", result["note"])
        summary = cluster_summary(result)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["count"], 1)

    def test_n_clusters_clamped(self):
        # 6 篇但请求 10 个聚类
        result = compute_clusters(_make_df(MULTI_TOPIC_ROWS), n_clusters=10)
        self.assertLess(result["n_clusters"], 10)
        self.assertIn("超过有效文档数", result["note"])


class TestUnclustered(unittest.TestCase):
    def test_unclustered_with_empty_text(self):
        result = compute_clusters(_make_df(FEW_ROWS), n_clusters=3)
        # FEW_ROWS 第二行 content 为空，预处理后为空文本，cluster = -1
        self.assertEqual(unclustered_count(result), 1)

    def test_unclustered_all_valid(self):
        result = compute_clusters(_make_df(MULTI_TOPIC_ROWS), n_clusters=3)
        # 夹具全部有效，未聚类数应为 0
        self.assertEqual(unclustered_count(result), 0)


class TestSwitchingDataset(unittest.TestCase):
    def test_fingerprint_changes_prevent_stale_result(self):
        fp1 = data_fingerprint(_make_df(MULTI_TOPIC_ROWS))
        fp2 = data_fingerprint(_make_df(MULTI_TOPIC_ROWS[:3]))
        # 数据集切换后指纹不同 → 界面缓存键不会命中旧结果
        self.assertNotEqual(fp1, fp2)
        # 相同数据集指纹一致 → 可复用已缓存结果
        self.assertEqual(fp1, data_fingerprint(_make_df(MULTI_TOPIC_ROWS)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
