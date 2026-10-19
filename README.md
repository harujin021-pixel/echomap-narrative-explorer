# EchoMap (English)

**AI-Powered Media Narrative Explorer**
Chinese name: **AI 驱动的媒体叙事探索平台**

> An independent project exploring explainable text-mining methods for media narrative analysis

---

## 1. Project Positioning & Research Question

EchoMap is an interactive analysis tool for digital media research. Using **explainable text-mining methods**
(TF-IDF keywords, TextRank extractive summaries, KMeans topic clustering, cosine similarity), it explores
the topic structure, keywords, and inter-article text similarity of news texts, helping users understand
the structural features of news content.

Core research question:

> How can explainable text-mining methods help users explore topic patterns
> and compare news coverage across media sources?

The project is positioned as an **independent project**, favoring simple, explainable Python
solutions that are easy for a beginner to maintain.

**Boundary statement**: this project does not aim to prove media bias, media manipulation, or reporting
intent. Text similarity **does not equal** a reprint relationship, causation, or shared stance; cluster IDs
are exploratory, algorithm-generated groups, **not** verified news categories; extractive summaries are
**not** fact-checks. The UI shows the same notices at the corresponding features.

> **Current progress: Phase 4.4 completed and passed manual acceptance** (data import / cleaning / quality
> report + text analysis algorithms + Streamlit interactive UI + data provenance & cross-source comparison
> + research demonstration documents).
> The project has **no real news data yet**. The example CSVs in this repository are **clearly labeled
> synthetic test data**, not real news; when the example data is loaded, the UI labels it as "synthetic
> test data" throughout.
> Users can upload their own CSV (real data) through the UI for analysis; all metrics are computed from
> the actual data.

### Research Demonstration

The repository currently contains no real news data; the demonstration is based entirely on a clearly
labeled synthetic corpus, is only meant to show the tool's capabilities, and **does not represent research
findings about any real media**:

- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — a ~3-minute UI demo flow
  (research question → data → methods → actual observations → limitations & next steps)
- [docs/PROJECT_INTRO.md](docs/PROJECT_INTRO.md) — project introduction draft (English main text + Chinese reference)
- [docs/EXAMPLE_OBSERVATIONS.md](docs/EXAMPLE_OBSERVATIONS.md) — verified example observations on
  synthetic data (SYNTHETIC DATA DEMONSTRATION; the numbers come from real program output)

---

## 2. Feature List (Implemented / Verified)

The features below are **implemented in the current code** and have passed 192 automated unit tests plus
browser-side manual acceptance (see [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md) for details):

### Data Import & Quality (Phase 1 + 3.1)
- CSV upload (with automatic encoding detection across utf-8-sig / utf-8 / gbk) and required-column validation
- Data cleaning: HTML tag/entity stripping, whitespace stripping, date parsing, removing rows with empty required columns, deduplication
- Data quality overview before/after cleaning (record counts, duplicate rows, missing required fields, date summary)
- One-click loading of the synthetic demo data (data identity labeled throughout); when an upload fails,
  the previous data is kept and a clear warning is shown

### Text Analysis (Phase 2)
- Chinese preprocessing: jieba word segmentation, stop-word filtering (a separately maintained stop-word list)
- TF-IDF keyword extraction (single article / corpus level)
- TextRank extractive summarization (PageRank-based; every summary sentence comes from the original text)
- Topic clustering (TF-IDF + KMeans, with representative keywords and the article list of each cluster)
- Article similarity (cosine similarity Top-N, excluding the article itself)

### Interactive UI (Phase 3)
- Data Overview: source distribution, publication date distribution, field completeness, body-length
  statistics (matplotlib charts; automatically falls back to the built-in chart when a CJK font is unavailable)
- Topic Clustering visualization: adjustable cluster count, per-topic counts / shares / representative
  keywords, browsing articles within a topic
- Article detail: title / source / date / body, keywords, extractive summary; placeholder notices shown
  when optional fields are missing
- Similar-articles list and article-to-article navigation (continue exploring)

### Data Provenance & Cross-Source Comparison (Phase 4)
- Data Provenance: data fingerprint, import information, cleaning steps (session-level display, not a
  persistent audit log)
