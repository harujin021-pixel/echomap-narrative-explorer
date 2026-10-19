# Example Observations (English)

> **SYNTHETIC DATA DEMONSTRATION / 合成数据演示**
> All observations in this document are based on a **clearly labeled synthetic corpus** and are only meant
> to demonstrate what kind of output this tool can produce.
> These contents are **not** research findings about any real media outlet and must not be cited as
> conclusions of real-world news research.

## 1. Dataset identity and how it was verified

| Item | Value (verified against an actual run) |
| --- | --- |
| Data file | `tests/fixtures/synthetic_news_corpus.csv` |
| `data_source` marker | `synthetic_test_fixture` |
| Data fingerprint (after cleaning) | `348efb47364aa397` (the UI Data Provenance shows the first 8 characters, `348efb47`) |
| Raw rows / rows after cleaning | 6 / 5 (the row with id=5 has an empty source and is removed by cleaning) |
| Source distribution | 示例媒体甲 (Example Media A): 2 articles; 乙 (B): 1; 丙 (C): 1; 丁 (D): 1 |
| Publication date range | 2024-05-01 ~ 2024-05-06 |
| Clustering reproducibility | KMeans with fixed `random_state=42`; results are stable for the same input and cluster count |

- Verification date: 2026-10-17; environment: Python 3.10.11 + the versions pinned in `requirements.txt`.
- Verification method: the project functions (`run_ingestion` / `source_keyword_compare` /
  `compute_clusters` / `source_cluster_crosstab` / `get_similar_articles` /
  `get_article_detail`) were called directly and the real outputs were read; all numbers were
  **transcribed verbatim**, with no polishing or cherry-picking.
- If the fixture file is modified, the fingerprint will change and every number in this document must be re-verified.

Command to reproduce the cleaning row counts:

```powershell
py -c "from src.data.pipeline import run_ingestion; r = run_ingestion('tests/fixtures/synthetic_news_corpus.csv'); print('raw =', len(r['raw']), '| clean =', len(r['clean']))"
```

## 2. Verified observations

Each observation has three parts: **program output** (verbatim numbers) → **what can be cautiously
described** → **what cannot be concluded**.

> Note on language: Chinese keyword tokens below are verbatim program output; the bracketed text after
> each token is an English gloss added for readers, not part of the output.

### Observation 1: Each source's high-weight keywords match its articles' subject matter (source keyword comparison, min_articles=1, top_k=5)

- **Program output**:
  - 示例媒体甲 (Example Media A; 2 articles, 2 keyword sets shown):
    - Article row0 (subway): 开通 [opened] 0.381255, 新线路 [new line] 0.381255, 地铁 [subway] 0.381255, 换乘 [transfer] 0.190628, 优化 [optimization] 0.190628
    - Article row2 (air quality): 改善 [improvement] 0.477836, 空气质量 [air quality] 0.477836, 增多 [increase] 0.238918, 户外活动 [outdoor activities] 0.238918, 居民 [residents] 0.238918
  - 示例媒体乙 (B; 1 article): 调整 [adjustment] 0.426401, 专用道 [dedicated lane] 0.426401, 公交 [bus] 0.426401, 效率 [efficiency] 0.213201, 通勤 [commuting] 0.213201
  - 示例媒体丙 (C; 1 article): 水质 [water quality] 0.547723, 治理 [treatment] 0.365148, 河流 [river] 0.365148, 关注 [attention] 0.182574, 受到 [received] 0.182574
  - 示例媒体丁 (D; 1 article): 大会 [conference] / 举办 [hosting] / 社区 [community] / 软件 [software] / 开源 [open source], all with weight 0.365148
- **What can be cautiously described**: within this synthetic corpus, the high-weight words shown for each
  source match the subject vocabulary of that source's articles (the corpus was constructed this way).
- **What cannot be concluded**: this says nothing about reporting tendencies, editorial stances, or wording
  habits of the sources — each source has only 1~2 articles, and the article texts were written by hand;
  a TF-IDF weight only expresses a word's relative discriminating power within the current corpus, not an
  importance or influence ranking.

