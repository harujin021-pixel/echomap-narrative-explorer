# EchoMap Data Preparation Guide (DATA_PREPARATION) — English

> Document version: Phase 4.2 (2026-10-17)
> Scope: preparing a **news-style CSV dataset** for upload through the EchoMap UI.
>
> **Reading conventions**:
> - "**Supported behavior**" = behavior implemented in the current code and verified by automated tests; you can rely on it directly.
> - "**Preparation guideline**" = a practice recommended when preparing data, so that the data imports smoothly and yields meaningful analysis results.
>
> ⚠️ **Important**: all example data in the EchoMap repository (including the `data/templates/` template and
> the `tests/fixtures/` fixtures) is **clearly labeled synthetic data**, not real news.
> Uploaded real data is kept only in the local session; the project ships no real news dataset and has no data crawler.

---

## 1. Purpose of this document

This guide helps you prepare a news-text CSV that EchoMap can import directly, explains what the system
actually does after import, how to verify your data via "Data Provenance", and the boundaries of the
current analysis capabilities.

## 2. CSV file format requirements (supported behavior + preparation guidelines)

| Item | Requirement | Type |
|---|---|---|
| File type | `.csv` (the UI file picker accepts only `.csv`) | Supported behavior |
| Delimiter | Half-width comma `,` (`;`, tabs, etc. are not supported) | Supported behavior |
| Header | The first row must be the column-name row | Supported behavior |
| Encoding | Automatically tried in order: `utf-8-sig` → `utf-8` → `gbk`; if all fail, an encoding error is reported | Supported behavior |
| Recommended encoding | **Preparation guideline**: save as UTF-8 (`utf-8-sig` with BOM also works) | Preparation guideline |
| Cells | Do not include unescaped line breaks or commas (wrap fields containing commas in quotes) | Preparation guideline |
| File size | No hard limit; try a few dozen to a few hundred rows first — loading and clustering slow down noticeably on large files | Preparation guideline |

## 3. Field specifications

### 3.1 Required fields (missing any **column name** makes import fail)

| Column | Meaning | Missing values allowed? |
|---|---|---|
| `title` | News headline | A cell may be empty, but **the row is removed by cleaning** |
| `content` | News body text | Same as above |
| `source` | Source media name | Same as above |

> Supported behavior: at import time, if any of these three **column names** is absent from the CSV, an
> error is raised immediately — "The CSV is missing required columns [...]" — with no silent handling.
> Supported behavior: during cleaning, any **row** where `title`/`content`/`source` is blank is removed;
> the gap between "Raw records → Records after cleaning" in Data Provenance includes these removals.

### 3.2 Optional fields

| Column | Meaning | UI behavior when missing (supported behavior) |
|---|---|---|
| `id` | Unique identifier (number or string) | `news_id` appears empty in analysis results; similarity matching falls back to title+source matching |
| `author` | Author | The detail page shows a placeholder notice; no error |
| `published_at` | Publication date/time | Date-related charts and the provenance date range exclude that row |
| `url` | Link to the original article | The detail page shows a placeholder notice |

> Supported behavior: **extra columns** in the CSV (e.g. `data_source`, `category`) are not deleted;
> they are shown in the data preview but do not participate in analysis.

### 3.3 Filling recommendations (preparation guidelines)

- `title`: keep the original headline text; do not truncate or rewrite it.
- `content`: the full body; very short text (less than one sentence) hurts summary and similarity quality.
- `source`: use consistent media names (unify the spelling of the same outlet — e.g. do not mix
  「XX日报」 and 「XX日报社」, two variant spellings of the same paper).
- `id`: recommended, and unique within the dataset; duplicate `id` values make similar-article matching ambiguous.

## 4. Date formats and parsing behavior

**Supported behavior** (per `src/data/cleaning.py`, parsed with pandas `format="mixed"`):

- ISO format `2024-05-01`, datetime format `2024-05-01 08:30:00`, and other common formats recognized by
  pandas are supported.
- **A row whose date cannot be parsed is not deleted**; the date is recorded as missing, and the UI
  date-distribution chart and the Data Provenance "Publication date range" automatically skip these rows.
- If **all** dates fail to parse or the column is empty, "Publication date range" shows `unavailable`,
  and the date-distribution chart shows an empty-state notice.

**Preparation guidelines**:

- Prefer a uniform `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`.
- Mixing multiple formats within one column can still parse, but unifying them is recommended to avoid ambiguity.
- Chinese-language dates (e.g. `2024年5月1日`) are **unverified** — whether they parse depends on pandas
  version behavior; test with a small sample import first (status: to be verified).

