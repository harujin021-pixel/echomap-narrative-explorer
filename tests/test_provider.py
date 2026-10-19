"""src.ai.provider 可插拔后端的单元测试。

覆盖：默认 mock、工厂函数、未知后端报错、环境变量配置；
Ollama 后端的真实 render 路径——成功取值、请求体构造、各类失败
（未配置模型 / 连接失败 / 超时 / 模型未下载 / HTTP 错误 / 非 JSON / 空内容）
统一抛 ProviderUnavailableError 且不伪造结果。
Gemini 在线后端的真实 render 路径——成功取值、请求体/请求头构造、密钥来源、
各类失败（未配置密钥 / 密钥无效 / 额度用尽 / 模型名错误 / 超时 / 连接失败 /
非 JSON / 无候选 / 空内容），同样统一抛 ProviderUnavailableError，
并校验密钥绝不回显到错误提示中。
全部本地测试：requests.post 被 mock 替换，不发任何真实网络请求。
"""

import unittest
from unittest.mock import patch

import requests

from src.ai.prompts import MOCK_MARKER, GenerationRequest, build_request
from src.ai.provider import (
    AVAILABLE_PROVIDERS,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GEMINI_TIMEOUT,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GROQ_TIMEOUT,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_TIMEOUT,
    DEFAULT_PROVIDER,
    ENV_GEMINI_API_KEY,
    ENV_GEMINI_MODEL,
    ENV_GEMINI_TIMEOUT,
    ENV_GROQ_API_KEY,
    ENV_GROQ_MODEL,
    ENV_GROQ_TIMEOUT,
    ENV_OLLAMA_HOST,
    ENV_OLLAMA_MODEL,
    ENV_OLLAMA_TIMEOUT,
    ENV_PROVIDER,
    GEMINI_API_BASE,
    GROQ_API_BASE,
    GeminiProvider,
    GroqProvider,
    MockProvider,
    OllamaProvider,
    ProviderUnavailableError,
    get_provider,
)
from tests.test_prompts import make_rec

POST_TARGET = "src.ai.provider.requests.post"
GET_TARGET = "src.ai.provider.requests.get"


def make_request() -> GenerationRequest:
    return build_request("xiaohongshu", make_rec(), "general", "practical")