- Real-data preparation guide and CSV templates ([docs/DATA_PREPARATION.md](docs/DATA_PREPARATION.md) + `data/templates/`)
- Cross-Source Comparison: source keyword comparison, source × topic distribution (with sample-size
  notices and interpretation-boundary notes)
- Research demonstration documents: demo script, project introduction draft, example observations on
  synthetic data (see "Research Demonstration" in Section 1)

### Not yet implemented (no fabricated progress)
- Narrative-frame comparison, stance detection, propagation-chain tracing — **not implemented** (the
  current cross-source comparison covers only keywords and topic distribution)
- Analysis report export — **not implemented**
- JSON / plain-text import — **not implemented** (CSV only at present)
- Collection and ingestion of real news data — **not implemented** (no crawler; real data must be
  prepared and uploaded by the user)

---

## 3. Directory Structure

```text
AI-Powered Media Narrative Explorer/   # = EchoMap project root (local working directory; no nested subdirectories)
├── app/
│   └── app.py             # Streamlit single-file main entry (data import + overview + clustering + detail/similar)
├── src/                   # Core source code (independently testable)
│   ├── data/              # Data loading, cleaning & quality report (Phase 1)
│   │   ├── loader.py      # CSV import and required-column validation
│   │   ├── cleaning.py    # Data cleaning
│   │   ├── quality.py     # Data quality report
│   │   └── pipeline.py    # End-to-end pipeline
│   ├── analysis/          # Text analysis algorithms (Phase 2)
│   │   ├── preprocessing.py    # Chinese preprocessing & stop words
│   │   ├── stopwords_zh.txt    # Chinese stop-word list (maintained separately)
│   │   ├── vectorize.py        # Shared TF-IDF utilities
│   │   ├── keywords.py         # TF-IDF keywords
│   │   ├── summarization.py    # TextRank extractive summary
│   │   ├── clustering.py       # KMeans topic clustering
│   │   ├── similarity.py       # Cosine similarity
│   │   └── source_compare.py   # Source keyword comparison & source × topic cross-tab (Phase 4.3)
│   ├── ui/                # UI helper pure functions (Phase 3)
│   │   ├── data_io.py     # Upload adapter & synthetic demo loading
│   │   ├── overview.py    # Overview statistics & charts
│   │   ├── cluster_view.py# Cluster display helpers
│   │   ├── article_view.py# Detail / similar-articles helpers
│   │   ├── i18n.py        # Bilingual UI strings (English/中文, Phase 4.5)
│   │   └── provenance.py  # Data provenance pure functions (Phase 4.1)
│   └── visualization/     # Visualization (reserved; currently unused)
├── tests/                 # Tests (stdlib unittest, 19 files / 192 tests)
│   └── fixtures/          # Synthetic test samples (clearly labeled; not real news)
├── data/raw/, data/processed/   # Data directories (excluded by .gitignore)
├── data/templates/        # Data preparation CSV templates (synthetic examples; see docs/DATA_PREPARATION.md)
├── reports/               # Quality report output (excluded by .gitignore)
├── docs/                  # DEVELOPMENT_LOG.md (development log), PHASE2_ANALYSIS.md (algorithm docs),
│                          # DATA_PREPARATION.md (data preparation guide), DEMO_SCRIPT.md (demo script),
│                          # PROJECT_INTRO.md (project introduction), EXAMPLE_OBSERVATIONS.md (example observations)
├── README.md
├── requirements.txt
├── .streamlit/config.toml # Disables Streamlit usage statistics
├── .gitignore
└── .env.example
```

---

## 4. Environment Requirements

Real environment verified on this machine (2026-10-17):

| Item | Version / Status |
| --- | --- |
| Operating system | Windows |
| Python | 3.10.11 |
| pip | 23.0.1 |
| Git | **Not installed** (cannot `git init`; `.gitignore` is ready) |

> **Important:** typing `python` directly on this machine hits a 0-byte Windows Store placeholder program.
> Please always use the Python launcher `py`, e.g. `py --version`.

---

## 5. Installation

### 5.1 Dependency status

- `streamlit`, `pandas`, `numpy`, `scikit-learn`, `jieba`, `matplotlib`, `networkx`, `wordcloud`, `requests`
  are **already installed** on this machine; versions are pinned in [requirements.txt](requirements.txt).