## 5. Handling of missing titles/bodies and duplicate news (supported behavior)

| Situation | System behavior |
|---|---|
| `title` / `content` / `source` is blank | The row is removed during cleaning and excluded from analysis |
| HTML tags / entities (e.g. `<p style="text-indent:2em">`, `&nbsp;`) left in text from web scraping | Stripped/unescaped during cleaning; if a required field becomes empty after stripping, the row is removed |
| All three required fields present but other fields missing | The row is kept; missing fields show placeholder notices in the UI |
| A fully duplicated row (all columns identical) | Automatically deduplicated during cleaning |
| Near-duplicate rows differing only in `id` | **Not** automatically deduplicated; both participate in analysis as two records; whether to keep them is your call (preparation guideline: deduplicate yourself first) |
| Duplicated articles with identical content (cross-source reprints) | Kept by the system; the similar-articles feature will show high similarity — **this does not imply a reprint relationship** (see Section 10) |

> Note: cleaning only removes "fully duplicated" rows; semantic duplicates and cross-source reprints are
> your responsibility to judge during data preparation.

## 6. How to prepare news data from sources you are allowed to use

**Preparation guidelines** (general advice; you must confirm the specific licensing yourself):

1. **Collect it yourself**: compile report texts that you (your team) are authorized to use, and enter them
   into a CSV row by row.
2. **Public datasets**: use public news datasets with a clear license that permits research/educational use
   (e.g. open datasets on data platforms). Always read the license terms before use.
3. **Export from your own data**: export a CSV from your existing research materials or class-project data.

> ⚠️ EchoMap **does not provide**, and does not plan to provide, web crawlers or automated scraping;
> please do not use this project to bulk-scrape copyright-protected news content.

## 7. Data provenance, licensing, privacy, and sensitive information (preparation guidelines)

- Only import data you **have the right to use**; content being publicly accessible on the web does not
  mean it may be freely redistributed or analyzed and displayed.
- Avoid including personal sensitive information in the CSV (ID numbers, addresses, phone numbers,
  information about minors, etc.); personal information appearing in news data should have been
  de-identified as needed during your data preparation.
- Uploaded data is kept only in the **current browser session** (Streamlit session state) and disappears
  after a refresh; the project does not write uploaded data into the project directory (quality report
  files are generated only when the ingestion script is explicitly invoked).
- When showing the project publicly, confirm that the dataset license permits public display of analysis results.

## 8. Import steps and verifying via Data Provenance

1. Start the app: `py -m streamlit run app/app.py` (from the project root).
2. In the sidebar, choose your file under "Upload CSV file" → click "**Import**".
3. After a successful import, verify the **Data Provenance** panel:
   - **Dataset name**: should show the name of your uploaded file; the source label should read "user-uploaded data".
   - **Raw records / Records after cleaning**: the difference = rows removed by cleaning (including rows
     with empty required fields and fully duplicated rows).
   - **Publication date range**: should match the actual dates in your data; `unavailable` means the date
     column was not parsed successfully.
   - **Data fingerprint**: a hash identifier of the current data content; identical content from the same
     upload yields the same fingerprint, and any data change changes the fingerprint.
   - **Imported at**: kept only in the current session and reset after a page refresh (as noted in the UI,
     **not a persistent log**).
4. In "Data Overview", check whether the source distribution and date distribution match your knowledge of
   the data — this is the first checkpoint for spotting data problems.

## 9. Common import problems and troubleshooting

| Symptom | Possible cause | How to troubleshoot |
|---|---|---|
| Message that the file encoding could not be detected ("Could not detect the file encoding...") | The file is not in one of the three encodings above (e.g. UTF-16, BIG5) | Re-save it as UTF-8 in an editor and retry |
| Message "The CSV is missing required columns [...]" | Misspelled column names, stray spaces, or the header is not on the first row | Check column names against Section 3; check the header row |
| Message that the data is empty / empty-file error | The file has only a header or is otherwise empty | Confirm the file contains data rows |
| Records after cleaning are far fewer than raw records | Many rows have empty required fields, or fully duplicated rows exist | Inspect the raw data; this is **expected cleaning behavior**, not an error |
| Date range shows "unavailable" | The `published_at` column is missing, entirely empty, or in an unparseable format | Check against Section 4; test with a small sample import |
| Some dates missing from the date-distribution chart | The dates of some rows failed to parse (the other rows are kept as normal) | Check how the dates in those rows are written |
| Nothing happens after upload | The "Import" button was not clicked | In this version import is button-triggered; after choosing a file you must confirm manually |
| Message "the page still shows the previously imported dataset" | This import failed, and the system kept the old data | Fix the file per the error message and retry; the old provenance record is not contaminated by the failed data |

