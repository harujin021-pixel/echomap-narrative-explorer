"""多来源新闻内容对比模块（src.analysis.source_compare）。

阶段 4.3 功能：按新闻来源分组的关键词对比，以及来源 × 聚类主题交叉分布。
只做当前样本中的内容统计——差异**不能**证明媒体立场、偏见、传播路径或因果关系。

设计原则：
    - 全部为纯函数，不依赖 Streamlit，可独立单元测试。
    - 复用 keywords_for_corpus（关键词算法）与 cluster_articles 的 labels
      （聚类标签），不重复实现任何算法。
    - 所有统计基于传入 DataFrame 的实际内容，缺失/不足时如实标注，
      不编造结果。
"""

from __future__ import annotations

import pandas as pd

from src.analysis.vectorize import combine_text_fields
from src.analysis.keywords import keywords_for_corpus

SOURCE_COL = "source"
NO_CLUSTER_LABEL = "未参与聚类"


def _group_counts(clean_df: pd.DataFrame) -> tuple[pd.Series, int]:
    """统计非空来源的文章数，返回 (来源计数(降序), 空来源行数)。"""
    if SOURCE_COL not in clean_df.columns:
        return (pd.Series(dtype=int), len(clean_df))
    sources = clean_df[SOURCE_COL].astype(str).str.strip()
    empty = int((sources == "").sum())
    valid = clean_df[sources != ""]
    counts = valid[SOURCE_COL].value_counts().sort_values(ascending=False)
    return (counts, empty)


def source_keyword_compare(
    clean_df: pd.DataFrame,
    top_k: int = 5,
    max_sources: int = 8,
    min_articles: int = 2,
) -> dict:
    """按新闻来源分组的 Top-N 关键词对比。

    参数:
        clean_df: 清洗后的新闻 DataFrame（需含 title/content/source）。
        top_k: 每个来源展示的关键词数。
        max_sources: 最多展示的来源数量（按文章数从多到少截取）。
        min_articles: 低于该文章数的来源跳过（结果不稳定），记入 skipped_sources。

    返回:
        dict：
        - per_source: [{source, article_count, keywords(DataFrame: row_index,
          rank, keyword, weight)}]，row_index 为该行在 clean_df 中的实际索引；
        - excluded_empty_source: 来源为空的行数；
        - skipped_sources: [(来源, 文章数)]，因样本过小被跳过；
        - total_sources / sources_shown: 有效来源总数 / 实际展示数；
        - note: 边界说明（无问题为 None）。

    说明:
        keywords 中的 weight 是 TF-IDF 权重（该来源文本内词语的相对区分能力），
        **不是**文章数量或媒体影响力。空来源、空文本、样本不足均如实标注，
        不编造结果。
    """
    empty_result = {
        "per_source": [],
        "excluded_empty_source": 0,
        "skipped_sources": [],
        "total_sources": 0,
        "sources_shown": 0,
        "note": "没有可用于对比的数据记录。",
    }
    if not isinstance(clean_df, pd.DataFrame) or clean_df.empty:
        return empty_result

    counts, empty_rows = _group_counts(clean_df)
    if counts.empty:
        result = dict(empty_result)
        result["excluded_empty_source"] = empty_rows
        result["note"] = "没有可识别的新闻来源，无法进行来源对比。"
        return result

    skipped: list[tuple[str, int]] = []
    selected = counts[counts >= min_articles].head(max_sources)
    skipped = [
        (str(src), int(cnt))
        for src, cnt in counts[counts < min_articles].items()
    ]

    per_source: list[dict] = []
    for source, count in selected.items():
        mask = clean_df[SOURCE_COL].astype(str).str.strip() == str(source)
        sub = clean_df[mask]  # 保留原行序与原索引
        texts = combine_text_fields(sub)
        kw = keywords_for_corpus(texts, top_k=top_k)
        if kw.empty:
            kw = pd.DataFrame(columns=["row_index", "rank", "keyword", "weight"])
        else:
            # doc_id 是该来源子集内的下标，映射回 clean_df 实际行索引
            kw = kw.copy()
            kw["row_index"] = sub.index[kw["doc_id"].astype(int)].astype(int)
        per_source.append(
            {
                "source": str(source),
                "article_count": int(count),
                "keywords": kw[["row_index", "rank", "keyword", "weight"]],
            }
        )

    note = None
    if len(counts) == 1:
        note = "当前数据集仅有一个新闻来源，无法进行来源之间的对比，以下仅为该来源的关键词。"
    if skipped:
        note = (
            (note or "")
            + f"以下来源文章数少于 {min_articles} 篇，样本过小、结果不稳定，已跳过："
            + "、".join(f"{s}({c}篇)" for s, c in skipped)
            + "。"
        )
    if len(counts) > len(selected):
        more = len(counts) - len(selected) - len(skipped)
        if more > 0:
            note = (note or "") + f"另有 {more} 个来源未展示（超过展示上限 {max_sources} 个）。"

    return {
        "per_source": per_source,
        "excluded_empty_source": empty_rows,
        "skipped_sources": skipped,
        "total_sources": int(len(counts)),
        "sources_shown": len(per_source),
        "note": note,
    }


