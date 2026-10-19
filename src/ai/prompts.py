"""多平台文案生成的平台注册表与提示词构建（src.ai.prompts）。

设计原则：
    - 平台可扩展：新增平台 = 在 PLATFORM_FIELDS / PLATFORM_NAMES_ZH 中加一项；
    - 全部为纯函数，不发起网络请求、不调用任何在线 AI API；
    - 提示词包含明确的事实边界指令：只基于给定新闻素材、保留来源、
      不编造数据/引用；
    - 受众与风格使用固定中文标签（进入提示词），界面标签由 i18n 层提供。
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 平台注册表：第一版支持 4 个平台；key 用于代码与会话状态，不进入界面文案
PLATFORMS: tuple[str, ...] = ("xiaohongshu", "wechat_mp", "douyin", "weibo")

# 平台中文名（进入提示词与模拟文案；属于"内容"而非界面 chrome）
PLATFORM_NAMES_ZH: dict[str, str] = {
    "xiaohongshu": "小红书",
    "wechat_mp": "微信公众号",
    "douyin": "抖音",
    "weibo": "微博",
}

# 各平台需要生成的字段（顺序即展示顺序）
PLATFORM_FIELDS: dict[str, tuple[str, ...]] = {
    "xiaohongshu": ("笔记标题", "正文", "话题标签"),
    "wechat_mp": ("文章标题", "摘要", "正文（含小标题）"),
    "douyin": ("开场钩子", "口播稿", "分镜建议", "结尾互动"),
    "weibo": ("热点短文", "话题表达", "互动文案"),
}

# 受众固定选项：key -> 提示词中使用的中文标签
AUDIENCES: dict[str, str] = {
    "general": "大众读者",
    "students": "学生群体",
    "professionals": "行业从业者",
}

# 风格固定选项：key -> 提示词中使用的中文标签（后续可扩展）
STYLES: dict[str, str] = {
    "practical": "实用干货",
    "educational": "知识科普",
    "casual": "轻松分享",
}

MOCK_MARKER = "【模拟响应 · 未接入本地模型】"


@dataclass
class GenerationRequest:
    """一次文案生成的全部输入（与具体模型后端无关）。

    将来接入 Ollama 时，OllamaProvider 直接消费该对象：
    build_prompt(request) 生成提示词 -> 本机接口调用 -> 返回文本。
    界面层不需要任何改动。
    """

    platform: str
    topic_label: str
    keywords: list[str] = field(default_factory=list)
    articles: list[dict] = field(default_factory=list)  # {title, source, date}
    audience: str = ""  # 中文标签，如 "大众读者"
    style: str = ""  # 中文标签，如 "实用干货"
    article_count: int = 0
    ratio_text: str = ""
    latest_date: str = ""


def validate_platform(platform: str) -> None:
    """校验平台 key；未知平台抛 ValueError（避免静默生成错误格式）。"""
    if platform not in PLATFORM_FIELDS:
        raise ValueError(f"未知平台: {platform!r}，可选: {sorted(PLATFORM_FIELDS)}")


def build_request(
    platform: str,
    rec: dict,
    audience_key: str,
    style_key: str,
) -> GenerationRequest:
    """把选题推荐结果（build_topic_recommendations 的单条输出）转换为生成请求。

    只读取 rec 中的既有字段做摘要，不重新计算、不虚构任何数据。
    """
    validate_platform(platform)
    if audience_key not in AUDIENCES:
        raise ValueError(f"未知受众: {audience_key!r}")
    if style_key not in STYLES:
        raise ValueError(f"未知风格: {style_key!r}")

    articles = [
        {"title": a.get("title") or "", "source": a.get("source") or "", "date": a.get("date") or ""}
        for a in rec.get("articles", [])
    ]
    dates = [a["date"] for a in articles if a["date"]]
    ratio = rec.get("ratio")
    return GenerationRequest(
        platform=platform,
        topic_label=" · ".join(k for k in rec.get("keywords", []) if k),
        keywords=[k for k in rec.get("keywords", []) if k],
        articles=articles,
        audience=AUDIENCES[audience_key],
        style=STYLES[style_key],
        article_count=int(rec.get("count", 0) or 0),
        ratio_text=f"{float(ratio):.1%}" if isinstance(ratio, (int, float)) else "",
        latest_date=max(dates) if dates else "",
    )


def _articles_block(request: GenerationRequest) -> str:
    """把关联新闻整理为提示词素材块（保留来源与日期，可溯源）。"""
    if not request.articles:
        return "（本选题暂无可展示的关联新闻）"
    lines = []
    for a in request.articles:
        date = a["date"] or "未知日期"
        source = a["source"] or "未知来源"
        title = a["title"] or "（无标题）"
        lines.append(f"- {title}｜来源：{source}｜日期：{date}")
    return "\n".join(lines)


def build_prompt(request: GenerationRequest) -> str:
    """构建发送给本地模型的中文提示词（纯函数，可测试、可预览）。

    提示词内嵌事实边界指令：只基于给定素材、保留来源、区分事实与观点、
    不编造新闻/数据/引用。本函数不发起任何网络请求。
    """
    validate_platform(request.platform)
    fields = "、".join(PLATFORM_FIELDS[request.platform])
    source_hint = request.articles[0]["source"] if request.articles else "相关媒体"
    return (
        f"你是新闻内容策划助手。请根据以下素材，为「{PLATFORM_NAMES_ZH[request.platform]}」"
        f"创作一篇面向{request.audience}的{request.style}文案，需要包含：{fields}。\n\n"
        f"【选题信息】\n"
        f"- 主题：{request.topic_label or '（未命名主题）'}\n"
        f"- 关键词：{'、'.join(request.keywords) or '无'}\n"
        f"- 主题规模：{request.article_count} 篇"
        f"（占参与聚类文章 {request.ratio_text or '未知'}）\n"
        f"- 主题内最新报道：{request.latest_date or '未知日期'}\n\n"
        f"【可用的关联新闻素材（创作依据，不要使用下方列表之外的任何事实）】\n"
        f"{_articles_block(request)}\n\n"
        f"【创作要求】\n"
        f"1. 只基于上述素材创作，不得编造新闻、数据、来源或引用；\n"
        f"2. 涉及新闻事实时保留来源信息（如：据{source_hint}报道）；\n"
        f"3. 区分新闻事实与观点表达，推测内容需使用“可能/据称”等措辞；\n"
        f"4. 素材不足以支撑的内容不要写，宁缺毋滥。\n"
    )


def mock_platform_copy(request: GenerationRequest) -> str:
    """按平台字段结构生成"模拟文案"，专供界面联调。

    每一行都带【模拟】标记，开头有总标记，结尾有说明，
    确保不会被误认为真实 AI 生成结果。确定性输出（同输入同输出）。
    """
    validate_platform(request.platform)
    topic = request.topic_label or "未命名主题"
    source_hint = request.articles[0]["source"] if request.articles else "相关媒体"
    latest = request.latest_date or "未知日期"

    body = (
        f"【模拟】这里是正文占位段落。真实接入本地模型后，此处将输出基于"
        f"「{topic}」选题、面向{request.audience}的{request.style}内容；"
        f"涉及新闻事实时会保留来源（如：据{source_hint}报道，主题内最新报道日期为{latest}）。"
    )

    sections: list[str] = []
    if request.platform == "xiaohongshu":
        sections = [
            ("笔记标题", f"【模拟】关于「{topic}」的演示标题（占位文案）"),
            ("正文", body),
            ("话题标签", f"【模拟】#{topic.replace(' ', '')} #演示数据 #占位标签"),
        ]
    elif request.platform == "wechat_mp":
        sections = [
            ("文章标题", f"【模拟】「{topic}」主题公众号文章标题（占位文案）"),
            ("摘要", f"【模拟】摘要占位：本文围绕{request.style}主题，面向{request.audience}。"),
            ("正文（含小标题）", f"【模拟】一、小标题占位\n{body}\n【模拟】二、小结占位"),
        ]
    elif request.platform == "douyin":
        sections = [
            ("开场钩子", f"【模拟】开场钩子占位：3 秒吸引{request.audience}注意的表达。"),
            ("口播稿", body),
            ("分镜建议", "【模拟】分镜占位：镜头1 主体画面 / 镜头2 数据图表示意 / 镜头3 收尾。"),
            ("结尾互动", "【模拟】结尾互动占位：引导关注与评论的固定话术。"),
        ]
    else:  # weibo
        sections = [
            ("热点短文", f"【模拟】140 字以内短文占位，围绕「{topic}」。{body}"),
            ("话题表达", f"【模拟】#{topic.replace(' ', '')}# 相关话题表达占位。"),
            ("互动文案", "【模拟】互动文案占位：邀请转发/评论的固定话术。"),
        ]

    lines = [MOCK_MARKER, ""]
    for name, text in sections:
        lines.append(f"== {name} ==")
        lines.append(text)
        lines.append("")
    lines.append(
        "【模拟数据说明】本段为界面联调用的固定模拟文案（未接入任何模型），"
        "不代表真实 AI 生成结果，请勿直接使用。"
    )
    return "\n".join(lines)
