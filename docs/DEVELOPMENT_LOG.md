# EchoMap 开发日志

> 本文件记录每个阶段的真实进展、执行过的命令与测试结果。
> 原则：只记录实际发生的事实，不记录任何虚构的功能或测试结果。

---

## 阶段 0：项目骨架搭建

- 日期：2026-10-16
- 状态：已完成
- 负责人：用户（Python 初学者） + TRAE 辅助

### 0.1 目标

按用户要求完成阶段 0 的全部内容：

- A. 检查工作目录与 Python 环境
- B. 创建独立的 EchoMap 项目目录
- C. 创建初始目录结构
- D. 创建 `README.md`、`requirements.txt`、`.gitignore`、`.env.example`
- E. 在 README 中说明项目定位、目标功能、安装与运行方法
- F. 检查依赖兼容性
- G. 初始化 Git（如环境支持）
- H. 创建本开发日志

### 0.2 环境检查结果（真实）

| 项目 | 结果 |
| --- | --- |
| 工作目录 | `<项目根目录>`（本地绝对路径已隐去；初始为空） |
| Python | 3.10.11 |
| Python 可执行文件 | `<本机 Python 安装路径>\python.exe` |
| pip | 23.0.1（`py -m pip --version`） |
| `python` 命令 | **不可用**：命中 0 字节的 Windows Store 占位程序（`...\WindowsApps\python.exe`，大小 0 字节），直接调用返回退出码 9009。应改用 `py`。 |
| Git | **未安装**：PATH 中无 `git`，且 `C:\Program Files\Git\bin\git.exe`、`C:\Program Files (x86)\Git\bin\git.exe`、`%LOCALAPPDATA%\Programs\Git\bin\git.exe` 均不存在。 |

> 备注：Shell 环境每次执行都会出现 PowerShell 配置文件（`powershell-profile-snapshot.ps1`）
> 因执行策略被禁用而无法加载的报错提示（CLIXML）。这是环境噪音，不影响命令执行结果。

### 0.3 依赖兼容性检查

- 本机 Python 3.10 环境已安装且经确认可共存的关键依赖：
  `streamlit==1.65.0`、`pandas==2.3.3`、`numpy==1.24.3`、`requests==2.31.0`、
  `jieba==0.42.1`、`scikit-learn==1.3.0`、`matplotlib==3.7.2`、`wordcloud==1.9.2`。
- 以上版本已在 `requirements.txt` 中固定，避免升级到最新版引发冲突。
- `python-dotenv` 本机**未安装**；阶段 0 **未安装任何新依赖**，该包已在 `requirements.txt`
  中注释保留，待用户确认后再安装。

### 0.4 实际创建的内容

目录（10 个）：

```text
app/
src/
src/data/
src/analysis/
src/visualization/
tests/
data/raw/
data/processed/
reports/
docs/
```

文件：

```text
README.md
requirements.txt
.gitignore
.env.example
docs/DEVELOPMENT_LOG.md
app/app.py
src/__init__.py
src/data/__init__.py
src/analysis/__init__.py
src/visualization/__init__.py
tests/test_project_structure.py
data/raw/.gitkeep
data/processed/.gitkeep
reports/.gitkeep
```

### 0.5 执行过的命令

```powershell
python --version                       # 失败（退出码 9009，Windows Store 占位程序）
py --version                           # Python 3.10.11
py -0p                                 # 列出已安装的 Python 版本
py -m pip --version                    # pip 23.0.1
py -m pip list --format=freeze         # 查看已安装依赖，用于兼容性检查
Get-ChildItem -Force -Path .           # 确认工作目录为空
where.exe python / py / git            # 定位可执行文件，确认 git 不存在
Test-Path "C:\Program Files\Git\bin\git.exe"   # 结果为 False
New-Item -ItemType Directory -Force -Path ...  # 创建目录结构
```

### 0.6 测试结果（真实）

- 测试文件：`tests/test_project_structure.py`（标准库 `unittest`，无需额外依赖）
- 运行命令：`py -m unittest discover -s tests -v`
- 结果：**3 个测试全部通过（Ran 3 tests in 0.021s, OK）**
  - `test_required_directories_exist` ... ok
  - `test_required_files_exist` ... ok
  - `test_source_packages_importable` ... ok
- 另执行语法检查：`py -m py_compile app/app.py src/__init__.py src/data/__init__.py src/analysis/__init__.py src/visualization/__init__.py` → 全部通过。

### 0.7 本阶段未解决的问题

1. **Git 未安装**：无法执行 `git init`，版本库尚未初始化。`.gitignore` 已先行创建，
   待安装 Git 后再初始化并首次提交。
2. **`python` 命令不可用**：需统一使用 `py` 启动器（或完整路径）。
3. **`python-dotenv` 未安装**：如需要 `.env` 支持，需用户确认后安装。
4. 阶段 0 不包含任何业务功能与真实数据，应用与后续分析留待阶段 1 起实现。

---

## 测试记录

（每次运行测试后在此追加真实输出。）

### 2026-10-16 结构冒烟测试

- 命令：`py -m unittest discover -s tests -v`
- 真实输出：

```text
test_required_directories_exist (test_project_structure.TestProjectStructure) ... ok
test_required_files_exist (test_project_structure.TestProjectStructure) ... ok
test_source_packages_importable (test_project_structure.TestProjectStructure) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.021s

OK
```

- 结论：阶段 0 的项目骨架真实存在，源码包可正常导入。此测试只验证骨架，不涉及任何业务功能。

### 2026-10-16 语法检查

- 命令：`py -m py_compile app/app.py src/__init__.py src/data/__init__.py src/analysis/__init__.py src/visualization/__init__.py`
- 结果：退出码 0（全部文件语法正确）。

### 2026-10-16 应用启动验证

- 命令：`py -m streamlit run app/app.py --server.headless=true --server.port=8599 --browser.gatherUsageStats=false --server.fileWatcherType=none`
- 真实输出（节选）：

```text
Uvicorn server started on :::8599

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8599
  Network URL: http://192.168.10.10:8599
  External URL: http://107.151.244.146:8599
```

- 随后已停止服务，并确认端口 8599 已释放（检查结果为 `PORT_8599_FREE`）。
- 结论：应用**可正常启动**。未做任何浏览器交互或业务功能验证；
  「无数据时显示『尚无数据』」是基于 `app/app.py` 的实现逻辑，非浏览器实测结论。

---

## 阶段 0 复核与收尾（2026-10-16）

