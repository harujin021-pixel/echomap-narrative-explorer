"""文本预处理模块的单元测试（标准库 unittest）。"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.preprocessing import (  # noqa: E402
    _HAS_LETTER_CHAR,
    load_sensitive_words,
    load_stopwords,
    normalize_text,
    preprocess_documents,
    preprocess_text,
    tokenize,
)


class TestPreprocessing(unittest.TestCase):
    def test_normalize_handles_non_string_and_blank(self):
        for value in [None, 123, 3.14, float("nan")]:
            self.assertEqual(normalize_text(value), "")
        self.assertEqual(normalize_text("   "), "")

    def test_normalize_collapses_whitespace(self):
        self.assertEqual(normalize_text("  你好   世界  "), "你好 世界")
        self.assertEqual(normalize_text("全角\u3000空格"), "全角 空格")

    def test_tokenize_filters_punctuation_and_stopwords(self):
        tokens = tokenize("地铁开通了，交通部门表示满意！")
        self.assertIn("地铁", tokens)
        self.assertNotIn("，", tokens)
        self.assertNotIn("！", tokens)
        self.assertNotIn("表示", tokens)  # 停用词
        self.assertNotIn("了", tokens)    # 停用词

    def test_tokenize_drops_single_char_tokens(self):
        # 单字（汉字/字母/数字）提前剔除，多字词保留
        tokens = tokenize("地铁开通了，交通部门表示满意！a 1 好")
        self.assertNotIn("a", tokens)
        self.assertNotIn("1", tokens)
        self.assertNotIn("好", tokens)
        self.assertIn("地铁", tokens)
        self.assertTrue(all(len(t) >= 2 for t in tokens), f"出现单字: {tokens}")

    def test_tokenize_single_char_input_only(self):
        self.assertEqual(tokenize("我 你 他"), [])
        self.assertEqual(tokenize("a 1 好"), [])

    def test_tokenize_drops_pure_number_tokens(self):
        # 纯数字 token（日期、编号等）一律剔除；含字母/汉字的 token 保留
        tokens = tokenize("发布于 2026 10 17 的 5G 新闻 3.14 AI")
        self.assertNotIn("2026", tokens)
        self.assertNotIn("10", tokens)
        self.assertNotIn("17", tokens)
        self.assertNotIn("3.14", tokens)
        self.assertIn("5g", tokens)
        self.assertIn("新闻", tokens)
        self.assertIn("ai", tokens)
        self.assertTrue(
            all(_HAS_LETTER_CHAR.search(t) for t in tokens),
            f"出现纯数字 token: {tokens}",
        )

    def test_tokenize_empty_inputs(self):
        for value in ["", "   ", None, 12, "！？，。；"]:
            self.assertEqual(tokenize(value), [], f"输入 {value!r} 应返回空列表")

    def test_tokenize_all_stopwords_filtered(self):
        self.assertEqual(tokenize("的 了 和 是 ！"), [])

    def test_preprocess_text_is_space_joined_tokens(self):
        text = "地铁开通"
        self.assertEqual(preprocess_text(text), " ".join(tokenize(text)))
        self.assertIn("地铁", preprocess_text(text).split())

    def test_load_stopwords_contains_common_words(self):
        stopwords = load_stopwords()
        self.assertIn("的", stopwords)
        self.assertIn("是", stopwords)

    def test_load_sensitive_words_from_builtin_file(self):
        sensitive = load_sensitive_words()
        self.assertIn("傻逼", sensitive)
        self.assertIn("裸聊", sensitive)
        # 注释行与空行不作为词条
        self.assertNotIn("#", sensitive)
        self.assertNotIn("", sensitive)

    def test_load_sensitive_words_missing_file_returns_empty(self):
        self.assertEqual(load_sensitive_words(path="不存在/敏感词表.txt"), set())

    def test_tokenize_filters_sensitive_words(self):
        # 「废物」在默认敏感词表中被命中；「傻逼」被 jieba 切成单字后由单字规则剔除
        tokens = tokenize("废物 环境 这个是傻逼！")
        self.assertNotIn("废物", tokens)
        self.assertNotIn("傻逼", tokens)
        self.assertNotIn("傻", tokens)
        self.assertNotIn("逼", tokens)
        self.assertIn("环境", tokens)

    def test_tokenize_sensitive_empty_set_disables_filter(self):
        tokens = tokenize("废物 环境", sensitive=set())
        self.assertIn("废物", tokens)
        self.assertIn("环境", tokens)

    def test_tokenize_keeps_nounish_tokens_only(self):
        # 中文 token 仅保留名词性词性：动词（操作/不负）、口语碎片（这波/变水，
        # 由 HMM 关闭 + 单字规则剔除）不进入结果；名词正常保留
        tokens = tokenize("操作 这波 冰糖 变水 营商 专员 不负 青山")
        self.assertIn("冰糖", tokens)
        self.assertIn("营商", tokens)
        self.assertIn("专员", tokens)
        self.assertIn("青山", tokens)
        self.assertNotIn("操作", tokens)
        self.assertNotIn("不负", tokens)
        self.assertNotIn("这波", tokens)
        self.assertNotIn("变水", tokens)

    def test_tokenize_filters_death_words(self):
        # 敏感词表负面伤亡类词条：不参与分析、不出现在界面
        tokens = tokenize("一起事故致人身亡，死亡人数上升。")
        self.assertNotIn("身亡", tokens)
        self.assertNotIn("死亡", tokens)
        self.assertIn("事故", tokens)

    def test_preprocess_documents_length_preserved(self):
        docs = preprocess_documents(["你好 世界", "", None])
        self.assertEqual(len(docs), 3)
        self.assertEqual(docs[1], "")
        self.assertEqual(docs[2], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
