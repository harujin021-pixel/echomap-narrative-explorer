"""模块 C：TextRank 抽取式摘要（src.analysis.summarization）。

阶段 2 功能：从文章**原文**中抽取若干句子组成摘要，不生成新内容、不调用外部 API。

算法原理：
    1. 按中文句末标点（。！？；）、半角 !?;、换行，以及限定条件的英文句点切分句子
       （英文句点仅在非小数且后跟空白/结尾/大写字母时切分，U.S. 等大写缩写可能误切）。
    2. 用分词后的词集合计算句子两两的相似度（词集合重叠的余弦式度量）。
    3. 以句子为节点、相似度为边权重构建图，用 PageRank（networkx 实现）为句子打分。
    4. 取分数最高的若干句，去重后按**原文顺序**输出。

局限性（务必知悉）：
    - 抽取式摘要只挑选原文句子，**不做**事实核查、真实性验证或观点判断；
      摘要存在不等于原文内容被证明为真。
    - 句子相似度只基于词面重叠，无法理解同义改写与语义等价。
    - 文章过短或句子间几乎没有共同词时，图的连边不足，排序信息量很低；
      此时函数会给出说明性的 note 字段，结果仅供参考。
"""

from __future__ import annotations

import math
import re

import networkx as nx
import numpy as np

from src.analysis.preprocessing import load_stopwords, normalize_text, tokenize

# 句子边界：中文/英文句末标点与换行。
# 英文句点 "." 仅在「前一个字符不是数字」且「后一个字符为空白/结尾/大写字母」时视为边界，
# 以减少误切小数（3.14）和小写缩写（e.g.）；对 U.S. 这类大写缩写仍可能误切，属已知局限。
_BOUNDARY = re.compile(r"([。！？!?；;\n]|(?<!\d)\.(?=\s|$|[A-Z]))")


def split_sentences(text: object) -> list[str]:
    """把文本切分为句子列表（保持原文顺序，去除空句）。

    边界规则：
        - 中文标点 。！？；与半角 !?;、换行 \n 一律视为句末。
        - 英文句点 . 仅在非小数（前后非数字）且后跟空白/结尾/大写字母时切分，
          避免误切 3.14 等小数；U.S. 等大写缩写仍可能被误切。
    """
    normalized = normalize_text(text)
    if not normalized:
        return []
    parts = _BOUNDARY.split(normalized)
    sentences: list[str] = []
    current = ""
    for i, part in enumerate(parts):
        current += part
        if i % 2 == 1:  # 奇数位是分隔符
            stripped = current.strip()
            if stripped:
                sentences.append(stripped)
            current = ""
    tail = current.strip()
    if tail:
        sentences.append(tail)
    return sentences


def _pairwise_similarity(token_sets: list[set[str]]) -> np.ndarray:
    """基于词集合重叠计算句子两两相似度（介于 0~1）。"""
    n = len(token_sets)
    sim = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = token_sets[i], token_sets[j]
            if not a or not b:
                continue
            intersection = len(a & b)
            if intersection == 0:
                continue
            value = intersection / math.sqrt(len(a) * len(b))
            sim[i, j] = sim[j, i] = value
    return sim


def summarize(
    text: object, top_n: int = 3, stopwords: set[str] | None = None
) -> dict:
    """对文本生成 TextRank 抽取式摘要，返回结构化字典。

    返回字段：
        summary          摘要句子列表（来自原文，按原文顺序，已去重）
        summary_indices  摘要句子在 split_sentences 结果中的下标
        num_sentences    原文句子总数
        note             边界情况或局限性说明

    对空文本、单句文本、相似度不足等情况均安全处理，不抛异常。
    """
    if top_n < 1:
        raise ValueError("top_n 必须 >= 1")

    sentences = split_sentences(text)
    n = len(sentences)
    result = {"summary": [], "summary_indices": [], "num_sentences": n, "note": ""}

    if n == 0:
        result["note"] = "空文本：没有可摘要的句子。"
        return result

    if n == 1:
        result["summary"] = [sentences[0]]
        result["summary_indices"] = [0]
        result["note"] = "仅有一句，未进行图排序，直接返回该句。"
        return result

    if stopwords is None:
        stopwords = load_stopwords()
    token_sets = [set(tokenize(s, stopwords=stopwords)) for s in sentences]
    sim = _pairwise_similarity(token_sets)

    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    has_edge = False
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] > 0:
                graph.add_edge(i, j, weight=float(sim[i, j]))
                has_edge = True

    if has_edge:
        scores = nx.pagerank(graph, weight="weight")
        note = ""
    else:
        # 无有效连边：PageRank 无信息，退化为按原文顺序选取
        scores = {i: 1.0 for i in range(n)}
        note = "句子间相似度不足（无有效连边），已退化为按原文顺序选取，结果仅供参考。"

    ranked = sorted(range(n), key=lambda i: scores[i], reverse=True)

    seen: set[str] = set()
    chosen: list[int] = []
    for i in ranked:
        key = sentences[i].strip()
        if key in seen:
            continue
        seen.add(key)
        chosen.append(i)
        if len(chosen) >= min(top_n, n):
            break

    chosen.sort()  # 恢复原文顺序

    result["summary"] = [sentences[i] for i in chosen]
    result["summary_indices"] = chosen
    if not note and len(chosen) < top_n:
        note = f"文章较短（共 {n} 句），可返回的摘要句不足 {top_n} 句。"
    result["note"] = note
    return result