## 10. Limitations of the current analysis capabilities (must read)

The following limitations are **inherent boundaries of the implemented algorithms** and are flagged in the
corresponding analysis sections of the UI:

- **Topic clustering**: the IDs produced by TF-IDF + KMeans are exploratory, algorithm-generated groups,
  **not** verified news categories; they cannot be used directly to claim media bias, reporting intent, or
  issue stance.
- **Keywords**: TF-IDF weights reflect a word's relative discriminating power in the text; they are
  **not equivalent to** news importance, social influence, or reporting tendency; because single-article
  keyword weights lack a corpus-level IDF reference, they are for reference only (as noted in the UI).
- **Similar articles**: cosine similarity only expresses surface/vector-level closeness under the current
  text representation; it **cannot prove** reprint relationships, propagation relationships, causation, or
  shared media stance.
- **Extractive summary**: composed of sentences selected from the original text by TextRank; it **may omit
  important information** and constitutes neither fact-checking nor authenticity verification.
- Clustering and keyword results on small samples (e.g. fewer than 20 articles) have limited stability and
  are recommended for method demonstration only.
- All of the above are text-statistics-level observation tools; any research conclusion aimed at the public
  requires manual review and methodological support.

## 11. Template file

The project provides `data/templates/news_dataset_template.csv`:

- 3 records **clearly labeled as synthetic examples** (titles start with 「合成示例：」 ["Synthetic example:"],
  and the `data_source` column is `synthetic_template`); **not real news**, for format demonstration only.
- The template demonstrates: how to fill all required fields, that `author` may be empty (row 3), that
  `url` may be empty (row 2), and the ISO date format.
- Usage: copy the file → replace with your own data (keep the column names; it is recommended to change the
  `data_source` marker to describe your actual source) → import per Section 8.
- The template can be imported directly for verification: it should show 3 raw rows, 3 rows after cleaning,
  0 duplicates, and a date range of 2024-03-01 ~ 2024-03-03.

---

# EchoMap 数据准备指南（DATA_PREPARATION）

> 文档版本：Phase 4.2（2026-10-17）
> 适用范围：准备通过 EchoMap 界面上传的**新闻类 CSV 数据集**。
>
> **阅读约定**：
> - 「**已支持行为**」= 当前代码已实现、已通过自动化测试验证的行为，可直接依赖。
> - 「**准备规范**」= 建议用户在准备数据时遵循的做法，目的是让数据顺利通过导入并获得有意义的分析结果。
>
> ⚠️ **重要**：EchoMap 项目仓库内的所有示例数据（含 `data/templates/` 模板与
> `tests/fixtures/` 夹具）均为**明确标记的合成数据**，不是真实新闻。
> 上传的真实数据仅保存在本地会话中，项目不内置任何真实新闻数据集，也没有数据爬虫。

---

## 1. 文档目的

帮助你把一份新闻文本 CSV 准备成 EchoMap 可以直接导入的格式，说明导入后系统的实际处理行为、
如何通过「数据档案」核对数据，以及当前分析能力的边界。

## 2. CSV 文件格式要求（已支持行为 + 准备规范）

| 项 | 要求 | 性质 |
|---|---|---|
| 文件类型 | `.csv`（界面文件选择器仅接受 `.csv`） | 已支持行为 |
| 分隔符 | 半角逗号 `,`（不支持 `;`、制表符等） | 已支持行为 |
| 表头 | 第一行必须是列名行 | 已支持行为 |
| 编码 | 依次自动尝试 `utf-8-sig` → `utf-8` → `gbk`；全部失败时报编码错误 | 已支持行为 |
| 推荐编码 | **准备规范**：使用 UTF-8（含 BOM 的 `utf-8-sig` 亦可）保存 | 准备规范 |
| 单元格 | 内部不要包含未转义的换行符或逗号（建议用引号包裹含逗号的字段） | 准备规范 |
| 文件大小 | 无硬性上限；建议先以数十至数百行试导入，大文件加载与聚类会明显变慢 | 准备规范 |

## 3. 字段规范

### 3.1 必需字段（缺少任一**列名**将无法导入）

