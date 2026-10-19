"""AI 选题推荐界面辅助（src.ui.strategist_view）—— 阶段 5.1。

设计原则（与既有 src.ui 辅助模块一致）：
    - 全部为纯函数，不依赖 Streamlit，便于单元测试；
    - 数值与内容均来自 build_topic_recommendations 的实际结果，
      缺失字段显示明确占位词，不编造；
    - 界面文案统一走 src.ui.i18n.t（中英双语）。
"""

from __future__ import annotations

import pandas as pd

from src.ui.i18n import t


def format_date(value: object) -> str | None:
    """把日期值（Timestamp / 字符串 / NaT / None）格式化为 YYYY-MM-DD。

    无法解析时返回 None（界面显示"未知日期"占位），不猜测。
    """
    if value is None:
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")


def topic_keywords_label(rec: dict, max_keywords: int = 3) -> str:
    """把选题代表关键词合并为短标签（最多前 max_keywords 个）。

    关键词来自聚类结果（预处理源头已过滤）；无关键词时返回空字符串，
    由界面显示"未命名主题"占位。
    """
    keywords = [str(k) for k in rec.get("keywords", []) if str(k)]
    return " · ".join(keywords[:max_keywords])


def topic_option_label(rec: dict, rank: int, lang: str = "zh") -> str:
    """生成选题选择器选项文案：#序号 关键词标签（N 篇 · 占比）。"""
    kw_label = topic_keywords_label(rec)
    if not kw_label:
        kw_label = t("st_topic_untitled", lang)
    return t(
        "st_option",
        lang,
        rank=rank,
        kw=kw_label,
        n=rec.get("count", 0),
        ratio=f"{float(rec.get('ratio', 0)):.1%}",
    )


def reason_text(rec: dict, lang: str = "zh") -> str:
    """生成一条选题的推荐理由（含数据依据，双语）。

    主题内最晚日期不可用时显示占位词，不虚构日期。
    """
    kw_label = topic_keywords_label(rec) or t("st_topic_untitled", lang)
    latest = None
    dates = [a.get("date") for a in rec.get("articles", []) if a.get("date")]
    if dates:
        latest = max(dates)
    if latest is None:
        latest = t("st_unknown_date", lang)
    return t(
        "st_reason",
        lang,
        n=rec.get("count", 0),
        ratio=f"{float(rec.get('ratio', 0)):.1%}",
        kw=kw_label,
        date=latest,
    )


def factor_value_text(value: float | None, lang: str = "zh") -> str:
    """把单个排序因子格式化为展示文本；None（不可用）显示占位词。"""
    if value is None:
        return t("st_factor_na", lang)
    return f"{float(value):.3f}"


def factor_rows(recommendations: list[dict], lang: str = "zh") -> list[dict]:
    """把各选题的三因子与综合排序值整理为表格行（供 st.table 展示）。"""
    rows: list[dict] = []
    for rank, rec in enumerate(recommendations, start=1):
        kw_label = topic_keywords_label(rec) or t("st_topic_untitled", lang)
        rows.append(
            {
                t("st_col_topic", lang): f"#{rank} {kw_label}",
                t("st_col_share", lang): factor_value_text(rec.get("factor_share"), lang),
                t("st_col_kw", lang): factor_value_text(rec.get("factor_kw"), lang),
                t("st_col_recency", lang): factor_value_text(rec.get("factor_recency"), lang),
                t("st_col_score", lang): factor_value_text(rec.get("score"), lang),
            }
        )
    return rows


def article_rows(rec: dict, lang: str = "zh") -> list[dict]:
    """把选题关联新闻整理为表格行（标题、来源、日期），缺失字段用占位词。"""
    no_title = t("ae_no_title", lang)
    unknown_source = t("ae_unknown_source", lang)
    unknown_date = t("ae_unknown_date", lang)
    rows: list[dict] = []
    for article in rec.get("articles", []):
        title = str(article.get("title") or "").strip()
        source = str(article.get("source") or "").strip()
        date = article.get("date")
        rows.append(
            {
                t("st_col_title", lang): title or no_title,
                t("st_col_source", lang): source or unknown_source,
                t("st_col_date", lang): date or unknown_date,
            }
        )
    return rows