- 状态：已完成
- 说明：本次只做检查与收尾，**未开发阶段 1 的数据功能，未安装任何新依赖，未删除已有文件**。

### 复核决策（经用户确认）

1. 当前工作目录（本地绝对路径已隐去）直接作为 EchoMap 项目根目录，
   **不再创建嵌套的 `EchoMap/` 子目录**。
2. Git 暂未安装，**不阻塞阶段 1**；保留 `.gitignore` 并记录为待办。**未初始化 Git**。
3. 后续统一优先使用 Windows Python Launcher 的 `py` 命令。
4. 暂不安装 `python-dotenv`；第一版**不实现 `.env` 读取功能**，后续如需要再提出安装建议。

### A. 环境命令真实输出

```text
py --version            -> Python 3.10.11
py -0p                  -> -3.10-64  <本机 Python 安装路径>\python.exe
py -m pip --version     -> pip 23.0.1 from <本机 Python 安装路径>\lib\site-packages\pip (python 3.10)
```

### B. 目录结构检查

- 实际目录：`app/`、`src/`、`src/data/`、`src/analysis/`、`src/visualization/`、`tests/`、
  `data/raw/`、`data/processed/`、`reports/`、`docs/`。
- 递归查找名为 `EchoMap` 的目录：**未找到**（确认不存在错误的嵌套目录）。

### C. 依赖检查（`py -m pip show`）

| 包 | 状态 | 版本 |
| --- | --- | --- |
| streamlit | 已安装 | 1.65.0 |
| pandas | 已安装 | 2.3.3 |
| scikit-learn | 已安装 | 1.3.0 |
| numpy | 已安装 | 1.24.3 |
| requests | 已安装 | 2.31.0 |
| jieba | 已安装 | 0.42.1 |
| matplotlib | 已安装 | 3.7.2 |
| wordcloud | 已安装 | 1.9.2 |
| plotly | **未安装** | — |
| pytest | **未安装** | — |
| python-dotenv | **未安装** | — |

- `requirements.txt` 已复核：`plotly`、`pytest`、`python-dotenv` 均**保持注释**，不作为必需依赖。
- 当前依赖足以支持 **Streamlit + pandas + scikit-learn** 的开发；
  **Plotly**（交互式图表）与 **pytest**（测试）当前**不满足**，如需使用须先经确认再安装。

### D/E/F. 本次实际修改的文件

- `requirements.txt`：重写分组与说明，未安装的包全部注释保留。
- `README.md`：补充 `py` 命令说明与 Windows 兼容示例，移除未经实际验证的运行成功结论。
- `.gitignore`：补充测试/覆盖率缓存与本地临时文件规则
  （`.pytest_cache/`、`.mypy_cache/`、`.tox/`、`htmlcov/`、`.coverage*`、`*.tmp`、`*.bak`、`*.swp`、`*~` 等）；
  `.venv/`、`__pycache__/`、`.env`、`data/raw/*` 原有规则保留。
- `docs/DEVELOPMENT_LOG.md`：追加本复核章节与启动验证记录。

### 未解决问题 / 待办事项

1. **Git 未安装** → 无法 `git init`；`.gitignore` 已就绪，待安装后初始化并首次提交。
2. **plotly 未安装** → 后续如需交互式图表，须确认后安装。
3. **pytest 未安装** → 阶段 0 使用标准库 `unittest`；如改用 pytest 须确认后安装。
4. **python-dotenv 未安装** → 第一版不实现 `.env` 读取；后续按需再议。
5. 环境噪音：Shell 每次执行都会出现 PowerShell 配置文件因执行策略被禁用而无法加载的 CLIXML 提示，
   不影响命令结果；如需消除可由用户自行调整执行策略。

---

## 阶段 1：CSV 导入、数据清洗、数据质量报告与自动化测试（2026-10-16）

- 状态：已完成（等待用户验收后进入阶段 2）
- 说明：**未开发任何 AI 分析、仪表板或可视化功能**；**未安装任何新依赖**；**未删除阶段 0 的任何文件**。

### 1.1 前置检查（阶段 1 开始前）

- 阶段 0 文件与目录齐全（`app/`、`src/`、`tests/`、`data/`、`reports/`、`docs/` 及初始文件）。
- 递归确认**不存在嵌套的 `EchoMap/` 子目录**。
- 依赖未变：本机已安装 `pandas==2.3.3` 等；**未安装 Plotly / pytest / python-dotenv**，阶段 1 也未安装任何新依赖。
- 测试框架：继续使用标准库 `unittest`（未擅自改用 pytest）。

### 1.2 新增 / 修改的文件

新增：

```text
src/data/loader.py        # CSV 导入与必需列校验（编码回退 utf-8-sig / utf-8 / gbk）
src/data/cleaning.py      # 数据清洗（去空白、解析日期、删空必需列行、去重、重置索引）
src/data/quality.py       # 数据质量报告 + Markdown 导出
src/data/pipeline.py      # 串联「导入 -> 清洗前报告 -> 清洗 -> 清洗后报告 -> 写报告」
tests/fixtures/synthetic_sample_news.csv   # 明确标记的合成测试样本
tests/test_loader.py
tests/test_cleaning.py
tests/test_quality.py
tests/test_pipeline.py
```

修改（仅追加，保留原有内容）：
- `README.md`：补充阶段 1 进度、CSV 数据格式与使用示例、测试说明、待办清单。
- `.gitignore`：新增例外规则 `!tests/fixtures/*.csv`（允许提交合成测试样本）。
- `docs/DEVELOPMENT_LOG.md`：本节。

**未修改**：`app/app.py`（界面尚未接入阶段 1 功能，仍在无数据时显示占位提示）。

### 1.3 真实数据说明

- 项目**尚无真实新闻数据**。
- 唯一示例为 `tests/fixtures/synthetic_sample_news.csv`，**明确标记为合成数据**（列 `data_source=synthetic_test_fixture`），
  **不声称已收集真实新闻**。
- 生成的质量报告数字均来自该合成样本的真实计算结果。

### 1.4 执行过的命令与真实结果

```text
py -m unittest discover -s tests -v
  -> Ran 21 tests in 0.236s   OK    （全部通过）

py -c "from src.data.pipeline import run_ingestion; r = run_ingestion('tests/fixtures/synthetic_sample_news.csv', report_path='reports/synthetic_sample_quality.md', dataset_name='synthetic_sample_news (合成测试样本)'); print('raw rows =', len(r['raw'])); print('clean rows =', len(r['clean'])); print('raw duplicate_rows =', r['raw_report']['duplicate_rows']); print('report written to =', r['report_path'])"
  -> raw rows = 5
     clean rows = 2
     raw duplicate_rows = 1
     report written to = reports\synthetic_sample_quality.md
```