| 列名 | 含义 | 允许缺失？ |
|---|---|---|
| `title` | 新闻标题 | 单元格可为空，但**该行会被清洗删除** |
| `content` | 新闻正文 | 同上 |
| `source` | 来源媒体名称 | 同上 |

> 已支持行为：导入时只要 CSV 中不存在这三个**列名**，会立即报错
> `CSV 文件缺少必需列 [...]`，不会静默处理。
> 已支持行为：清洗阶段会删除 `title`/`content`/`source` 任一为空白的**行**，
> 数据档案中的「原始记录数 → 清洗后记录数」差异即包含这部分删除。

### 3.2 可选字段

| 列名 | 含义 | 缺失时的界面表现（已支持行为） |
|---|---|---|
| `id` | 唯一标识（数字或字符串） | 分析结果中 `news_id` 显示为空；相似度匹配回退到标题+来源匹配 |
| `author` | 作者 | 详情页显示占位提示，不报错 |
| `published_at` | 发布日期/时间 | 日期相关图表与档案日期范围不包含该行 |
| `url` | 原文链接 | 详情页显示占位提示 |

> 已支持行为：CSV 中**额外的列**（如 `data_source`、`category`）不会被删除，
> 会在数据预览中一并显示，但不参与分析。

### 3.3 填写建议（准备规范）

- `title`：保留原标题文字，不要截断或改写。
- `content`：完整正文；过短（少于一句）会影响摘要与相似度质量。
- `source`：使用一致的媒体名称（同一媒体请统一写法，如不要混用「XX日报」与「XX 日报社」）。
- `id`：建议提供，且在数据集内唯一；重复 `id` 会导致相似新闻匹配歧义。

## 4. 日期格式与解析行为

**已支持行为**（依据 `src/data/cleaning.py`，使用 pandas `format="mixed"` 解析）：

- 支持 ISO 格式 `2024-05-01`、带时间格式 `2024-05-01 08:30:00` 及 pandas 可识别的常见格式。
- **无法解析的日期该行不会被删除**，日期记为缺失；界面日期分布图与数据档案
  「发布日期范围」自动跳过这些行。
- 若**全部**日期都无法解析或列为空，「发布日期范围」显示 `不可用`，日期分布图显示空状态提示。

**准备规范**：

