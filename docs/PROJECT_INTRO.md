# EchoMap — AI-Powered Media Narrative Explorer
# 项目介绍（Project Introduction）

> **Status / 状态**：项目介绍**初稿**。标注【To confirm / 待确认】的内容需作者本人核实后
> 才能对外使用。本文不声称系统已完成真实新闻研究、立场识别、传播链追踪或因果分析。

---

## English Version

### Project Overview

EchoMap is an interactive web application for exploring news text with explainable
text-mining methods. A user uploads a CSV file of news articles; the app checks and
documents data quality, then surfaces keyword structure, extractive summaries,
exploratory topic clusters, article-to-article similarity, and cross-source
comparisons. It is built as a single-page Streamlit application (Python, pandas,
scikit-learn, jieba, matplotlib) with the analysis logic kept in testable pure
functions, covered by an automated unit-test suite.

### Research Question and Motivation

Core research question:

> How can explainable text-mining methods help users explore topic patterns
> and compare news coverage across media sources?

The motivation is interpretability and traceability. Rather than a black-box model
producing opaque labels, EchoMap uses methods whose outputs can be inspected and
explained step by step: TF-IDF keyword weights, TextRank extractive summaries built
from original sentences, KMeans cluster assignments with representative keywords, and
cosine-similarity rankings. Every result view in the interface states what the numbers
do and do not mean — for example, similarity is explicitly not reprinting, causation,
or stance agreement, and cluster numbers are exploratory groups rather than validated
news categories.

### Data and Methods

- **Input**: user-provided CSV (required columns: title / content / source; optional:
  id, author, published_at, url). The project has **no crawler and no external API**;
  real data must be supplied by the user. The repository contains only clearly labeled
  **synthetic fixtures** for testing and demonstration.
- **Pipeline**: CSV ingestion with encoding fallback (utf-8-sig / utf-8 / gbk) →
  cleaning (whitespace trimming, date parsing, dropping rows with empty required
  fields, deduplication) → quality report comparing raw and cleaned data.
- **Analysis methods**: TF-IDF keywords (per document and per source corpus), TextRank
  extractive summarization, KMeans topic clustering with a fixed random state for
  reproducibility, cosine-similarity Top-N, and a source × cluster cross-tabulation.
- **Traceability**: each loaded dataset gets a content fingerprint shown in the UI
  alongside import metadata and the cleaning steps applied; synthetic data is labeled
  as such everywhere it appears.

### Current Implementation

Phases delivered and verified to date:

- Data ingestion, cleaning, and quality reporting (CSV upload, encoding fallback,
  cleaning, raw-vs-clean quality overview)
- Text analysis: preprocessing (jieba + stopword list), TF-IDF keywords, TextRank
  summarization, KMeans clustering, cosine similarity
- Streamlit interface: data import, quality overview, source/date distributions,
  adjustable topic-clustering explorer, multi-source comparison (source keywords and
  source × cluster distribution), article detail with similar-article navigation
- Data provenance panel, a data-preparation guide with a CSV template
  (`docs/DATA_PREPARATION.md`), and demonstration documents (demo script, verified
  example observations on synthetic data)
- Automated test suite: 163 unit tests (standard-library unittest), all passing at the
  last full run

### Limitations and Future Work

- **No real-news study has been conducted.** All validated behavior is demonstrated on
  labeled synthetic fixtures; no claims are made about real media.
- Single-document TF-IDF weights degrade to term-frequency scale; TextRank relies on
  lexical overlap; cluster labels are exploratory and sensitive to parameters on small
  corpora; similarity reflects vector closeness only.
- Preprocessing is Chinese-focused; no clustering-quality metrics are provided yet.
- Future work: adoption of real user-supplied datasets, analysis report export,
  performance validation on larger corpora, and more robust topic-quality evaluation.

### Personal Contribution

- Defined the research question, project scope, and phased development plan
  (documented in `docs/DEVELOPMENT_LOG.md`).
- Implemented the codebase in Python using AI-assisted development; kept analysis
  logic in pure functions separate from the UI so it can be tested independently.
- Wrote and maintained the unit-test suite; required all automated tests to pass
  before each phase was accepted.
- Verified features manually in the browser at each phase and kept an honest
  development log, including failures and their root causes.
- Authored the data-preparation guide and CSV template so real datasets can be
  adopted later without code changes.

【To confirm / 待确认】before external use — the items below are intentional
placeholders, left blank rather than filled with assumptions:

1. AI-assisted development wording:
   `[TO CONFIRM: how to phrase the AI-assisted development workflow; the current
   draft uses "AI-assisted development"]`
2. Project timeline:
   `[TO CONFIRM: start date – end date, time invested]`
