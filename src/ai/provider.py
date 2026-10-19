"""可插拔的文案生成后端（src.ai.provider）。

架构约定（换后端不改界面）：
    - 界面层只做：构造 GenerationRequest -> provider.render(request) -> 文本；
    - MockProvider：默认后端，输出带【模拟响应】标记的固定占位文案，
      专供界面联调，绝不冒充真实 AI 生成结果；
    - OllamaProvider：本机本地模型后端，经 http://127.0.0.1:11434/api/chat
      调用（本机接口，不是在线 API），提示词由 prompts.build_prompt 生成。
      未配置模型/服务未启动/超时等失败情形一律抛 ProviderUnavailableError，
      并给出明确中文提示，绝不伪造结果；界面零改动即可切换。
    - GeminiProvider：在线模型后端，经 Google Gemini 官方 REST 接口调用
      （使用其免费额度），用于部署到云端后本机没有 Ollama 的场景；
      密钥只从环境变量或部署平台的 Secrets 读取，绝不硬编码、绝不回显。
      未配置密钥/密钥无效/额度用尽/超时等失败情形同样抛
      ProviderUnavailableError，绝不伪造结果。
    - GroqProvider：另一个在线模型后端，经 Groq 官方 OpenAI 兼容接口调用
      （同样使用其免费额度），作为 Gemini 之外的备选：任一服务额度用尽时
      可在界面直接切到另一个，不必改代码或重启。密钥读取与失败处理
      同 Gemini，同样绝不硬编码、绝不回显。

配置方式（环境变量，无硬编码密钥；Ollama 仅访问本机 127.0.0.1）：
    ECHOMAP_LLM_PROVIDER   "mock"（默认）/ "ollama" / "gemini" / "groq"
    ECHOMAP_OLLAMA_MODEL   Ollama 模型名（如 qwen3:1.7b），ollama 模式必填
    ECHOMAP_OLLAMA_HOST    可选，默认 http://127.0.0.1:11434
    ECHOMAP_OLLAMA_TIMEOUT 可选，单次生成超时秒数（默认 180）
    ECHOMAP_GEMINI_API_KEY Gemini 密钥，gemini 模式必填（也可用平台 Secrets）
    ECHOMAP_GEMINI_MODEL   可选，默认 gemini-2.0-flash
    ECHOMAP_GEMINI_TIMEOUT 可选，单次生成超时秒数（默认 60）
    ECHOMAP_GROQ_API_KEY   Groq 密钥，groq 模式必填（也可用平台 Secrets）
    ECHOMAP_GROQ_MODEL     可选，默认 llama-3.3-70b-versatile
    ECHOMAP_GROQ_TIMEOUT   可选，单次生成超时秒数（默认 60）
"""

from __future__ import annotations

import os

import requests

from src.ai.prompts import GenerationRequest, build_prompt, mock_platform_copy

ENV_PROVIDER = "ECHOMAP_LLM_PROVIDER"
ENV_OLLAMA_MODEL = "ECHOMAP_OLLAMA_MODEL"
ENV_OLLAMA_HOST = "ECHOMAP_OLLAMA_HOST"
ENV_OLLAMA_TIMEOUT = "ECHOMAP_OLLAMA_TIMEOUT"
ENV_GEMINI_API_KEY = "ECHOMAP_GEMINI_API_KEY"
ENV_GEMINI_MODEL = "ECHOMAP_GEMINI_MODEL"
ENV_GEMINI_TIMEOUT = "ECHOMAP_GEMINI_TIMEOUT"
ENV_GROQ_API_KEY = "ECHOMAP_GROQ_API_KEY"
ENV_GROQ_MODEL = "ECHOMAP_GROQ_MODEL"
ENV_GROQ_TIMEOUT = "ECHOMAP_GROQ_TIMEOUT"

PROVIDER_MOCK = "mock"
PROVIDER_OLLAMA = "ollama"
PROVIDER_GEMINI = "gemini"
PROVIDER_GROQ = "groq"
AVAILABLE_PROVIDERS: tuple[str, ...] = (
    PROVIDER_MOCK,
    PROVIDER_OLLAMA,
    PROVIDER_GEMINI,
    PROVIDER_GROQ,
)

DEFAULT_PROVIDER = PROVIDER_MOCK

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_TIMEOUT = 180.0

# Gemini 官方 REST 接口（免费额度即可调用；模型名可用环境变量覆盖）
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_GEMINI_TIMEOUT = 60.0

# Groq 官方 OpenAI 兼容接口（免费额度即可调用；模型名可用环境变量覆盖）
GROQ_API_BASE = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_TIMEOUT = 60.0


