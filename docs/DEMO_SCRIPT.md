# EchoMap 演示脚本（约 3 分钟）

> 面向项目展示 / 演示场景的界面演示流程。解说词中引用的数值均来自
> [EXAMPLE_OBSERVATIONS.md](EXAMPLE_OBSERVATIONS.md) 已核验的真实程序输出。
> **演示数据是合成测试数据，演示中必须如实说明，不得表述为真实新闻研究。**

## 演示前准备（不计入 3 分钟）

1. 在项目根目录执行：

   ```powershell
   py -m streamlit run app/app.py
   ```

2. 浏览器打开 `http://localhost:8501`。
3. 确认侧边栏显示「当前状态：尚未导入数据」（若显示旧数据，刷新页面即可重置）。
4. 表述纪律：不使用「立场」「偏见」「因果」「转载」描述任何结果；当前数据是合成的，要明说。

## 流程总览

| 步骤 | 内容 | 建议用时 | 累计 |
| --- | --- | --- | --- |
| 1 | 研究问题与研究定位 | 20 秒 | 0:20 |
| 2 | 导入合成数据 · 数据档案与质量概览 | 35 秒 | 0:55 |
| 3 | 数据概览（来源 / 日期分布） | 15 秒 | 1:10 |
| 4 | 主题聚类分析 | 30 秒 | 1:40 |
| 5 | 多来源对比 | 30 秒 | 2:10 |
| 6 | 新闻详情与相似新闻 | 30 秒 | 2:40 |
| 7 | 局限与下一步 | 20 秒 | 3:00 |

---

## 步骤 1：研究问题与研究定位（0:00–0:20，约 20 秒）

- **界面操作**：页面停留在顶部，展开「About This Research / 关于本研究」折叠区，念出其中的研究问题。
- **应看到**：页面顶部的研究定位说明；折叠区内的研究问题、当前数据状态、方法能/不能支持什么。
- **解说词**：
  > 「EchoMap 回答的研究问题是：可解释的文本挖掘方法，如何帮助用户探索新闻主题模式、
  > 并对比不同媒体的报道内容？我选择 TF-IDF、TextRank、KMeans 和余弦相似度这类
  > 可解释的方法，而不是黑箱模型——每一步结果都能说清楚是怎么来的。」
- **建议用时**：20 秒。

## 步骤 2：导入合成数据 · 数据档案与质量概览（0:20–0:55，约 35 秒）

- **界面操作**：点击侧边栏「加载合成示例数据」按钮。
- **应看到**：
  - 提示「当前数据来源：合成测试数据（文件：synthetic_news_corpus.csv）」及非真实新闻的标注；
  - 数据档案：原始记录数 6、清洗后记录数 5、数据指纹 `348efb47`；
  - 数据质量概览：被清洗掉的记录数 1；
  - 清洗后数据预览表。
- **解说词**：
  > 「内置示例是一份明确标记的合成语料——6 条原始记录清洗后剩 5 条，有一行因为
  > 来源字段为空被清洗删除。顶部的数据档案给出数据指纹 348efb47，同一份数据
  > 任何时候都能凭指纹对上号；界面上也全程标注这是合成数据。」
- **建议用时**：35 秒。

## 步骤 3：数据概览（0:55–1:10，约 15 秒）

- **界面操作**：向下滚动到「数据概览」。
- **应看到**：清洗后新闻数量 5、新闻来源数量 4、发布日期范围 2024-05-01 ~ 2024-05-06；来源分布图（甲 2、乙 1、丙 1、丁 1）与日期分布图。
- **解说词**：
  > 「概览部分给出基础分布：4 个来源、5 篇文章。规模很小，但足以演示完整的分析流程。」
- **建议用时**：15 秒。

## 步骤 4：主题聚类分析（1:10–1:40，约 30 秒）

- **界面操作**：滚动到「主题聚类分析」，保持默认聚类数 3；可在「选择主题查看文章」下拉框切换一次。
- **应看到**：
  - 主题 0：1 篇（20%），关键词：社区、软件、开源、大会、举办
  - 主题 1：2 篇（40%），关键词：公交、专用道、调整、开通、新线路
  - 主题 2：2 篇（40%），关键词：水质、改善、空气质量、河流、治理
  - 主题分布柱状图；每主题文章列表。
- **解说词**：
  > 「默认 3 个主题：开源大会单独一组，地铁和公交两篇一组，空气质量和河流水质一组。
  > 注意主题编号是算法生成的探索性分组——我故意不给它们起『交通』『环境』这样的名字，
  > 因为那会暗示类别已经被验证过，而实际上没有。」
- **建议用时**：30 秒。

## 步骤 5：多来源对比（1:40–2:10，约 30 秒）

- **界面操作**：滚动到「多来源对比」，确认滑杆「每个来源至少包含的文章数」为 1；查看来源关键词与「来源 × 主题分布」表。
- **应看到**：
  - 4 个来源的关键词卡（甲有 2 组关键词，乙/丙/丁各 1 组）；
  - 来源×主题表：甲的两篇文章分属主题 1 和主题 2（行占比 0.5 / 0.5），其余来源各占一个主题；
  - 各处的解读边界提示（差异≠立场/偏见/因果）。