- **Not installed yet, and not required for now** (kept commented out in requirements.txt):
  - `plotly` (current charts use the already-installed matplotlib)
  - `pytest` (tests use the stdlib `unittest`)
  - `python-dotenv` (no `.env` reading for now)
- Phase 3 installed **no new dependencies**.

### 5.2 Install commands (run as needed)

```powershell
# Optional: create and activate a virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install the enabled dependencies
py -m pip install -r requirements.txt
```

> If you use the currently installed dependencies directly, you can skip this step.

---

## 6. Running

### 6.1 Run the app

From the project root:

```powershell
py -m streamlit run app/app.py
```

After startup, choose a data source in the **left sidebar**:
- Click "Load synthetic demo data" — loads the built-in synthetic corpus (labeled as synthetic test data throughout);
- Or upload your own CSV (must contain the required columns, see Section 7) and click "Import".

Page layout: Data Provenance & Data Quality Overview → Cleaned Data Preview → Data Overview (source / date
distributions) → Topic Clustering → Cross-Source Comparison → Article Detail & Similar Articles.

### 6.2 Run the tests

From the project root:

```powershell
py -m unittest discover -s tests -v
```

The tests use the stdlib `unittest` and need no extra dependencies. Currently **19 test files / 192 tests**:

- Phase 1: `test_project_structure.py`, `test_loader.py`, `test_cleaning.py`,
  `test_quality.py`, `test_pipeline.py` (21 tests)
- Phase 2: `test_preprocessing.py`, `test_keywords.py`, `test_summarization.py`,
  `test_clustering.py`, `test_similarity.py` (47 tests)
- Phase 3: `test_data_io.py`, `test_app_helpers.py`, `test_overview.py`,
  `test_cluster_view.py`, `test_article_view.py` (59 tests)
- Phase 4: `test_provenance.py`, `test_source_compare.py`, `test_data_template.py`,
  `test_i18n.py` (65 tests)

Latest full run: **192 passed / 0 failed / 0 errors, exit status 0**
(see the phase-by-phase records in DEVELOPMENT_LOG.md).

---

## 7. Data Notes

> 📄 **Preparing your own news data?** Please read [docs/DATA_PREPARATION.md](docs/DATA_PREPARATION.md) first:
> CSV format and field specifications, date formats, cleaning behavior, data licensing & privacy notes,
> and common import troubleshooting.
> Companion template: `data/templates/news_dataset_template.csv` (3 clearly labeled synthetic example records).

### 7.1 Data categories (important)

| Data type | Location | Notes |
| --- | --- | --- |
| Synthetic test data | `tests/fixtures/*.csv` | Manually fabricated news text; the `data_source` column is marked `synthetic_test_fixture`; **not real news**; used only for development and testing |
| User-uploaded data | Uploaded via the UI | Provenance is the user's responsibility; the UI labels it "user-uploaded data" |
| Real news data | `data/raw/` (currently empty) | **The project has no real news data yet**; if it is ever connected, the data must be prepared and uploaded by the user |

The data-source labels in the UI are generated dynamically from the actual load result: the synthetic
example shows "synthetic test data" together with a not-real-news notice; user uploads show "user-uploaded
data" plus the file name. When an upload fails, the last successfully imported dataset is kept with a
prominent warning — a failed file is never disguised as imported data.

### 7.2 CSV data format

Required columns:

| Column | Meaning |
| --- | --- |
| `title` | News headline |
| `content` | News body text |
| `source` | Source media |

Optional columns: `id`, `author`, `published_at`, `url`.

Cleaning rules (see `src/data/cleaning.py`): strip leading/trailing whitespace → parse `published_at`
(failures recorded as missing, **rows are not deleted**) → delete rows with any empty required column →
delete fully duplicated rows → reset the index.

### 7.3 Command-line import (optional)

```powershell
py -c "from src.data.pipeline import run_ingestion; r = run_ingestion('tests/fixtures/synthetic_news_corpus.csv'); print('raw rows =', len(r['raw'])); print('clean rows =', len(r['clean']))"
```

