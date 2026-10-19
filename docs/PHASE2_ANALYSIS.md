# EchoMap 阶段 2 文档：AI 文本分析模块

> 本文件说明阶段 2 实现的中文文本分析模块：调用方式、输入输出字段、算法原理、
> 参数配置、边界情况与已知局限性。
>
> **重要前提**：本阶段只实现「分析算法」本身，**不包含** Streamlit 界面、不做仪表板、
> 不接入任何外部 API 或在线模型。所有算法均在本机运行，使用现有依赖
> （jieba、scikit-learn、networkx）。
>
> 项目当前**尚无真实新闻数据**。本文档中的示例一律使用
> `tests/fixtures/synthetic_news_corpus.csv`（**明确标记的合成测试数据**），
> **不是真实新闻**，相关结果**不构成**对真实新闻语料的分析结论。

---

## 0. 模块总览与调用方式

| 模块 | 文件 | 职责 | 主要入口 |
| --- | --- | --- | --- |
| A 预处理 | `src/analysis/preprocessing.py` | 文本规范化、jieba 分词、去停用词 | `preprocess_text` / `tokenize` / `preprocess_documents` / `load_stopwords` |
| （共享） | `src/analysis/vectorize.py` | 统一的 TF-IDF 向量化工具 | `combine_text_fields` / `build_tfidf` |
| B 关键词 | `src/analysis/keywords.py` | TF-IDF 关键词提取（单篇 / 语料） | `extract_keywords` / `keywords_for_document` / `keywords_for_corpus` |
| C 摘要 | `src/analysis/summarization.py` | TextRank 抽取式摘要 | `summarize` / `split_sentences` |
| D 聚类 | `src/analysis/clustering.py` | TF-IDF + KMeans 主题聚类 | `cluster_articles` |
| E 相似度 | `src/analysis/similarity.py` | 余弦相似度 Top-N 相似文章 | `find_similar_articles` / `compute_similarity_matrix` |

设计原则：

1. 每个功能职责单一，分文件实现，避免把所有算法堆进一个文件。
2. 接口接收 **阶段 1 处理后的 `pandas.DataFrame`**（复用 `title` / `content` / `source`
   以及可选的 `id` / `published_at` 字段），不另造不兼容的数据结构。
3. 结果返回 **DataFrame 或 dict** 结构化数据，便于测试与后续接入，不直接打印。
4. 边界情况（空文本、小样本、单篇、全停用词、重复文本）**安全处理，不崩溃**。
5. 参数尽量可配置，聚类固定随机种子以尽量复现。

调用方式（在项目根目录执行）：

```python
from src.data.pipeline import run_ingestion
from src.analysis.keywords import extract_keywords
from src.analysis.summarization import summarize
from src.analysis.clustering import cluster_articles
from src.analysis.similarity import find_similar_articles

df = run_ingestion("tests/fixtures/synthetic_news_corpus.csv")["clean"]
```

---

## 1. 模块 A：文本预处理（`preprocessing.py`）

### 1.1 预处理规则（透明、固定）

1. **非字符串安全处理**：`None` / `NaN` / 数字等一律转为空字符串 `""`，不抛异常。
2. **空白与标点**：全角空格 `\u3000` 归一为半角空格；连续空白折叠为单个空格；
   去除首尾空白。
3. **分词**：使用 **jieba 词性标注模式**（`jieba.posseg`），**HMM 新词发现关闭**
   （`HMM=False`），避免把口语碎片猜测合并成新词（如「这波」「变水」）。
4. **token 过滤**：丢弃不含任何汉字/字母/数字的 token（即纯标点、纯空白）；
   丢弃长度小于 2 的 token（单字在关键词/主题分析中区分意义有限，提前剔除）；
   丢弃不含任何汉字/字母的纯数字 token（如 2026、17、3.14 等日期编号类噪声）；
   token 统一转小写（对英文有效）。
5. **停用词过滤**：丢弃停用词表中的词。停用词表位于独立文件
   `src/analysis/stopwords_zh.txt`（每行一词，`#` 开头为注释），便于后续维护。
6. **敏感词过滤**：丢弃敏感词表中的词。敏感词表位于独立文件
   `src/analysis/sensitive_words.txt`（格式同停用词表），命中词不参与
   关键词 / 聚类 / 相似度等分析结果，也不出现在界面；**原始字段不做修改**。