- **解说词**：
  > 「来源对比把『不同媒体的报道差异』变成可观察的文本现象：来源关键词、来源×主题分布。
  > 甲媒体的两篇文章落在了两个主题里。当然，这里只有 5 篇合成文章，这些输出只是演示，
  > 不构成任何媒体对比的研究结论。」
- **建议用时**：30 秒。

## 步骤 6：新闻详情与相似新闻（2:10–2:40，约 30 秒）

- **界面操作**：滚动到「新闻详情与相似新闻」，在下拉框选择 #0（城市地铁新线路开通）；稍作停留后点击某条相似新闻的「查看该新闻」按钮演示跳转。
- **应看到**：
  - 文章标题、来源、日期与正文；
  - 关键词表（开通 0.371391、新线路 0.371391、地铁 0.371391、换乘 0.185695、优化 0.185695）；
  - 抽取式摘要（2 句，全部来自原文）；
  - 相似新闻 Top3：公交专用道 0.1070、空气质量 0.0546、河流水质 0.0169。
- **解说词**：
  > 「单篇视图提供关键词、抽取式摘要——摘要句子全部来自原文——以及相似新闻。
  > 最相似的是公交那篇，相似度 0.107，数值整体很低；这类稀疏小语料下，
  > 词面少量重叠就能排到前面。点『查看该新闻』可以跳转过去继续探索。」
- **建议用时**：30 秒。

## 步骤 7：局限与下一步（2:40–3:00，约 20 秒）

- **界面操作**：滚动回页面顶部（或结束于当前区块口头收束）。
- **应看到**：无（口头收束，可顺带指向侧边栏数据状态标记）。
- **解说词**：
  > 「最后说明边界：本次演示全部基于合成数据；这套方法不能识别媒体立场、
  > 不能追踪传播链、不能得出因果结论。真实数据接入是下一步——使用者按
  > 数据准备文档上传自己的 CSV，即可复用同一套分析流程。」
- **建议用时**：20 秒。

---

## 备注

- 各步骤「应看到」的内容以当前代码实际渲染为准；若系统缺少中文字体，图表会自动降级为内置图表并显示说明，演示时可顺带说明这一降级设计。
- 上传真实 CSV 的交互（原生文件对话框）不适合现场演示时，可只演示合成示例加载，并说明上传入口位于侧边栏。
- 中文稿之外另附英文讲稿（见文末「English Version」），两版对应相同的操作流程、
  实际功能与研究边界；如两版出现不一致，以中文稿为准并需同步修正英文稿。
- 总时长按建议用时合计约 3 分 00 秒；实际演示允许 ±15 秒浮动。

---

# EchoMap Demo Script (~3 minutes) — English Version

> English narration mirroring the accepted Chinese script above: same UI actions,
> same verified numbers, same research boundaries. UI labels are quoted in Chinese
> because the interface itself is in Chinese. If the two versions diverge, the
> Chinese version is authoritative.

## Pre-demo preparation (not counted in the 3 minutes)

1. From the project root, run:

   ```powershell
   py -m streamlit run app/app.py
   ```

2. Open `http://localhost:8501` in a browser.
3. Confirm the sidebar shows「当前状态：尚未导入数据」(no data imported yet); refresh
   the page to reset if a previous session is still displayed.
4. Ground rules: never describe any result as stance, bias, causation, or reprinting;
   state openly that the demo data are synthetic.

## Flow overview

| Step | Content | Time | Running total |
| --- | --- | --- | --- |
| 1 | Research question and positioning | 20 s | 0:20 |
| 2 | Load synthetic data · provenance & quality overview | 35 s | 0:55 |
| 3 | Data overview (source / date distributions) | 15 s | 1:10 |
| 4 | Topic clustering | 30 s | 1:40 |
| 5 | Multi-source comparison | 30 s | 2:10 |
| 6 | Article detail and similar articles | 30 s | 2:40 |
| 7 | Limitations and next steps | 20 s | 3:00 |

---

## Step 1: Research question and positioning (0:00–0:20, ~20 s)

- **UI action**: stay at the top of the page; expand the "About This Research / 关于本研究"
  expander and read out the research question.
- **What you should see**: the research-positioning statement; the expander with the
  research question, the current data status, and what the methods can and cannot support.
- **Suggested narration**:
  > "The research question behind EchoMap is: how can explainable text-mining methods
  > help users explore topic patterns and compare news coverage across media sources?
  > I chose explainable methods — TF-IDF, TextRank, KMeans, cosine similarity — instead
  > of black-box models, so every result can be traced and explained."
- **Timing**: 20 seconds.

## Step 2: Load synthetic data · provenance and quality overview (0:20–0:55, ~35 s)