### Observation 2: With the default cluster count of 3, the 5 articles split into groups of 1 / 2 / 2 (KMeans, random_state=42)

- **Program output** (clustered_documents=5; no article was excluded from clustering):
  - Topic 0: 1 article (20%), representative keywords: 社区 [community], 软件 [software], 开源 [open source], 大会 [conference], 举办 [hosting] → corresponds to D's open-source-conference article
  - Topic 1: 2 articles (40%), representative keywords: 公交 [bus], 专用道 [dedicated lane], 调整 [adjustment], 开通 [opened], 新线路 [new line] → corresponds to the subway + bus articles
  - Topic 2: 2 articles (40%), representative keywords: 水质 [water quality], 改善 [improvement], 空气质量 [air quality], 河流 [river], 治理 [treatment] → corresponds to the air-quality + river-water-quality articles
- **What can be cautiously described**: within this synthetic corpus and with n=3, articles with similar
  subject vocabulary were grouped together.
- **What cannot be concluded**: this does not show that the data has a real news-category structure such as
  "transport / environment". Cluster IDs are exploratory, algorithm-generated groups — this app deliberately
  does not assign category names to the IDs; on small samples the result is parameter-sensitive (see Observation 3).

### Observation 3: Changing the cluster count to 2 changes the grouping (sensitivity)

- **Program output** (n=2, random_state=42):
  - Topic 0: 2 articles (40%), keywords: 公交 [bus], 专用道 [dedicated lane], 调整 [adjustment], 开通 [opened], 新线路 [new line]
  - Topic 1: 3 articles (60%), keywords: 水质 [water quality], 改善 [improvement], 空气质量 [air quality], 河流 [river], 治理 [treatment]
  - The open-source-conference article is merged into Topic 1 (the environment word group) this time,
    whereas it formed its own group at n=3.
- **What can be cautiously described**: changing the cluster count changes the grouping; the open-source
  article's assignment varies with n.
- **What cannot be concluded**: one cannot infer that some "correct" number of groups exists, nor
  over-interpret the meaning of any single group.

### Observation 4: Source × topic distribution (cross-tab at n=3)

- **Program output** (article counts; row proportions in parentheses, denominator = all articles of that source):

  | Source | Topic 0 | Topic 1 | Topic 2 |
  | --- | --- | --- | --- |
  | 示例媒体甲 (Example Media A) | 0 | 1 (0.5) | 1 (0.5) |
  | 示例媒体乙 (B) | 0 | 1 (1.0) | 0 |
  | 示例媒体丙 (C) | 0 | 0 | 1 (1.0) |
  | 示例媒体丁 (D) | 1 (1.0) | 0 | 0 |

- **What can be cautiously described**: the only source with 2 articles (A) has its articles spread across
  two topics at n=3; every other source has exactly 1 article, so its proportion is always 1.0.
- **What cannot be concluded**: this does not show that any source "covers more ground" or "focuses more on
  a topic" — with 1~2 articles per source, row proportions are highly sensitive to the cluster count and the
  random seed, and carry demonstration value only.

### Observation 5: Similarity values are low overall, and the "most similar" pair can cross subject boundaries (cosine similarity)

- **Program output**:
  - Querying with row0 (subway), Top 4: bus dedicated lane 0.107030 > air quality 0.054618 > river water quality 0.016886 > open-source conference 0.016780
  - Querying with row4 (open-source conference), Top 1 is **river water quality treatment** (0.039564),
    followed by air quality 0.021612, bus dedicated lane 0.019444, subway 0.016780
- **What can be cautiously described**: every article pair in this synthetic corpus scores below 0.11;
  articles on related subjects (subway → bus) score highest, but on a sparse, small corpus, scattered
  surface word overlap alone can put an unrelated article first (open source → river water quality).
- **What cannot be concluded**: similarity ranking does not imply reprinting, same-topic assignment, shared
  stance, or any propagation relationship; Top 1 does not guarantee semantic relatedness.

### Observation 6: The same word has different weights under different analysis scopes

- **Program output**: the word 开通 [opened] has weight 0.371391 in the single-article detail view for row0,
  and weight 0.381255 in the source keyword comparison (示例媒体甲 / Example Media A).
