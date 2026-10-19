"""模块 E：文章相似度（src.analysis.similarity）。

阶段 2 功能：基于 TF-IDF 向量用**余弦相似度**查找某篇文章的 Top-N 相似文章。

重要说明（务必知悉）：
    - 文本相似度只反映**词面/向量层面的接近程度**；
      **不等于**转载关系、因果关系、立场一致，也**不能**推断媒体之间存在传播关系。
    - 结果会排除查询文章自身。
    - 完全相同的文章（重复文本）相似度为 1.0，这是词面完全一致的结果，同样不代表转载。
    - 只有极少数文章能返回时（如语料很小），返回不足 top_n 条是正常现象。
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.analysis.vectorize import build_tfidf, combine_text_fields

ID_COL = "id"
RESULT_COLUMNS = [
    "query_id",
    "matched_id",
    "matched_title",
    "matched_source",
    "similarity",
    "rank",
]


def _series_or_blank(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series([""] * len(df), index=df.index)


def compute_similarity_matrix(texts, stopwords: set[str] | None = None):
    """计算文本两两余弦相似度矩阵。

    返回 (matrix, sims, processed)。若所有文本预处理后为空，返回 (None, None, processed)。
    """
    vectorizer, matrix, processed = build_tfidf(texts, stopwords=stopwords)
    if matrix is None:
        return None, None, processed
    return matrix, cosine_similarity(matrix), processed


def find_similar_articles(
    df: pd.DataFrame,
    query_index: int | None = None,
    query_id=None,
    top_n: int = 5,
    text_columns: tuple[str, ...] = ("title", "content"),
    stopwords: set[str] | None = None,
) -> pd.DataFrame:
    """查找某篇文章的 Top-N 相似文章。

    参数：
        df             Phase 1 处理后的 DataFrame。
        query_index    查询文章的**行下标**（与 query_id 二选一）。
        query_id       查询文章的 id 值（与 query_index 二选一）。
        top_n          返回的相似文章数量。
        text_columns   用哪些列拼接文本，默认 title + content。

    返回列：query_id、matched_id、matched_title、matched_source、similarity、rank。
    边界情况（语料仅 1 篇、查询文章为空文本、无正相似度）返回空 DataFrame，不抛异常。
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("find_similar_articles 需要 pandas.DataFrame")
    if top_n < 1:
        raise ValueError("top_n 必须 >= 1")
    if query_index is None and query_id is None:
        raise ValueError("必须提供 query_index 或 query_id 之一")

    empty = pd.DataFrame(columns=RESULT_COLUMNS)

    texts = combine_text_fields(df, text_columns)
    vectorizer, matrix, processed = build_tfidf(texts, stopwords=stopwords)

    if matrix is None or len(df) < 2:
        return empty  # 语料为空或只有一篇文章

    # 解析查询文章的行下标
    if query_index is not None:
        if not 0 <= query_index < len(df):
            raise IndexError(f"query_index 越界: {query_index}")
        query_pos = query_index
    else:
        ids = _series_or_blank(df, ID_COL)
        matches = ids.index[ids.astype(str) == str(query_id)].tolist()
        if not matches:
            raise KeyError(f"未找到 query_id={query_id}")
        query_pos = matches[0]

    if not processed[query_pos].strip():
        return empty  # 查询文章预处理后为空文本

    sims = cosine_similarity(matrix)
    scores = sims[query_pos].copy()
    scores[query_pos] = -1.0  # 排除自身

    order = np.argsort(scores)[::-1]
    order = [int(i) for i in order if scores[i] > 0][:top_n]

    ids = _series_or_blank(df, ID_COL)
    titles = _series_or_blank(df, "title")
    sources = _series_or_blank(df, "source")

    rows = [
        {
            "query_id": ids.iloc[query_pos],
            "matched_id": ids.iloc[i],
            "matched_title": titles.iloc[i],
            "matched_source": sources.iloc[i],
            "similarity": round(float(scores[i]), 6),
            "rank": rank,
        }
        for rank, i in enumerate(order, start=1)
    ]
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)
