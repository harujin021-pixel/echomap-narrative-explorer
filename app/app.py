"""EchoMap —— AI 驱动的媒体叙事探索平台（Streamlit 单文件主入口）。

当前已实现（Phase 3.1 ~ 4.3 已验收；4.4 文档与说明区块；4.5 中英双语界面；
    5.1 AI 推荐选题——本地规则版，复用聚类与关键词结果，侧边栏页面切换）：
    - 数据导入：CSV 上传 / 合成示例加载，复用 Phase 1 清洗与质量报告管道
    - 数据质量概览与清洗后数据预览
    - 数据档案（Data Provenance）：数据指纹、导入信息、清洗步骤
    - 数据概览：来源分布、日期分布、字段完整性、正文长度统计
    - 主题聚类分析：TF-IDF + KMeans，可调聚类数，含代表关键词与簇内文章
    - 多来源对比：来源关键词对比、来源×主题分布
    - 新闻详情：关键词提取、TextRank 抽取式摘要
    - 相似新闻：余弦相似度 Top-N，支持文章间跳转继续探索
    - 关于本研究：可折叠静态说明区块（研究问题、方法边界、数据状态）
    - 界面语言：侧边栏「Language / 语言」切换（默认 English，可切中文）

界面静态文案集中在 src/ui/i18n.py；数据内容（新闻标题、正文、来源名、
关键词）按原样展示不翻译；算法层生成的提示（聚类 note、摘要 note、
来源对比 note）仍为中文，属于本阶段的已知边界。

数据来源由 session_state 标记并在界面持续可见；
合成测试数据全程标注，不代表真实新闻。
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# 本地以 `py -m streamlit run app/app.py` 启动时，解释器会把当前目录加入
# 模块搜索路径，`from src...` 因此可用；云端平台以 `streamlit run app/app.py`
# 方式启动时不会，需要显式加入项目根目录，否则导入会失败。
_ROOT_DIR = Path(__file__).resolve().parents[1]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from src.ai.topics import MAX_ARTICLES_PER_TOPIC, build_topic_recommendations
from src.ai.prompts import AUDIENCES, PLATFORMS, STYLES, build_prompt, build_request
from src.ai.provider import (
    ENV_GEMINI_MODEL,
    ENV_GROQ_MODEL,
    ENV_OLLAMA_MODEL,
    PROVIDER_GEMINI,
    PROVIDER_MOCK,
    PROVIDER_GROQ,
    PROVIDER_OLLAMA,
    GeminiProvider,
    GroqProvider,
    MockProvider,
    OllamaProvider,
    get_provider,
)
from src.ai.safety import analyze_text, category_counts
from src.data.loader import DataValidationError
from src.analysis.source_compare import (
    source_cluster_crosstab,
    source_keyword_compare,
)
from src.analysis.keywords import keywords_for_corpus
from src.analysis.vectorize import combine_text_fields
from src.ui.article_view import (
    field_or_placeholder,
    get_article_detail,
    get_similar_articles,
)
from src.ui.cluster_view import (
    articles_in_cluster,
    cluster_summary,
    CLUSTERING_PIPELINE_VERSION,
    compute_clusters,
    data_fingerprint,
    unclustered_count,
    wordlists_fingerprint,
)
from src.ui.data_io import load_synthetic_demo, load_uploaded_csv
from src.ui.i18n import t
from src.ui.provenance import build_provenance, dataset_tag
from src.ui.strategist_view import (
    article_rows,
    factor_rows,
    reason_text,
    topic_keywords_label,
    topic_option_label,
)
from src.ui.overview import (
    compute_overview_stats,
    date_distribution,
    find_cjk_font,
    make_bar_chart,
    source_distribution,
)

# 项目根目录（app/app.py 的上一级目录）
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 内部数据来源标记（session_state 中保持中文原值）→ 英文展示文案
_SOURCE_LABEL_EN = {
    "合成测试数据": "synthetic test data",
    "用户上传数据": "user-uploaded data",
}

# 全局界面样式（视觉优化）：仅调整留白、配色、圆角与卡片阴影，
# 不改变任何组件、交互或分析逻辑；所有文案仍由 i18n 模块控制。
_GLOBAL_CSS = """
<style>
/* ============ 基础：字体与页面框架 ============ */
html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", "Helvetica Neue", "PingFang SC",
                 "Microsoft YaHei", sans-serif;
}

[data-testid="stAppViewContainer"] > .main .block-container,
section.main > div.block-container {
    padding-top: 1.1rem;
    padding-bottom: 4rem;
    max-width: 1220px;
}

/* ============ 顶部品牌横幅（深蓝渐变） ============ */
.echomap-hero {
    background: linear-gradient(120deg, #1F4E79 0%, #2E6DA4 58%, #3E8AC7 100%);
    border-radius: 16px;
    padding: 2.1rem 2.4rem 2rem 2.4rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 12px 28px rgba(31, 78, 121, 0.24);
}
.echomap-hero-title {
    color: #FFFFFF;
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.8px;
    line-height: 1.1;
    margin: 0;
}
.echomap-hero-sub {
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.92rem;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-top: 0.5rem;
}
.echomap-hero-tag {
    display: inline-block;
    margin-top: 0.9rem;
    padding: 0.25rem 0.7rem;
    background: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 999px;
    color: #FFFFFF;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.4px;
}

/* ============ 标题层级：左侧彩色竖条 ============ */
h1 {
    color: #1A2332;
    font-weight: 800;
}
h2 {
    color: #1A2332;
    font-weight: 700;
    border-left: 5px solid #1F4E79;
    padding-left: 0.7rem;
    margin-top: 0.4rem;
    margin-bottom: 0.6rem;
    letter-spacing: -0.2px;
}
h3 {
    color: #1A2332;
    font-weight: 700;
    border-left: 4px solid #3E8AC7;
    padding-left: 0.6rem;
    margin-top: 0.3rem;
}
h4, h5, h6 {
    color: #33405A;
    font-weight: 600;
}

/* ============ 区块卡片容器 ============
   每个区块容器内放置一个不可见的 .echomap-card 标记，用 :has() 精确命中该
   容器本身（不依赖 Streamlit 内部 class），渲染成白底圆角卡片；用 !important
   覆盖 Streamlit 给带边框容器写入的行内样式。 */
.echomap-card { display: none; }
[data-testid="stVerticalBlock"]:has(
    > [data-testid="stElementContainer"] .echomap-card
) {
    background: #FFFFFF !important;
    border: 1px solid #E3E8EF !important;
    border-left: 5px solid #1F4E79 !important;
    border-radius: 14px !important;
    box-shadow: 0 3px 12px rgba(16, 24, 40, 0.06) !important;
    padding: 1.2rem 1.4rem 1rem 1.4rem !important;
    transition: box-shadow 0.25s ease, border-left-color 0.25s ease;
}
/* 悬停时轻微抬升，强化"每张卡片是一个模块"的层次感 */
[data-testid="stVerticalBlock"]:has(
    > [data-testid="stElementContainer"] .echomap-card
):hover {
    box-shadow: 0 10px 24px rgba(16, 24, 40, 0.11) !important;
    border-left-color: #2E6DA4 !important;
}

/* ============ 指标卡：浅蓝渐变 + 左侧强调 ============ */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #FFFFFF 0%, #EEF4FC 100%);
    border: 1px solid #DCE6F5;
    border-left: 4px solid #1F4E79;
    border-radius: 12px;
    padding: 0.85rem 0.95rem;
    box-shadow: 0 2px 8px rgba(31, 78, 121, 0.08);
}
/* 指标值默认按单行省略号截断且容器有固定高度（日期区间会被截成
   "2024-05-01 ..."）。这里解除固定高度与裁剪、允许换行，保证长文本
   完整显示；同时略降字号，让常见日期区间尽量单行排下。 */
