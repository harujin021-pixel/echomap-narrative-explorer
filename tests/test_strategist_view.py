"""src.ui.strategist_view 选题推荐界面辅助的单元测试（阶段 5.1）。

覆盖：日期格式化（正常/字符串/缺失/无法解析）、关键词标签、双语选项与
理由文案、因子表格、关联新闻占位词。不依赖 Streamlit 与网络。
"""

import unittest
from datetime import datetime

import pandas as pd

from src.ui.strategist_view import (
    article_rows,
    factor_rows,
    factor_value_text,
    format_date,
    reason_text,
    topic_keywords_label,
    topic_option_label,
)


def make_rec() -> dict:
    return {
        "cluster": 1,
        "keywords": ["科技", "公司", "智能", "设备"],
        "count": 3,
        "ratio": 0.5,
        "articles": [
            {"title": "科技新品发布0", "source": "示例乙", "date": "2026-01-10", "row_index": 3},
            {"title": "科技新品发布1", "source": "示例乙", "date": "2026-01-10", "row_index": 4},
        ],
        "factor_share": 0.5,
        "factor_kw": 0.8,
        "factor_recency": 1.0,
        "score": 0.76,
    }


class TestFormatDate(unittest.TestCase):
    def test_timestamp(self):
        self.assertEqual(format_date(datetime(2026, 1, 2)), "2026-01-02")

    def test_string_date(self):
        self.assertEqual(format_date("2026-01-02"), "2026-01-02")

    def test_none_and_invalid(self):
        self.assertIsNone(format_date(None))
        self.assertIsNone(format_date("bad input"))
        self.assertIsNone(format_date(pd.NaT))


class TestTopicLabels(unittest.TestCase):
    def test_keywords_label_max_three(self):
        label = topic_keywords_label(make_rec())
        self.assertEqual(label, "科技 · 公司 · 智能")

    def test_keywords_label_empty(self):
        self.assertEqual(topic_keywords_label({"keywords": []}), "")

    def test_option_label_zh(self):
        label = topic_option_label(make_rec(), rank=1, lang="zh")
        self.assertIn("#1", label)
        self.assertIn("3 篇", label)
        self.assertIn("科技", label)

    def test_option_label_en(self):
        label = topic_option_label(make_rec(), rank=2, lang="en")
        self.assertIn("#2", label)
        self.assertIn("articles", label)


class TestReasonText(unittest.TestCase):
    def test_zh_with_latest_date(self):
        text = reason_text(make_rec(), lang="zh")
        self.assertIn("3 篇", text)
        self.assertIn("50.0%", text)
        self.assertIn("2026-01-10", text)

    def test_zh_without_articles_shows_unknown(self):
        rec = make_rec()
        rec["articles"] = []
        self.assertIn("未知", reason_text(rec, lang="zh"))

    def test_en_without_articles_shows_unknown(self):
        rec = make_rec()
        rec["articles"] = []
        self.assertIn("unknown", reason_text(rec, lang="en"))


class TestFactorDisplay(unittest.TestCase):
    def test_value_text(self):
        self.assertEqual(factor_value_text(0.5), "0.500")
        self.assertEqual(factor_value_text(None, lang="zh"), "—")
        self.assertEqual(factor_value_text(None, lang="en"), "—")

    def test_factor_rows(self):
        rows = factor_rows([make_rec()], lang="zh")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertIn("#1", row["选题"])
        self.assertEqual(row["主题占比"], "0.500")
        self.assertEqual(row["关键词强度"], "0.800")
        self.assertEqual(row["时间新近度"], "1.000")
        self.assertEqual(row["综合排序值"], "0.760")

    def test_factor_rows_en_columns(self):
        rows = factor_rows([make_rec()], lang="en")
        row = rows[0]
        self.assertIn("Topic", row)
        self.assertIn("Score", row)


class TestArticleRows(unittest.TestCase):
    def test_normal_rows(self):
        rows = article_rows(make_rec(), lang="zh")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["标题"], "科技新品发布0")
        self.assertEqual(rows[0]["来源"], "示例乙")
        self.assertEqual(rows[0]["日期"], "2026-01-10")

    def test_missing_fields_use_placeholders(self):
        rec = make_rec()
        rec["articles"] = [
            {"title": "", "source": None, "date": None, "row_index": 0},
        ]
        rows = article_rows(rec, lang="zh")
        self.assertEqual(rows[0]["标题"], "（无标题）")
        self.assertEqual(rows[0]["来源"], "未知来源")
        self.assertEqual(rows[0]["日期"], "未知日期")


if __name__ == "__main__":
    unittest.main()
