"""src.ai.safety 本地敏感信息检测与脱敏的单元测试。

覆盖：正常通过、敏感词命中、手机号/身份证/邮箱识别、脱敏文本正确性、
空内容与异常路径的"无法确定"、类别汇总、重叠片段不去重计数、导出闸门语义。
全部本地纯函数测试，不联网。
"""

import unittest
from unittest.mock import patch

from src.ai import safety
from src.ai.safety import (
    CAT_EMAIL,
    CAT_ID_CARD,
    CAT_PHONE,
    CAT_SENSITIVE_WORD,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_UNCERTAIN,
    SafetyReport,
    analyze_text,
    category_counts,
)


class TestCleanText(unittest.TestCase):
    def test_clean_text_passes_and_not_masked(self):
        text = "这是一段关于人工智能芯片研发的普通文案，来源示例科技报。"
        report = analyze_text(text)
        self.assertEqual(report.status, STATUS_PASS)
        self.assertTrue(report.passed)
        self.assertEqual(report.findings, ())
        self.assertEqual(report.masked_text, text)

    def test_uncertain_is_not_passed(self):
        report = SafetyReport(STATUS_UNCERTAIN, (), "", reason="empty")
        self.assertFalse(report.passed)
        report = SafetyReport(STATUS_FAIL, (), "x")
        self.assertFalse(report.passed)


class TestSensitiveWord(unittest.TestCase):
    def test_sensitive_word_fails_and_masked(self):
        report = analyze_text("据报道，事故造成人员死亡。")
        self.assertEqual(report.status, STATUS_FAIL)
        self.assertIn("死亡", [f.term for f in report.findings])
        self.assertEqual(report.findings[0].category, CAT_SENSITIVE_WORD)
        self.assertNotIn("死亡", report.masked_text)
        self.assertIn("***", report.masked_text)


class TestPII(unittest.TestCase):
    def test_phone_detected(self):
        report = analyze_text("联系方式：13812345678 请勿外传。")
        self.assertEqual(report.status, STATUS_FAIL)
        cats = {f.category for f in report.findings}
        self.assertIn(CAT_PHONE, cats)
        self.assertIn("[手机号已脱敏]", report.masked_text)
        self.assertNotIn("13812345678", report.masked_text)

    def test_id_card_not_also_phone(self):
        report = analyze_text("证件号 110101199003074567 已存档。")
        cats = [f.category for f in report.findings]
        self.assertEqual(cats, [CAT_ID_CARD])
        self.assertIn("[证件号已脱敏]", report.masked_text)

    def test_email_detected_case_insensitive_host(self):
        report = analyze_text("请发送至 User.Name@Example.COM 联系。")
        self.assertIn(CAT_EMAIL, {f.category for f in report.findings})
        self.assertIn("[邮箱已脱敏]", report.masked_text)
        self.assertNotIn("User.Name@Example.COM", report.masked_text)

    def test_number_embedded_in_longer_run_not_detected(self):
        # 19 位纯数字不应被判为手机号（避免误报）
        report = analyze_text("编号 1381234567890123456 无关。")
        self.assertNotIn(CAT_PHONE, {f.category for f in report.findings})


class TestUncertain(unittest.TestCase):
    def test_empty_or_non_string(self):
        for value in ("", "   ", None, 123):
            report = analyze_text(value)
            self.assertEqual(report.status, STATUS_UNCERTAIN)
            self.assertEqual(report.reason, "empty")
            self.assertFalse(report.passed)

    def test_scan_error_is_uncertain(self):
        with patch("src.ai.safety.load_sensitive_words", side_effect=RuntimeError("boom")):
            report = analyze_text("正常文案")
        self.assertEqual(report.status, STATUS_UNCERTAIN)
        self.assertEqual(report.reason, "error")
        self.assertFalse(report.passed)


class TestCounts(unittest.TestCase):
    def test_category_counts_order_and_values(self):
        report = analyze_text("死亡与自杀 及 电话13812345678 邮箱 a@b.com")
        counts = dict(category_counts(report))
        self.assertEqual(counts[CAT_SENSITIVE_WORD], 2)
        self.assertEqual(counts[CAT_PHONE], 1)
        self.assertEqual(counts[CAT_EMAIL], 1)
        # 顺序遵循 CATEGORIES：phone, id_card, email, sensitive_word
        self.assertEqual([c for c, _ in category_counts(report)], [CAT_PHONE, CAT_EMAIL, CAT_SENSITIVE_WORD])

    def test_no_findings_gives_empty_counts(self):
        self.assertEqual(category_counts(analyze_text("干净文案")), [])

    def test_scan_finds_all_categories(self):
        report = analyze_text("自杀 手机13812345678 证件110101199003074567 邮箱 a@b.com")
        self.assertEqual(
            [c for c, _ in category_counts(report)],
            [CAT_PHONE, CAT_ID_CARD, CAT_EMAIL, CAT_SENSITIVE_WORD],
        )


class TestMaskingEdge(unittest.TestCase):
    def test_overlapping_spans_masked_once(self):
        # 同一位置的重复敏感词不应产生重复占位
        report = safety.analyze_text("死亡死亡")
        self.assertEqual(report.masked_text.count("***"), 2)

    def test_masked_preserves_surrounding_text(self):
        report = analyze_text("前文 死亡 后文")
        self.assertEqual(report.masked_text, "前文 *** 后文")


if __name__ == "__main__":
    unittest.main()