[data-testid="stMetric"],
[data-testid="stMetric"] [data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    height: auto !important;
    max-height: none !important;
    min-height: 0 !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #1F4E79;
    font-weight: 700;
    font-size: 1.3rem;
    line-height: 1.3;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    overflow-wrap: break-word;
    max-width: 100%;
}
[data-testid="stMetricLabel"] {
    color: #5B6472;
    font-weight: 600;
}

/* ============ 按钮 ============ */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #1F4E79;
    color: #1F4E79;
    box-shadow: 0 3px 10px rgba(31, 78, 121, 0.16);
    transform: translateY(-1px);
}
.stButton > button[data-testid="baseButton-primary"],
button[kind="primary"] {
    background: linear-gradient(120deg, #1F4E79 0%, #2E6DA4 100%);
    border: 1px solid #1F4E79;
    color: #FFFFFF;
    box-shadow: 0 4px 14px rgba(31, 78, 121, 0.28);
}

/* ============ 表格：深蓝表头 + 斑马纹 ============ */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid #E3E8EF;
    border-radius: 10px;
    overflow: hidden;
}
[data-testid="stTable"] table {
    border-collapse: collapse;
    width: 100%;
}
[data-testid="stTable"] thead tr th {
    background: #1F4E79;
    color: #FFFFFF;
    font-weight: 600;
    text-align: left;
    padding: 0.55rem 0.85rem;
}
[data-testid="stTable"] tbody td {
    padding: 0.5rem 0.85rem;
    border-bottom: 1px solid #EEF1F5;
    background: #FFFFFF;
    color: #1A2332;
}
[data-testid="stTable"] tbody tr:nth-child(even) td {
    background: #F5F8FC;
}

/* ============ 折叠面板 ============ */
[data-testid="stExpander"] {
    border: 1px solid #E3E8EF;
    border-radius: 12px;
    background: #FFFFFF;
    box-shadow: 0 1px 5px rgba(16, 24, 40, 0.05);
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-weight: 600;
    color: #1A2332;
    background: #F8FAFC;
    padding: 0.55rem 0.9rem;
}
[data-testid="stExpander"] summary:hover {
    color: #1F4E79;
}

/* ============ 提示条与代码块 ============ */
[data-testid="stAlert"] {
    border-radius: 10px;
    border-left-width: 4px;
}
[data-testid="stCode"], [data-testid="stCode"] pre {
    border-radius: 10px;
}
[data-testid="stCode"] pre {
    background: #F5F8FC;
    border: 1px solid #E3E8EF;
}

/* ============ 侧边栏 ============ */
[data-testid="stSidebar"] {
    background: #F8FAFC;
    border-right: 1px solid #E3E8EF;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] h2 {
    border-left: none;
    border-bottom: 3px solid #1F4E79;
    padding-left: 0;
    padding-bottom: 0.45rem;
    margin-bottom: 0.9rem;
}

/* ============ 标签页：通透的分段导航 ============ */
[data-testid="stTabs"] [role="tablist"] {
    gap: 0.35rem;
    border-bottom: 1px solid #E3E8EF;
    margin-bottom: 1.1rem;
}
[data-testid="stTab"] {
    font-weight: 600;
    color: #5B6472;
    padding: 0.45rem 1rem;
    border-radius: 8px 8px 0 0;
}
[data-testid="stTab"]:hover,
[data-testid="stTab"][aria-selected="true"],
[data-testid="stTab"][data-selected="true"] {
    color: #1F4E79;
}

/* ============ 模块之间的装饰分隔（渐隐细线 + 菱形节点） ============
   纯装饰元素，位于两个模块卡片之间，弱化区块之间的硬边界；
   不含任何文案，因此不涉及多语言，也不改变模块数量与顺序。 */
.echomap-divider {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin: 0.1rem 0 0.2rem 0;
}
.echomap-divider::before,
.echomap-divider::after {
    content: "";
    flex: 1 1 0;
    height: 1px;
    background: linear-gradient(
        90deg,
        rgba(31, 78, 121, 0) 0%,
        #C7D8EC 45%,
        #C7D8EC 55%,
        rgba(31, 78, 121, 0) 100%
    );
}
.echomap-divider > span {
    width: 7px;
    height: 7px;
    background: #3E8AC7;
    border-radius: 2px;
    transform: rotate(45deg);
    box-shadow: 0 0 0 4px rgba(62, 138, 199, 0.13);
}

/* ============ 说明文字与分隔线 ============ */
[data-testid="stCaptionContainer"] {
    color: #6B7280;
}
hr {
    border-color: #E3E8EF;
}
</style>
"""


def _inject_global_css() -> None:
    """注入一次性全局样式（纯视觉调整，不改变任何组件或功能）。"""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def _render_hero(lang: str) -> None:
    """渲染顶部品牌横幅（深蓝渐变 + 白色标题），替代裸标题。

    文案仍取自 i18n（app_caption），中英双语切换时同步更新；
    仅做视觉呈现，不改变任何数据或交互逻辑。
    """
    st.markdown(
        f"""
        <div class="echomap-hero">
            <div class="echomap-hero-title">EchoMap</div>
            <div class="echomap-hero-sub">{t("app_caption", lang)}</div>
            <div class="echomap-hero-tag">Explainable Text Mining · Media Narrative</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _card() -> None:
    """在区块容器内放置不可见标记，供 CSS :has() 命中并渲染为卡片。

    仅用于视觉分区，不产生可见内容，也不影响任何组件与数据。
    """
    st.markdown('<span class="echomap-card"></span>', unsafe_allow_html=True)