- 推荐统一使用 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`。
- 同一列内混合多种格式虽可解析，但建议统一，避免歧义。
- 中文日期（如 `2024年5月1日`）**未经验证**，能否解析取决于 pandas 版本行为，使用前请先小样本试导入（标注：待验证）。

## 5. 标题 / 正文缺失与重复新闻的处理（已支持行为）

| 情况 | 系统行为 |
|---|---|
| `title` / `content` / `source` 为空白 | 该行在清洗阶段被删除，不计入分析 |
| 文本中残留网页抓取的 HTML 标签/实体（如 `<p style="text-indent:2em">`、`&nbsp;`） | 清洗阶段自动剥除/还原；若必需字段剥除后变为空白，该行同样被删除 |
| 三个必需字段齐全但其他字段缺失 | 该行保留，缺失字段在界面显示占位提示 |
| 整行完全重复（所有列都相同） | 清洗阶段自动去重 |
| 仅 `id` 不同的近似重复行 | **不会被自动去重**，会作为两条记录参与分析；是否保留由你决定（准备规范：先自行去重） |
| 重复但内容相同的文章（不同来源转载） | 系统保留；相似新闻功能会显示高相似度——**这不代表转载关系**（见第 10 节） |

> 说明：清洗只删除「完全重复」的行；语义重复、跨来源转载由你在数据准备阶段自行判断。

## 6. 如何从允许使用的来源准备新闻数据

**准备规范**（以下为通用建议，具体授权需你自行确认）：

1. **自行收集**：整理你（团队）有使用授权的报道文本，逐条录入 CSV。
2. **公开数据集**：使用明确注明许可证、允许研究/教育用途的公开新闻数据集
   （如数据平台上的开放数据集）。使用前务必阅读其许可条款。
3. **自建数据导出**：从你已有的调研资料、课堂项目数据导出 CSV。

> ⚠️ EchoMap **不提供**、也不计划提供网络爬虫或自动抓取功能；
> 请勿利用本项目批量抓取受版权保护的新闻内容。

## 7. 数据来源、授权、隐私与敏感信息注意事项（准备规范）

- 只导入你**有权使用**的数据；公开网页内容不等于可随意再分发或分析展示。
- 避免 CSV 中包含个人敏感信息（身份证号、住址、电话、未成年人信息等）；
  新闻数据中出现的个人信息应已在你的数据准备阶段做必要的脱敏。
- 上传的数据仅保存在**当前浏览器会话**中（Streamlit 会话状态），刷新后消失；
  项目不会把上传数据写入项目目录（质量报告文件仅在显式调用导入脚本时才生成）。
- 项目公开展示时，请确认数据集许可证允许公开展示分析结果。

## 8. 导入步骤与数据档案核对

1. 启动应用：`py -m streamlit run app/app.py`（在项目根目录执行）。
2. 侧边栏「上传 CSV 文件」选择你的文件 → 点击「**开始导入**」。
3. 导入成功后核对**数据档案（Data Provenance）**：
   - **数据集名称**：应显示你上传的文件名；来源标记应为「用户上传数据」。
   - **原始记录数 / 清洗后记录数**：两者之差 = 被清洗删除的行（含必需字段空行与完全重复行）。
   - **发布日期范围**：应与你数据中的实际日期一致；显示 `不可用` 说明日期列未解析成功。
   - **数据指纹**：当前数据内容的哈希标识；同一次上传的内容指纹相同，数据一变指纹即变。
   - **导入时间**：仅保存在当前会话，刷新页面后重置（界面已注明，**非持久化日志**）。
4. 在「数据概览」检查来源分布与日期分布是否符合你对数据的了解——这是发现数据问题的第一道关口。

## 9. 常见导入问题与排查

| 现象 | 可能原因 | 排查方法 |
|---|---|---|
| 提示「无法用候选编码解码」 | 文件不是上述三种编码（如 UTF-16、BIG5） | 用编辑器另存为 UTF-8 后重试 |
| 提示「CSV 文件缺少必需列 [...]」 | 列名拼写错误、多余空格、表头不在第一行 | 对照第 3 节列名；检查表头行 |
| 提示数据为空 / 空文件错误 | 文件只有表头或内容为空 | 确认文件有数据行 |
| 清洗后记录数远小于原始数 | 大量行必需字段为空或存在完全重复行 | 检查原始数据；此为**预期清洗行为**，非错误 |
| 日期范围显示「不可用」 | `published_at` 列缺失、全空或格式无法解析 | 对照第 4 节；用小样本试导入 |
| 日期分布图缺日期 | 部分行日期解析失败（正常保留其余行） | 检查那些行的日期写法 |
| 上传后没反应 | 未点击「开始导入」按钮 | 本版本为按钮触发导入，选择文件后需手动确认 |
| 提示「当前显示的仍是上一份成功导入的数据」 | 本次导入失败，系统保留了旧数据 | 按错误提示修正文件后重试；旧档案不会被失败数据污染 |

## 10. 当前分析能力的限制（必读）

以下限制是**已实现算法的固有边界**，已在界面各分析区块同步标注：

- **主题聚类**：TF-IDF + KMeans 产生的编号是算法生成的探索性分组，
  **不是**经过验证的新闻类别，不能直接据此断言媒体偏见、报道意图或议题立场。
- **关键词**：TF-IDF 权重反映词语在文本中的相对区分能力，
  **不等同于**新闻重要性、社会影响力或报道倾向；单篇文章的关键词权重因缺少
  语料级 IDF 参考，仅具参考价值（界面已注明）。
- **相似新闻**：余弦相似度只表示当前文本表示方法下词面/向量层面的接近程度，
  **不能证明**转载关系、传播关系、因果关系或媒体立场一致。
- **抽取式摘要**：由 TextRank 从原文挑选句子组成，**可能遗漏重要信息**，
  不构成事实核查或真实性验证。
- 小样本数据（如少于 20 篇）的聚类与关键词结果稳定性有限，建议仅用于方法演示。
- 以上均为文本统计层面的观察工具；任何面向公众的研究结论需要人工复核与方法学支持。

## 11. 模板文件

项目提供 `data/templates/news_dataset_template.csv`：

- 3 条**明确标记为合成示例**的记录（标题以「合成示例：」开头，`data_source` 列为 `synthetic_template`），
  **不是真实新闻**，仅用于演示格式。
- 该模板演示了：必需字段齐全的写法、`author` 可为空（第 3 行）、`url` 可为空（第 2 行）、ISO 日期格式。
- 使用方式：复制该文件 → 替换为你自己的数据（保留列名与 `data_source` 标记建议改为你的实际来源说明）→ 按第 8 节导入。
- 该模板可直接导入验证：应显示原始 3 行、清洗后 3 行、0 重复、日期范围 2024-03-01 ~ 2024-03-03。