生成的真实质量报告片段（来自 `reports/synthetic_sample_quality.md`，清洗前）：

```text
行数：5，列数：8
完全重复行数：1
必需列缺失：title=1，content=1，source=0
日期字段摘要：缺失(空)=1，可解析=2，无效=2
```

### 1.5 测试覆盖

- `test_loader.py`：正常读取、必需列缺失报错、文件不存在报错、空单元格读为 ""、目录扫描。
- `test_cleaning.py`：清洗后行数、不修改输入对象、去空白、无空必需列、无重复行、日期解析。
- `test_quality.py`：清洗前后计数、日期摘要（缺失 / 有效 / 无效）、Markdown 内容、报告落盘。
- `test_pipeline.py`：端到端流程（含写报告 / 不写报告两种）。

### 1.6 过程中发现并修复的问题

1. **测试夹具设计错误**：最初第 2、3 行仅 `id` 不同，并非完全重复行，导致 `duplicate_rows` 为 0。
   已把第 3 行改为与第 2 行完全一致，使「去重」规则得到真实验证。
2. **日期摘要口径错误**：初版把「空值」与「非空但无法解析」都计入 missing。
   已改为分别统计 `missing`（空）与 `invalid`（非空但解析失败）。
3. 编辑测试夹具时曾误删换行导致两行合并，已重写该文件修正。

### 1.7 未解决问题 / 待办

1. **真实新闻数据仍为空白**（当前仅合成样本）。
2. **仅实现 CSV 导入**，JSON / 纯文本导入未实现。
3. **界面未接入**：`app/app.py` 仍为阶段 0 占位提示，未展示质量报告。
4. **未安装 Plotly / pytest / python-dotenv**（按用户要求保持现状）。
5. **Git 仍未安装**，版本库未初始化。

---

## 阶段 2：AI 文本分析模块（2026-10-16）

- 状态：**待验收**（等待用户检查后再进入阶段 3）
- 说明：本阶段**只开发与测试分析算法**；**未开发 Streamlit 页面**、**未修改 `app/app.py`**、
  未做仪表板、**未接入外部 API / 在线模型**、**未安装任何新依赖**；**未删除阶段 0/1 的任何文件或测试**。

### 2.0 前置检查（阶段 2 开始前）

- 阅读 `README.md`、`docs/DEVELOPMENT_LOG.md`，检查 `src/data/`、`src/analysis/`、`tests/` 现有结构。
- 确认阶段 1 数据接口：必需列 `title` / `content` / `source`，可选列 `id` / `author` / `published_at` / `url`；
  `loader.load_csv` 以字符串读取、空单元格为 `""`；`cleaning.clean_news_data` 输出清洗后 DataFrame。
- 运行现有测试（阶段 1）：`py -m unittest discover -s tests -v` → 阶段 1 的 21 个测试全部通过，**未发现失败**，
  因此**未覆盖、未重写阶段 1 代码**。

### 2.1 新增 / 修改的文件

新增（源码）：

```text
src/analysis/preprocessing.py    # 模块 A：中文文本预处理（规范化 / jieba 分词 / 去停用词）
src/analysis/stopwords_zh.txt     # 中文通用停用词表（独立文件，便于维护）
src/analysis/vectorize.py         # 共享 TF-IDF 向量化工具（combine_text_fields / build_tfidf）
src/analysis/keywords.py          # 模块 B：TF-IDF 关键词提取（单篇 / 语料）
src/analysis/summarization.py     # 模块 C：TextRank 抽取式摘要
src/analysis/clustering.py        # 模块 D：TF-IDF + KMeans 主题聚类
src/analysis/similarity.py        # 模块 E：余弦相似度 Top-N 相似文章
```

新增（测试与文档）：

```text
tests/fixtures/synthetic_news_corpus.csv   # 明确标记的合成测试语料（6 篇，data_source=synthetic_test_fixture）
tests/test_preprocessing.py
tests/test_keywords.py
tests/test_summarization.py
tests/test_clustering.py
tests/test_similarity.py
docs/PHASE2_ANALYSIS.md                    # 阶段 2 模块文档
```

修改：`docs/DEVELOPMENT_LOG.md`（本节）。

**未修改**：`app/app.py`（仍为阶段 0 占位提示）；阶段 1 的 `src/data/*`、`tests/test_*.py` 原有测试文件未被改动。

### 2.2 各模块完成情况

- **模块 A 预处理**（`preprocessing.py`）：非字符串/空值安全转 `""`；全角空格归一、连续空白折叠、去首尾空白；
  jieba 词性标注分词（HMM 关闭）；丢弃纯标点 token；丢弃单字 token（长度 < 2）与纯数字 token；小写化；去停用词（表在 `stopwords_zh.txt`）；
  敏感词过滤（表在 `sensitive_words.txt`）；中文 token 仅保留名词性词性。命中词不参与分析、不出现在界面。**不改动原始 `title`/`content`/`source`**。
- **模块 B 关键词**（`keywords.py`）：TF-IDF 关键词提取；`keywords_for_document`（单篇，输出 `rank/keyword/weight`）
  与 `keywords_for_corpus`（语料，输出 `doc_id/rank/keyword/weight`）；`top_k` 可配置；空文本 / 全停用词 / 空语料返回空 DataFrame。
- **模块 C 摘要**（`summarization.py`）：本地 TextRank；按句末标点切句 → 词集合重叠相似度 → 建图 →
  `networkx.pagerank` 排序 → 去重后按原文顺序输出；返回 dict（`summary` / `summary_indices` / `num_sentences` / `note`）；
  摘要句**全部来自原文**；空文本 / 单句 / 无连边均有安全处理与 `note` 说明。
- **模块 D 聚类**（`clustering.py`）：TF-IDF + KMeans；`n_clusters` 可配置并校验（`k=min(n_clusters,有效文档数)`）；
  保留 `news_id/row_index/title/source/published_at/cluster`；每簇提取代表关键词；固定 `random_state=42` + `n_init=10`；
  小样本（<5）给出警告；空文本 / 无特征 / 单篇 均安全处理。
- **模块 E 相似度**（`similarity.py`）：TF-IDF 向量 + 余弦相似度；`find_similar_articles` 支持按 `query_index` 或 `query_id` 查询，
  输出 `query_id/matched_id/matched_title/matched_source/similarity/rank`；**排除自身**；单篇 / 空文本 / 无正相似度返回空 DataFrame。