- **UI action**: click「加载合成示例数据」(Load synthetic demo data) in the sidebar.
- **What you should see**:
  - the notice「当前数据来源：合成测试数据（文件：synthetic_news_corpus.csv）」with the
    not-real-news warning;
  - the Data Provenance panel: raw rows 6, clean rows 5, fingerprint `348efb47`;
  - the quality overview: 1 record removed by cleaning;
  - the cleaned-data preview table.
- **Suggested narration**:
  > "The built-in example is a clearly labeled synthetic corpus — six raw records become
  > five after cleaning, because one row had an empty source field. The data-provenance
  > panel shows the fingerprint 348efb47, so the same dataset can always be identified.
  > The UI labels this as synthetic data throughout."
- **Timing**: 35 seconds.

## Step 3: Data overview (0:55–1:10, ~15 s)

- **UI action**: scroll to「数据概览」(Data overview).
- **What you should see**: 5 cleaned articles, 4 sources, date range
  2024-05-01 ~ 2024-05-06; the source distribution chart (甲 2、乙 1、丙 1、丁 1) and the
  date distribution chart.
- **Suggested narration**:
  > "The overview shows basic distributions: four sources, five articles. The corpus is
  > small, but it is enough to demonstrate the full analysis pipeline."
- **Timing**: 15 seconds.

## Step 4: Topic clustering (1:10–1:40, ~30 s)

- **UI action**: scroll to「主题聚类分析」(Topic clustering); keep the default of 3
  clusters; optionally switch the「选择主题查看文章」(select topic) dropdown once.
- **What you should see**:
  - Topic 0: 1 article (20%), keywords: 社区、软件、开源、大会、举办
  - Topic 1: 2 articles (40%), keywords: 公交、专用道、调整、开通、新线路
  - Topic 2: 2 articles (40%), keywords: 水质、改善、空气质量、河流、治理
  - the topic-size chart and the per-topic article lists.
- **Suggested narration**:
  > "With the default of three topics, the open-source article stands alone, the metro
  > and bus articles group together, and the air-quality and river articles group
  > together. Topic numbers are exploratory algorithm output — I deliberately avoid
  > naming them 'transport' or 'environment', because that would imply the categories
  > were validated, and they are not."
- **Timing**: 30 seconds.

## Step 5: Multi-source comparison (1:40–2:10, ~30 s)

- **UI action**: scroll to「多来源对比」(Multi-source comparison); confirm the slider
  「每个来源至少包含的文章数」is 1; review the source keyword cards and the
  「来源 × 主题分布」(source × topic) table.
- **What you should see**:
  - keyword cards for all four sources (甲 has two keyword groups, 乙/丙/丁 one each);
  - the source × topic table: source 甲's two articles fall into topics 1 and 2
    (row shares 0.5 / 0.5); each other source holds a single topic;
  - interpretation-boundary captions everywhere (differences ≠ stance / bias / causation).
- **Suggested narration**:
  > "The comparison block turns 'differences between media sources' into observable text
  > properties: source keywords and the source-by-topic table. Source 甲's two articles
  > land in two different topics. With only five synthetic articles, these outputs are
  > demonstrations of the tool — not findings about any real media."
- **Timing**: 30 seconds.

## Step 6: Article detail and similar articles (2:10–2:40, ~30 s)

- **UI action**: scroll to「新闻详情与相似新闻」(Article detail & similar articles);
  select #0（城市地铁新线路开通）in the dropdown; then click「查看该新闻」(view this
  article) on one similar-article row to demo the jump.
- **What you should see**:
  - title, source, date, and body text;
  - the keyword table (开通 0.371391、新线路 0.371391、地铁 0.371391、换乘 0.185695、
    优化 0.185695);
  - the extractive summary (2 sentences, all taken from the original text);
  - similar articles Top3: 公交专用道 0.1070、空气质量 0.0546、河流水质 0.0169.
- **Suggested narration**:
  > "The single-article view offers keywords, an extractive summary whose sentences all
  > come from the original text, and similar articles. The closest match is the bus
  > article at 0.107 — similarity values are low overall; in a sparse small corpus a few
  > shared surface tokens can rank first. The 'view' button jumps to that article so you
  > can keep exploring."
- **Timing**: 30 seconds.

## Step 7: Limitations and next steps (2:40–3:00, ~20 s)

- **UI action**: scroll back to the top (or close verbally at the current section).
- **What you should see**: nothing new (verbal wrap-up; you may point at the sidebar
  data-status label).
- **Suggested narration**:
  > "To close: everything shown today is synthetic data. These methods cannot detect
  > media stance, trace propagation chains, or establish causation. Ingesting real data
  > is the next step — users can upload their own CSV following the data-preparation
  > guide and reuse the same analysis pipeline."
- **Timing**: 20 seconds.

---

## Notes (English version)

- "What you should see" reflects the current UI; if the system lacks Chinese fonts,
  charts degrade to built-in ones with a visible notice — mention this fallback if it
  appears.
- If the native file dialog is unsuitable for a live demo, use only the synthetic demo
  button and mention the upload entry in the sidebar verbally.
- Total time by the suggested timings is about 3 minutes; ±15 seconds of slack is
  acceptable.