class FakeResponse:
    """最小化的 requests 响应替身（不触发任何真实请求）。"""

    def __init__(self, status_code: int = 200, payload: object = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json in fake response")
        return self._payload


class TestGetProvider(unittest.TestCase):
    def test_default_is_mock(self):
        self.assertEqual(DEFAULT_PROVIDER, "mock")
        self.assertIsInstance(get_provider(), MockProvider)
        self.assertEqual(get_provider().name, "mock")

    def test_explicit_names(self):
        self.assertIsInstance(get_provider("mock"), MockProvider)
        self.assertIsInstance(get_provider("ollama"), OllamaProvider)
        self.assertIsInstance(get_provider("gemini"), GeminiProvider)
        self.assertIsInstance(get_provider("groq"), GroqProvider)

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            get_provider("chatgpt")
        with self.assertRaises(ValueError):
            get_provider("openai")

    def test_env_override(self):
        with patch.dict("os.environ", {ENV_PROVIDER: "ollama"}):
            self.assertIsInstance(get_provider(), OllamaProvider)
        with patch.dict("os.environ", {ENV_PROVIDER: "mock"}):
            self.assertIsInstance(get_provider(), MockProvider)
        with patch.dict("os.environ", {ENV_PROVIDER: "bogus"}):
            with self.assertRaises(ValueError):
                get_provider()

    def test_registry_contents(self):
        self.assertIn("mock", AVAILABLE_PROVIDERS)
        self.assertIn("ollama", AVAILABLE_PROVIDERS)
        self.assertIn("gemini", AVAILABLE_PROVIDERS)
        self.assertIn("groq", AVAILABLE_PROVIDERS)


class TestMockProvider(unittest.TestCase):
    def test_render_marked_and_deterministic(self):
        provider = MockProvider()
        text1 = provider.render(make_request())
        text2 = provider.render(make_request())
        self.assertIn(MOCK_MARKER, text1)
        self.assertIn("【模拟】", text1)
        self.assertEqual(text1, text2)

    def test_render_returns_str(self):
        self.assertIsInstance(MockProvider().render(make_request()), str)

    def test_render_makes_no_network_call(self):
        with patch(POST_TARGET) as post:
            MockProvider().render(make_request())
        post.assert_not_called()


class TestOllamaConfig(unittest.TestCase):
    def test_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            provider = OllamaProvider()
        self.assertEqual(provider.model, "")
        self.assertEqual(provider.host, DEFAULT_OLLAMA_HOST)
        self.assertEqual(provider.timeout, DEFAULT_OLLAMA_TIMEOUT)

    def test_model_from_env(self):
        with patch.dict("os.environ", {ENV_OLLAMA_MODEL: "qwen3:1.7b"}):
            self.assertEqual(OllamaProvider().model, "qwen3:1.7b")

    def test_host_and_timeout_from_env(self):
        env = {
            ENV_OLLAMA_MODEL: "qwen3:1.7b",
            ENV_OLLAMA_HOST: "http://127.0.0.1:9999/",
            ENV_OLLAMA_TIMEOUT: "30",
        }
        with patch.dict("os.environ", env, clear=True):
            provider = OllamaProvider()
        self.assertEqual(provider.host, "http://127.0.0.1:9999")  # 去除尾部斜杠
        self.assertEqual(provider.timeout, 30.0)

    def test_invalid_timeout_falls_back(self):
        for bad in ("abc", "0", "-5"):
            with patch.dict("os.environ", {ENV_OLLAMA_TIMEOUT: bad}, clear=True):
                self.assertEqual(OllamaProvider().timeout, DEFAULT_OLLAMA_TIMEOUT)


class TestOllamaRender(unittest.TestCase):
    def setUp(self):
        self.provider = OllamaProvider(model="qwen3:1.7b")

    def test_missing_model_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            provider = OllamaProvider()
        self.assertEqual(provider.model, "")
        with patch(POST_TARGET) as post:
            with self.assertRaises(ProviderUnavailableError) as ctx:
                provider.render(make_request())
        post.assert_not_called()  # 未配置模型时不得发起请求
        self.assertIn(ENV_OLLAMA_MODEL, str(ctx.exception))

    def test_success_returns_content_and_correct_payload(self):
        fake = FakeResponse(payload={"message": {"content": "  真实生成的文案  "}})
        with patch(POST_TARGET, return_value=fake) as post:
            text = self.provider.render(make_request())
        self.assertEqual(text, "真实生成的文案")  # 已去除首尾空白
        args, kwargs = post.call_args
        self.assertEqual(args[0], f"{DEFAULT_OLLAMA_HOST}/api/chat")
        body = kwargs["json"]
        self.assertEqual(body["model"], "qwen3:1.7b")
        self.assertFalse(body["stream"])
        self.assertFalse(body["think"])  # 关闭思考模式
        self.assertEqual(len(body["messages"]), 1)
        self.assertIn("小红书", body["messages"][0]["content"])
        self.assertEqual(kwargs["timeout"], self.provider.timeout)

    def test_custom_host_used(self):
        provider = OllamaProvider(model="qwen3:1.7b", host="http://127.0.0.1:1234")
        fake = FakeResponse(payload={"message": {"content": "ok"}})
        with patch(POST_TARGET, return_value=fake) as post:
            provider.render(make_request())
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:1234/api/chat")

    def test_thinking_not_included(self):
        # 只取 message.content，模型思考过程（thinking）不得进入结果
        fake = FakeResponse(
            payload={"message": {"content": "最终文案", "thinking": "中间推理过程"}}
        )
        with patch(POST_TARGET, return_value=fake):
            text = self.provider.render(make_request())
        self.assertEqual(text, "最终文案")
        self.assertNotIn("中间推理过程", text)

    def test_connection_error(self):
        with patch(POST_TARGET, side_effect=requests.exceptions.ConnectionError("refused")):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        msg = str(ctx.exception)
        self.assertIn("127.0.0.1", msg)
        self.assertIn("Ollama", msg)

    def test_timeout(self):
        with patch(POST_TARGET, side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("超时", str(ctx.exception))

    def test_other_request_exception(self):
        with patch(POST_TARGET, side_effect=requests.exceptions.RequestException("boom")):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_model_not_found_404(self):
        fake = FakeResponse(status_code=404, text="model not found")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        msg = str(ctx.exception)
        self.assertIn("qwen3:1.7b", msg)
        self.assertIn("ollama pull", msg)

    def test_http_error_status(self):
        fake = FakeResponse(status_code=500, text="internal error")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("500", str(ctx.exception))

    def test_invalid_json(self):
        fake = FakeResponse(status_code=200, payload=None)
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_empty_content(self):
        fake = FakeResponse(payload={"message": {"content": "   "}})
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("空内容", str(ctx.exception))


class TestOllamaAvailability(unittest.TestCase):
    """is_available() 探测：不抛异常，供界面提示用。"""

    def test_reachable(self):
        with patch(GET_TARGET, return_value=FakeResponse(status_code=200)) as get:
            self.assertTrue(OllamaProvider(model="qwen3:1.7b").is_available())
        self.assertIn("/api/tags", get.call_args.args[0])

    def test_bad_status(self):
        with patch(GET_TARGET, return_value=FakeResponse(status_code=500)):
            self.assertFalse(OllamaProvider(model="qwen3:1.7b").is_available())

    def test_connection_error(self):
        with patch(GET_TARGET, side_effect=requests.exceptions.ConnectionError("refused")):
            self.assertFalse(OllamaProvider(model="qwen3:1.7b").is_available())


class TestGeminiConfig(unittest.TestCase):
    """Gemini 后端的配置读取：模型名、超时、密钥来源与可用性判断。"""

    def test_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            provider = GeminiProvider(api_key="k")
        self.assertEqual(provider.model, DEFAULT_GEMINI_MODEL)
        self.assertEqual(provider.timeout, DEFAULT_GEMINI_TIMEOUT)

    def test_model_and_timeout_from_env(self):
        env = {ENV_GEMINI_MODEL: "gemini-2.5-flash", ENV_GEMINI_TIMEOUT: "12"}
        with patch.dict("os.environ", env, clear=True):
            provider = GeminiProvider(api_key="k")
        self.assertEqual(provider.model, "gemini-2.5-flash")
        self.assertEqual(provider.timeout, 12.0)

    def test_invalid_timeout_falls_back(self):
        for bad in ("abc", "0", "-5"):
            with patch.dict("os.environ", {ENV_GEMINI_TIMEOUT: bad}, clear=True):
                self.assertEqual(
                    GeminiProvider(api_key="k").timeout, DEFAULT_GEMINI_TIMEOUT
                )

    def test_api_key_from_env(self):
        with patch.dict("os.environ", {ENV_GEMINI_API_KEY: "  env-key  "}, clear=True):
            self.assertEqual(GeminiProvider().api_key, "env-key")

    def test_is_available(self):
        self.assertTrue(GeminiProvider(api_key="k").is_available())
        self.assertFalse(GeminiProvider(api_key="").is_available())


class TestGeminiRender(unittest.TestCase):
    """Gemini 后端的真实 render 路径（requests.post 全部被替换）。"""

    def setUp(self):
        self.provider = GeminiProvider(
            model="gemini-2.0-flash", api_key="test-key"
        )

    def test_missing_key_raises_and_makes_no_request(self):
        provider = GeminiProvider(model="gemini-2.0-flash", api_key="")
        with patch(POST_TARGET) as post:
            with self.assertRaises(ProviderUnavailableError) as ctx:
                provider.render(make_request())
        post.assert_not_called()  # 未配置密钥时不得发起在线请求
        self.assertIn(ENV_GEMINI_API_KEY, str(ctx.exception))

    def test_success_returns_content_and_correct_request(self):
        fake = FakeResponse(
            payload={"candidates": [{"content": {"parts": [{"text": "  生成文案  "}]}}]}
        )
        with patch(POST_TARGET, return_value=fake) as post:
            text = self.provider.render(make_request())
        self.assertEqual(text, "生成文案")  # 已去除首尾空白

        args, kwargs = post.call_args
        self.assertEqual(
            args[0],
            f"{GEMINI_API_BASE}/models/gemini-2.0-flash:generateContent",
        )
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], "test-key")
        parts = kwargs["json"]["contents"][0]["parts"]
        self.assertEqual(len(parts), 1)
        self.assertIn("小红书", parts[0]["text"])  # 提示词来自 prompts 模块
        self.assertEqual(kwargs["timeout"], self.provider.timeout)

    def test_multiple_parts_are_concatenated(self):
        fake = FakeResponse(
            payload={
                "candidates": [
                    {"content": {"parts": [{"text": "前半"}, {"text": "后半"}]}}
                ]
            }
        )
        with patch(POST_TARGET, return_value=fake):
            self.assertEqual(self.provider.render(make_request()), "前半后半")

    def test_invalid_key_never_echoed(self):
        for status in (401, 403):
            fake = FakeResponse(status_code=status, text="forbidden")
            with patch(POST_TARGET, return_value=fake):
                with self.assertRaises(ProviderUnavailableError) as ctx:
                    self.provider.render(make_request())
            msg = str(ctx.exception)
            self.assertIn(str(status), msg)
            self.assertIn(ENV_GEMINI_API_KEY, msg)
            self.assertNotIn("test-key", msg)  # 密钥绝不回显

    def test_quota_exceeded_429(self):
        fake = FakeResponse(status_code=429, text="quota exceeded")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("429", str(ctx.exception))
        self.assertIn("额度", str(ctx.exception))

    def test_model_not_found_404(self):
        fake = FakeResponse(status_code=404, text="model not found")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("gemini-2.0-flash", str(ctx.exception))

    def test_http_error_status(self):
        fake = FakeResponse(status_code=500, text="internal error")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("500", str(ctx.exception))

    def test_timeout(self):
        with patch(POST_TARGET, side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("超时", str(ctx.exception))

    def test_connection_error(self):
        with patch(
            POST_TARGET, side_effect=requests.exceptions.ConnectionError("refused")
        ):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("generativelanguage.googleapis.com", str(ctx.exception))

    def test_other_request_exception(self):
        with patch(POST_TARGET, side_effect=requests.exceptions.RequestException("boom")):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_invalid_json(self):
        fake = FakeResponse(status_code=200, payload=None)
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_blocked_by_safety_no_candidates(self):
        fake = FakeResponse(
            status_code=200, payload={"promptFeedback": {"blockReason": "SAFETY"}}
        )
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        msg = str(ctx.exception)
        self.assertIn("SAFETY", msg)
        self.assertIn("安全策略", msg)

    def test_no_candidates_without_reason(self):
        fake = FakeResponse(status_code=200, payload={"candidates": []})
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_empty_content_with_finish_reason(self):
        fake = FakeResponse(
            status_code=200,
            payload={"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": []}}]},
        )
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("MAX_TOKENS", str(ctx.exception))

    def test_empty_content(self):
        fake = FakeResponse(
            status_code=200,
            payload={"candidates": [{"content": {"parts": [{"text": "   "}]}}]},
        )
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("空内容", str(ctx.exception))