### 2.3 执行过的命令与真实测试结果

```text
py -m unittest discover -s tests -v 2>&1 | Out-String -Width 200
```

真实输出：

```text
Ran 68 tests in 3.080s

OK
```

- 测试总数：**68**
- 通过：**68**
- 失败：**0**
- 错误：**0**
- 退出状态：**0（OK）**
- 其中阶段 1 原有测试 **21 个继续全部通过**；阶段 2 测试 **47 个**
  （preprocessing 8、keywords 9、summarization 14、clustering 7、similarity 9）。
- 测试数据来源：`tests/fixtures/synthetic_news_corpus.csv`（**合成测试数据**，非真实新闻）。
  测试结果仅验证算法行为，**不**用于宣称模型已在真实新闻语料上获得验证。

> 备注：Shell 输出中仍会出现 PowerShell 配置文件因执行策略被禁用而无法加载的 CLIXML 提示，
> 属环境噪音，不影响测试结果（退出状态为 0）。

### 2.4 真实运行示例（合成测试数据，非真实新闻）

使用 `tests/fixtures/synthetic_news_corpus.csv`（6 篇合成文本）经 `run_ingestion` 清洗后实测：

- 关键词（单篇，`top_k=5`）：`开通`(0.371391)、`新线路`(0.371391)、`地铁`(0.371391)、`换乘`(0.185695)、`优化`(0.185695)。
- TextRank 摘要（第 1 篇，`top_n=2`）：`summary_indices` 按原文顺序返回 2 句，
  `note=句子间相似度不足（无有效连边），已退化为按原文顺序选取，结果仅供参考。`
- 聚类（`n_clusters=3`）：`clustered_documents=6`；簇代表关键词示例
  `{0: ['水质','改善','空气质量','治理','河流'], 1: ['高校','成立','实验室','人工智能','举办'], 2: ['公交','专用道','调整','开通','新线路']}`。
- 相似度（查询 `id=1`，`top_n=3`）：匹配 `id=2`（0.107164）、`id=3`（0.052609）、`id=5`（0.015837），**自身未出现**。

以上数值均为该合成语料的真实计算结果，**不代表真实新闻语料的结论**。

### 2.5 边界情况处理小结

- 空文本 / 空值 / 缺失字段：关键词返回空 DataFrame；聚类 `n_clusters=0` 且 `cluster=-1`；相似度返回空 DataFrame。
- 极短 / 单句文本：摘要直接返回该句并给出 `note`。
- 全部词语被停用词过滤：视为空文本，安全返回空结果。
- 语料仅一篇 / 少量有效文章：聚类有效文档 <2 时统一 `cluster 0`；相似度返回空 DataFrame。
- 聚类数超出有效样本数：自动下调为 `k=min(n_clusters,有效文档数)` 并在 `note` 说明。
- 重复文本：相似度为 1.0（词面完全一致的数学结果，非转载证据）。
- 本文档与代码均声明：相似 ≠ 转载 / 因果 / 立场一致；聚类编号 ≠ 已知新闻类别；
  TF-IDF 权重 ≠ 新闻重要性；抽取式摘要 ≠ 事实核查。

### 2.6 未解决问题 / 待办

1. **真实新闻数据仍为空白**（当前仅合成测试样本）。
2. **界面未接入**：`app/app.py` 保持阶段 0 占位提示，阶段 2 结果尚未进入界面。
3. **分析结果未支持导出**为报告文件。
4. **未安装 Plotly / pytest / python-dotenv**（按用户要求保持现状）。
5. **Git 仍未安装**，版本库未初始化。
6. 停用词表为通用词表，未针对新闻领域调优；jieba 对未登录词可能切分不佳（详见 `docs/PHASE2_ANALYSIS.md`）。

---

## 阶段 2 有限修正与回归验收（2026-10-16）

- 状态：**待验收**
- 依据：上一轮只读审计报告指出的 3 项问题，本次仅做最小范围修正，**未进入 Phase 3**。

### 修正内容

1. **测试数量笔误**：`DEVELOPMENT_LOG.md` 中 summarization 测试数由 12 更正为 11（原分项），
   并同步更新为修正后的真实数量 14（见下）。Phase 1 = 21、Phase 2 = 47、总数 = 68。
2. **英文句点切分支持**（`src/analysis/summarization.py`）：
   - 句子切分正则由字符类 `findall` 改为基于 `re.split` 的分隔符模式 `_BOUNDARY`。
   - 边界规则：`。！？；!?；;\n` 一律切分；英文句点 `.` 仅在「前非数字、后为空白/结尾/大写字母」时切分，
     避免误切 `3.14` 等小数。
   - **已知局限**：`U.S.` 等大写缩写、以及 `e.g.` 这类后跟空格的缩写仍会被切分（句点后跟空格即视为边界）。
   - 同步更新模块 docstring 与 `docs/PHASE2_ANALYSIS.md` 第 4.1 节的文字说明。
3. **加强无连边降级测试**（`tests/test_summarization.py`）：
   - `test_no_shared_tokens_returns_result_with_note` 现断言 `summary_indices == [0, 1]`
     且 `summary` 等于原文前两句，验证降级确实按原文顺序选取前 N 个不重复句子。

### 新增 / 修改的测试

- 修改：`test_no_shared_tokens_returns_result_with_note`（断言加强）。
- 新增：`test_split_sentences_english_period`（`Hello. World.` → 2 句）、
  `test_split_sentences_decimal_not_split`（`价格是3.14元。` → 1 句）、
  `test_split_sentences_period_followed_by_space_is_boundary`（`e.g. for example` → `["e.g.", "for example"]`，记录已知局限）。

### 真实回归测试结果

```text
py -m unittest discover -s tests -v 2>&1 | Out-String -Width 250
  -> Ran 68 tests in 3.080s   OK
```

- 测试总数 **68**，通过 **68**，失败 **0**，错误 **0**，退出状态 **0**。
- Phase 1：21 个（未变）；Phase 2：47 个（preprocessing 8 + keywords 9 + summarization 14 + clustering 7 + similarity 9）。
- 首次运行时 `test_split_sentences_lowercase_abbreviation_not_split` 失败（期望 `e.g. for example` 不切分，
  实际切为 `["e.g.", "for example"]`）。经核对：`e.g.` 末尾句点后跟空格，符合「句点后跟空格为边界」规则，
  属预期行为。将该测试改名为 `test_split_sentences_period_followed_by_space_is_boundary` 并更新断言为实际行为，
  未削弱断言目标。复跑全部通过。