def _module_divider() -> None:
    """在两个模块卡片之间渲染装饰性分隔线（纯视觉，无文案、无功能影响）。

    只做视觉过渡，不增删任何模块，也不参与任何数据与分析逻辑。
    """
    st.markdown(
        '<div class="echomap-divider"><span></span></div>',
        unsafe_allow_html=True,
    )


def _backend_options() -> list[str]:
    """返回当前环境下实际可用的模型后端选项。

    mock 与 ollama 始终保留（本机是否可用由界面提示判断）；
    gemini / groq 只在配置了密钥时出现——避免未配置密钥的部署里，
    评审点开下拉就看到一个必然失败、且提示"未配置密钥"的选项。
    后端代码不删：配好密钥后选项会自动出现，无需改代码或重启应用。
    """
    options = [PROVIDER_MOCK, PROVIDER_OLLAMA]
    if GeminiProvider().is_available():
        options.append(PROVIDER_GEMINI)
    if GroqProvider().is_available():
        options.append(PROVIDER_GROQ)
    return options


def _date_only(value: Any) -> str:
    """把带时间的 ISO 时间戳裁剪成日期部分，仅用于紧凑展示，不改动底层数据。

    质量报告的日期摘要使用完整 ISO 时间戳（如 2024-05-01T00:00:00），
    放进指标卡会因过长而折行或截断；这里只裁剪展示文案。无值时沿用 "—"。
    """
    if value is None or str(value).strip() == "":
        return "—"
    text = str(value)
    return text.split("T")[0] if "T" in text else text


def _display_source_label(label: str | None, lang: str) -> str | None:
    """把内部中文数据来源标记映射为当前语言的展示文案（仅展示层映射）。

    session_state 中存储的标记保持中文不变；未知标记按原样展示，不虚构来源。
    """
    if lang != "en" or label is None:
        return label
    return _SOURCE_LABEL_EN.get(label, label)


def sidebar_data_status(
    label: str | None, filename: str | None, lang: str = "zh"
) -> str:
    """根据数据来源标记生成侧边栏常显状态文案（纯函数，便于测试）。

    规则（依据 session_state 中由加载流程写入的实际标记，不做猜测）：
        - "合成测试数据" → 强调非真实新闻的警示文案
        - "用户上传数据" → 标注用户上传及文件名
        - None（未导入）→ 未导入提示
        - 其他值 → 未知状态提示（不虚构来源）
    lang="zh" 为默认，与既有行为及测试断言完全一致。
    """
    if label == "合成测试数据":
        return t("status_synthetic", lang)
    if label == "用户上传数据":
        name = filename or ("unknown file" if lang == "en" else "未知文件")
        return t("status_user", lang, name=name)
    if label is None:
        return t("status_none", lang)
    unknown = "unknown" if lang == "en" else "未知"
    unknown_file = "unknown file" if lang == "en" else "未知文件"
    return t("status_other", lang, label=label or unknown, name=filename or unknown_file)


def _friendly_error(exc: Exception, lang: str = "zh") -> str:
    """把异常转换为用户可理解的提示，不暴露 traceback。

    异常消息本身来自数据层（中文），匹配逻辑与语言无关；
    仅返回的界面文案随 lang 变化，默认中文与既有测试一致。
    """
    if isinstance(exc, DataValidationError):
        msg = str(exc)
        if "缺少必需列" in msg:
            return t("err_missing_cols", lang)
        if "编码" in msg or "decode" in msg.lower():
            return t("err_encoding", lang)
        return t("err_format", lang, msg=msg)
    return t("err_generic", lang, exc=exc)