**Note: the example file above is synthetic data, not real news.**
Importing via the UI upload/example button writes no report files; to generate a quality report file,
call `src/data/pipeline.run_ingestion` yourself with its `report_path` parameter.

---

## 8. Algorithm Documentation

For the principles, parameters, edge-case handling, and known limitations of each analysis module (IDF
degradation in single-article TF-IDF, TextRank's surface-word-overlap limitation and mis-segmentation of
English abbreviations, the exploratory nature of cluster IDs, similarity ≠ reprinting, etc.), see
[docs/PHASE2_ANALYSIS.md](docs/PHASE2_ANALYSIS.md). The UI shows corresponding notices as well.

---

## 9. Development Log

Phase progress, commands that were run, and real test results are all recorded in
[docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md).

---

## 10. Known Limitations & TODOs

**Known limitations (all flagged in the UI)**:
- For a single article, TF-IDF weights degrade to term-frequency scale and only serve as a reference for
  frequent words in the text;
- TextRank is based on surface word overlap, and capitalized English abbreviations such as `U.S.` may be
  mis-segmented;
- Cluster IDs are exploratory, algorithm-generated groups and are unstable on small samples;
- Text similarity only reflects surface/vector-level closeness;
- Chinese display in matplotlib depends on system fonts (automatic fallback when unavailable);
- The project has never validated its analysis results on a real news corpus; all verified conclusions
  are based solely on synthetic test data.

**TODOs**:
- [ ] Install Git and initialize the version repository (Git is not installed in the current environment).
- [ ] Prepare and ingest **real news data** (uploaded by the user; the project has no crawler).
- [ ] More cross-source comparison dimensions (e.g. narrative-frame analysis) — beyond the current scope, not scheduled.
- [ ] Analysis report export.
- [ ] Support JSON / plain-text import.
- [ ] Performance validation on large corpora (thousands of rows or more).
- [ ] If needed later, confirm installing `plotly` / `pytest` / `python-dotenv` (none currently installed).

---

# 中文说明

# EchoMap

**AI-Powered Media Narrative Explorer**
中文名称：**AI 驱动的媒体叙事探索平台**

> 面向媒体叙事分析的独立项目

---

## 1. 项目定位与研究问题

EchoMap 是一个面向数字媒体研究的交互式分析工具。它通过**可解释的文本挖掘方法**
（TF-IDF 关键词、TextRank 抽取式摘要、KMeans 主题聚类、余弦相似度）探索新闻文本的
主题结构、关键词与文章间文本相似性，辅助理解新闻内容的结构特征。

核心研究问题：

> How can explainable text-mining methods help users explore topic patterns
> and compare news coverage across media sources?

本项目定位为**独立的项目**，优先采用简单、可解释、适合初学者维护的 Python 技术方案。

**边界声明**：本项目不以证明媒体偏见、媒体操纵或报道意图为目标。文本相似度**不等于**
转载关系、因果关系或立场一致；聚类编号是算法生成的探索性分组，**不是**已验证的新闻类别；
抽取式摘要**不是**事实核查。界面在相应功能处均有同样的提示。

> **当前进度：Phase 4.4 已完成并通过人工验收**（数据导入/清洗/质量报告 + 文本分析算法 +
> Streamlit 交互界面 + 数据可追溯性与多来源对比 + 研究演示文档）。
> 项目**尚无真实新闻数据**。仓库内的示例 CSV 均为**明确标记的合成测试数据**，不是真实新闻；
> 界面加载示例数据时会全程标注「合成测试数据」。
> 用户可通过界面上传自己的 CSV（真实数据）进行分析，所有指标均由实际数据计算得出。

### 研究演示（Research Demonstration）

当前仓库没有真实新闻数据；演示全部基于明确标记的合成语料，仅用于展示工具能力，
**不代表任何真实媒体的研究发现**：

- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) —— 约 3 分钟的界面演示流程
  （研究问题 → 数据 → 方法 → 实际观察 → 局限与下一步）
- [docs/PROJECT_INTRO.md](docs/PROJECT_INTRO.md) —— 项目介绍初稿（英文主稿 + 中文对照）
- [docs/EXAMPLE_OBSERVATIONS.md](docs/EXAMPLE_OBSERVATIONS.md) —— 合成数据上已核验的
  示例观察（SYNTHETIC DATA DEMONSTRATION，数值来自真实程序输出）