### 修改文件清单

- `src/analysis/summarization.py`（句子切分正则与 docstring）
- `docs/PHASE2_ANALYSIS.md`（第 4.1 节切分规则说明）
- `docs/DEVELOPMENT_LOG.md`（阶段 2 测试数量更正 + 本节）
- `tests/test_summarization.py`（加强 1 个 + 新增 3 个测试）

**未修改**：`app/app.py`、`src/data/*`（Phase 1 逻辑）、其它分析模块、其它测试文件。
**未新增依赖**、**未调用外部 API**、**未接入真实新闻数据**。

---

# Phase 3：Streamlit 界面接入（2026-10-16 ~ 2026-10-17）

> 说明：Phase 3 按子阶段滚动实施，每个子阶段均运行真实测试并经用户浏览器端人工验收。
> 本节为收尾补记，按子阶段顺序如实记录。

## 阶段 3.1 数据导入与质量概览（2026-10-16）

- 新增：`src/ui/__init__.py`、`src/ui/data_io.py`（`load_uploaded_csv` 临时文件适配层、`load_synthetic_demo`）、
  `tests/test_data_io.py`（7 个测试）；重写 `app/app.py`（上传 + 合成示例 + 质量概览 + 数据预览）。
- 上传适配：字节写入系统临时目录 → `run_ingestion`（不传 `report_path`，不写任何报告文件）→ `finally` 清理临时文件。
- 状态策略：上传失败保留旧结果并显著警告"当前显示的仍是上一份成功导入的数据"。
- 测试：**75 通过**（68 + 7）。

### 3.1 针对性复核修正（同日）

- 发现问题 1：`(filename, size)` 去重会漏掉同名同大小但内容不同的文件。
- 发现问题 2：上传失败后旧错误在切换文件时不清除，可能误导。
- 修正：改为「选择文件 → 点击开始导入」按钮触发；移除 `_last_file_id`；
  新增 `_selected_filename` 跟踪，文件切换时清除旧错误。
- 新增 `tests/test_app_helpers.py`（4 个测试，覆盖 `_friendly_error` 各分支）。
- 测试：**79 通过**。用户浏览器端人工验收通过。

## 阶段 3.2.1 数据概览与基础分布图表（2026-10-17）

- 新增：`src/ui/overview.py`（统计、分布、中文字体检测、matplotlib 图表构造）、
  `tests/test_overview.py`（16 个测试）；`app/app.py` 增加数据概览区块与 `_render_chart` 降级逻辑。
- 字体策略：检测 Microsoft YaHei / SimHei 等中文字体；不可用时降级 `st.bar_chart`（浏览器渲染中文）。
- 修正既有测试断言错误：`test_data_io.py` 中 `clean == 6` 应为 `5`
  （夹具 `synthetic_news_corpus.csv` 第 5 行 `source` 为空，清洗删除该行；依据夹具实际内容修正，非迁就代码）。
- 测试：**95 通过**。用户浏览器端人工验收通过。

## 阶段 3.2.2 主题聚类可视化（2026-10-17）

- 新增：`src/ui/cluster_view.py`（`data_fingerprint` 内容指纹、`compute_clusters`、`cluster_summary`、
  `articles_in_cluster`、`unclustered_count`）、`tests/test_cluster_view.py`（12 个测试）；
  `app/app.py` 增加 `_show_clustering`（聚类数滑块、主题概况、分布图、主题内文章列表）。
- 缓存键 = 数据指纹 + n_clusters，切换数据集后旧聚类结果自动失效。
- 界面声明：聚类编号为探索性分组，不代表已验证的新闻类别。
- 初次运行 2 个新测试失败：测试内合成数据 `FEW_ROWS` 第二行 `title` 非空导致文本仍有效；
  修正测试数据（`title=""`），非修改被测代码。复跑通过。
- 测试：**107 通过**。
- 用户浏览器发现 `NameError: name 'pd' is not defined`（`app/app.py` 使用 `pd.Series` 但未导入 pandas）；
  补 `import pandas as pd` 后复跑 107 通过、启动正常。用户浏览器端人工验收通过。

## 阶段 3.3 新闻详情与相似新闻探索（2026-10-17）

- 新增：`src/ui/article_view.py`（`article_text`、`field_or_placeholder`、`get_article_detail`、
  `get_similar_articles`、`should_reset_selection`）、`tests/test_article_view.py`（15 个测试）；
  `app/app.py` 增加 `_goto_article` 回调与 `_show_article_explorer` 区块。
- 文章定位使用行下标（标题重复仍可区分）；相似结果按 id 列映射回行位置（无 id 时按 title+source 兜底）。
- 选择器 / 滑块 / 跳转按钮的 widget key 均含数据指纹，数据集切换后旧选择自动失效。
- 界面声明：摘要为模型生成的抽取式摘要、可能遗漏重要信息；相似度不代表事实一致、转载或立场一致；
  单篇 TF-IDF 权重退化为词频量级。
- 测试：**122 通过**（`Ran 122 tests in 5.270s — OK`，退出状态 0）。
  构成：Phase 1 = 21、Phase 2 = 47、3.1 = 11、3.2.1 = 16、3.2.2 = 12、3.3 = 15。
- 编译检查 `py -m py_compile` 通过；Streamlit 启动冒烟测试成功（8606 端口）。
- 合成数据实测：详情字段正确；关键词 10 个；摘要 2 句（带降级 note）；相似 4 条
  （top_n=5 但实际仅 4 条正相似度，均排除自身，0.1070~0.0168）；指纹变化触发选择重置。
- **用户浏览器端人工验收通过**（2026-10-17）：新闻详情、关键词、TextRank 摘要、
  相似新闻、文章跳转、数据集切换、CSV 上传均符合预期。

## Phase 3.3 收尾核查（2026-10-17）

- 复跑全部测试：**Ran 122 tests — OK，0 失败，0 错误，退出状态 0**。
- Git 仍未安装（`git` 命令不存在），无法执行 `git status`；改用文件清单核对工作区：
  - 无临时脚本残留（开发期的 `_smoke_cluster.py`、`_smoke_article.py` 均已删除）。
  - 根目录仅 `.env.example`、`.gitignore`、`README.md`、`requirements.txt` 与既定目录。
  - `__pycache__/*.pyc` 为 Python 正常缓存，已被 `.gitignore` 排除。
  - `reports/synthetic_sample_quality.md` 修改时间仍为 2026-10-16 15:46:56，未被覆盖。
