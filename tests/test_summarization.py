"""TextRank 抽取式摘要模块的单元测试（标准库 unittest）。"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.summarization import split_sentences, summarize  # noqa: E402


class TestSummarization(unittest.TestCase):
    def test_summary_sentences_come_from_source(self):
        text = "地铁新线路今日开通。早高峰通勤时间缩短。交通部门将增加班次。市民表示欢迎。"
        result = summarize(text, top_n=2)
        self.assertGreater(len(result["summary"]), 0)
        for sentence in result["summary"]:
            self.assertIn(sentence, text, "摘要句必须来自原文")

    def test_empty_text(self):
        result = summarize("", top_n=3)
        self.assertEqual(result["summary"], [])
        self.assertEqual(result["num_sentences"], 0)
        self.assertTrue(result["note"])

    def test_none_text(self):
        result = summarize(None, top_n=3)
        self.assertEqual(result["summary"], [])

    def test_single_sentence(self):
        result = summarize("只有一句话。", top_n=3)
        self.assertEqual(result["summary"], ["只有一句话。"])
        self.assertEqual(result["summary_indices"], [0])
        self.assertTrue(result["note"])

    def test_top_n_limits_count(self):
        text = "第一句讲交通。第二句讲通勤。第三句讲班次。第四句讲换乘。"
        result = summarize(text, top_n=2)
        self.assertLessEqual(len(result["summary"]), 2)

    def test_top_n_greater_than_sentences(self):
        text = "第一句讲交通。第二句讲通勤。"
        result = summarize(text, top_n=10)
        self.assertLessEqual(len(result["summary"]), 2)
        self.assertTrue(result["note"])

    def test_order_preserved(self):
        text = "甲句谈到交通通勤。乙句也谈交通通勤。丙句谈交通通勤与班次。丁句谈交通通勤换乘。"
        result = summarize(text, top_n=3)
        self.assertEqual(result["summary_indices"], sorted(result["summary_indices"]))

    def test_no_duplicate_sentences(self):
        text = "交通拥堵严重。交通拥堵严重。环保问题突出。"
        result = summarize(text, top_n=3)
        self.assertEqual(len(result["summary"]), len(set(result["summary"])))

    def test_no_shared_tokens_returns_result_with_note(self):
        text = "苹果生长在山坡。量子物理很复杂。足球比赛很精彩。"
        result = summarize(text, top_n=2)
        sentences = split_sentences(text)
        # 无有效连边时降级为按原文顺序选取前 N 个不重复句子
        self.assertEqual(result["summary_indices"], [0, 1])
        self.assertEqual(result["summary"], [sentences[0], sentences[1]])
        self.assertTrue(result["note"])

    def test_split_sentences(self):
        self.assertEqual(len(split_sentences("第一句。第二句！第三句？")), 3)
        self.assertEqual(split_sentences(""), [])
        self.assertEqual(split_sentences(None), [])

    def test_split_sentences_english_period(self):
        # 常见英文句末句点应被切分
        self.assertEqual(
            split_sentences("Hello. World."),
            ["Hello.", "World."],
        )

    def test_split_sentences_decimal_not_split(self):
        # 小数不应被误切
        self.assertEqual(
            split_sentences("价格是3.14元。"),
            ["价格是3.14元。"],
        )

    def test_split_sentences_period_followed_by_space_is_boundary(self):
        # 句点后跟空格视为边界（即使是 e.g. 这类缩写），属已知局限
        self.assertEqual(
            split_sentences("e.g. for example"),
            ["e.g.", "for example"],
        )

    def test_invalid_top_n(self):
        with self.assertRaises(ValueError):
            summarize("文本。", top_n=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