class TestGroqConfig(unittest.TestCase):
    """Groq 后端的配置读取：模型名、超时、密钥来源与可用性判断。"""

    def test_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            provider = GroqProvider(api_key="k")
        self.assertEqual(provider.model, DEFAULT_GROQ_MODEL)
        self.assertEqual(provider.timeout, DEFAULT_GROQ_TIMEOUT)

    def test_model_and_timeout_from_env(self):
        env = {ENV_GROQ_MODEL: "llama-3.1-8b-instant", ENV_GROQ_TIMEOUT: "15"}
        with patch.dict("os.environ", env, clear=True):
            provider = GroqProvider(api_key="k")
        self.assertEqual(provider.model, "llama-3.1-8b-instant")
        self.assertEqual(provider.timeout, 15.0)

    def test_invalid_timeout_falls_back(self):
        for bad in ("abc", "0", "-1"):
            with patch.dict("os.environ", {ENV_GROQ_TIMEOUT: bad}, clear=True):
                self.assertEqual(GroqProvider(api_key="k").timeout, DEFAULT_GROQ_TIMEOUT)

    def test_api_key_from_env(self):
        with patch.dict("os.environ", {ENV_GROQ_API_KEY: "  env-key  "}, clear=True):
            self.assertEqual(GroqProvider().api_key, "env-key")

    def test_is_available(self):
        self.assertTrue(GroqProvider(api_key="k").is_available())
        self.assertFalse(GroqProvider(api_key="").is_available())


