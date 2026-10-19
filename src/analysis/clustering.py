"""模块 D：主题聚类（src.analysis.clustering）。

阶段 2 功能：用 TF-IDF 向量化 + KMeans 对新闻文本聚类，并给出每个聚类的代表关键词。

重要说明（务必知悉）：
    - 聚类标签只是算法产生的**编号**，不是预先验证的新闻类别；
      不要把 cluster 0/1/2… 直接命名为确定的「政治」「社会」「经济」等类别。
    - 每行的结果保留原始标识字段（若存在 id）、标题、来源、发布时间与聚类标签。
    - 固定 random_state 以保证**同一输入与参数**下结果可复现（KMeans 仍依赖初值，
      故用固定种子 + n_init 降低波动）。
    - 有效文档太少时聚类不稳定，会在返回的 note 中给出解释性警告。
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.analysis.vectorize import build_tfidf, combine_text_fields

ID_COL = "id"
RESULT_COLUMNS = ["news_id", "row_index", "title", "source", "published_at", "cluster"]

# 低于该有效文档数时给出小样本警告
SMALL_SAMPLE_THRESHOLD = 5


def _series_or_blank(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series([""] * len(df), index=df.index)


def _cluster_keywords(vectorizer, matrix, labels, top_k: int) -> dict[int, list[str]]:
    """为每个聚类提取平均 TF-IDF 最高的若干词作为代表关键词。"""
    names = vectorizer.get_feature_names_out()
    labels = np.asarray(labels)
    result: dict[int, list[str]] = {}
    for label in sorted(set(labels.tolist())):
        mask = labels == label
        mean_vec = np.asarray(matrix[mask].mean(axis=0)).ravel()
        order = np.argsort(mean_vec)[::-1]
        words = [names[j] for j in order if mean_vec[j] > 0][:top_k]
        result[int(label)] = words
    return result


def cluster_articles(
    df: pd.DataFrame,
    n_clusters: int = 3,
    text_columns: tuple[str, ...] = ("title", "content"),
    random_state: int = 42,
    top_keywords: int = 5,
    stopwords: set[str] | None = None,
) -> dict:
    """对 DataFrame 中的文章做 KMeans 主题聚类。

    返回字典：
        labels            DataFrame，列为 news_id、row_index、title、source、published_at、cluster
        cluster_keywords  {聚类编号: [代表关键词, ...]}
        n_clusters        实际使用的聚类数
        clustered_documents  参与聚类的有效文档数
        note             边界情况 / 小样本说明

    边界处理：空文本 / 无有效特征 / 有效文档 < 2 / n_clusters 超过有效文档数，均安全处理。
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("cluster_articles 需要 pandas.DataFrame")
    if n_clusters < 1:
        raise ValueError("n_clusters 必须 >= 1")

    texts = combine_text_fields(df, text_columns)
    vectorizer, matrix, processed = build_tfidf(texts, stopwords=stopwords)

    base = pd.DataFrame(
        {
            "news_id": _series_or_blank(df, ID_COL),
            "row_index": range(len(df)),
            "title": _series_or_blank(df, "title"),
            "source": _series_or_blank(df, "source"),
            "published_at": _series_or_blank(df, "published_at"),
        }
    )
    base["cluster"] = -1

    if matrix is None:
        return {
            "labels": base[RESULT_COLUMNS],
            "cluster_keywords": {},
            "n_clusters": 0,
            "clustered_documents": 0,
            "note": "所有文本在预处理后均为空，无法聚类。",
        }

    valid_rows = [i for i, text in enumerate(processed) if text.strip()]
    sub_matrix = matrix[valid_rows]

    if len(valid_rows) < 2:
        labels = np.zeros(len(valid_rows), dtype=int)
        k = 1
        note = "有效文本不足 2 篇，无法形成有意义的聚类；有效文档统一标记为 cluster 0。"
    else:
        k = min(n_clusters, len(valid_rows))
        model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = model.fit_predict(sub_matrix)
        note = ""
        if k < n_clusters:
            note = f"请求的聚类数 {n_clusters} 超过有效文档数 {len(valid_rows)}，已自动调整为 {k}。"
        if len(valid_rows) < SMALL_SAMPLE_THRESHOLD:
            warn = f"有效文档数较少（{len(valid_rows)} 篇），聚类结果不稳定，仅供参考。"
            note = (note + " " + warn).strip()

    for row_index, label in zip(valid_rows, labels):
        base.at[row_index, "cluster"] = int(label)

    cluster_keywords = _cluster_keywords(vectorizer, sub_matrix, labels, top_keywords)

    return {
        "labels": base[RESULT_COLUMNS],
        "cluster_keywords": cluster_keywords,
        "n_clusters": k,
        "clustered_documents": len(valid_rows),
        "note": note,
    }