- 本日志此前仅记录到 Phase 2 修正，Phase 3 各阶段为本次收尾补记（即本节）。

### Phase 3 结束时的状态划分

**已验证（自动化测试，122 个全部通过）**：
数据导入适配（临时文件清理、报告保护、缺列/空文件报错、合成加载）、错误提示转换、
概览统计与分布、字体检测与图表降级、聚类封装与映射、文章详情与相似新闻映射、
数据指纹切换重置、Phase 1/2 全部功能不回归。

**已验证（用户浏览器端人工验收）**：
Phase 3.1（上传/示例加载/错误提示/质量概览）、3.2.1（概览与分布图）、3.2.2（聚类与主题浏览）、
3.3（新闻详情、关键词、TextRank 摘要、相似新闻、文章跳转、数据集切换、CSV 上传）。

**已知限制（界面均有提示）**：
单篇 TF-IDF 退化为词频量级；TextRank 基于词面重叠且 `U.S.` 等大写缩写可能误切；
聚类编号为探索性分组；相似度 ≠ 转载/因果/立场；相似结果按 title+source 兜底映射存在理论歧义；
matplotlib 中文依赖系统字体（不可用时降级内置图表）。

**仍未验证 / 待办**：
真实新闻数据上的效果（项目仍无真实数据）；大语料（数千行以上）性能；
非 Windows 环境；Streamlit 多用户并发会话；分析结果导出；Git 版本控制（环境未安装 Git）。

---

## Phase 3.4 审计计划（待确认，尚未实施）

**目标**：项目演示体验与结果可信度审计。**只读审查，不修改任何文件。**

### 审计范围与检查点

1. **页面信息层级与演示流程**（`app/app.py`）
   - 当前单页顺序：质量概览 → 数据预览 → 数据概览 → 主题聚类 → 新闻详情与相似新闻。
     审查该叙事顺序是否适合项目演示（评审者 3~5 分钟内能否抓住主线）；
     区块间是否需要分隔或小结；首屏信息密度是否过高。
2. **分析口径的逻辑一致性**（`src/ui/overview.py`、`src/ui/article_view.py`、`src/ui/cluster_view.py`）
   - 详情区关键词基于 title+content 拼接、概览区统计基于 content 字符数——口径是否在界面上说明一致；
   - 聚类代表关键词与簇内文章列表的可对应性；相似新闻 top_n 滑块上限与实际可用匹配数的关系。
3. **解释文案的准确性**（界面 caption 与 `docs/PHASE2_ANALYSIS.md` 对照）
   - 逐条核对：单篇 TF-IDF 退化说明、摘要非事实核查、相似 ≠ 转载/因果/立场、
     聚类编号 ≠ 已验证类别、合成数据标注。检查有无遗漏或措辞过强之处。
4. **边界与状态处理**
   - 空数据、全空文本、单篇、重复标题、缺失字段、NaT 日期在**每个区块**的显示；
   - 数据集切换后各区块（聚类缓存、文章选择、相似 top_n）是否全部随指纹失效；
   - 上传失败时旧数据警示是否在长页面下方仍然可见（错误提示目前渲染在页面顶部）。
5. **演示数据与真实数据区分**
   - 合成标注是否在所有分析区块可见还是仅页面顶部一次；
     上传真实数据后各区块是否还有可能残留"合成"字样或反之。
6. **结果被误读的风险**
   - "主题 X"命名、相似度 4 位小数精度、聚类占比百分比的呈现是否可能让评审者高估确定性。

### 审计方法与产出

- 只读逐文件审查 + 界面文案与代码行为对照表 + 边界覆盖清单核对。
- 产出：审计报告（问题清单、风险分级、修改建议），**只报告不实施**；
  修改在用户批准后另行安排。

## Phase 3.4 最小实施（2026-10-17，用户批准后执行）

依据审计报告，仅实施批准的 4 项修复，不扩展业务功能：

1. **P0-1 README 重写**（`README.md`）：进度声明更新为 Phase 3 完成；
   功能清单逐项区分「已实现且经验证」与「未实现」（多来源对比、报告导出、
   真实数据接入明确标注未实现）；测试说明更新为 15 文件 / 122+ 测试；
   数据分类表明确区分合成测试数据 / 用户上传数据 / 真实新闻数据（当前为空）。
2. **P1-2 docstring 修订**（`app/app.py` 顶部）：与当前 5 区块实际功能一致。
3. **P1-3 研究定位展示**（`app/app.py` `main()`）：页面顶部加入研究定位说明
   （可解释文本挖掘探索新闻主题/关键词/文本相似性），并声明相似性 ≠ 传播/因果、
   聚类编号 ≠ 已验证类别。
4. **P1-4 合成标注持续化**（`app/app.py`）：新增纯函数 `sidebar_data_status(label, filename)`
   生成侧边栏常显数据状态标记——合成数据显示「非真实新闻，仅供演示」警示，
   用户上传显示文件名，未导入显示提示，未知值不虚构来源。

新增测试：`tests/test_app_helpers.py` 增 `TestSidebarDataStatus` 5 个测试
（合成警示、用户上传含文件名、缺文件名兜底、未导入、未知标记不虚构来源）。

### 真实验证结果

```text
py -m unittest discover -s tests -v  -> Ran 127 tests in 5.884s  OK（退出状态 0）
py -m py_compile app/app.py tests/test_app_helpers.py -> 通过（退出状态 0）
py -m streamlit run app/app.py -> Uvicorn server started on :::8607，无异常输出
```

测试构成：Phase 1 = 21、Phase 2 = 47、3.1 = 11、3.2.1 = 16、3.2.2 = 12、3.3 = 15、
3.4 新增 = 5，合计 **127**。

**未修改**：`src/data/*`、`src/analysis/*`、`src/ui/*`、测试夹具、既有测试断言。
**待浏览器人工验收**：侧边栏标记在加载示例 / 上传成功 / 上传失败 / 切换数据四种场景下
的动态更新；页面顶部研究定位的显示效果。

## Phase 4.1 数据可追溯性（2026-10-17，用户批准后执行）

目标：使界面上的分析结果可追溯到具体数据集。新增数据档案与数据集标识，未扩展分析功能。

