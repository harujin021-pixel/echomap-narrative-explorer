"""多来源对比模块（src.analysis.source_compare）的单元测试（标准库 unittest）。

所有测试数据均为合成构造（标题/正文/来源均为编造文本），不是真实新闻。
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from src.analysis.source_compare import (  # noqa: E402
    NO_CLUSTER_LABEL,
    small_sources,
    source_cluster_crosstab,
    source_keyword_compare,
)


def make_df(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    """rows: (title, content, source)，构造带默认索引的合成 DataFrame。"""
    return pd.DataFrame(
        [{"title": t, "content": c, "source": s} for t, c, s in rows]
    )


TRANSPORT = [
    ("合成：地铁三号线开通", "地铁三号线今日正式开通，市民出行更加便捷。", "甲媒体"),
    ("合成：公交专用道调整", "市区公交专用道方案公布，通勤时间有望缩短。", "甲媒体"),
]
ENV = [
    ("合成：河流水质改善", "监测显示河流水质持续改善，治理措施初见成效。", "乙媒体"),
    ("合成：空气质量提升", "本月空气质量优良天数增加，蓝天保卫战推进顺利。", "乙媒体"),
    ("合成：垃圾分类推广", "多个社区开始试行垃圾分类，回收利用率提升。", "乙媒体"),
]
TECH = [("合成：人工智能实验室成立", "本地高校成立人工智能实验室，聚焦应用研究。", "丙媒体")]


class TestSourceKeywordCompare(unittest.TestCase):
    def test_multiple_sources_basic(self):
        df = make_df(TRANSPORT + ENV + TECH)
        out = source_keyword_compare(df, top_k=3, min_articles=1)
        self.assertEqual(out["total_sources"], 3)
        self.assertEqual(out["sources_shown"], 3)  # 2/3/1 篇均 >= min_articles=1
        self.assertEqual(out["excluded_empty_source"], 0)
        # 每个来源都有非空关键词
        for item in out["per_source"]:
            self.assertFalse(item["keywords"].empty)
            self.assertIn("row_index", item["keywords"].columns)
            self.assertTrue((item["keywords"]["weight"] > 0).all())

    def test_row_index_maps_back_to_source_rows(self):
        """关键词的 row_index 必须能映射回该来源在 clean_df 中的实际行。"""
        df = make_df(TRANSPORT + ENV)
        out = source_keyword_compare(df, top_k=3)
        for item in out["per_source"]:
            expected = {i for i in df.index if df.loc[i, "source"] == item["source"]}
            for ri in item["keywords"]["row_index"]:
                self.assertIn(int(ri), expected)
                # 映射回原文可核对：该行的 source 与分组一致
                self.assertEqual(df.loc[int(ri), "source"], item["source"])

    def test_single_source(self):
        df = make_df(TRANSPORT)
        out = source_keyword_compare(df, top_k=3)
        self.assertEqual(out["total_sources"], 1)
        self.assertEqual(out["sources_shown"], 1)
        self.assertIn("仅", out["note"] or "")  # 单来源提示

    def test_empty_source_rows_excluded(self):
        df = make_df(TRANSPORT)
        df.loc[len(df)] = ["合成：无来源标题", "合成：无来源正文", ""]
        out = source_keyword_compare(df, top_k=3)
        self.assertEqual(out["excluded_empty_source"], 1)
        self.assertFalse(any("无来源" in item["source"] for item in out["per_source"]))

    def test_empty_dataframe(self):
        out = source_keyword_compare(pd.DataFrame(), top_k=3)
        self.assertEqual(out["per_source"], [])
        self.assertIn("没有", out["note"])

    def test_small_source_skipped(self):
        df = make_df(TRANSPORT + TECH)  # TECH 来源仅 1 篇
        out = source_keyword_compare(df, top_k=3, min_articles=2)
        self.assertEqual(out["sources_shown"], 1)  # 仅 2 篇的来源
        skipped_names = [s for s, _ in out["skipped_sources"]]
        self.assertEqual(skipped_names, ["丙媒体"])
        self.assertIn("样本过小", out["note"])

    def test_max_sources_limits_display(self):
        rows = TRANSPORT + ENV + TECH + [
            ("合成：体育赛事开赛", "全市运动会今日开幕，多个项目展开角逐。", "丁媒体"),
        ]
        df = make_df(rows)  # 来源：2/3/1/1 篇
        out = source_keyword_compare(df, top_k=2, min_articles=1, max_sources=2)
        self.assertEqual(out["sources_shown"], 2)
        # 展示的是文章数最多的前两个来源
        counts = [item["article_count"] for item in out["per_source"]]
        self.assertEqual(counts, sorted(counts, reverse=True))
        self.assertIn("未展示", out["note"])

    def test_dataset_switch_changes_result(self):
        df_a = make_df(TRANSPORT + ENV)
        df_b = make_df(TRANSPORT)
        out_a = source_keyword_compare(df_a, top_k=3)
        out_b = source_keyword_compare(df_b, top_k=3)
        self.assertNotEqual(out_a["total_sources"], out_b["total_sources"])
        self.assertEqual(len(out_a["per_source"]), 2)
        self.assertEqual(len(out_b["per_source"]), 1)


class TestSourceClusterCrosstab(unittest.TestCase):
    def _labels(self, rows: list[tuple[str, int]]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "news_id": str(i + 1),
                    "row_index": i,
                    "title": f"标题{i}",
                    "source": s,
                    "published_at": pd.NaT,
                    "cluster": c,
                }
                for i, (s, c) in enumerate(rows)
            ]
        )

    def test_crosstab_counts_and_totals(self):
        df = make_df(TRANSPORT + ENV)
        labels = self._labels([("甲媒体", 0), ("甲媒体", 1), ("乙媒体", 0), ("乙媒体", 0), ("乙媒体", 1)])
        out = source_cluster_crosstab(df, labels)
        self.assertEqual(out["counts"].sum().sum(), 5)
        self.assertEqual(out["total_rows"], 5)
        self.assertEqual(int(out["counts"].loc["甲媒体"].sum()), 2)
        self.assertEqual(int(out["counts"].loc["乙媒体"].sum()), 3)

    def test_row_pct_denominator_is_source_total(self):
        """行占比分母 = 该来源全部文章数（含未参与聚类的行）。"""
        df = make_df(TRANSPORT + ENV)
        labels = self._labels(
            [("甲媒体", 0), ("甲媒体", 1), ("甲媒体", -1), ("乙媒体", 0)]
        )
        out = source_cluster_crosstab(df, labels)
        # 甲媒体 3 篇：簇0=1/3、簇1=1/3、未参与=1/3
        self.assertAlmostEqual(float(out["row_pct"].loc["甲媒体", "0"]), 1 / 3, places=4)
        self.assertAlmostEqual(float(out["row_pct"].loc["甲媒体"].sum()), 1.0, places=6)
        self.assertIn(NO_CLUSTER_LABEL, out["counts"].columns)
        self.assertIn("未参与聚类", out["note"])

    def test_missing_labels_returns_note(self):
        df = make_df(TRANSPORT)
        out = source_cluster_crosstab(df, None)
        self.assertTrue(out["counts"].empty)
        self.assertIn("暂无聚类结果", out["note"])

    def test_empty_labels_returns_note(self):
        df = make_df(TRANSPORT)
        out = source_cluster_crosstab(df, pd.DataFrame())
        self.assertTrue(out["counts"].empty)
        self.assertIn("暂无聚类结果", out["note"])

    def test_labels_without_source_column(self):
        df = make_df(TRANSPORT)
        labels = pd.DataFrame({"row_index": [0, 1], "cluster": [0, 1]})
        out = source_cluster_crosstab(df, labels)
        self.assertTrue(out["counts"].empty)
        self.assertIn("缺少来源字段", out["note"])


class TestSmallSources(unittest.TestCase):
    def test_flags_small_sources(self):
        counts = pd.Series({"甲": 3, "乙": 1, "丙": 2})
        self.assertEqual(small_sources(counts, threshold=2), ["乙"])

    def test_empty_series(self):
        self.assertEqual(small_sources(pd.Series(dtype=int)), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