def source_cluster_crosstab(
    clean_df: pd.DataFrame,
    cluster_labels: pd.DataFrame | None,
) -> dict:
    """来源 × 聚类主题的分布交叉表。

    参数:
        clean_df: 清洗后的新闻 DataFrame（用于核对来源总数）。
        cluster_labels: cluster_articles 返回的 labels DataFrame
            （含 row_index / source / cluster；cluster=-1 表示未参与聚类）。
            为 None 或空时返回空表与说明。

    返回:
        dict：
        - counts: DataFrame（行=来源，列=聚类编号字符串 + 「未参与聚类」，
          值=文章数）；
        - row_pct: 行占比，**分母是该来源的全部文章数**（含未参与聚类的行）；
        - total_rows: 参与统计的文章总数（等于 labels 行数）；
        - note: 边界说明（无问题为 None）。
    """
    empty = {
        "counts": pd.DataFrame(),
        "row_pct": pd.DataFrame(),
        "total_rows": 0,
        "note": "暂无聚类结果：请先在「主题聚类分析」中成功执行聚类。",
    }
    if cluster_labels is None or not isinstance(cluster_labels, pd.DataFrame):
        return empty
    if cluster_labels.empty or "cluster" not in cluster_labels.columns:
        return empty
    if SOURCE_COL not in cluster_labels.columns:
        return {**empty, "note": "聚类结果中缺少来源字段，无法生成来源 × 主题分布。"}

    labels = cluster_labels.copy()
    labels[SOURCE_COL] = labels[SOURCE_COL].astype(str).str.strip()
    labels = labels[labels[SOURCE_COL] != ""]
    if labels.empty:
        return {**empty, "note": "聚类结果中没有可识别的新闻来源。"}

    cluster_col = labels["cluster"].apply(
        lambda c: NO_CLUSTER_LABEL if int(c) < 0 else str(int(c))
    )
    counts = pd.crosstab(labels[SOURCE_COL], cluster_col)
    # 列排序：聚类编号按数值升序，未参与聚类排最后
    ordered = sorted(
        [c for c in counts.columns if c != NO_CLUSTER_LABEL],
        key=lambda x: int(x),
    ) + ([NO_CLUSTER_LABEL] if NO_CLUSTER_LABEL in counts.columns else [])
    counts = counts[ordered]

    row_totals = counts.sum(axis=1)
    # 不在此处四舍五入：保持完整精度，占比展示由界面层负责格式化
    row_pct = counts.div(row_totals, axis=0)

    note = None
    if NO_CLUSTER_LABEL in counts.columns and counts[NO_CLUSTER_LABEL].sum() > 0:
        note = (
            f"有 {int(counts[NO_CLUSTER_LABEL].sum())} 篇文章未参与聚类"
            "（文本无效或样本不足），已单列统计。"
        )

    return {
        "counts": counts,
        "row_pct": row_pct,
        "total_rows": int(len(labels)),
        "note": note,
    }


def small_sources(counts: pd.Series, threshold: int = 2) -> list[str]:
    """返回文章数低于 threshold 的来源列表（结果可能不稳定）。"""
    if counts is None or len(counts) == 0:
        return []
    return [str(s) for s, c in counts.items() if c < threshold]