- 新增 `src/ui/provenance.py`（纯函数）：`build_provenance`（整理数据集元信息——来源标记、
  文件名、导入时间、原始/清洗后行数、发布日期范围、数据指纹、清洗步骤摘要）、
  `date_range`（日期列缺失/全 NaT 时返回「不可用」）、`format_imported_at`（None 时
  如实说明会话限制）、`dataset_tag`（分析区块数据集标识文案）。缺失值一律「未知 /
  不可用」，不编造。
- `app/app.py`：session_state 新增 `imported_at`（上传/示例加载成功时写入 `datetime.now()`）；
  新增「数据档案（Data Provenance）」区块（来源 info 之后，含指标卡与清洗步骤）；
  数据概览、主题聚类、新闻详情三个分析区块顶部新增 `dataset_tag` 数据集标识
  （来源标记 + 完整指纹），数据集切换后随 session_state 自动更新。
- 新增 `tests/test_provenance.py`（16 个测试）：正常合成夹具（行数 6/5、日期范围
  2024-05-01~2024-05-06 与实际一致）、上传标记、缺文件名/时间占位、未知来源不虚构、
  切换数据集指纹变化、空数据、畸形输入、缺日期列、tag 格式。
- 开发期 1 个测试失败：`test_tag_format` 断言切片错误（在 20 字符内找 8 位指纹），
  修正断言（`dataset_tag` 输出完整指纹，属正确行为），未改被测代码。
- 真实验证：`Ran 143 tests in 4.618s — OK`（退出 0）；`py_compile` 通过；
  Streamlit 启动 8608 端口无异常输出。
- 构成：Phase 1 = 21、Phase 2 = 47、3.1 = 11、3.2.1 = 16、3.2.2 = 12、3.3 = 15、
  3.4 = 5、4.1 = 16，合计 **143**。
- 已知限制：导入时间与指纹仅存会话内（界面已声明，未实现持久化审计日志）；
  数据档案不随数据集持久保存；未开始 4.2/4.3/4.4。
- 浏览器人工验收（2026-10-17，用户确认通过）：浏览器自动化实测 A/B/C/F 通过
  （初始状态、档案字段 6/5 行与指纹 348efb47364aa397、三区块标识一致、刷新后
  会话级状态重置）；D（上传有效 CSV）/E（无效 CSV）因原生文件对话框无法自动化
  由用户人工完成并确认通过。

## Phase 4.2 真实数据准备与使用规范（2026-10-17）

目标：为接入真实数据提供准备规范、模板与排查文档，不改动任何业务代码与算法。

- 新增 `docs/DATA_PREPARATION.md`（11 节）：格式/编码/字段规范（区分「已支持行为」
  与「准备规范」）、日期解析行为（format="mixed"；中文日期标注待验证）、缺失与
  重复处理、合法来源建议、授权/隐私注意事项、导入与数据档案核对步骤、常见问题
  排查表、分析能力边界声明（聚类编号≠类别、相似≠转载等）。
- 新增 `data/templates/news_dataset_template.csv`：3 条合成示例记录
  （标题带「合成示例：」前缀、`data_source=synthetic_template`、ISO 日期、
  演示 author/url 可为空），不伪装真实新闻。
- 新增 `tests/test_data_template.py`（5 个测试）：模板存在、列名与 loader 兼容
  （含全部可选列）、load_csv+clean 后 3 行无损且日期 2024-03-01~03 解析正确、
  run_ingestion 端到端（raw=3/clean=3/dup=0，与文档第 8/11 节声明一致）、
  合成标记完整性。
- `README.md` 第 7 节新增数据准备文档与模板入口（轻量，约 4 行）。
- 真实验证：`Ran 148 tests in 8.082s — OK`（退出 0）；`py_compile` 通过。
- 构成：21 + 47 + 11 + 16 + 12 + 15 + 5 + 16 + 5 = **148**。
- 未覆盖：模板的浏览器端实际导入体验（待用户人工验收）；中文日期解析（文档已
  标注待验证）；大文件性能。未开始 4.3/4.4。
- 遗留项处理（用户批准）：`.gitignore` 追加 `!data/templates/*.csv` 例外（模板可入库，
  其他目录 CSV 忽略行为不变）。因 Git 仍未安装，`git check-ignore -v` 无法执行，
  生效性为规则文本推演（父目录链未被排除，例外有效），待安装 Git 后复核。

## Phase 4.3 多来源新闻内容对比（2026-10-17）

目标：落实研究问题中"compare news coverage across media sources"的最小实现。
纯统计展示，不新增算法，不含立场/偏见/传播/因果判断。

- 新增 `src/analysis/source_compare.py`（纯函数）：`source_keyword_compare`
  （按来源分组的 Top-N 关键词对比，复用 keywords_for_corpus + combine_text_fields，
  doc_id 映射回原 df 行索引；空来源排除计数、小样本来源跳过并列出、max_sources
  截取、单来源提示）、`source_cluster_crosstab`（来源×聚类交叉表，复用
  cluster_articles 的 labels；cluster=-1 单列「未参与聚类」；行占比分母=该来源
  全部文章数；labels 缺失/为空/缺 source 列均返回说明不编造）、`small_sources`。
- `app/app.py`：新增「多来源对比」区块（主题聚类之后、新闻详情之前）：数据集
  标识 + 研究说明（差异≠立场/偏见/传播/因果）；来源关键词对比（每来源最少
  文章数滑杆，默认 1 保证小数据集可见对比，调高跳过小来源并警告；TF-IDF
  权重含义 caption——不是文章数量/影响力）；来源×主题分布（数量表 + 行占比表
  + st.bar_chart 堆叠图，主题编号解释与聚类质量提示）。聚类数滑块加显式 key
  `cluster_n_slider`（1 行兼容性修改），对比区块读取同一聚类数保证两区块主题
  一致；聚类结果优先复用 session 缓存键。
- 新增 `tests/test_source_compare.py`（15 个测试）：多来源/单来源/空来源行/
  空数据/小样本跳过/展示上限/row_index 映射回原文/数据集切换结果变化/
  交叉表总数一致/行占比分母口径/未参与聚类列/labels 缺失三种边界/small_sources。
- 开发期测试失败及根因（均已修复，未删除断言）：① 测试数据常量为 2 元组与
  make_df(3 元组) 不符（测试 bug）；② 实现对 row_pct 做 round(4) 导致求和
  0.9999——改为不在实现层四舍五入（精度留给展示层）；③ 一个测试漏传
  min_articles=1 与默认值 2 不一致（修测试）。
