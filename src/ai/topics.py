"""AI 选题推荐（src.ai.topics）—— 阶段 5.1，本地规则版（不依赖任何模型）。

复用现有分析结果，不重复实现分析算法：
    - 主题与代表关键词来自 src.analysis.clustering.cluster_articles 的结果
      （经 src.ui.cluster_view.cluster_summary 汇总，关键词已在预处理源头
      统一过滤单字、纯数字、停用词与敏感词）；
    - 主题内文章来自 src.ui.cluster_view.articles_in_cluster；
    - 关键词强度依据 src.analysis.keywords.keywords_for_corpus 的语料级
      TF-IDF 权重（由调用方计算后传入）。

排序规则（明确、可解释，三因子加权）：
    综合排序值 = 0.5 × 主题占比 + 0.3 × 关键词强度 + 0.2 × 时间新近度
    - 主题占比   factor_share ：该主题文章数 / 参与聚类的文章总数（0~1）；
    - 关键词强度 factor_kw    ：主题代表关键词在语料级 TF-IDF 中的平均权重，
      除以各主题中的最大值归一化到 0~1；
    - 时间新近度 factor_recency：1 - (数据集最晚日期 - 主题内最晚日期) /
      (最晚日期 - 最早日期)，主题内最新 = 1；无可解析日期时该因子不可用。
    某因子不可用时（无日期、无关键词权重），按其余可用因子的权重重新归一化，
    并在结果中如实标记，不做任何虚构填充。

边界声明（务必知悉）：
    - 排序值仅描述当前数据集内部的统计结构，用于辅助浏览选题；
      新闻数量 ≠ 平台流量 ≠ 用户真实兴趣，本模块不预测任何内容表现。
    - 合成语料上的"推荐"只用于演示功能，不代表任何真实热点。
    - 本模块为纯函数，不做界面展示；文案与标注由界面层（i18n）生成。
"""

from __future__ import annotations

import pandas as pd

from src.ui.cluster_view import articles_in_cluster, cluster_summary

DATE_COL = "published_at"

# 三因子权重（固定并公开，保证排序规则可解释、可复现）
WEIGHT_SHARE = 0.5
WEIGHT_KEYWORD = 0.3
WEIGHT_RECENCY = 0.2

# 每条选题展示的关联新闻条数上限（避免界面过长；完整列表可在聚类区块查看）
MAX_ARTICLES_PER_TOPIC = 5

RESULT_KEYS = (
    "recommendations",
    "no_dates",
    "kw_factor_available",
    "small_sample",
    "clustered_documents",
)


def _series_dates(clean_df: pd.DataFrame) -> pd.Series:
    """把日期列安全解析为 datetime Series（列缺失或全 NaT 由调用方判断）。"""
    if DATE_COL not in clean_df.columns:
        return pd.Series(pd.NaT, index=clean_df.index)
    return pd.to_datetime(clean_df[DATE_COL], format="mixed", errors="coerce")


def keyword_mean_weights(corpus_keywords: pd.DataFrame | None) -> dict[str, float]:
    """计算每个关键词在语料级 TF-IDF 结果中的平均权重。

    corpus_keywords 为 keywords_for_corpus 的输出
    （列：doc_id、rank、keyword、weight；空 DataFrame 或 None 返回空 dict）。
    """
    if not isinstance(corpus_keywords, pd.DataFrame) or corpus_keywords.empty:
        return {}
    if not {"keyword", "weight"}.issubset(corpus_keywords.columns):
        return {}
    positive = corpus_keywords[corpus_keywords["weight"] > 0]
    if positive.empty:
        return {}
    means = positive.groupby("keyword")["weight"].mean()
    return {str(k): float(v) for k, v in means.items()}


def _topic_articles(clean_df: pd.DataFrame, cluster_result: dict, cluster_id: int) -> list[dict]:
    """取某主题下的关联新闻（标题、来源、日期、原始行号），限制展示条数。

    日期格式化为 YYYY-MM-DD 字符串；无法解析的日期如实返回 None，不虚构。
    """
    articles_df = articles_in_cluster(cluster_result, cluster_id)
    dates = pd.to_datetime(articles_df[DATE_COL], format="mixed", errors="coerce")
    rows: list[dict] = []
    for pos, (_, row) in enumerate(articles_df.iterrows()):
        if pos >= MAX_ARTICLES_PER_TOPIC:
            break
        date_value = dates.iloc[pos]
        rows.append(
            {
                "title": str(row.get("title") or ""),
                "source": str(row.get("source") or ""),
                "date": date_value.strftime("%Y-%m-%d") if pd.notna(date_value) else None,
                "row_index": int(row["row_index"]),
            }
        )
    return rows