---

## 2. 功能清单（已实现 / 已验证）

以下功能**当前代码已实现**，并通过 192 个自动化单元测试与浏览器端人工验收
（详见 [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)）：

### 数据导入与质量（Phase 1 + 3.1）
- CSV 上传（含编码自动识别 utf-8-sig / utf-8 / gbk）与必需列校验
- 数据清洗：剥除 HTML 标签/实体、去空白、日期解析、删除必需列为空的行、去重
- 清洗前后数据质量概览（记录数、重复行、必需字段缺失、日期摘要）
- 合成示例数据一键加载（全程标注数据身份）；上传失败时保留旧数据并明确警示

### 文本分析（Phase 2）
- 中文预处理：jieba 分词（词性标注，关闭 HMM 新词猜测）、名词性词性过滤、停用词过滤（独立停用词表）、单字与纯数字 token 提前剔除、敏感词过滤（独立敏感词表）
- TF-IDF 关键词提取（单篇 / 语料级）
- TextRank 抽取式摘要（基于 PageRank，摘要句全部来自原文）
- 主题聚类（TF-IDF + KMeans，含各簇代表关键词与簇内文章列表）
- 文章相似度（余弦相似度 Top-N，排除自身）

### 交互界面（Phase 3）
- 数据概览：来源分布、发布日期分布、字段完整性、正文长度统计（matplotlib 图表，
  中文字体不可用时自动降级为内置图表）
- 主题聚类可视化：可调聚类数、各主题数量/占比/代表关键词、主题内文章浏览
- 新闻详情：标题/来源/日期/正文、关键词、抽取式摘要，可选字段缺失时显示占位提示
- 相似新闻列表与文章间跳转（继续探索）

### 数据可追溯性与多来源对比（Phase 4）
- 数据档案（Data Provenance）：数据指纹、导入信息、清洗步骤（会话级展示，非持久化审计日志）
- 真实数据准备规范与 CSV 模板（[docs/DATA_PREPARATION.md](docs/DATA_PREPARATION.md) + `data/templates/`）
- 多来源对比：来源关键词对比、来源×主题分布（含样本量提示与解读边界说明）
- 研究演示文档：演示脚本、项目介绍初稿、合成数据示例观察（见第 1 节「研究演示」）

### 尚未实现（不虚构进度）
- 叙事框架对比、立场识别、传播链追踪 —— **未实现**（当前多来源对比仅覆盖关键词与主题分布）
- 分析报告导出 —— **未实现**
- JSON / 纯文本导入 —— **未实现**（当前仅 CSV）
- 真实新闻数据的采集与接入 —— **未实现**（无爬虫；真实数据需用户自行上传）

---

## 3. 目录结构

```text
AI-Powered Media Narrative Explorer/   # = EchoMap 项目根目录（本机工作目录，无嵌套子目录）
├── app/
│   └── app.py             # Streamlit 单文件主入口（数据导入 + 概览 + 聚类 + 详情/相似）
├── src/                   # 核心源码（可独立测试）
│   ├── data/              # 数据读取、清洗与质量报告（Phase 1）
│   │   ├── loader.py      # CSV 导入与必需列校验
│   │   ├── cleaning.py    # 数据清洗
│   │   ├── quality.py     # 数据质量报告
│   │   └── pipeline.py    # 串联流程
│   ├── analysis/          # 文本分析算法（Phase 2）
│   │   ├── preprocessing.py    # 中文预处理、停用词与敏感词过滤
│   │   ├── stopwords_zh.txt    # 中文停用词表（独立维护）
│   │   ├── sensitive_words.txt # 敏感词表（独立维护，不参与分析、不出现在界面）
│   │   ├── vectorize.py        # 共享 TF-IDF 工具
│   │   ├── keywords.py         # TF-IDF 关键词
│   │   ├── summarization.py    # TextRank 抽取式摘要
│   │   ├── clustering.py       # KMeans 主题聚类
│   │   ├── similarity.py       # 余弦相似度
│   │   └── source_compare.py   # 来源关键词对比与来源×主题交叉表（Phase 4.3）
│   ├── ui/                # 界面辅助纯函数（Phase 3）
│   │   ├── data_io.py     # 上传适配层与合成示例加载
│   │   ├── overview.py    # 概览统计与图表
│   │   ├── cluster_view.py# 聚类展示辅助
│   │   ├── article_view.py# 详情/相似新闻辅助
│   │   ├── i18n.py        # 中英双语界面文案（Phase 4.5）
│   │   └── provenance.py  # 数据档案纯函数（Phase 4.1）
│   └── visualization/     # 可视化（预留，当前未使用）
├── tests/                 # 测试（标准库 unittest，19 个文件 / 192 个测试）
│   └── fixtures/          # 合成测试样本（明确标记，非真实新闻）
├── data/raw/, data/processed/   # 数据目录（被 .gitignore 排除）
├── data/templates/        # 数据准备 CSV 模板（合成示例，见 docs/DATA_PREPARATION.md）
├── reports/               # 质量报告输出（被 .gitignore 排除）
├── docs/                  # DEVELOPMENT_LOG.md（开发日志）、PHASE2_ANALYSIS.md（算法文档）、
│                          # DATA_PREPARATION.md（数据准备规范）、DEMO_SCRIPT.md（演示脚本）、
│                          # PROJECT_INTRO.md（项目介绍）、EXAMPLE_OBSERVATIONS.md（示例观察）
├── README.md
├── requirements.txt
├── .streamlit/config.toml # 关闭 Streamlit 使用统计
├── .gitignore
└── .env.example
```