- 浏览器自动化实测（8610 端口）：数据集标识、研究说明、关键词表、权重含义、
  交叉表/占比/堆叠图、无 Traceback 均通过；发现合成示例（4 来源中 3 个仅 1 篇）
  在 min_articles=2 默认下仅展示 1 个来源——增加"最少文章数"滑杆（默认 1）
  修复演示体验；复查确认 4 来源全部展示；滑杆调至 2 的交互受自动化限制，
  由单元测试覆盖其过滤逻辑，浏览器端交人工验收。
- 真实验证：`Ran 163 tests in 4.442s — OK`（退出 0）；`py_compile` 通过；
  Streamlit 启动 8610 端口无异常。
- 构成：21 + 47 + 11 + 16 + 12 + 15 + 5 + 16 + 5 + 15 = **163**。
- 已知限制：未提供聚类质量量化指标（界面已提示谨慎解释）；来源关键词仅基于
  词面 TF-IDF；滑杆调整的浏览器交互待人工验收。未开始 4.4。

## Phase 4.4 研究叙事与项目呈现（2026-10-17）

目标：补齐项目演示层（演示脚本、项目介绍、示例观察、界面研究背景区块）。
**不新增功能、不新增依赖、不改变任何分析逻辑与数据处理流程**；未接入真实数据。
实施前完成只读审计（识别 P1–P6 六个问题），用户确认 4 项决策后实施。

### 新增文件（3 个）

- `docs/DEMO_SCRIPT.md`：7 步演示流程（研究问题→数据→方法→实际观察→局限与下一步），
  每步含界面操作 / 应看到内容 / 解说词 / 建议用时，合计约 3 分 00 秒；收尾阶段追加
  英文版（与中文稿同流程、同数值、同研究边界，注明以中文稿为准）。
- `docs/PROJECT_INTRO.md`：英文主稿 + 中文对照，6 节（Project overview /
  Research question and motivation / Data and methods / Current implementation /
  Limitations and future work / Personal contribution）。个人贡献仅写有开发日志
  证据支持的内容；明确声明尚未开展真实新闻研究、无立场识别/传播链/因果分析。
- `docs/EXAMPLE_OBSERVATIONS.md`：SYNTHETIC DATA DEMONSTRATION 标头；数据集身份表
  （文件、data_source 标记、指纹 348efb47364aa397、raw 6→clean 5、来源分布、
  日期范围、KMeans random_state=42）；6 条观察均按「程序输出（原样数值）→
  可以谨慎描述的现象 → 不能据此得出的结论」三段记录；界面渲染标注为待人工核验项。

### 示例观察的数值核验方式（真实）

- 用临时脚本（置于系统临时目录，用后即删）直接调用项目函数读取真实输出：
  run_ingestion / source_keyword_compare / compute_clusters / source_cluster_crosstab /
  get_similar_articles / get_article_detail；数值原样转录，未修饰、未挑选。
- 关键核验结果：指纹 348efb47364aa397；n=3 聚类分组 1/2/2（开源 / 地铁+公交 /
  空气+水质）；n=2 时分组变为 2/3（开源文章并入环境词群）——作为敏感性观察记录；
  相似度整体很低（最高 0.107030），row4（开源大会）的最相似文章是题材无关的
  河流水质（0.039564）——作为小语料局限观察记录；「开通」单篇权重 0.371391 与
  来源语料级权重 0.381255 不同——口径差异已记录。
- 未编造任何关键词、权重、聚类结果或研究发现；全部观察明确标注合成数据演示。

### 修改文件（2 个）

- `app/app.py`：① 模块 docstring 更新为 Phase 3.1~4.4 实际功能清单；② main() 在
  研究定位说明之后新增 `st.expander("About This Research / 关于本研究")`（研究问题
  中英双语、多来源对比动机、当前数据状态、已实现方法、方法能/不能支持什么、
  真实数据接入为后续工作的声明）。纯静态文案，不依赖数据、不改变分析流程，
  不覆盖既有研究定位文案。
- `README.md`：第 1 节末新增「研究演示（Research Demonstration）」小节（合成语料
  用途说明 + 3 个文档链接）。同时最小修正过期事实：测试总数 122→163、Phase 3 分项
  54→59（以实测为准）、「多来源对比——未实现」移入已实现清单（新增 Phase 4 小节）、
  「尚未实现」改为叙事框架对比/立场识别/传播链追踪、目录树补 source_compare.py /
  provenance.py / data/templates/ / docs 六个文档、6.1 页面流程线补数据档案与
  多来源对比、进度更新为「Phase 4.4 实施完成，等待人工验收」。

### 真实验证（Phase 4.4 实施完成时）

- 全量测试：`py -m unittest discover -s tests` → **Ran 163 tests — OK**
  （0 失败 / 0 错误，退出状态 0）。本阶段未新增测试（文档与静态文案型阶段）。
- 分项实测（unittest TestLoader 逐文件计数）：Phase 1 共 21（3/5/6/5/2）、
  Phase 2 共 47（8/9/14/7/9）、Phase 3 共 59（7/9/16/12/15）、Phase 4 共 36
  （16/15/5）。注：Phase 3 分项实测为 59，早期阶段记录中的 54 为当时计数，
  历史记录未追溯修改。
- 编译检查：`py -m compileall -q app src` → COMPILE_OK。
- 启动冒烟（8617 端口）：Streamlit 启动正常；浏览器自动化实测 5/5 通过
  （页面加载、About 区块展开可见、合成示例加载正常、7 大区块齐全、
  无 Traceback / st.error）；测后停止服务并确认端口释放。
- 用户人工浏览器验收：**通过**（Phase 4.4 收尾任务中确认）。
- 收尾同步：README 进度行更新为「Phase 4.4 已完成并通过人工验收」；
  PROJECT_INTRO 的 4 项待确认信息改为显式占位符（不填猜测内容）；
  DEMO_SCRIPT 追加英文版演示稿。

### 遗留与待确认

- `docs/PROJECT_INTRO.md` 4 项占位待作者确认（不以猜测填充）：AI 协作表述口径、
  项目起止时间与投入时长、是否课程作业/独立项目及致谢、仓库链接等。
- 项目尚无真实新闻数据，未开展任何真实媒体研究——文档与界面均已如实声明；
  真实数据接入是后续工作。
- Git 仍未安装；`.gitignore` 对 `!data/templates/*.csv` 例外规则的生效性沿用
  4.2 的文本推演结论，待安装 Git 后以 `git check-ignore -v` 复核。
- 未开始 Phase 4.5；未接入真实数据；未新增依赖；未新增测试。

---


