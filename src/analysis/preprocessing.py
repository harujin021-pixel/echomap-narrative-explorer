"""中文文本预处理（src.analysis.preprocessing）。

阶段 2 功能：为关键词提取、摘要、聚类、相似度提供**统一、可复用**的预处理。
本模块只做文本规范化与分词，**不会修改**原始 title / content / source 字段。

预处理规则：
    1. 非字符串（None / NaN / 数字等）一律安全转为空字符串，不抛异常。
    2. 全角空格与连续空白折叠为单个空格，并去除首尾空白。
    3. 使用 jieba 词性标注模式分词（posseg，HMM 新词发现关闭，
       避免把口语碎片猜测合并成新词，如「这波」「变水」）。
    4. 丢弃纯标点 / 纯空白的 token；token 统一转小写（对英文有效）。
    5. 丢弃长度小于 2 的 token（单个汉字/字母/数字在关键词与主题
       分析中区分意义有限，提前剔除，避免出现在关键词结果中）；
       并丢弃不含任何汉字/字母的纯数字 token（如 2026、17、3.14，
       避免日期、编号类噪声进入关键词结果）。
    6. 丢弃停用词表中的词（停用词表位于同目录 stopwords_zh.txt）。
    7. 丢弃敏感词表中的词（敏感词表位于同目录 sensitive_words.txt，
       可独立维护；命中词不参与分析也不出现在界面，原始字段不修改）。
    8. 含汉字的 token 仅保留名词性词性（名词/人名/地名/机构名/专名，
       及名动词、名形词、简称、成语、习用语）；动词、代词、形容词等
       剔除。英文/数字混合 token 不做词性检查。

局限性（务必知悉）：
    - 规则简单，不做同义词合并、词形还原（lemmatization）、专有名词识别。
    - 停用词表是通用高频词表，未针对新闻领域调优；删词可能误删有信息量的词。
    - 词性过滤依赖 jieba 词典与标注规则，可能误判（个别名词被标为动词等）；
      HMM 关闭后未登录新词不再合并，会被切成单字剔除，属已知取舍。
    - 不做繁体/简体转换；不做拼写纠错。
    - 分词依赖 jieba 词典，对未登录词（新词、人名、简称）可能切分不佳。
    因此预处理结果**只用于分析**，不代表对原文含义的完整还原。
"""

from __future__ import annotations

import re
from pathlib import Path

import jieba
import jieba.posseg as pseg

DEFAULT_STOPWORDS_PATH = Path(__file__).with_name("stopwords_zh.txt")
DEFAULT_SENSITIVE_WORDS_PATH = Path(__file__).with_name("sensitive_words.txt")

# 只要 token 中包含至少一个汉字/字母/数字，就认为是“有意义”的 token
_HAS_WORD_CHAR = re.compile(r"[0-9A-Za-z\u4e00-\u9fff]")
# token 中须包含至少一个汉字/字母：纯数字（2026、17、3.14 等）一律剔除
_HAS_LETTER_CHAR = re.compile(r"[A-Za-z\u4e00-\u9fff]")
_MULTI_SPACE = re.compile(r"\s+")

# 短于此长度的 token 一律丢弃（单字在关键词/主题分析中区分意义有限）
MIN_TOKEN_LENGTH = 2

# token 中含汉字时要求词性为名词性（ICTCLAS 标注）：
#   前缀 "n" 覆盖 n/nr/ns/nt/nz/ng（名词/人名/地名/机构名/其他专名），
#   另保留 vn（名动词）、an（名形词）、j（简称略语）、i（成语）、l（习用语）。
#   动词、形容词、代词、量词等（如「操作」「不负」「这波」）无独立检索意义，剔除。
_KEPT_POS_EXACT = {"vn", "an", "j", "i", "l"}
_HAS_CJK = re.compile(r"[\u4e00-\u9fff]")

_stopwords_cache: set[str] | None = None
_sensitive_cache: set[str] | None = None


def load_stopwords(path: str | Path | None = None) -> set[str]:
    """读取停用词表（默认使用内置 stopwords_zh.txt）。

    文件格式：每行一个词，# 开头为注释，空行忽略。
    若指定文件不存在，返回空集合（不抛异常）。
    """
    global _stopwords_cache

    if path is None:
        if _stopwords_cache is None:
            _stopwords_cache = _read_stopwords(DEFAULT_STOPWORDS_PATH)
        return set(_stopwords_cache)

    return _read_stopwords(Path(path))


def load_sensitive_words(path: str | Path | None = None) -> set[str]:
    """读取敏感词表（默认使用内置 sensitive_words.txt）。

    文件格式与停用词表一致：每行一个词，# 开头为注释，空行忽略。
    若指定文件不存在，返回空集合（不抛异常）。
    """
    global _sensitive_cache

    if path is None:
        if _sensitive_cache is None:
            _sensitive_cache = _read_stopwords(DEFAULT_SENSITIVE_WORDS_PATH)
        return set(_sensitive_cache)

    return _read_stopwords(Path(path))


def _read_stopwords(path: Path) -> set[str]:
    if not path.is_file():
        return set()

    words: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if not word or word.startswith("#"):
            continue
        words.add(word.lower())
    return words


def normalize_text(text: object) -> str:
    """安全地规范化文本：非字符串 -> ""；折叠空白并去首尾空白。"""
    if not isinstance(text, str):
        return ""
    text = text.replace("\u3000", " ")  # 全角空格
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


def tokenize(
    text: object,
    stopwords: set[str] | None = None,
    sensitive: set[str] | None = None,
) -> list[str]:
    """分词并过滤标点、停用词与敏感词，返回 token 列表。

    空值、空白文本、非字符串输入一律返回空列表。
    sensitive 为 None 时自动加载内置敏感词表；传入空集合表示不过滤敏感词。
    """
    normalized = normalize_text(text)
    if not normalized:
        return []

    if stopwords is None:
        stopwords = load_stopwords()
    if sensitive is None:
        sensitive = load_sensitive_words()

    tokens: list[str] = []
    for raw, flag in pseg.lcut(normalized, HMM=False):
        token = raw.strip().lower()
        if not token or not _HAS_WORD_CHAR.search(token):
            continue  # 纯标点 / 纯空白
        if len(token) < MIN_TOKEN_LENGTH:
            continue  # 单字（单个汉字/字母/数字），提前剔除
        if not _HAS_LETTER_CHAR.search(token):
            continue  # 纯数字（2026、17、3.14 等），剔除
        if token in stopwords:
            continue
        if token in sensitive:
            continue  # 敏感词：不参与分析、不出现在界面
        if _HAS_CJK.search(token) and not (
            flag.startswith("n") or flag in _KEPT_POS_EXACT
        ):
            continue  # 非名词性中文词（动词/代词/形容词等），不作为关键词
        tokens.append(token)
    return tokens


def preprocess_text(text: object, stopwords: set[str] | None = None) -> str:
    """把文本预处理成以空格分隔的 token 串（供向量化使用）。"""
    return " ".join(tokenize(text, stopwords=stopwords))


def preprocess_documents(
    texts, stopwords: set[str] | None = None
) -> list[str]:
    """批量预处理可迭代文本，返回等长的预处理字符串列表。"""
    if stopwords is None:
        stopwords = load_stopwords()
    return [preprocess_text(t, stopwords=stopwords) for t in texts]