---

## 4. 环境要求

本机已检查到的真实环境（2026-10-17）：

| 项目 | 版本 / 状态 |
| --- | --- |
| 操作系统 | Windows |
| Python | 3.10.11 |
| pip | 23.0.1 |
| Git | **未安装**（无法 `git init`；`.gitignore` 已就绪） |

> **重要提示：** 本机直接输入 `python` 会命中一个 0 字节的 Windows Store 占位程序。
> 请统一使用 Python 启动器 `py`，例如 `py --version`。

---

## 5. 安装方法

### 5.1 依赖现状

- `streamlit`、`pandas`、`numpy`、`scikit-learn`、`jieba`、`matplotlib`、`networkx`、`wordcloud`、`requests`
  在本机**已安装**，版本已在 [requirements.txt](requirements.txt) 中固定。
- **尚未安装、暂不作为必需依赖**（在 requirements.txt 中保持注释）：
  - `plotly`（当前图表用已安装的 matplotlib）
  - `pytest`（测试用标准库 `unittest`）
  - `python-dotenv`（暂不实现 `.env` 读取）
- Phase 3 **未安装任何新依赖**。

### 5.2 安装命令（按需执行）

```powershell
# 可选：创建并激活虚拟环境
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装已启用的依赖
py -m pip install -r requirements.txt
```

> 如果直接使用当前已安装的依赖，可跳过本步。

---

## 6. 运行方法

### 6.1 运行应用

在项目根目录执行：

```powershell
py -m streamlit run app/app.py
```

启动后在**左侧边栏**选择数据来源：
- 点击「加载合成示例数据」——加载内置合成语料（全程标注为合成测试数据）；
- 或上传自己的 CSV（需包含必需列，见第 7 节），点击「开始导入」。

页面展示：数据档案与质量概览 → 清洗后数据预览 → 数据概览（来源/日期分布）→
主题聚类分析 → 多来源对比 → 新闻详情与相似新闻。

### 6.2 运行测试

在项目根目录执行：

```powershell
py -m unittest discover -s tests -v
```

测试使用标准库 `unittest`，无需额外依赖。当前共 **19 个测试文件 / 192 个测试**：

- Phase 1：`test_project_structure.py`、`test_loader.py`、`test_cleaning.py`、
  `test_quality.py`、`test_pipeline.py`（21 个）
- Phase 2：`test_preprocessing.py`、`test_keywords.py`、`test_summarization.py`、
  `test_clustering.py`、`test_similarity.py`（47 个）
- Phase 3：`test_data_io.py`、`test_app_helpers.py`、`test_overview.py`、
  `test_cluster_view.py`、`test_article_view.py`（59 个）
- Phase 4：`test_provenance.py`、`test_source_compare.py`、`test_data_template.py`、
  `test_i18n.py`（65 个）