7. **词性过滤**：含汉字的 token 仅保留名词性词性（名词/人名/地名/机构名/
   专名，及名动词、名形词、简称、成语、习用语），动词、代词、形容词等
   无独立检索意义的词剔除；英文/数字混合 token 不做词性检查。

> **不修改原始字段**：本模块只产出用于分析的 token 串，**不覆盖** `title` / `content` / `source`。

### 1.2 主要函数

| 函数 | 输入 | 输出 |
| --- | --- | --- |
| `load_stopwords(path=None)` | 可选停用词文件路径 | `set[str]`（默认读内置文件，带缓存） |
| `load_sensitive_words(path=None)` | 可选敏感词文件路径 | `set[str]`（默认读内置文件，带缓存） |
| `normalize_text(text)` | 任意对象 | 规范化后的字符串 |
| `tokenize(text, stopwords=None, sensitive=None)` | 任意对象 | `list[str]` token 列表 |
| `preprocess_text(text, stopwords=None)` | 任意对象 | 空格分隔的 token 串（供向量化使用） |
| `preprocess_documents(texts, stopwords=None)` | 文本可迭代对象 | 等长的预处理字符串列表 |

### 1.3 局限性

- 不做同义词合并、词形还原（lemmatization）、专有名词识别。
- 停用词表是**通用高频词表**，未针对新闻领域调优，删词可能误删有信息量的词。
- 不做繁简转换、拼写纠错。
- 分词依赖 jieba 词典，对未登录词（新词、人名、简称）可能切分不佳。
- 因此预处理结果**只用于分析**，不代表对原文含义的完整还原。

---

## 2. 共享向量化工具（`vectorize.py`）

- `combine_text_fields(df, columns=("title","content"))`：把多列文本按行拼接，
  缺失列自动跳过；**不修改**传入 DataFrame。
- `build_tfidf(texts, stopwords=None, **kwargs)`：预处理后构建 TF-IDF 矩阵，
  返回 `(vectorizer, matrix, processed)`。
  **若所有文本预处理后均为空，返回 `(None, None, processed)`，不抛异常**，由调用方决定处理策略。
- 分词后文本已是空格分隔，故 `TfidfVectorizer` 使用 `token_pattern=r"(?u)\S+"` 按空白切分还原 token。
- 使用 sklearn 默认的 `smooth_idf`（平滑 IDF）。

---

## 3. 模块 B：TF-IDF 关键词提取（`keywords.py`）

### 3.1 原理

TF-IDF = 词频（TF）× 逆文档频率（IDF）。一个词的 TF-IDF 权重
**在当前语料中**该文档里出现得多、而在其它文档中出现得少时更高，
衡量的是词的**相对区分能力**。

### 3.2 接口与输出

| 函数 | 输入 | 输出字段 |
| --- | --- | --- |
| `keywords_for_document(text, top_k=10)` | 单篇文本 | `rank`、`keyword`、`weight` |
| `keywords_for_corpus(texts, top_k=10)` | 文本序列 | `doc_id`、`rank`、`keyword`、`weight` |
| `extract_keywords(texts, top_k=10)` | str→单篇；序列→语料 | 同对应函数 |

- 结果按权重降序，`weight` 保留 6 位小数。
- `top_k` 可配置；`top_k < 1` 抛 `ValueError`。
- 空文本 / 全部词被停用词过滤 / 空语料 → 返回**空 DataFrame**（含正确列名），不崩溃。

### 3.3 重要局限（必须知悉）

- TF-IDF 权重**不等于**新闻重要性、社会影响力或事实重要性。
- **单篇文本**时语料级 IDF 会退化：`smooth_idf` 使所有词 idf 近似相等，此时权重 ≈ 词频，
  **不具备跨文章可比性**。故单篇结果只应作为「文内高频词」参考，
  **不得**当作具有统计可靠性的重要性排名。
- 结果未做任何人工校验，不构成对新闻主题的权威判断。

---

## 4. 模块 C：TextRank 抽取式摘要（`summarization.py`）

### 4.1 原理