class ProviderUnavailableError(RuntimeError):
    """所选后端当前不可用（未安装/未启动/未配置），界面据此明确提示。"""


class MockProvider:
    """模拟后端：确定性占位文案，带醒目【模拟】标记，供界面联调。"""

    name = PROVIDER_MOCK

    def render(self, request: GenerationRequest) -> str:
        return mock_platform_copy(request)


class OllamaProvider:
    """Ollama 本机后端：向 127.0.0.1:11434 的 /api/chat 发起本地推理请求。

    仅访问本机回环地址，不调用任何在线 AI API；失败一律抛
    ProviderUnavailableError（未配置模型 / 服务未启动 / 模型未下载 / 超时 /
    返回异常），绝不返回伪造内容。请求关闭思考模式（think=false），
    且只取 message.content 作为最终文案，模型思考过程不进入结果。
    """

    name = PROVIDER_OLLAMA

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.model = (model or os.environ.get(ENV_OLLAMA_MODEL, "")).strip()
        self.host = (
            host or os.environ.get(ENV_OLLAMA_HOST, "") or DEFAULT_OLLAMA_HOST
        ).rstrip("/")
        self.timeout = timeout if timeout is not None else _timeout_from_env()

    def is_available(self) -> bool:
        """探测本机 Ollama 服务是否可达（GET /api/tags，短超时）。

        仅访问本机回环地址；任何异常一律视为不可用，不抛异常，供界面提示用。
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
        except requests.exceptions.RequestException:
            return False
        return response.status_code == 200

    def render(self, request: GenerationRequest) -> str:
        if not self.model:
            raise ProviderUnavailableError(
                "本地模型后端已启用，但未配置模型名：请设置环境变量 "
                f"{ENV_OLLAMA_MODEL}（如 qwen3:1.7b）后重启应用。"
            )

        prompt = build_prompt(request)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            # 关闭思考模式：思考过程不是交付内容，且会显著拖慢生成
            # （实测 qwen3:1.7b 本机开启思考约 56s，关闭后约数秒）。
            "think": False,
            "options": {"temperature": 0.7},
        }
        url = f"{self.host}/api/chat"

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise ProviderUnavailableError(
                f"本地模型生成超时（超过 {self.timeout:.0f} 秒）：模型可能仍在加载，"
                "请稍后重试，或通过 ECHOMAP_OLLAMA_TIMEOUT 调大超时。"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise ProviderUnavailableError(
                f"无法连接本地 Ollama 服务（{self.host}）：请确认已安装且正在运行"
                "（ollama serve），或改用 mock 后端。"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ProviderUnavailableError(
                f"调用本地 Ollama 服务失败：{exc}"
            ) from exc

        if response.status_code == 404:
            raise ProviderUnavailableError(
                f"本地 Ollama 未找到模型「{self.model}」：请先执行 "
                f"`ollama pull {self.model}`。"
            )
        if response.status_code != 200:
            raise ProviderUnavailableError(
                f"本地 Ollama 返回错误（HTTP {response.status_code}）："
                f"{response.text[:200]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderUnavailableError(
                "本地 Ollama 返回内容无法解析为 JSON，未生成文案。"
            ) from exc

        content = str((data.get("message") or {}).get("content") or "").strip()
        if not content:
            raise ProviderUnavailableError(
                "本地模型返回了空内容：请重试，或确认模型已正确加载。"
            )
        return content


class GeminiProvider:
    """Google Gemini 在线后端（免费额度）：供云端部署使用。

    与 Ollama 后端同构：只需 .name 与 .render(request)，界面零改动即可切换。
    密钥读取顺序为【进程环境变量 → 部署平台 Secrets】，两者都没有时视为未配置；
    密钥只用于请求头，绝不写入日志、绝不回显到界面或错误提示。
    """

    name = PROVIDER_GEMINI

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.model = (
            model or os.environ.get(ENV_GEMINI_MODEL, "") or DEFAULT_GEMINI_MODEL
        ).strip()
        self.api_key = (
            api_key if api_key is not None else _gemini_api_key()
        ).strip()
        self.timeout = timeout if timeout is not None else _gemini_timeout_from_env()

    def is_available(self) -> bool:
        """是否已配置密钥；不做网络探测，避免无谓的在线请求消耗配额。"""
        return bool(self.api_key)

    def render(self, request: GenerationRequest) -> str:
        if not self.api_key:
            raise ProviderUnavailableError(
                "在线模型后端（Gemini）已启用，但未配置 API 密钥：请设置环境变量 "
                f"{ENV_GEMINI_API_KEY}，或在部署平台的 Secrets 中添加该键后重新运行。"
            )

        prompt = build_prompt(request)
        url = f"{GEMINI_API_BASE}/models/{self.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7},
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )
        except requests.exceptions.Timeout as exc:
            raise ProviderUnavailableError(
                f"在线模型生成超时（超过 {self.timeout:.0f} 秒）：请稍后重试，"
                "或改用 mock 后端。"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise ProviderUnavailableError(
                "无法连接在线模型服务（generativelanguage.googleapis.com）："
                "请检查运行环境的网络出口后重试，或改用 mock 后端。"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ProviderUnavailableError(
                f"调用在线模型服务失败：{exc}"
            ) from exc

        if response.status_code in (401, 403):
            raise ProviderUnavailableError(
                f"在线模型拒绝了本次请求（HTTP {response.status_code}）："
                f"API 密钥无效或未授权，请核对 {ENV_GEMINI_API_KEY}。"
            )
        if response.status_code == 429:
            raise ProviderUnavailableError(
                "在线模型已达免费额度上限（HTTP 429）：请稍后重试，"
                "或在界面切回 mock 后端。"
            )
        if response.status_code == 404:
            raise ProviderUnavailableError(
                f"在线模型未找到「{self.model}」：请核对环境变量 "
                f"{ENV_GEMINI_MODEL} 中的模型名。"
            )
        if response.status_code != 200:
            raise ProviderUnavailableError(
                f"在线模型返回错误（HTTP {response.status_code}）："
                f"{response.text[:200]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderUnavailableError(
                "在线模型返回内容无法解析为 JSON，未生成文案。"
            ) from exc

        # 安全策略拦截：官方会把原因放在 promptFeedback.blockReason
        candidates = data.get("candidates") or []
        if not candidates:
            block_reason = str(
                (data.get("promptFeedback") or {}).get("blockReason") or ""
            ).strip()
            if block_reason:
                raise ProviderUnavailableError(
                    f"在线模型的安全策略拦截了本次请求（{block_reason}）："
                    "请调整选题或提示词后重试。"
                )
            raise ProviderUnavailableError("在线模型未返回任何候选内容：请重试。")

        content = "".join(
            str(part.get("text") or "")
            for part in (candidates[0].get("content") or {}).get("parts") or []
        ).strip()
        if not content:
            finish_reason = str(candidates[0].get("finishReason") or "").strip()
            if finish_reason and finish_reason != "STOP":
                raise ProviderUnavailableError(
                    f"在线模型未生成正文（finishReason={finish_reason}）：请重试。"
                )
            raise ProviderUnavailableError("在线模型返回了空内容：请重试。")
        return content


class GroqProvider:
    """Groq 在线后端（免费额度）：Gemini 之外的备选在线模型。

    走 Groq 官方 OpenAI 兼容接口（/chat/completions），只依赖 requests，
    不引入额外 SDK。与 Gemini/Ollama 后端同构（.name + .render），界面零改动
    即可切换；任一服务额度用尽时可切到另一个，不必改代码或重启应用。
    密钥读取与失败处理同 Gemini：绝不硬编码、绝不回显、绝不伪造结果。
    """

    name = PROVIDER_GROQ

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.model = (
            model or os.environ.get(ENV_GROQ_MODEL, "") or DEFAULT_GROQ_MODEL
        ).strip()
        self.api_key = (api_key if api_key is not None else _groq_api_key()).strip()
        self.timeout = timeout if timeout is not None else _groq_timeout_from_env()

    def is_available(self) -> bool:
        """是否已配置密钥；不做网络探测，避免无谓的在线请求消耗配额。"""
        return bool(self.api_key)

    def render(self, request: GenerationRequest) -> str:
        if not self.api_key:
            raise ProviderUnavailableError(
                "在线模型后端（Groq）已启用，但未配置 API 密钥：请设置环境变量 "
                f"{ENV_GROQ_API_KEY}，或在部署平台的 Secrets 中添加该键后重新运行。"
            )

        prompt = build_prompt(request)
        url = f"{GROQ_API_BASE}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )
        except requests.exceptions.Timeout as exc:
            raise ProviderUnavailableError(
                f"在线模型生成超时（超过 {self.timeout:.0f} 秒）：请稍后重试，"
                "或改用 mock 后端。"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise ProviderUnavailableError(
                "无法连接在线模型服务（api.groq.com）：请检查运行环境的网络出口"
                "后重试，或改用 mock 后端。"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ProviderUnavailableError(f"调用在线模型服务失败：{exc}") from exc

        if response.status_code in (401, 403):
            raise ProviderUnavailableError(
                f"在线模型拒绝了本次请求（HTTP {response.status_code}）："
                f"API 密钥无效或未授权，请核对 {ENV_GROQ_API_KEY}。"
            )
        if response.status_code == 429:
            raise ProviderUnavailableError(
                "在线模型已达免费额度或速率上限（HTTP 429）：请稍后重试，"
                "或在界面切换到另一个在线后端（Gemini）或 mock 后端。"
            )
        if response.status_code == 404:
            raise ProviderUnavailableError(
                f"在线模型未找到「{self.model}」：请核对环境变量 "
                f"{ENV_GROQ_MODEL} 中的模型名。"
            )
        if response.status_code != 200:
            raise ProviderUnavailableError(
                f"在线模型返回错误（HTTP {response.status_code}）："
                f"{response.text[:200]}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderUnavailableError(
                "在线模型返回内容无法解析为 JSON，未生成文案。"
            ) from exc

        # 安全策略拦截：OpenAI 兼容格式放在 error 字段
        error = data.get("error")
        if error:
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise ProviderUnavailableError(
                f"在线模型的安全策略拦截了本次请求：{str(message)[:200]}"
            )

        choices = data.get("choices") or []
        if not choices:
            raise ProviderUnavailableError("在线模型未返回任何候选内容：请重试。")
        content = str(
            (choices[0].get("message") or {}).get("content") or ""
        ).strip()
        if not content:
            finish_reason = str(choices[0].get("finish_reason") or "").strip()
            if finish_reason and finish_reason != "stop":
                raise ProviderUnavailableError(
                    f"在线模型未生成正文（finish_reason={finish_reason}）：请重试。"
                )
            raise ProviderUnavailableError("在线模型返回了空内容：请重试。")
        return content


def _timeout_from_env() -> float:
    """读取超时环境变量；缺省或非法值退回默认，非正值一律视为非法。"""
    raw = os.environ.get(ENV_OLLAMA_TIMEOUT, "")
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_OLLAMA_TIMEOUT
    return value if value > 0 else DEFAULT_OLLAMA_TIMEOUT


def _gemini_timeout_from_env() -> float:
    """读取 Gemini 超时环境变量；缺省或非法值退回默认，非正值一律视为非法。"""
    raw = os.environ.get(ENV_GEMINI_TIMEOUT, "")
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_GEMINI_TIMEOUT
    return value if value > 0 else DEFAULT_GEMINI_TIMEOUT


def _config_value(key: str) -> str:
    """读取配置项：优先进程环境变量，其次部署平台 Secrets，都没有则空串。

    云端部署（如 Streamlit Community Cloud）通常把密钥放在 Secrets 中，
    而本地开发用环境变量；两种方式都要能生效，否则部署后需要手工在界面切换。
    只读取、不回显；Secrets 不可用（本地未配置 secrets.toml）时按未配置处理，
    不把异常细节暴露到界面或日志。
    """
    value = os.environ.get(key, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(key, "") or "").strip()
    except Exception:
        return ""


def _gemini_api_key() -> str:
    """读取 Gemini 密钥（环境变量或部署平台 Secrets）；只读取、不回显。"""
    return _config_value(ENV_GEMINI_API_KEY)


def _groq_timeout_from_env() -> float:
    """读取 Groq 超时环境变量；缺省或非法值退回默认，非正值一律视为非法。"""
    raw = os.environ.get(ENV_GROQ_TIMEOUT, "")
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_GROQ_TIMEOUT
    return value if value > 0 else DEFAULT_GROQ_TIMEOUT


def _groq_api_key() -> str:
    """读取 Groq 密钥（环境变量或部署平台 Secrets）；只读取、不回显。"""
    return _config_value(ENV_GROQ_API_KEY)


def get_provider(name: str | None = None):
    """按名称返回后端实例；默认读环境变量/平台 Secrets，再退回 mock。

    未知名称抛 ValueError；返回对象只需具备 .name 与 .render(request)。
    """
    chosen = (name or _config_value(ENV_PROVIDER) or DEFAULT_PROVIDER).strip().lower()
    if chosen == PROVIDER_MOCK:
        return MockProvider()
    if chosen == PROVIDER_OLLAMA:
        return OllamaProvider()
    if chosen == PROVIDER_GEMINI:
        return GeminiProvider()
    if chosen == PROVIDER_GROQ:
        return GroqProvider()
    raise ValueError(
        f"未知模型后端: {chosen!r}，可选: {list(AVAILABLE_PROVIDERS)}"
    )