最近一次全量运行结果：**192 通过 / 0 失败 / 0 错误，退出状态 0**
（详见 DEVELOPMENT_LOG.md 的各阶段记录）。

---

## 7. 数据说明

> 📄 **准备自己的新闻数据？** 请先阅读 [docs/DATA_PREPARATION.md](docs/DATA_PREPARATION.md)：
> CSV 格式与字段规范、日期格式、清洗行为、数据授权与隐私注意事项、常见导入问题排查。
> 配套模板：`data/templates/news_dataset_template.csv`（3 条明确标记的合成示例记录）。

### 7.1 数据分类（重要）

| 数据类型 | 位置 | 说明 |
| --- | --- | --- |
| 合成测试数据 | `tests/fixtures/*.csv` | 人工编造的新闻文本，`data_source` 列标记为 `synthetic_test_fixture`，**不是真实新闻**；仅用于开发与测试 |
| 用户上传数据 | 通过界面上传 | 来源由用户负责；界面会标注为「用户上传数据」 |
| 真实新闻数据 | `data/raw/`（当前为空） | **项目尚无真实新闻数据**；如接入需用户自行准备并上传 |

界面中的数据来源标记由实际加载结果动态生成：合成示例显示「合成测试数据」并附
非真实新闻声明；用户上传显示「用户上传数据」及文件名。上传失败时保留上一份成功
数据并显著警示，不会把失败文件伪装成已导入数据。

### 7.2 CSV 数据格式

必需列：

| 列名 | 含义 |
| --- | --- |
| `title` | 新闻标题 |
| `content` | 新闻正文 |
| `source` | 来源媒体 |

可选列：`id`、`author`、`published_at`、`url`。

清洗规则（见 `src/data/cleaning.py`）：剥除 HTML 标签并还原 HTML 实体（如 `&nbsp;`）→ 去除首尾空白
→ 解析 `published_at`（失败记为缺失，**不删行**）
→ 删除必需列为空的行 → 删除完全重复行 → 重置索引。

### 7.3 命令行导入流程（可选）

```powershell
py -c "from src.data.pipeline import run_ingestion; r = run_ingestion('tests/fixtures/synthetic_news_corpus.csv'); print('raw rows =', len(r['raw'])); print('clean rows =', len(r['clean']))"
```

**注意：上述示例文件是合成数据，不是真实新闻。**
界面通过上传/示例按钮导入时不会写任何报告文件；如需生成质量报告文件，
可参考 `src/data/pipeline.run_ingestion` 的 `report_path` 参数自行调用。

---

## 8. 算法文档

各分析模块的原理、参数、边界处理与已知局限（单篇 TF-IDF 的 IDF 退化、
TextRank 的词面相似局限与英文缩写误切、聚类编号的探索性质、相似度 ≠ 转载等）
详见 [docs/PHASE2_ANALYSIS.md](docs/PHASE2_ANALYSIS.md)。界面相应位置亦有提示。

---

## 9. 开发日志

阶段进展、运行过的命令与真实测试结果，统一记录在
[docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)。

---

## 10. 已知限制与待办事项

**已知限制（界面均有提示）**：
- 单篇文章的 TF-IDF 权重退化为词频量级，仅作文内高频词参考；
- TextRank 基于词面重叠，`U.S.` 等大写英文缩写可能被误切分；
- 聚类编号是算法探索性分组，小样本下不稳定；
- 文本相似度只反映词面/向量接近程度；
- matplotlib 中文显示依赖系统字体（不可用时自动降级）；
- 项目从未在真实新闻语料上验证分析效果，所有已验证结论仅基于合成测试数据。

**待办事项**：
- [ ] 安装 Git 并初始化版本库（当前环境未安装 Git）。
- [ ] 准备并接入**真实新闻数据**（用户自行上传；项目无爬虫）。
- [ ] 更多来源对比维度（如叙事框架分析）——超出当前范围，未排期。
- [ ] 分析报告导出。
- [ ] 支持 JSON / 纯文本导入。
- [ ] 大语料（数千行以上）性能验证。
- [ ] 如后续需要，再确认安装 `plotly` / `pytest` / `python-dotenv`（当前均未安装）。