class TestGroqRender(unittest.TestCase):
    """Groq 后端的真实 render 路径（requests.post 全部被替换）。"""

    def setUp(self):
        self.provider = GroqProvider(
            model="llama-3.3-70b-versatile", api_key="test-key"
        )

    def test_missing_key_raises_and_makes_no_request(self):
        provider = GroqProvider(model="llama-3.3-70b-versatile", api_key="")
        with patch(POST_TARGET) as post:
            with self.assertRaises(ProviderUnavailableError) as ctx:
                provider.render(make_request())
        post.assert_not_called()  # 未配置密钥时不得发起在线请求
        self.assertIn(ENV_GROQ_API_KEY, str(ctx.exception))

    def test_success_returns_content_and_correct_request(self):
        fake = FakeResponse(
            payload={"choices": [{"message": {"content": "  生成文案  "}}]}
        )
        with patch(POST_TARGET, return_value=fake) as post:
            text = self.provider.render(make_request())
        self.assertEqual(text, "生成文案")

        args, kwargs = post.call_args
        self.assertEqual(args[0], f"{GROQ_API_BASE}/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["model"], "llama-3.3-70b-versatile")
        messages = kwargs["json"]["messages"]
        self.assertEqual(messages[0]["role"], "user")
        self.assertIn("小红书", messages[0]["content"])
        self.assertEqual(kwargs["timeout"], self.provider.timeout)

    def test_invalid_key_never_echoed(self):
        for status in (401, 403):
            fake = FakeResponse(status_code=status, text="unauthorized")
            with patch(POST_TARGET, return_value=fake):
                with self.assertRaises(ProviderUnavailableError) as ctx:
                    self.provider.render(make_request())
            msg = str(ctx.exception)
            self.assertIn(str(status), msg)
            self.assertIn(ENV_GROQ_API_KEY, msg)
            self.assertNotIn("test-key", msg)

    def test_rate_limit_429_mentions_alternative_backend(self):
        fake = FakeResponse(status_code=429, text="rate limited")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        msg = str(ctx.exception)
        self.assertIn("429", msg)
        self.assertIn("Gemini", msg)  # 提示可切到另一个在线后端

    def test_model_not_found_404(self):
        fake = FakeResponse(status_code=404, text="model not found")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("llama-3.3-70b-versatile", str(ctx.exception))

    def test_http_error_status(self):
        fake = FakeResponse(status_code=500, text="internal error")
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("500", str(ctx.exception))

    def test_timeout(self):
        with patch(POST_TARGET, side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("超时", str(ctx.exception))

    def test_connection_error(self):
        with patch(
            POST_TARGET, side_effect=requests.exceptions.ConnectionError("refused")
        ):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("api.groq.com", str(ctx.exception))

    def test_other_request_exception(self):
        with patch(POST_TARGET, side_effect=requests.exceptions.RequestException("boom")):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_invalid_json(self):
        fake = FakeResponse(status_code=200, payload=None)
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_error_payload_is_reported(self):
        fake = FakeResponse(
            status_code=200,
            payload={"error": {"message": "content policy violation"}},
        )
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("安全策略", str(ctx.exception))

    def test_no_choices(self):
        fake = FakeResponse(status_code=200, payload={"choices": []})
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError):
                self.provider.render(make_request())

    def test_empty_content_with_finish_reason(self):
        fake = FakeResponse(
            status_code=200,
            payload={"choices": [{"finish_reason": "length", "message": {"content": ""}}]},
        )
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("length", str(ctx.exception))

    def test_empty_content(self):
        fake = FakeResponse(
            status_code=200,
            payload={"choices": [{"message": {"content": "   "}}]},
        )
        with patch(POST_TARGET, return_value=fake):
            with self.assertRaises(ProviderUnavailableError) as ctx:
                self.provider.render(make_request())
        self.assertIn("空内容", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