def _init_session_state() -> None:
    defaults = {
        "ingestion_result": None,
        "data_source_label": None,
        "upload_error": None,
        "current_filename": None,
        "_selected_filename": None,
        "imported_at": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _handle_upload(uploaded: Any, lang: str) -> None:
    """处理用户上传的 CSV 文件（由「开始导入」按钮触发），更新 session_state。

    每次按钮点击都会处理当前文件，不做 (name, size) 去重——
    同名同大小但内容不同的文件也能被正确重新处理。
    """
    try:
        result = load_uploaded_csv(uploaded)
        st.session_state["ingestion_result"] = result
        st.session_state["data_source_label"] = "用户上传数据"
        st.session_state["upload_error"] = None
        st.session_state["current_filename"] = uploaded.name
        st.session_state["imported_at"] = datetime.now()
    except Exception as exc:
        # 调试信息写入终端，不展示给用户
        print("[EchoMap] 上传处理异常：")
        traceback.print_exc()
        st.session_state["upload_error"] = _friendly_error(exc, lang)
        # 失败时不替换旧结果，界面会给出"当前显示的仍是上一份数据"的警告


def _handle_synthetic_demo(lang: str) -> None:
    """加载合成示例数据，更新 session_state。"""
    try:
        result = load_synthetic_demo()
        st.session_state["ingestion_result"] = result
        st.session_state["data_source_label"] = "合成测试数据"
        st.session_state["upload_error"] = None
        st.session_state["current_filename"] = "synthetic_news_corpus.csv"
        st.session_state["imported_at"] = datetime.now()
    except Exception as exc:
        print("[EchoMap] 加载合成示例异常：")
        traceback.print_exc()
        st.session_state["upload_error"] = _friendly_error(exc, lang)


def _show_provenance(
    result: dict, label: str | None, filename: str | None, lang: str
) -> dict:
    """数据档案区块：展示当前数据集的可追溯元信息（阶段 4.1）。

    返回 build_provenance 的结果 dict，供其他区块复用（避免重复计算指纹）。
    """
    prov = build_provenance(
        result,
        _display_source_label(label, lang),
        filename,
        st.session_state.get("imported_at"),
        lang=lang,
    )

    with st.expander(t("prov_expander", lang), expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric(t("prov_metric_raw", lang), prov["raw_rows"])
        col2.metric(t("prov_metric_clean", lang), prov["clean_rows"])
        col3.metric(t("prov_metric_fp", lang), str(prov["fingerprint"])[:8])
        st.write(f"{t('prov_dataset_name', lang)}{prov['dataset_name']}")
        st.write(f"{t('prov_source_label', lang)}{prov['source_label']}")
        st.write(f"{t('prov_imported_at', lang)}{prov['imported_at']}")
        st.write(f"{t('prov_date_range', lang)}{prov['date_min']} ~ {prov['date_max']}")
        st.write(f"{t('prov_cleaning_steps', lang)}{prov['cleaning_steps']}")
        st.caption(t("prov_caption", lang))
    return prov


def _show_quality_overview(result: dict, lang: str) -> None:
    """展示数据质量概览，数值均来自实际报告。"""
    raw_report = result["raw_report"]
    clean_report = result["clean_report"]

    st.subheader(t("qo_title", lang))

    col1, col2, col3 = st.columns(3)
    col1.metric(t("qo_metric_raw", lang), raw_report["rows"])
    col2.metric(t("qo_metric_clean", lang), clean_report["rows"])
    col3.metric(
        t("qo_metric_removed", lang),
        raw_report["rows"] - clean_report["rows"],
    )

    st.write(t("qo_dup", lang, n=raw_report["duplicate_rows"]))

    # 必需字段缺失情况
    st.markdown(t("qo_missing_header", lang))
    req_cols = ["title", "content", "source"]
    raw_missing = raw_report.get("missing_required_columns", {})
    clean_missing = clean_report.get("missing_required_columns", {})
    rows = []
    for col in req_cols:
        rows.append(
            {
                t("qo_col_field", lang): col,
                t("qo_col_raw", lang): raw_missing.get(col, "—"),
                t("qo_col_clean", lang): clean_missing.get(col, "—"),
            }
        )
    st.table(rows)

    # 日期字段摘要
    raw_date = raw_report.get("date_summary")
    if raw_date is not None:
        st.markdown(t("qo_date_header", lang))
        dcol1, dcol2, dcol3, dcol4 = st.columns(4)
        dcol1.metric(t("qo_valid", lang), raw_date.get("valid", 0))
        dcol2.metric(t("qo_missing", lang), raw_date.get("missing", 0))
        dcol3.metric(t("qo_invalid", lang), raw_date.get("invalid", 0))
        dcol4.metric(
            t("qo_range", lang),
            f"{_date_only(raw_date.get('min'))} ~ {_date_only(raw_date.get('max'))}",
        )


def _show_data_preview(result: dict, lang: str) -> None:
    """展示清洗后数据的前若干行。"""
    st.subheader(t("dp_title", lang))
    clean_df = result["clean"]
    st.dataframe(clean_df.head(20), use_container_width=True)
    st.caption(t("dp_caption", lang, n=len(clean_df)))


def _render_chart(series, title: str, xlabel: str, ylabel: str, font_name, lang: str) -> None:
    """渲染柱状图：matplotlib 优先（中文字体可用时），否则降级为 st.bar_chart。

    字体不可用时降级为 Streamlit 原生图表（浏览器渲染中文，不依赖系统字体），
    保证页面不因字体问题报错。
    """
    fig = make_bar_chart(series, title, xlabel, ylabel, font_name=font_name)
    if fig is not None:
        st.pyplot(fig)
    else:
        # 降级：Streamlit 原生图表（中文由浏览器渲染）
        st.bar_chart(series)
        st.caption(t("chart_fallback", lang))


def _dataset_tag_caption(result: dict, lang: str) -> str:
    """生成当前区块的数据集标识文案（复用同一数据指纹机制）。"""
    return dataset_tag(
        build_provenance(
            result,
            _display_source_label(st.session_state["data_source_label"], lang),
            st.session_state["current_filename"],
            st.session_state.get("imported_at"),
            lang=lang,
        ),
        lang=lang,
    )


def _show_overview(result: dict, lang: str) -> None:
    """数据概览：基础指标 + 来源分布 + 日期分布。

    所有数值均来自当前清洗后 DataFrame，空状态有明确提示。
    """
    clean_df = result["clean"]

    st.subheader(t("ov_title", lang))
    st.caption(_dataset_tag_caption(result, lang))

    if clean_df.empty:
        st.info(t("ov_empty", lang))
        return

    stats = compute_overview_stats(clean_df)

    # —— 基础指标 ——
    col1, col2, col3 = st.columns(3)
    col1.metric(t("ov_articles", lang), stats["rows"])
    col2.metric(t("ov_sources", lang), stats["n_sources"])
    if stats["date_min"] and stats["date_max"]:
        col3.metric(t("ov_range", lang), f"{stats['date_min']} ~ {stats['date_max']}")
    else:
        col3.metric(t("ov_range", lang), t("ov_no_date", lang))

    # —— 字段完整性 ——
    st.markdown(t("ov_completeness_header", lang))
    if stats["completeness"]:
        comp_rows = [
            {
                t("ov_col_field", lang): col,
                t("ov_col_nonempty", lang): n,
                t("ov_col_total", lang): stats["rows"],
            }
            for col, n in stats["completeness"].items()
        ]
        st.table(comp_rows)
    else:
        st.caption(t("ov_no_required", lang))

    # —— 正文长度统计 ——
    st.markdown(t("ov_len_header", lang))
    cl = stats["content_length"]
    if cl is not None:
        lcol1, lcol2, lcol3, lcol4 = st.columns(4)
        lcol1.metric(t("ov_min", lang), cl["min"])
        lcol2.metric(t("ov_max", lang), cl["max"])
        lcol3.metric(t("ov_mean", lang), cl["mean"])
        lcol4.metric(t("ov_median", lang), cl["median"])
    else:
        st.caption(t("ov_no_content", lang))

    # —— 分布图表 ——
    font_name = find_cjk_font()

    st.markdown(t("ov_src_header", lang))
    src_dist = source_distribution(clean_df)
    if src_dist.empty:
        st.info(t("ov_src_none", lang))
    elif len(src_dist) == 1:
        st.info(t("ov_src_single", lang, src=src_dist.index[0], n=int(src_dist.iloc[0])))
    else:
        _render_chart(
            src_dist,
            t("chart_src_title", lang),
            t("chart_src_x", lang),
            t("chart_y_articles", lang),
            font_name,
            lang,
        )

    st.markdown(t("ov_date_header", lang))
    date_dist = date_distribution(clean_df)
    if date_dist.empty:
        st.info(t("ov_date_none", lang))
    else:
        date_dist.index = date_dist.index.astype(str)
        _render_chart(
            date_dist,
            t("chart_date_title", lang),
            t("chart_date_x", lang),
            t("chart_y_articles", lang),
            font_name,
            lang,
        )


def _show_clustering(result: dict, lang: str) -> None:
    """主题聚类分析展示。

    基于当前清洗后数据执行聚类，展示各主题数量、占比、代表关键词
    及主题内文章列表。聚类结果使用 session_state 缓存，以数据指纹
    + n_clusters 为键，避免切换数据集后沿用旧结果。

    重要提示：聚类编号是算法生成的探索性分组，不是预先验证的新闻类别。
    """
    clean_df = result["clean"]

    st.subheader(t("cl_title", lang))
    st.caption(_dataset_tag_caption(result, lang))
    st.caption(t("cl_caption", lang))

    if clean_df.empty:
        st.info(t("cl_empty", lang))
        return

    # 聚类数滑块：范围 2 ~ max(2, 记录数)，默认 3（不超过记录数）
    max_n = max(2, len(clean_df))
    default_n = min(3, max_n)
    n_clusters = st.slider(
        t("cl_slider", lang),
        min_value=2,
        max_value=max_n,
        value=default_n,
        step=1,
        key="cluster_n_slider",  # 显式 key：来源对比区块需读取同一聚类数，保证两区块主题一致
        help=t("cl_slider_help", lang),
    )

    # 数据指纹 + 算法版本 + 词表指纹 + n_clusters 作为缓存键：
    # 切换数据集、算法更新或词表增删词条后自动失效，不沿用旧结果
    fp = data_fingerprint(clean_df)
    cache_key = (
        f"clustering_v{CLUSTERING_PIPELINE_VERSION}"
        f"_{wordlists_fingerprint()}_{fp}_{n_clusters}"
    )

    if cache_key not in st.session_state:
        try:
            cluster_result = compute_clusters(clean_df, n_clusters=n_clusters)
            st.session_state[cache_key] = cluster_result
        except Exception as exc:
            st.error(t("cl_fail", lang, e=exc))
            return

    cr = st.session_state[cache_key]

    # 算法提示（note 由算法层生成，当前仅中文，属已知边界）
    if cr["note"]:
        st.warning(cr["note"])

    # 未参与聚类的文章
    unclustered = unclustered_count(cr)
    if unclustered > 0:
        st.info(t("cl_unclustered", lang, n=unclustered))

    # 主题汇总
    summary = cluster_summary(cr)
    if not summary:
        st.info(t("cl_no_result", lang))
        return

    st.markdown(t("cl_summary_header", lang))
    for item in summary:
        kw_text = "、".join(item["keywords"][:5]) or "—"
        st.write(
            t(
                "cl_item",
                lang,
                c=item["cluster"],
                n=item["count"],
                r=f"{item['ratio']:.1%}",
                kw=kw_text,
            )
        )

    # 主题规模柱状图
    st.markdown(t("cl_dist_header", lang))
    sizes = pd.Series(
        {s["cluster"]: s["count"] for s in summary}
    )
    font_name = find_cjk_font()
    _render_chart(
        sizes,
        t("chart_cl_title", lang),
        t("chart_cl_x", lang),
        t("chart_y_articles", lang),
        font_name,
        lang,
    )

    # 主题选择器 + 文章列表
    cluster_ids = [s["cluster"] for s in summary]
    selected_cluster = st.selectbox(
        t("cl_select", lang),
        options=cluster_ids,
        format_func=lambda x: t("cl_select_fmt", lang, x=x, n=sizes[x]),
    )

    if selected_cluster is not None:
        articles = articles_in_cluster(cr, selected_cluster)
        st.markdown(t("cl_articles_md", lang, c=selected_cluster, n=len(articles)))
        if articles.empty:
            st.caption(t("cl_articles_empty", lang))
        else:
            st.dataframe(articles, use_container_width=True, hide_index=True)


def _goto_article(fp: str, pos: int) -> None:
    """相似新闻列表中点击「查看」时的回调：跳转到指定文章。"""
    st.session_state[f"article_select_{fp}"] = pos


def _show_source_compare(result: dict, lang: str) -> None:
    """多来源对比区块（阶段 4.3）：来源关键词对比 + 来源×主题分布。

    所有统计仅描述当前数据集内的内容差异；差异不代表媒体立场、偏见、
    传播路径或因果关系。
    """
    clean_df = result["clean"]
    fp = data_fingerprint(clean_df)

    st.subheader(t("sc_title", lang))
    st.caption(_dataset_tag_caption(result, lang))
    st.caption(t("sc_caption", lang))

    if clean_df.empty:
        st.info(t("sc_empty", lang))
        return

    # —— 模块 A：来源关键词对比 ——
    st.markdown(t("sc_kw_header", lang))
    # 最少文章数可调：默认 1 保证小数据集（如合成示例）可见对比效果；
    # 调高后小样本来源会被跳过并给出警告
    min_articles = st.slider(
        t("sc_min_slider", lang),
        min_value=1,
        max_value=5,
        value=1,
        step=1,
        key=f"cmp_min_articles_{fp}",  # 含数据指纹：切换数据集后自动重置
        help=t("sc_min_help", lang),
    )
    compare = source_keyword_compare(
        clean_df, top_k=5, min_articles=min_articles, max_sources=8
    )

    if compare["note"]:
        st.warning(compare["note"])
    if not compare["per_source"]:
        st.info(t("sc_no_kw", lang))
    else:
        source_names = [item["source"] for item in compare["per_source"]]
        max_cols = 3
        for start in range(0, len(source_names), max_cols):
            chunk = compare["per_source"][start : start + max_cols]
            cols = st.columns(len(chunk))
            for col, item in zip(cols, chunk):
                with col:
                    st.markdown(
                        t("sc_source_md", lang, src=item["source"], n=item["article_count"])
                    )
                    if item["keywords"].empty:
                        st.caption(t("sc_kw_empty", lang))
                    else:
                        st.dataframe(
                            item["keywords"][["rank", "keyword", "weight"]],
                            hide_index=True,
                        )
        st.caption(t("sc_weight_caption", lang))

    # —— 模块 B：来源 × 聚类主题分布 ——
    st.markdown(t("sc_cross_header", lang))
    n_clusters = st.session_state.get("cluster_n_slider", 3)
    cluster_result = st.session_state.get(f"clustering_{fp}_{n_clusters}")
    if cluster_result is None:
        try:
            cluster_result = compute_clusters(clean_df, n_clusters=n_clusters)
        except Exception:
            cluster_result = None

    if cluster_result is None:
        st.info(t("sc_no_cluster", lang))
        return

    cross = source_cluster_crosstab(clean_df, cluster_result["labels"])
    if cross["counts"].empty:
        st.info(cross["note"])
        return

    if cross["note"]:
        st.warning(cross["note"])

    left, right = st.columns(2)
    with left:
        st.markdown(t("sc_counts_md", lang))
        st.dataframe(cross["counts"], use_container_width=True)
    with right:
        st.markdown(t("sc_pct_md", lang))
        st.dataframe(cross["row_pct"].round(4), use_container_width=True)

    st.bar_chart(cross["counts"])
    st.caption(t("sc_chart_caption", lang))


def _show_article_explorer(result: dict, lang: str) -> None:
    """新闻详情与相似新闻展示。

    通过行下标选择文章（区分标题重复），展示详情、关键词、TextRank 摘要、
    相似新闻列表，并支持继续探索。
    """
    clean_df = result["clean"]

    st.subheader(t("ae_title", lang))
    st.caption(_dataset_tag_caption(result, lang))
    st.caption(t("ae_caption", lang))

    if clean_df.empty:
        st.info(t("ae_empty", lang))
        return

    fp = data_fingerprint(clean_df)
    # 用数据指纹作为选择器 key 的一部分：数据集切换后旧选择自动失效
    select_key = f"article_select_{fp}"

    def _fmt(i: int) -> str:
        row = clean_df.iloc[i]
        title = str(row.get("title") or t("ae_no_title", lang))
        source = str(row.get("source") or t("ae_unknown_source", lang))
        return f"#{i} ｜ {title} ｜ {source}"

    idx = st.selectbox(
        t("ae_select", lang),
        options=list(range(len(clean_df))),
        format_func=_fmt,
        key=select_key,
    )

    # ---- 详情面板 ----
    try:
        detail = get_article_detail(clean_df, idx, top_k=10, top_n=3)
    except Exception as exc:
        st.error(t("ae_analyze_fail", lang, e=exc))
        return

    st.markdown(f"### {field_or_placeholder(clean_df.iloc[idx], 'title', t('ae_no_title', lang))}")
    st.write(
        t(
            "ae_source_line",
            lang,
            v=field_or_placeholder(clean_df.iloc[idx], "source", t("ae_unknown_source", lang)),
        )
    )
    st.write(
        t(
            "ae_date_line",
            lang,
            v=field_or_placeholder(clean_df.iloc[idx], "published_at", t("ae_unknown_date", lang)),
        )
    )
    st.markdown("---")

    with st.expander(t("ae_body_expander", lang), expanded=True):
        content_text = field_or_placeholder(clean_df.iloc[idx], "content", t("ae_no_content", lang))
        st.write(content_text)

    # 关键词
    st.markdown(t("ae_kw_header", lang))
    st.caption(t("ae_kw_caption", lang))
    if detail["keywords"].empty:
        st.info(t("ae_kw_empty", lang))
    else:
        st.dataframe(detail["keywords"], use_container_width=True, hide_index=True)

    # 摘要
    st.markdown(t("ae_sum_header", lang))
    st.caption(t("ae_sum_caption", lang))
    summary_dict = detail["summary"]
    if not summary_dict["summary"]:
        st.info(t("ae_sum_empty", lang) if not summary_dict["note"] else summary_dict["note"])
    else:
        for i, sentence in enumerate(summary_dict["summary"], 1):
            st.write(f"{i}. {sentence}")
        if summary_dict["note"]:
            st.caption(t("ae_sum_note", lang, note=summary_dict["note"]))

    st.markdown("---")

    # ---- 相似新闻 ----
    st.markdown(t("ae_sim_header", lang))
    max_top = max(1, len(clean_df) - 1)
    top_n = st.slider(
        t("ae_sim_slider", lang),
        min_value=1,
        max_value=max_top,
        value=min(3, max_top),
        step=1,
        key=f"sim_topn_{fp}",
    )

    sim_df = get_similar_articles(clean_df, idx, top_n=top_n)
    if sim_df.empty:
        st.info(t("ae_sim_empty", lang))
        return

    for _, row in sim_df.iterrows():
        pos = int(row["row_index"])
        col1, col2 = st.columns([6, 2])
        with col1:
            st.markdown(
                t(
                    "ae_sim_row",
                    lang,
                    title=row["title"],
                    source=row["source"],
                    date=row["published_at"][:10] if row["published_at"] else "—",
                    sim=f"{row['similarity']:.4f}",
                )
            )
        with col2:
            if 0 <= pos < len(clean_df):
                st.button(
                    t("ae_view_btn", lang),
                    key=f"goto_{fp}_{pos}",
                    on_click=_goto_article,
                    args=(fp, pos),
                )
    st.caption(t("ae_sim_caption", lang))


def _show_topic_recommendations(result: dict, lang: str) -> dict | None:
    """AI 推荐选题区块（阶段 5.1，本地规则，不调用任何在线 AI 服务）。

    复用主题聚类区块的同一份聚类缓存（相同缓存键，含算法版本 + 词表指纹 +
    数据指纹 + 聚类数），并复用语料级 TF-IDF 关键词结果；排序规则在界面
    完整公开。合成数据全程标注"非真实热点"。

    返回当前选中的选题字典（无法生成选题时返回 None，供下方文案区块使用）。
    """
    clean_df = result["clean"]

    st.subheader(t("st_title", lang))
    st.caption(_dataset_tag_caption(result, lang))
    st.caption(t("st_caption", lang))

    if st.session_state.get("data_source_label") == "合成测试数据":
        st.warning(t("st_synthetic_notice", lang))

    if clean_df.empty:
        st.info(t("st_empty", lang))
        return None

    # 与主题聚类区块共享同一聚类结果（相同缓存键），不重复计算
    fp = data_fingerprint(clean_df)
    n_clusters = st.session_state.get("cluster_n_slider", 3)
    cache_key = (
        f"clustering_v{CLUSTERING_PIPELINE_VERSION}"
        f"_{wordlists_fingerprint()}_{fp}_{n_clusters}"
    )
    if cache_key not in st.session_state:
        try:
            st.session_state[cache_key] = compute_clusters(clean_df, n_clusters=n_clusters)
        except Exception as exc:
            st.error(t("cl_fail", lang, e=exc))
            return None
    cluster_result = st.session_state[cache_key]

    # 语料级关键词权重（关键词强度因子依据），按数据指纹 + 词表指纹缓存
    kw_cache_key = f"topic_corpus_kw_{wordlists_fingerprint()}_{fp}"
    if kw_cache_key not in st.session_state:
        texts = combine_text_fields(clean_df, ("title", "content"))
        st.session_state[kw_cache_key] = keywords_for_corpus(texts, top_k=10)

    rec = build_topic_recommendations(
        clean_df, cluster_result, st.session_state[kw_cache_key], top_n=5
    )

    if cluster_result.get("note"):
        st.warning(cluster_result["note"])
    unclustered = unclustered_count(cluster_result)
    if unclustered > 0:
        st.info(t("cl_unclustered", lang, n=unclustered))
    if rec["small_sample"]:
        st.info(t("st_note_small_sample", lang, n=rec["clustered_documents"]))
    if rec["no_dates"]:
        st.info(t("st_note_no_dates", lang))
    if not rec["kw_factor_available"]:
        st.info(t("st_note_kw_na", lang))
    if not rec["recommendations"]:
        st.info(t("st_empty", lang))
        return None

    # 排序规则与边界声明（完全公开，可复现）
    st.markdown(t("st_rule_header", lang))
    st.markdown(t("st_rule_md", lang))
    st.caption(t("st_scope_caption", lang))

    labels = [
        topic_option_label(item, rank, lang)
        for rank, item in enumerate(rec["recommendations"], start=1)
    ]
    options = list(range(len(labels)))
    idx = st.selectbox(
        t("st_title", lang),
        options=options,
        format_func=lambda i: labels[i],
        key=f"st_topic_select_{fp}",
    )
    chosen = rec["recommendations"][idx]

    # 选题详情：标题（关键词构成）、推荐理由与数据依据
    topic_title = topic_keywords_label(chosen) or t("st_topic_untitled", lang)
    st.markdown(f"### {topic_title}")
    st.write(reason_text(chosen, lang))

    # 排序因子明细
    st.markdown(t("st_factors_header", lang))
    st.table(factor_rows(rec["recommendations"], lang))

    # 关联新闻（可溯源：标题/来源/日期，与聚类区块同一数据）
    rows = article_rows(chosen, lang)
    if rows:
        st.markdown(
            t("st_articles_header", lang, n=len(rows), max=MAX_ARTICLES_PER_TOPIC)
        )
        st.table(rows)

    return chosen


def _show_copywriting(result: dict, lang: str, chosen_rec: dict) -> None:
    """AI 文案生成区块（可插拔本地后端；界面内可切换，无需重启）。

    - 平台/受众/风格选择 -> build_request -> provider.render -> 可编辑预览；
    - 后端选择器（mock / ollama / gemini / groq）在此直接生效：mock 输出带
      【模拟】标记的占位文案；ollama 经本机 127.0.0.1:11434 调用本地模型；
      gemini / groq 经各自官方接口调用在线模型（均为免费额度）。
      选项按环境动态生成：未配置密钥的在线后端不出现在下拉里；
    - mock 不发任何请求，ollama 只访问本机回环地址，gemini / groq 会把提示词
      发送至对应厂商接口——各模式的差异在界面上明确标注，不做模糊处理。
    """
    fp = data_fingerprint(result["clean"])

    st.subheader(t("cp_title", lang))
    st.caption(t("cp_caption", lang))

    # —— 模型后端选择（会话内切换即生效；环境变量仅作为默认值）——
    # 选项按当前环境动态生成：未配置密钥的在线后端不出现在下拉里。
    options = _backend_options()
    env_default = get_provider().name
    if env_default not in options:
        env_default = PROVIDER_MOCK
    backend = st.selectbox(
        t("cp_provider_label", lang),
        options=options,
        index=options.index(env_default),
        format_func=lambda b: t(f"cp_backend_{b}", lang),
        key="cp_backend",
    )
    if backend == PROVIDER_OLLAMA:
        model = st.text_input(
            t("cp_model_label", lang),
            value=os.environ.get(ENV_OLLAMA_MODEL, ""),
            key="cp_model_name",
        )
        provider = OllamaProvider(model=model)
        if provider.is_available():
            st.success(t("cp_backend_online", lang))
        else:
            st.warning(t("cp_backend_offline", lang))
        st.warning(t("cp_ollama_notice", lang))
    elif backend == PROVIDER_GEMINI:
        model = st.text_input(
            t("cp_gemini_model_label", lang),
            value=os.environ.get(ENV_GEMINI_MODEL, ""),
            key="cp_gemini_model_name",
        )
        provider = GeminiProvider(model=model or None)
        if provider.is_available():
            st.success(t("cp_gemini_ready", lang))
        else:
            st.warning(t("cp_gemini_no_key", lang))
        st.warning(t("cp_gemini_notice", lang))
    elif backend == PROVIDER_GROQ:
        model = st.text_input(
            t("cp_groq_model_label", lang),
            value=os.environ.get(ENV_GROQ_MODEL, ""),
            key="cp_groq_model_name",
        )
        provider = GroqProvider(model=model or None)
        if provider.is_available():
            st.success(t("cp_groq_ready", lang))
        else:
            st.warning(t("cp_groq_no_key", lang))
        st.warning(t("cp_groq_notice", lang))
    else:
        provider = MockProvider()
        st.warning(t("cp_mock_notice", lang))

    cluster_tag = chosen_rec.get("cluster", "x")
    platform = st.selectbox(
        t("cp_platform", lang),
        options=list(PLATFORMS),
        format_func=lambda p: t(f"cp_platform_{p}", lang),
        key=f"cp_platform_{fp}",
    )
    audience = st.selectbox(
        t("cp_audience", lang),
        options=list(AUDIENCES),
        format_func=lambda a: t(f"cp_audience_{a}", lang),
        key=f"cp_audience_{fp}",
    )
    style = st.selectbox(
        t("cp_style", lang),
        options=list(STYLES),
        format_func=lambda s: t(f"cp_style_{s}", lang),
        key=f"cp_style_{fp}",
    )

    # 文案内容存"普通会话键"（store_key，不受组件消失清理影响）；
    # 编辑框用独立组件键，实例化前按需同步：
    #   - 本轮刚点击"生成"（sync 标记）→ 强制显示新文案；
    #   - 组件键不在会话中（首次渲染/平台切回后组件状态被清理）→ 恢复 store；
    #   - 其余情况不做同步，避免覆盖用户正在编辑的内容；
    # 编辑后回写 store，切换平台/选题互不残留
    store_key = f"cp_store_{fp}_{platform}_{cluster_tag}"
    widget_key = f"cp_w_{fp}_{platform}_{cluster_tag}"
    sync_key = f"cp_sync_{fp}_{platform}_{cluster_tag}"

    with st.expander(t("cp_prompt_expander", lang)):
        try:
            request = build_request(platform, chosen_rec, audience, style)
            st.code(build_prompt(request), language=None)
        except Exception as exc:
            st.error(t("cp_fail", lang, e=exc))

    if st.button(
        t("cp_generate_btn", lang),
        key=f"cp_btn_{fp}_{platform}_{cluster_tag}",
    ):
        try:
            request = build_request(platform, chosen_rec, audience, style)
            with st.spinner(t("cp_generating", lang)):
                st.session_state[store_key] = provider.render(request)
            st.session_state[sync_key] = True
        except Exception as exc:
            st.error(t("cp_fail", lang, e=exc))

    if (st.session_state.get(sync_key) or widget_key not in st.session_state) and (
        store_key in st.session_state
    ):
        st.session_state[widget_key] = st.session_state[store_key]
    st.session_state[sync_key] = False

    edited = st.text_area(
        t("cp_editor", lang),
        key=widget_key,
        height=360,
    )
    st.session_state[store_key] = edited

    # —— 敏感信息检测与脱敏（本地规则，不联网）：仅"通过"才允许导出 ——
    if edited:
        report = analyze_text(edited)
        st.markdown(t("safety_header", lang))
        if report.passed:
            st.success(t("safety_pass", lang))
            st.caption(t("cp_copy_hint", lang))
            st.code(edited, language=None)
        else:
            if report.status == "fail":
                st.error(t("safety_fail", lang, n=len(report.findings)))
            else:
                st.warning(t("safety_uncertain", lang))
            if report.findings:
                st.markdown(t("safety_items_header", lang))
                for category, count in category_counts(report):
                    st.write(f"- {t(f'safety_cat_{category}', lang)}: {count}")
            st.caption(t("safety_masked_preview", lang))
            st.text(report.masked_text)
            st.caption(t("safety_export_disabled", lang))


def main() -> None:
    st.set_page_config(page_title="EchoMap", layout="wide")
    _inject_global_css()
    _init_session_state()

    # —— 语言切换（侧边栏顶部；English 为默认，供英文授课项目评审使用）——
    lang_choice = st.sidebar.radio(
        "Language / 语言",
        options=["English", "中文"],
        horizontal=True,
        key="lang_radio",
    )
    lang = "en" if lang_choice == "English" else "zh"

    # —— 页面切换：仪表板（默认，原有功能不变）/ AI 推荐选题（阶段 5.1）——
    page = st.sidebar.radio(
        t("st_page_radio", lang),
        options=["dashboard", "strategist"],
        format_func=lambda p: (
            t("st_page_dashboard", lang)
            if p == "dashboard"
            else t("st_page_strategist", lang)
        ),
        key="page_radio",
    )

    _render_hero(lang)
    st.markdown(t("positioning_md", lang))

    # —— 关于本研究（可折叠静态说明，不依赖数据，不改变分析流程）——
    with st.expander(t("about_expander", lang)):
        st.markdown(t("about_rq_md", lang))
        st.markdown(t("about_motivation_md", lang))
        st.markdown(t("about_data_md", lang))
        st.markdown(t("about_methods_md", lang))
        st.markdown(t("about_cancannot_md", lang))
        st.caption(t("about_more_caption", lang))

    st.divider()

    # —— 侧边栏：数据导入 ——
    with st.sidebar:
        st.header(t("sb_import_header", lang))

        # 常显数据状态标记：随实际加载结果动态生成，合成数据全程可见
        st.markdown(
            f"**{sidebar_data_status(st.session_state['data_source_label'], st.session_state['current_filename'], lang)}**"
        )

        uploaded = st.file_uploader(
            t("sb_upload_label", lang),
            type=["csv"],
            help=t("sb_upload_help", lang),
        )

        # 用户选择的文件变化时，清除上一次导入留下的错误提示，避免误导
        selected_name = uploaded.name if uploaded is not None else None
        if st.session_state["_selected_filename"] != selected_name:
            st.session_state["_selected_filename"] = selected_name
            st.session_state["upload_error"] = None

        if uploaded is not None:
            st.caption(t("sb_selected", lang, name=uploaded.name, size=uploaded.size))
            if st.button(t("sb_import_btn", lang), type="primary", key="import_btn"):
                _handle_upload(uploaded, lang)

        st.divider()
        if st.button(t("sb_demo_btn", lang), type="secondary", key="demo_btn"):
            _handle_synthetic_demo(lang)

    # —— 错误提示 ——
    if st.session_state["upload_error"]:
        st.error(st.session_state["upload_error"])
        if st.session_state["ingestion_result"] is not None:
            st.warning(t("err_import_kept_old", lang))

    # —— 数据来源标记 ——
    result = st.session_state["ingestion_result"]
    if result is None:
        st.info(t("info_no_data", lang))
        return

    label = st.session_state["data_source_label"]
    filename = st.session_state["current_filename"]
    display_label = _display_source_label(label, lang)
    st.info(t("info_current_source", lang, label=display_label, filename=filename))

    # —— 页面分流：AI 推荐选题页不渲染仪表板区块（原有功能保持不变）——
    if page == "strategist":
        with st.container(border=True):
            _card()
            chosen_rec = _show_topic_recommendations(result, lang)
        if chosen_rec is not None:
            _module_divider()
            with st.container(border=True):
                _card()
                _show_copywriting(result, lang, chosen_rec)
        else:
            st.info(t("cp_empty_hint", lang))
        return

    if label == "合成测试数据":
        st.caption(t("caption_synthetic_notice", lang))

    # 用标签页把 7 个区块归入 3 组：首屏只展示一组，避免纵向堆叠造成的疲劳。
    # 模块一个都不删，只是分组展示；每个区块仍包进卡片容器。
    tab_profile, tab_topics, tab_articles = st.tabs(
        [
            t("dash_tab_profile", lang),
            t("dash_tab_topics", lang),
            t("dash_tab_articles", lang),
        ]
    )

    with tab_profile:
        with st.container(border=True):
            _card()
            _show_provenance(result, label, filename, lang)
        _module_divider()
        with st.container(border=True):
            _card()
            _show_quality_overview(result, lang)
        _module_divider()
        with st.container(border=True):
            _card()
            _show_data_preview(result, lang)

    with tab_topics:
        with st.container(border=True):
            _card()
            _show_overview(result, lang)
        _module_divider()
        with st.container(border=True):
            _card()
            _show_clustering(result, lang)
        _module_divider()
        with st.container(border=True):
            _card()
            _show_source_compare(result, lang)

    with tab_articles:
        with st.container(border=True):
            _card()
            _show_article_explorer(result, lang)


if __name__ == "__main__":
    main()
