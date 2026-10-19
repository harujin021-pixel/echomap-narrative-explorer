"""数据概览辅助模块的单元测试（标准库 unittest）。

测试 src.ui.overview 的纯函数，覆盖正常数据、空数据、
全缺失日期、单一来源等边界。所有数据均为合成构造。
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.overview import (  # noqa: E402
    compute_overview_stats,
    date_distribution,
    find_cjk_font,
    make_bar_chart,
    source_distribution,
)


def _make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(
            df["published_at"], format="mixed", errors="coerce"
        )
    return df


NORMAL_ROWS = [
    {"title": "标题一", "content": "正文内容一", "source": "来源甲", "published_at": "2024-05-01"},
    {"title": "标题二", "content": "正文内容二二", "source": "来源甲", "published_at": "2024-05-01"},
    {"title": "标题三", "content": "正文内容三三三", "source": "来源乙", "published_at": "2024-05-03"},
]

SINGLE_SOURCE_ROWS = [
    {"title": "标题一", "content": "正文一", "source": "唯一来源", "published_at": "2024-05-01"},
    {"title": "标题二", "content": "正文二", "source": "唯一来源", "published_at": "2024-05-02"},
]

NO_DATE_ROWS = [
    {"title": "标题一", "content": "正文一", "source": "来源甲"},
    {"title": "标题二", "content": "正文二", "source": "来源乙"},
]

BAD_DATE_ROWS = [
    {"title": "标题一", "content": "正文一", "source": "来源甲", "published_at": "not-a-date"},
    {"title": "标题二", "content": "正文二", "source": "来源乙", "published_at": ""},
]


class TestComputeOverviewStats(unittest.TestCase):
    def test_normal_data(self):
        stats = compute_overview_stats(_make_df(NORMAL_ROWS))
        self.assertEqual(stats["rows"], 3)
        self.assertEqual(stats["n_sources"], 2)
        self.assertEqual(stats["date_min"], "2024-05-01")
        self.assertEqual(stats["date_max"], "2024-05-03")
        self.assertEqual(stats["valid_dates"], 3)
        self.assertEqual(stats["completeness"]["title"], 3)
        self.assertEqual(stats["completeness"]["content"], 3)
        self.assertEqual(stats["completeness"]["source"], 3)
        self.assertEqual(stats["content_length"]["min"], 5)
        self.assertEqual(stats["content_length"]["max"], 7)
        self.assertAlmostEqual(stats["content_length"]["mean"], 6.0)

    def test_empty_dataframe(self):
        stats = compute_overview_stats(pd.DataFrame())
        self.assertEqual(stats["rows"], 0)
        self.assertEqual(stats["n_sources"], 0)
        self.assertIsNone(stats["date_min"])
        self.assertIsNone(stats["date_max"])
        self.assertEqual(stats["valid_dates"], 0)
        self.assertEqual(stats["completeness"], {})
        self.assertIsNone(stats["content_length"])

    def test_no_date_column(self):
        stats = compute_overview_stats(_make_df(NO_DATE_ROWS))
        self.assertEqual(stats["rows"], 2)
        self.assertIsNone(stats["date_min"])
        self.assertEqual(stats["valid_dates"], 0)

    def test_all_dates_invalid(self):
        stats = compute_overview_stats(_make_df(BAD_DATE_ROWS))
        self.assertEqual(stats["rows"], 2)
        self.assertEqual(stats["valid_dates"], 0)
        self.assertIsNone(stats["date_min"])
        self.assertIsNone(stats["date_max"])

    def test_single_source(self):
        stats = compute_overview_stats(_make_df(SINGLE_SOURCE_ROWS))
        self.assertEqual(stats["n_sources"], 1)


class TestSourceDistribution(unittest.TestCase):
    def test_normal_counts(self):
        dist = source_distribution(_make_df(NORMAL_ROWS))
        self.assertEqual(int(dist["来源甲"]), 2)
        self.assertEqual(int(dist["来源乙"]), 1)
        # 按数量降序
        self.assertEqual(dist.index[0], "来源甲")

    def test_empty_dataframe(self):
        self.assertTrue(source_distribution(pd.DataFrame()).empty)

    def test_single_source(self):
        dist = source_distribution(_make_df(SINGLE_SOURCE_ROWS))
        self.assertEqual(len(dist), 1)
        self.assertEqual(int(dist.iloc[0]), 2)


class TestDateDistribution(unittest.TestCase):
    def test_normal_counts(self):
        dist = date_distribution(_make_df(NORMAL_ROWS))
        self.assertEqual(int(dist.sum()), 3)
        # 2024-05-01 有两篇
        values = list(dist.values)
        self.assertIn(2, values)

    def test_empty_dataframe(self):
        self.assertTrue(date_distribution(pd.DataFrame()).empty)

    def test_all_dates_invalid(self):
        self.assertTrue(date_distribution(_make_df(BAD_DATE_ROWS)).empty)

    def test_no_date_column(self):
        self.assertTrue(date_distribution(_make_df(NO_DATE_ROWS)).empty)


class TestFontAndChart(unittest.TestCase):
    def test_find_cjk_font_returns_str_or_none(self):
        font = find_cjk_font()
        self.assertTrue(font is None or isinstance(font, str))

    def test_make_bar_chart_empty_series_returns_none(self):
        fig = make_bar_chart(
            pd.Series(dtype=int), "t", "x", "y", font_name="SimHei"
        )
        self.assertIsNone(fig)

    def test_make_bar_chart_no_font_returns_none(self):
        series = pd.Series({"a": 1, "b": 2})
        fig = make_bar_chart(series, "t", "x", "y", font_name=None)
        self.assertIsNone(fig)

    def test_make_bar_chart_with_font_returns_figure(self):
        import matplotlib.pyplot as plt

        font = find_cjk_font()
        if font is None:
            self.skipTest("系统无可用中文字体，跳过 matplotlib 图表构造")
        series = pd.Series({"来源甲": 2, "来源乙": 1})
        fig = make_bar_chart(series, "标题", "x", "y", font_name=font)
        self.assertIsNotNone(fig)
        plt.close(fig)


if __name__ == "__main__":
    unittest.main(verbosity=2)