1. 按中文句末标点（`。！？；`）、半角 `!?;`、换行切分句子；英文句点 `.` 仅在「前非数字、后为空白/结尾/大写字母」时视为边界，以避免误切 `3.14` 等小数。`U.S.` 等大写缩写仍可能被误切，属已知局限。
2. 对每句分词后取词集合，用「词集合重叠 / √(len(a)·len(b))」计算句子两两相似度（0~1）。
3. 以句子为节点、相似度为边权重构建无向图，用 **networkx 的 `pagerank`**（PageRank）为句子打分。
4. 取分数最高的若干句，**去重**后按**原文顺序**输出。

摘要**完全由原文句子组成**，不生成任何新内容，不调用外部 API / 在线模型。

### 4.2 接口与输出

`summarize(text, top_n=3, stopwords=None)` 返回 dict：

| 字段 | 含义 |
| --- | --- |
| `summary` | 摘要句子列表（来自原文，按原文顺序，已去重） |
| `summary_indices` | 摘要句在 `split_sentences` 结果中的下标 |
| `num_sentences` | 原文句子总数 |
| `note` | 边界情况 / 局限性说明 |

- `top_n` 可配置；`top_n < 1` 抛 `ValueError`。

### 4.3 边界处理

- **空文本** → `summary` 为空，`note` 说明「没有可摘要的句子」。
- **仅一句** → 直接返回该句，`note` 说明未做图排序。
- **句间无有效连边**（相似度全为 0）→ 退化为按原文顺序选取，`note` 明确提示「结果仅供参考」。
- 可返回句子不足 `top_n` 时，`note` 说明文章较短。

### 4.4 局限性

- 抽取式摘要**只挑选原文句子**，**不做事实核查、真实性验证或观点判断**；
  摘要包含某句不等于该句内容被证明为真。
- 句子相似度只基于**词面重叠**，无法理解同义改写与语义等价。
- 文章过短或句子间几乎没有共同词时，图的连边不足，排序信息量很低，此时结果仅供参考。

---

## 5. 模块 D：主题聚类（`clustering.py`）

### 5.1 原理

对拼接后的文本做 TF-IDF 向量化，再用 **KMeans** 聚类；
对每个聚类取其平均 TF-IDF 最高的若干词作为**代表关键词**。

### 5.2 接口与输出

`cluster_articles(df, n_clusters=3, text_columns=("title","content"), random_state=42, top_keywords=5, stopwords=None)` 返回 dict：

| 字段 | 含义 |
| --- | --- |
| `labels` | DataFrame：`news_id`、`row_index`、`title`、`source`、`published_at`、`cluster` |
| `cluster_keywords` | `{聚类编号: [代表关键词, ...]}` |
| `n_clusters` | 实际使用的聚类数 |
| `clustered_documents` | 参与聚类的有效文档数 |
| `note` | 边界情况 / 小样本说明 |

### 5.3 参数与边界处理

- `n_clusters < 1` 抛 `ValueError`。
- **聚类数校验**：`k = min(n_clusters, 有效文档数)`，并在 `note` 说明已自动调整。
- **有效文档 < 2**：无法形成有意义的聚类，有效文档统一标记为 `cluster 0`，`note` 说明原因。
- **所有文本预处理后为空**：无有效特征，不聚类，`n_clusters=0`，所有行 `cluster=-1`，`note` 说明。
- **小样本警告**：有效文档数 < `SMALL_SAMPLE_THRESHOLD`（=5）时，`note` 给出「结果不稳定，仅供参考」的警告。
- **可复现性**：固定 `random_state=42` 与 `n_init=10`，同一输入与参数下结果可复现（KMeans 依赖初值，用固定种子降低波动）。

### 5.4 局限与命名约束

- 聚类标签只是算法产生的**编号**，**不是预先验证的新闻类别**；
  **不得**把 `cluster 0/1/2…` 直接命名为确定的「政治」「社会」「经济」等类别，除非有明确证据支持。
- 每行保留原始标识字段（若 `id` 存在则映射为 `news_id`）、标题、来源、发布时间，便于回溯。
- 小样本或特征稀疏时聚类不稳定，结果仅供参考。

---

## 6. 模块 E：文章相似度（`similarity.py`）

### 6.1 原理

