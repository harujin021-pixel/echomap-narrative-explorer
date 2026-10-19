"""新闻详情与相似新闻辅助模块（src.ui.article_view）。

阶段 3.3 功能：为 Streamlit 界面提供单篇新闻详情与相似新闻的纯函数封装。

设计原则：
    - 全部为纯函数，不依赖 Streamlit，便于单元测试。
    - 文章定位使用**行下标**（row_index），标题重复时仍能区分不同文章。
    - 关键词、摘要、相似度分别复用 Phase 2 的 keywords / summarization /
      similarity 模块，本模块不重复实现算法，只做数据组装与行映射。
    - 相似度结果需要映射回原始 DataFrame 的行位置：优先按 id 列匹配；
      无 id 列或 id 为空时按 title+source 兜底（清洗流程已删除完全重复行，
      title+source 组合可视为近似唯一，但仍存在理论上的歧义，属已知局限）。
    - 文本相似度**不代表**事实一致、转载关系或媒体立场一致。
"""

from __future__ import annotations

import pandas as pd

from src.analysis.keywords import keywords_for_document
from src.analysis.similarity import find_similar_articles
from src.analysis.summarization import summarize

ID_COL = "id"

SIMILAR_COLUMNS = [
    "row_index",
    "matched_id",
    "title",
    "source",
    "published_at",
    "similarity",
    "rank",
]


def article_text(row: pd.Series) -> str:
    """把一行数据拼接为分析文本（标题 + 空格 + 正文）。"""
    title = str(row.get("title") or "").strip()
    content = str(row.get("content") or "").strip()
    return f"{title} {content}".strip()


def field_or_placeholder(row: pd.Series, column: str, placeholder: str) -> str:
    """读取字段值；列缺失、为空或 NaT 时返回占位提示，不编造内容。"""
    if column not in row.index:
        return placeholder
    value = row[column]
    if value is None:
        return placeholder
    text = str(value).strip()
    if text == "" or text == "NaT":
        return placeholder
    return text


def get_article_detail(
    df: pd.DataFrame, row_index: int, top_k: int = 10, top_n: int = 3
) -> dict:
    """获取单篇新闻的详情分析结果。

    返回字段：
        row_index     行下标（稳定定位键）
        news_id       id 列值（无 id 列或为空时为 None）
        title/source/published_at/content  原始字段（缺失时为空字符串）
        keywords      关键词 DataFrame（rank/keyword/weight，可能为空）
        summary       summarize() 的结果字典（含 summary/note 等）
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("get_article_detail 需要 pandas.DataFrame")
    if not 0 <= row_index < len(df):
        raise IndexError(f"row_index 越界: {row_index}（共 {len(df)} 行）")

    row = df.iloc[row_index]
    text = article_text(row)

    news_id = row.get(ID_COL) if ID_COL in df.columns else None
    if news_id is not None and str(news_id).strip() == "":
        news_id = None

    published_at = ""
    if "published_at" in df.columns:
        value = row["published_at"]
        if value is not None and str(value) not in ("", "NaT"):
            published_at = str(value)

    return {
        "row_index": row_index,
        "news_id": news_id,
        "title": str(row.get("title") or ""),
        "source": str(row.get("source") or ""),
        "published_at": published_at,
        "content": str(row.get("content") or ""),
        "keywords": keywords_for_document(text, top_k=top_k),
        "summary": summarize(text, top_n=top_n),
    }


def _match_positions(df: pd.DataFrame, sim_df: pd.DataFrame) -> list[int]:
    """把相似度结果逐行映射回 df 的行位置。

    优先按 id 列匹配；无 id 列或该行 id 为空时按 title+source 兜底。
    找不到时记为 -1（调用方不应提供跳转入口）。
    """
    positions: list[int] = []
    has_id = ID_COL in df.columns
    for _, m in sim_df.iterrows():
        pos = -1
        matched_id = str(m["matched_id"]).strip()
        if has_id and matched_id:
            hits = df.index[df[ID_COL].astype(str) == matched_id].tolist()
            if hits:
                pos = int(hits[0])
        if pos == -1:
            mask = (df["title"].astype(str) == str(m["matched_title"])) & (
                df["source"].astype(str) == str(m["matched_source"])
            )
            hits = df.index[mask].tolist()
            if hits:
                pos = int(hits[0])
        positions.append(pos)
    return positions


def get_similar_articles(
    df: pd.DataFrame, row_index: int, top_n: int = 5
) -> pd.DataFrame:
    """查找相似新闻并补充行位置与发布时间。

    返回列：row_index、matched_id、title、source、published_at、similarity、rank。
    语料不足 2 篇、查询文本为空、无正相似度匹配时返回空 DataFrame（不抛异常）。
    结果条数不超过实际可用的正相似度匹配数量。
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(columns=SIMILAR_COLUMNS)

    sim_df = find_similar_articles(df, query_index=row_index, top_n=top_n)
    if sim_df.empty:
        return pd.DataFrame(columns=SIMILAR_COLUMNS)

    positions = _match_positions(df, sim_df)
    published: list[str] = []
    for pos in positions:
        if 0 <= pos < len(df) and "published_at" in df.columns:
            value = df.iloc[pos]["published_at"]
            published.append("" if value is None or str(value) == "NaT" else str(value))
        else:
            published.append("")

    return pd.DataFrame(
        {
            "row_index": positions,
            "matched_id": sim_df["matched_id"].tolist(),
            "title": sim_df["matched_title"].tolist(),
            "source": sim_df["matched_source"].tolist(),
            "published_at": published,
            "similarity": sim_df["similarity"].tolist(),
            "rank": sim_df["rank"].tolist(),
        },
        columns=SIMILAR_COLUMNS,
    )


def should_reset_selection(stored_fp, current_fp) -> bool:
    """数据指纹变化时应重置文章选择，避免新数据集沿用旧选择。"""
    return stored_fp != current_fp
