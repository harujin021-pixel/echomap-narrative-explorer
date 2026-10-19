"""主题聚类界面辅助模块（src.ui.cluster_view）。

阶段 3.2.2 功能：为 Streamlit 界面提供主题聚类的纯函数封装。

设计原则：
    - 全部为纯函数，不依赖 Streamlit，便于单元测试。
    - 聚类计算复用 src.analysis.clustering.cluster_articles，不重复实现算法。
    - data_fingerprint 用于界面缓存键：数据内容变化时指纹变化，
      避免切换数据集后错误沿用旧的聚类结果。
    - CLUSTERING_PIPELINE_VERSION 同样进入缓存键：算法更新后递增版本号，
      使旧会话缓存失效。
    - 聚类标签是算法编号，不代表已验证的新闻类别。
"""

from __future__ import annotations

import hashlib

import pandas as pd

from src.analysis.clustering import cluster_articles
from src.analysis.preprocessing import load_sensitive_words, load_stopwords

# 聚类/预处理算法版本号：进入界面缓存键。
# 预处理或聚类算法更新（如新增单字、纯数字、敏感词过滤）后递增，
# 使同一会话中旧的聚类缓存自动失效，避免界面沿用旧算法的结果。
CLUSTERING_PIPELINE_VERSION = "3"


def wordlists_fingerprint() -> str:
    """计算停用词与敏感词表的内容指纹（短哈希字符串）。

    词条增删后指纹变化，进入界面缓存键后可让旧聚类缓存自动失效，
    无需手动递增算法版本号。
    """
    payload = "|".join(sorted(load_stopwords())) + "||" + "|".join(
        sorted(load_sensitive_words())
    )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]


def data_fingerprint(df: pd.DataFrame) -> str:
    """计算 DataFrame 内容指纹（短哈希字符串）。

    内容或结构不同的数据产生不同指纹；相同数据指纹稳定一致。
    用于界面缓存键，确保切换数据集后不会沿用旧的聚类结果。
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("data_fingerprint 需要 pandas.DataFrame")
    hashed = pd.util.hash_pandas_object(df, index=True).values
    payload = (
        str(df.shape).encode()
        + "|".join(map(str, df.columns)).encode()
        + hashed.tobytes()
    )
    return hashlib.md5(payload).hexdigest()[:16]


def compute_clusters(clean_df: pd.DataFrame, n_clusters: int) -> dict:
    """对清洗后数据执行主题聚类，返回 cluster_articles 的结果字典。

    结果包含：labels（DataFrame，含 row_index 与 cluster）、
    cluster_keywords、n_clusters、clustered_documents、note。
    聚类数超出有效文档数时由 cluster_articles 自动下调并在 note 说明。
    """
    return cluster_articles(clean_df, n_clusters=n_clusters)


def cluster_summary(result: dict) -> list[dict]:
    """汇总各主题信息，返回列表（每项为一个主题）。

    每项包含：
        cluster   聚类编号
        count     该主题文章数
        ratio     占参与聚类文章的比例（0~1，保留 4 位小数）
        keywords  代表关键词列表
    按 cluster 编号升序。无有效聚类时返回空列表。
    """
    labels = result["labels"]
    keywords_map = result["cluster_keywords"]
    total = int(result["clustered_documents"])

    summary: list[dict] = []
    if total <= 0:
        return summary

    clustered = labels[labels["cluster"] >= 0]
    for cluster_id in sorted(int(c) for c in clustered["cluster"].unique()):
        count = int((clustered["cluster"] == cluster_id).sum())
        summary.append(
            {
                "cluster": cluster_id,
                "count": count,
                "ratio": round(count / total, 4),
                "keywords": list(keywords_map.get(cluster_id, [])),
            }
        )
    return summary


def articles_in_cluster(result: dict, cluster_id: int) -> pd.DataFrame:
    """返回指定主题下的文章（标题、来源、发布时间、原始行号）。

    按原始行号升序，保持与清洗后数据一致的顺序。
    cluster_id 无文章时返回带表头的空 DataFrame。
    """
    labels = result["labels"]
    cols = ["news_id", "row_index", "title", "source", "published_at"]
    matched = labels[labels["cluster"] == cluster_id]
    return matched[cols].sort_values("row_index").reset_index(drop=True)


def unclustered_count(result: dict) -> int:
    """返回未参与聚类的文章数（cluster == -1，即预处理后文本为空的行）。"""
    labels = result["labels"]
    return int((labels["cluster"] == -1).sum())