对拼接后的文本做 TF-IDF 向量化，用 **余弦相似度** 度量文章间向量接近程度，
返回查询文章的 Top-N 相似文章。

### 6.2 接口与输出

`find_similar_articles(df, query_index=None, query_id=None, top_n=5, text_columns=("title","content"), stopwords=None)` 返回 DataFrame：

| 字段 | 含义 |
| --- | --- |
| `query_id` | 查询文章的 id（若存在） |
| `matched_id` | 匹配文章的 id（若存在） |
| `matched_title` | 匹配文章标题 |
| `matched_source` | 匹配文章来源 |
| `similarity` | 余弦相似度（保留 6 位小数） |
| `rank` | 排名（从 1 开始，按相似度降序） |

- `query_index` 与 `query_id` 二选一，均未提供时抛 `ValueError`；
  `query_index` 越界抛 `IndexError`；`query_id` 未找到抛 `KeyError`。
- `top_n` 可配置；`top_n < 1` 抛 `ValueError`。

### 6.3 边界处理

- **排除自身**：查询文章自身相似度置为 `-1.0`，不会出现在结果中。
- **只有一篇文章 / 语料全空** → 返回**空 DataFrame**（含正确列名）。
- 仅保留相似度 `> 0` 的匹配；语料很小时返回不足 `top_n` 条属正常。
- **重复文章**（文本完全一致）相似度为 `1.0`，这是词面完全一致的数学结果。

### 6.4 必须说明的限制

- 文本相似度**只反映词面/向量层面的接近程度**，
  **不等于**转载关系、因果关系、立场一致，也**不能**推断媒体之间存在传播关系。
- 相似度 `1.0` 同样**不代表转载**。

---

## 7. 参数配置汇总

| 模块 | 参数 | 默认值 | 说明 |
| --- | --- | --- | --- |
| 关键词 | `top_k` | 10 | 每篇返回的关键词数 |
| 摘要 | `top_n` | 3 | 摘要句数 |
| 聚类 | `n_clusters` | 3 | 期望聚类数（超出有效文档数时自动下调） |
| 聚类 | `random_state` | 42 | 固定随机种子 |
| 聚类 | `top_keywords` | 5 | 每个聚类代表关键词数 |
| 相似度 | `top_n` | 5 | 相似文章数 |
| 文本列 | `text_columns` | `("title","content")` | 参与拼接的列 |

---

## 8. 如何运行测试

在项目根目录执行：

```powershell
py -m unittest discover -s tests -v
```

阶段 2 新增测试文件：`test_preprocessing.py`、`test_keywords.py`、
`test_summarization.py`、`test_clustering.py`、`test_similarity.py`（标准库 `unittest`）。
覆盖：正常中文文本、空文本/空值/缺失字段、极短/单句文本、全部被停用词过滤、
单篇 / 少量有效文章、聚类数超出有效样本数、相似度不返回自身、摘要句来自原文、
固定参数下的聚类可复现性，以及阶段 1 原有测试继续通过。

---

## 9. 已知局限（汇总）

1. 停用词表为通用词表，未针对新闻领域调优。
2. 不做繁简转换、同义词合并、词形还原。
3. jieba 对未登录词可能切分不佳。
4. 单篇 TF-IDF 的 IDF 退化，权重不可跨文章比较。
5. TextRank 只基于词面重叠，无法理解语义等价；**抽取式摘要非事实核查**。
6. 聚类标签是编号，**不是**已验证的新闻类别；小样本不稳定。
7. 文本相似**不等于**转载、因果或立场一致。
8. 以上结果均**未经人工/领域校验**，**不构成**对真实新闻语料的权威结论。

---

## 10. 当前尚未完成的功能

- **未接入界面**：`app/app.py` 保持阶段 0 占位提示不变，本阶段不做 Streamlit 页面或仪表板。
- **无真实新闻数据**：当前只有合成测试样本（`tests/fixtures/`），未导入真实新闻。
- **未导出分析报告**：分析结果尚未支持导出为报告文件。
- **未接入外部 API / 在线模型**：按阶段边界要求，本阶段全部本地算法实现。
- **未安装新依赖**：未安装 plotly / pytest / python-dotenv。
- **差异对比、可视化** 等目标功能尚未实现（留待后续阶段）。