- **What can be cautiously described**: single-article TF-IDF and source-corpus-level TF-IDF use different
  IDF scopes, so the same word's weights are not directly comparable across sections.
- **What cannot be concluded**: any cross-section comparison of weight rankings (e.g. "source A values this
  word more than the single article does").

## 3. Items pending hands-on verification

- The UI presentation (matplotlib chart fonts and fallback, expander interaction, column-width layout)
  falls under browser-side manual acceptance; this document verifies library-level function outputs only.
- The numbers quoted in the [DEMO_SCRIPT.md](DEMO_SCRIPT.md) narration all come from this document; if the
  dataset is replaced, they must be re-verified and updated in sync.

---

# 示例观察（Example Observations）

> **SYNTHETIC DATA DEMONSTRATION / 合成数据演示**
> 本文全部观察基于**明确标记的合成语料**，仅用于演示这套工具能产出什么样的输出。
> 这些内容**不是**对任何真实媒体的研究发现，不得引用为真实世界的新闻研究结论。

## 1. 数据集身份与核验方式

| 项目 | 值（实际运行核验） |
| --- | --- |
| 数据文件 | `tests/fixtures/synthetic_news_corpus.csv` |
| `data_source` 标记 | `synthetic_test_fixture` |
| 数据指纹（清洗后） | `348efb47364aa397`（界面数据档案显示前 8 位 `348efb47`） |
| 原始行数 / 清洗后行数 | 6 / 5（id=5 行 source 为空，被清洗删除） |
| 来源分布 | 示例媒体甲 2 篇、乙 1 篇、丙 1 篇、丁 1 篇 |
| 发布日期范围 | 2024-05-01 ~ 2024-05-06 |
| 聚类可复现性 | KMeans 固定 `random_state=42`，同一输入与聚类数下结果稳定 |

- 核验日期：2026-10-17；环境：Python 3.10.11 + `requirements.txt` 固定版本。
- 核验方式：直接调用项目内函数（`run_ingestion` / `source_keyword_compare` /
  `compute_clusters` / `source_cluster_crosstab` / `get_similar_articles` /
  `get_article_detail`）读取真实输出，数值**原样转录**，未做任何修饰或挑选。
- 若 fixtures 文件内容被修改，指纹会变化，本文所有数值需重新核验。

清洗行数复现命令：

```powershell
py -c "from src.data.pipeline import run_ingestion; r = run_ingestion('tests/fixtures/synthetic_news_corpus.csv'); print('raw =', len(r['raw']), '| clean =', len(r['clean']))"
```

## 2. 已核验观察

每条观察分三部分：**程序输出**（原样数值）→ **可以谨慎描述的现象** → **不能据此得出的结论**。

### 观察 1：各来源的高权重关键词与文章题材一致（来源关键词对比，min_articles=1, top_k=5）

- **程序输出**：
  - 示例媒体甲（2 篇，展示 2 组关键词）：
    - 文章 row0（地铁）：开通 0.381255、新线路 0.381255、地铁 0.381255、换乘 0.190628、优化 0.190628
    - 文章 row2（空气质量）：改善 0.477836、空气质量 0.477836、增多 0.238918、户外活动 0.238918、居民 0.238918
  - 示例媒体乙（1 篇）：调整 0.426401、专用道 0.426401、公交 0.426401、效率 0.213201、通勤 0.213201
  - 示例媒体丙（1 篇）：水质 0.547723、治理 0.365148、河流 0.365148、关注 0.182574、受到 0.182574
  - 示例媒体丁（1 篇）：大会 / 举办 / 社区 / 软件 / 开源，权重均为 0.365148
- **可以谨慎描述的现象**：在当前合成语料内，各来源展示出的高权重词与其对应文章的题材词汇一致（语料即按此构造）。
- **不能据此得出的结论**：不能说明各来源存在报道倾向、编辑立场或用词习惯差异——每来源仅 1~2 篇文章，且文章内容是人为编写的；TF-IDF 权重只表示词在当前语料内的相对区分能力，不是重要性或影响力排名。

### 观察 2：默认聚类数 3 时，5 篇文章分成 1 / 2 / 2 三组（KMeans，random_state=42）

- **程序输出**（clustered_documents=5，无未参与聚类的文章）：
  - 主题 0：1 篇（20%），代表关键词：社区、软件、开源、大会、举办 → 对应丁的开源大会文章
  - 主题 1：2 篇（40%），代表关键词：公交、专用道、调整、开通、新线路 → 对应地铁 + 公交两篇
  - 主题 2：2 篇（40%），代表关键词：水质、改善、空气质量、河流、治理 → 对应空气质量 + 河流水质两篇
- **可以谨慎描述的现象**：在当前合成语料与 n=3 参数下，题材用词相近的文章被分到同一组。
- **不能据此得出的结论**：不能说明数据存在「交通类 / 环境类」等真实新闻类别结构。聚类编号是算法生成的探索性分组——本应用也刻意不给编号冠以类别名；小样本下结果对参数敏感（见观察 3）。

### 观察 3：聚类数改为 2 时分组改变（敏感性）

- **程序输出**（n=2，random_state=42）：
  - 主题 0：2 篇（40%），关键词：公交、专用道、调整、开通、新线路
  - 主题 1：3 篇（60%），关键词：水质、改善、空气质量、河流、治理
  - 开源大会文章此次被并入主题 1（环境词群），而 n=3 时它单独成组。
- **可以谨慎描述的现象**：改变聚类数会改变分组结果，开源文章的归属随 n 变化。
- **不能据此得出的结论**：不能推断存在某个「正确」的组数，也不能对任何一组的含义过度解读。

### 观察 4：来源 × 主题分布（n=3 交叉表）

- **程序输出**（文章数量；括号内为行占比，分母=该来源全部文章数）：

  | 来源 | 主题 0 | 主题 1 | 主题 2 |
  | --- | --- | --- | --- |
  | 示例媒体甲 | 0 | 1（0.5） | 1（0.5） |
  | 示例媒体乙 | 0 | 1（1.0） | 0 |
  | 示例媒体丙 | 0 | 0 | 1（1.0） |
  | 示例媒体丁 | 1（1.0） | 0 | 0 |

- **可以谨慎描述的现象**：唯一拥有 2 篇文章的来源（甲），其文章在 n=3 下分布在两个主题；其余来源各只有 1 篇，占比恒为 1.0。
- **不能据此得出的结论**：不能说明某来源「覆盖面更广」或「更专注某话题」——每来源 1~2 篇的样本量下，行占比对聚类数与随机种子高度敏感，仅具演示意义。

### 观察 5：相似度数值整体很低，且「最相似」可能跨题材（余弦相似度）

- **程序输出**：
  - 以 row0（地铁）查询，Top4：公交专用道 0.107030 > 空气质量 0.054618 > 河流水质 0.016886 > 开源大会 0.016780
  - 以 row4（开源大会）查询，Top1 是**河流水质治理**（0.039564），其后为空气质量 0.021612、公交专用道 0.019444、地铁 0.016780
- **可以谨慎描述的现象**：本合成语料内所有文章对的相似度都低于 0.11；题材相近的文章（地铁→公交）相似度最高，但稀疏小语料下，仅靠零星词面重叠即可让题材无关的文章排到第一位（开源→河流水质）。
- **不能据此得出的结论**：相似度排名不代表转载、同题、立场一致或任何传播关系；Top1 不保证语义相关。

### 观察 6：同一词语在不同分析口径下权重不同

- **程序输出**：「开通」一词在 row0 单篇文章详情中权重 0.371391，在来源关键词对比（示例媒体甲）中权重 0.381255。
- **可以谨慎描述的现象**：单篇 TF-IDF 与来源语料级 TF-IDF 的 IDF 口径不同，同一词的权重不可跨区块直接比较。
- **不能据此得出的结论**：任何跨区块的权重排序比较（例如「甲来源比单篇文章更重视这个词」）。

## 3. 待实际核验项

- 界面端展示（matplotlib 图表字体与降级、expander 交互、列宽布局）属于浏览器人工验收范围；本文仅核验库级函数输出。
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md) 解说词引用的数值均出自本文；若更换数据集，需重新核验后同步更新。
