"""共享的 TF-IDF 向量化工具（src.analysis.vectorize）。

阶段 2 功能：为关键词、聚类、相似度提供统一的文本向量化入口，
避免在多个算法模块里重复实现向量化逻辑。
"""

from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.analysis.preprocessing import preprocess_documents

# 预处理后文本已是空格分隔的 token 串，因此按空白切分即可还原 token
TOKEN_PATTERN = r"(?u)\S+"

DEFAULT_TEXT_COLUMNS = ("title", "content")


def combine_text_fields(
    df: pd.DataFrame, columns: Sequence[str] = DEFAULT_TEXT_COLUMNS
) -> list[str]:
    """把 DataFrame 的多列文本按行拼接为一段文本（缺失列自动跳过）。

    仅用于分析，**不修改**传入的 DataFrame。
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("combine_text_fields 需要 pandas.DataFrame")

    present = [c for c in columns if c in df.columns]
    if not present:
        raise ValueError(f"数据中不存在任何指定文本列: {list(columns)}")

    combined: list[str] = []
    for _, row in df.iterrows():
        parts = [str(row[c]).strip() for c in present]
        combined.append(" ".join(p for p in parts if p))
    return combined


def build_tfidf(
    texts: Iterable[str],
    stopwords: set[str] | None = None,
    **vectorizer_kwargs,
) -> tuple[TfidfVectorizer | None, object | None, list[str]]:
    """对原始文本列表做预处理并构建 TF-IDF 矩阵。

    返回 (vectorizer, matrix, processed_texts)。
    若所有文本在预处理后都为空，则返回 (None, None, processed)，
    由调用方决定如何处理（**不抛异常**）。
    """
    raw = list(texts)
    processed = preprocess_documents(raw, stopwords=stopwords)

    if not any(t.strip() for t in processed):
        return None, None, processed

    vectorizer = TfidfVectorizer(token_pattern=TOKEN_PATTERN, **vectorizer_kwargs)
    matrix = vectorizer.fit_transform(processed)
    return vectorizer, matrix, processed


def keyword_weights(matrix_row) -> list[tuple[str, float]]:
    """把矩阵某一行的 (feature_index, weight) 稀疏项展开为列表。"""
    coo = matrix_row.tocoo()
    return list(zip(coo.col.tolist(), coo.data.tolist()))