3. Coursework / independent project and acknowledgments:
   `[TO CONFIRM: whether this is coursework or an independent project; advisor or
   collaborator acknowledgments if any]`
4. Repository link / contact / demo video:
   `[TO CONFIRM: links to include]`

---

## 中文对照

### 项目概述

EchoMap 是一个用可解释文本挖掘方法探索新闻文本的交互式 Web 应用。用户上传新闻
CSV 文件后，应用会检查并记录数据质量，然后呈现关键词结构、抽取式摘要、探索性
主题聚类、文章间相似度以及跨来源对比。项目采用单页 Streamlit 应用实现
（Python、pandas、scikit-learn、jieba、matplotlib），分析逻辑保持为可独立测试的
纯函数，并有自动化单元测试覆盖。

### 研究问题与动机

核心研究问题：

> 可解释的文本挖掘方法，如何帮助用户探索新闻主题模式、并对比不同媒体的报道内容？

动机是可解释性与可追溯性。EchoMap 不使用产生不透明标签的黑箱模型，而是选用输出
可以被逐步检查和解释的方法：TF-IDF 关键词权重、由原句构成的 TextRank 抽取式摘要、
带代表关键词的 KMeans 聚类、余弦相似度排序。界面中每个结果视图都说明这些数字
**能**和**不能**说明什么——例如，相似度明确不代表转载、因果或立场一致；聚类编号
是探索性分组而非已验证的新闻类别。

### 数据与方法

- **输入**：用户提供的 CSV（必需列：title / content / source；可选：id、author、
  published_at、url）。项目**没有爬虫和外部 API**；真实数据须由使用者自行提供。
  仓库内只有明确标记的**合成测试数据**，用于测试与演示。
- **流程**：CSV 导入（编码回退 utf-8-sig / utf-8 / gbk）→ 清洗（去空白、日期解析、
  删除必需字段为空的行、去重）→ 原始与清洗后数据的质量对比报告。
- **分析方法**：TF-IDF 关键词（单篇与来源语料级）、TextRank 抽取式摘要、固定随机
  种子的 KMeans 主题聚类、余弦相似度 Top-N、来源×聚类交叉表。
- **可追溯性**：每个载入的数据集都有内容指纹，与导入信息、清洗步骤一并显示在界面；
  合成数据在出现处均予标注。

### 当前实现

已交付并验证的阶段：

- 数据导入、清洗与质量报告（CSV 上传、编码回退、清洗、原始/清洗后质量概览）
- 文本分析：预处理（jieba 分词 + 停用词表）、TF-IDF 关键词、TextRank 摘要、
  KMeans 聚类、余弦相似度
- Streamlit 界面：数据导入、质量概览、来源/日期分布、可调聚类数的主题探索、
  多来源对比（来源关键词与来源×主题分布）、新闻详情与相似新闻跳转
- 数据档案区块、数据准备规范与 CSV 模板（`docs/DATA_PREPARATION.md`）、
  演示文档（演示脚本、合成数据上的已核验示例观察）
- 自动化测试：163 个单元测试（标准库 unittest），最近一次全量运行全部通过

### 局限与后续工作

- **尚未开展任何真实新闻研究。** 所有已验证行为均在明确标记的合成数据上演示；
  不对真实媒体作任何断言。
- 单篇 TF-IDF 权重退化为词频量级；TextRank 依赖词面重叠；聚类标签是探索性的，
  小语料下对参数敏感；相似度仅反映向量接近程度。
- 预处理以中文为主；尚未提供聚类质量指标。
- 后续工作：接入使用者提供的真实数据集、分析报告导出、更大语料的性能验证、
  更稳健的主题质量评估。

### 个人贡献

- 确定研究问题、项目范围与分阶段开发计划（记录于 `docs/DEVELOPMENT_LOG.md`）。
- 使用 AI 辅助开发方式以 Python 实现全部代码；将分析逻辑与界面分离为可独立测试的
  纯函数。
- 编写并维护单元测试套件；要求每个阶段自动化测试全部通过后才进入验收。
- 每阶段在浏览器中人工验证功能，并保持诚实的开发日志记录（包括失败及根因）。
- 撰写数据准备规范与 CSV 模板，使真实数据集后续可以不经代码改动直接接入。

【To confirm / 待确认】（对外使用前需确认）——以下为有意保留的占位项，
不以猜测内容填充：

1. AI 协作表述口径：
   `[待确认：如何表述与 AI 协作开发的方式；当前草稿使用 "AI-assisted development"]`
2. 项目起止时间与投入时长：
   `[待确认：起止日期、投入时长]`
3. 课程作业 / 独立项目与致谢：
   `[待确认：是否属于课程作业或独立项目；如需致谢指导教师或合作者请补充]`
4. 仓库链接 / 联系方式 / 演示视频：
   `[待确认：需要附上的链接]`