def build_topic_recommendations(
    clean_df: pd.DataFrame,
    cluster_result: dict,
    corpus_keywords: pd.DataFrame | None = None,
    top_n: int = 5,
) -> dict:
    """基于现有聚类结果与语料级关键词，生成排序后的候选选题列表。

    参数:
        clean_df: 清洗后的新闻 DataFrame（用于日期因子与关联新闻溯源）。
        cluster_result: cluster_articles 的结果字典（labels / cluster_keywords 等）。
        corpus_keywords: keywords_for_corpus 的结果（可选；用于关键词强度因子）。
        top_n: 返回的选题数量上限（>=1）。

    返回:
        dict，含 RESULT_KEYS 中全部字段：
            recommendations      选题列表（按综合排序值降序，最多 top_n 条）
            no_dates             True 表示数据无可解析日期，时间因子未参与排序
            kw_factor_available  False 表示关键词强度因子整体不可用
            small_sample         True 表示参与聚类的文章数 < 5（小样本提示）
            clustered_documents  参与聚类的文章数
        每条 recommendation 含：
            cluster          聚类编号
            keywords         代表关键词列表（已过敏感词/单字/纯数字过滤）
            count / ratio    主题文章数与占比
            articles         关联新闻（title/source/date/row_index，≤5 条）
            factor_share / factor_kw / factor_recency  各因子（0~1；不可用为 None）
            score            综合排序值（可用因子加权归一，4 位小数）
    """
    if not isinstance(clean_df, pd.DataFrame):
        raise TypeError("build_topic_recommendations 需要 pandas.DataFrame")
    if not isinstance(cluster_result, dict):
        raise TypeError("cluster_result 需要是 cluster_articles 的结果字典")
    if top_n < 1:
        raise ValueError("top_n 必须 >= 1")

    base = {
        "recommendations": [],
        "no_dates": False,
        "kw_factor_available": True,
        "small_sample": False,
        "clustered_documents": int(cluster_result.get("clustered_documents", 0) or 0),
    }

    summary = cluster_summary(cluster_result)
    if not summary:
        return base

    base["small_sample"] = base["clustered_documents"] < 5
    kw_means = keyword_mean_weights(corpus_keywords)

    # 数据集整体日期范围（用于时间新近度因子）
    all_dates = _series_dates(clean_df).dropna()
    no_dates = all_dates.empty
    base["no_dates"] = no_dates
    global_min = all_dates.min() if not no_dates else None
    global_max = all_dates.max() if not no_dates else None
    span_days = (global_max - global_min).days if not no_dates else 0

    drafts: list[dict] = []
    for item in summary:
        keywords = list(item["keywords"])
        factor_share = float(item["ratio"])
        factor_share = min(max(factor_share, 0.0), 1.0)

        # 关键词强度：代表关键词的平均语料权重（缺失词按 0 计）
        keyword_weights = [kw_means.get(kw, 0.0) for kw in keywords]
        factor_kw: float | None = None
        if kw_means and keywords:
            factor_kw = sum(keyword_weights) / len(keyword_weights)

        # 时间新近度：主题内最晚日期距数据集最晚日期越近，因子越高
        factor_recency: float | None = None
        recency_days: int | None = None
        topic_articles = _topic_articles(clean_df, cluster_result, item["cluster"])
        if not no_dates and topic_articles:
            # 展示条数可能少于主题内文章数，改用 labels 全量日期计算主题最晚日期
            labels = cluster_result.get("labels")
            if isinstance(labels, pd.DataFrame) and not labels.empty:
                in_cluster = labels[labels["cluster"] == item["cluster"]]
                topic_date_all = pd.to_datetime(
                    in_cluster[DATE_COL], format="mixed", errors="coerce"
                ).dropna() if DATE_COL in in_cluster.columns else pd.Series(dtype="datetime64[ns]")
            else:
                topic_date_all = pd.Series(dtype="datetime64[ns]")
            latest = None
            candidates = [d for d in (topic_date_all.dropna().tolist())]
            if candidates:
                latest = max(candidates)
            if latest is not None:
                recency_days = int((global_max - latest).days)
                if span_days > 0:
                    factor_recency = 1.0 - recency_days / span_days
                    factor_recency = min(max(factor_recency, 0.0), 1.0)
                else:
                    factor_recency = 1.0  # 全数据集同一天：各主题同等新近

        drafts.append(
            {
                "cluster": item["cluster"],
                "keywords": keywords,
                "count": item["count"],
                "ratio": item["ratio"],
                "articles": topic_articles,
                "factor_share": factor_share,
                "factor_kw": factor_kw,
                "factor_recency": factor_recency,
                "recency_days": recency_days,
                "score": None,
            }
        )

    # 关键词强度归一化：除以各主题最大平均权重
    kw_values = [d["factor_kw"] for d in drafts if d["factor_kw"] is not None]
    kw_max = max(kw_values) if kw_values else 0.0
    if kw_max <= 0:
        base["kw_factor_available"] = False
        for d in drafts:
            d["factor_kw"] = None
    else:
        for d in drafts:
            if d["factor_kw"] is not None:
                d["factor_kw"] = min(max(d["factor_kw"] / kw_max, 0.0), 1.0)

    # 综合排序：可用因子按权重归一（避免对不可用因子虚构取值）
    for d in drafts:
        weighted: list[tuple[float, float]] = []
        weighted.append((WEIGHT_SHARE, d["factor_share"]))
        if d["factor_kw"] is not None:
            weighted.append((WEIGHT_KEYWORD, d["factor_kw"]))
        if d["factor_recency"] is not None:
            weighted.append((WEIGHT_RECENCY, d["factor_recency"]))
        total_w = sum(w for w, _ in weighted)
        score = sum(w * v for w, v in weighted) / total_w if total_w > 0 else 0.0
        d["score"] = round(float(score), 4)

    drafts.sort(key=lambda d: (-d["score"], -d["count"], d["cluster"]))
    base["recommendations"] = drafts[:top_n]
    return base
