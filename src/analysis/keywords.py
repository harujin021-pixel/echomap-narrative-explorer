"""模块 B：TF-IDF 关键词提取（src.analysis.keywords）。

阶段 2 功能：对**单篇**或**一组**新闻文本提取 TF-IDF 关键词，返回结构化结果。

重要说明（务必知悉）：
    - TF-IDF 权重衡量的是词在当前语料中的**相对区分能力**（在该文档中高、在其它文档中低），
      **不等同于**新闻重要性、社会影响力或事实重要性。
    - **单篇文章**时，语料级 IDF 会退化：sklearn 的 smooth_idf 使所有词的 idf 近似相等，
      此时权重 ≈ 词频(TF)，不具备跨文章可比性。因此单篇结果只应作为「文内高频词」参考，
      **不能**当作具有统计可靠性的重要性排名。
    - 相关功能只在本文件内实现，不涉及外部 API 或在线模型。
"""

from __future__ import annotations

import pandas as pd

from src.analysis.vectorize import build_tfidf

DOCUMENT_COLUMNS = ["rank", "keyword", "weight"]
CORPUS_COLUMNS = ["doc_id", "rank", "keyword", "weight"]


def keywords_for_document(
    text: str, top_k: int = 10, stopwords: set[str] | None = None
) -> pd.DataFrame:
    """对单篇文本提取 TF-IDF 关键词。

    返回列：rank、keyword、weight（按权重降序）。
    空文本或全部词被过滤时返回空 DataFrame（不抛异常）。

    注意：单篇文本的权重退化为词频量级，见模块顶部说明。
    """
    if top_k < 1:
        raise ValueError("top_k 必须 >= 1")

    vectorizer, matrix, _ = build_tfidf([text], stopwords=stopwords)
    if matrix is None:
        return pd.DataFrame(columns=DOCUMENT_COLUMNS)

    names = vectorizer.get_feature_names_out()
    row = matrix[0].tocoo()
    pairs = sorted(zip(row.col.tolist(), row.data.tolist()), key=lambda p: p[1], reverse=True)
    pairs = [p for p in pairs if p[1] > 0][:top_k]

    rows = [
        {"rank": i, "keyword": names[col], "weight": round(float(weight), 6)}
        for i, (col, weight) in enumerate(pairs, start=1)
    ]
    return pd.DataFrame(rows, columns=DOCUMENT_COLUMNS)


def keywords_for_corpus(
    texts, top_k: int = 10, stopwords: set[str] | None = None
) -> pd.DataFrame:
    """对一组文本按文档逐篇提取 TF-IDF 关键词。

    返回列：doc_id（文本在输入序列中的下标）、rank、keyword、weight。
    空语料或全部文本为空时返回空 DataFrame（不抛异常）。
    """
    if top_k < 1:
        raise ValueError("top_k 必须 >= 1")

    text_list = list(texts)
    vectorizer, matrix, _ = build_tfidf(text_list, stopwords=stopwords)
    if matrix is None:
        return pd.DataFrame(columns=CORPUS_COLUMNS)

    names = vectorizer.get_feature_names_out()
    rows: list[dict] = []
    for doc_id in range(matrix.shape[0]):
        row = matrix[doc_id].tocoo()
        pairs = sorted(
            zip(row.col.tolist(), row.data.tolist()), key=lambda p: p[1], reverse=True
        )[:top_k]
        for rank, (col, weight) in enumerate(pairs, start=1):
            if weight <= 0:
                continue
            rows.append(
                {
                    "doc_id": doc_id,
                    "rank": rank,
                    "keyword": names[col],
                    "weight": round(float(weight), 6),
                }
            )
    return pd.DataFrame(rows, columns=CORPUS_COLUMNS)


def extract_keywords(texts, top_k: int = 10, stopwords: set[str] | None = None):
    """便捷入口：传入 str 返回单篇结果（DataFrame），传入序列返回语料结果（DataFrame）。"""
    if isinstance(texts, str):
        return keywords_for_document(texts, top_k=top_k, stopwords=stopwords)
    return keywords_for_corpus(texts, top_k=top_k, stopwords=stopwords)
