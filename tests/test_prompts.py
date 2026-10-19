"""src.ai.prompts 平台注册表与提示词构建的单元测试。

覆盖：平台注册表完整性、校验、请求构建（正常/异常）、提示词内容
（含来源与事实边界指令）、模拟文案（标记齐全、确定性、按平台分字段）。
全部纯函数测试，不发任何网络请求。
"""

import unittest

from src.ai.prompts import (
    MOCK_MARKER,
    PLATFORMS,
    PLATFORM_FIELDS,
    PLATFORM_NAMES_ZH,
    STYLES,
    AUDIENCES,
    build_prompt,
    build_request,
    mock_platform_copy,
    validate_platform,
)


def make_rec() -> dict:
    return {
        "cluster": 1,
        "keywords": ["科技", "公司", "智能"],
        "count": 3,
        "ratio": 0.5,
        "articles": [
            {"title": "科技新品发布0", "source": "示例乙", "date": "2026-01-10", "row_index": 3},
            {"title": "科技新品发布1", "source": "", "date": None, "row_index": 4},
        ],
        "factor_share": 0.5,
        "factor_kw": 0.8,
        "factor_recency": 1.0,
        "score": 0.76,
    }


def make_request(platform: str = "xiaohongshu"):
    return build_request(platform, make_rec(), "general", "practical")


class TestPlatformRegistry(unittest.TestCase):
    def test_four_platforms_registered(self):
        self.assertEqual(
            set(PLATFORMS), {"xiaohongshu", "wechat_mp", "douyin", "weibo"}
        )
        self.assertEqual(set(PLATFORM_FIELDS), set(PLATFORMS))
        self.assertEqual(set(PLATFORM_NAMES_ZH), set(PLATFORMS))
        for key in PLATFORMS:
            self.assertTrue(PLATFORM_FIELDS[key])
            self.assertTrue(PLATFORM_NAMES_ZH[key])

    def test_audience_and_style_options(self):
        self.assertEqual(set(AUDIENCES), {"general", "students", "professionals"})
        self.assertEqual(set(STYLES), {"practical", "educational", "casual"})

    def test_validate_platform(self):
        validate_platform("weibo")  # 不抛异常
        with self.assertRaises(ValueError):
            validate_platform("twitter")


class TestBuildRequest(unittest.TestCase):
    def test_normal_request(self):
        req = make_request()
        self.assertEqual(req.platform, "xiaohongshu")
        self.assertEqual(req.topic_label, "科技 · 公司 · 智能")
        self.assertEqual(req.audience, "大众读者")
        self.assertEqual(req.style, "实用干货")
        self.assertEqual(req.article_count, 3)
        self.assertEqual(req.ratio_text, "50.0%")
        self.assertEqual(req.latest_date, "2026-01-10")
        self.assertEqual(len(req.articles), 2)
        # 缺失字段被归一为空串，不引入 None
        self.assertEqual(req.articles[1]["source"], "")
        self.assertEqual(req.articles[1]["date"], "")

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            build_request("twitter", make_rec(), "general", "practical")
        with self.assertRaises(ValueError):
            build_request("weibo", make_rec(), "kids", "practical")
        with self.assertRaises(ValueError):
            build_request("weibo", make_rec(), "general", "luxury")


class TestBuildPrompt(unittest.TestCase):
    def test_prompt_contains_key_elements(self):
        prompt = build_prompt(make_request())
        self.assertIn("小红书", prompt)
        self.assertIn("大众读者", prompt)
        self.assertIn("实用干货", prompt)
        self.assertIn("科技", prompt)
        self.assertIn("科技新品发布0", prompt)
        self.assertIn("示例乙", prompt)
        self.assertIn("2026-01-10", prompt)
        self.assertIn("不得编造", prompt)

    def test_prompt_without_articles(self):
        rec = make_rec()
        rec["articles"] = []
        req = build_request("weibo", rec, "students", "casual")
        prompt = build_prompt(req)
        self.assertIn("暂无可展示的关联新闻", prompt)
        self.assertIn("相关媒体", prompt)

    def test_prompt_deterministic(self):
        req = make_request()
        self.assertEqual(build_prompt(req), build_prompt(req))


class TestMockCopy(unittest.TestCase):
    def test_marker_and_placeholder_in_every_platform(self):
        for platform in PLATFORMS:
            text = mock_platform_copy(make_request(platform))
            self.assertIn(MOCK_MARKER, text)
            self.assertIn("模拟数据说明", text)
            self.assertIn("【模拟】", text)
            for field_name in PLATFORM_FIELDS[platform]:
                self.assertIn(f"== {field_name} ==", text)

    def test_deterministic(self):
        req = make_request("douyin")
        self.assertEqual(mock_platform_copy(req), mock_platform_copy(req))

    def test_unknown_platform_raises(self):
        req = make_request()
        req.platform = "twitter"
        with self.assertRaises(ValueError):
            mock_platform_copy(req)


if __name__ == "__main__":
    unittest.main()
