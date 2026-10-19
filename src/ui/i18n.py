"""界面文案中英双语字典（Phase 4.5）。

app.py 的全部静态界面文案集中在此模块；EN / ZH 两个字典的键集合必须一致
（由 tests/test_i18n.py 校验）。

边界（如实声明）：
    - 本模块只管界面静态文案（标题、按钮、说明、提示、表格列名）。
    - 数据内容不翻译：新闻标题、正文、关键词、来源名称均按原样展示。
    - 算法层生成的提示（聚类 note、摘要 note、来源对比 note）仍为中文，
      属于本阶段的已知边界。
"""

from __future__ import annotations

SUPPORTED_LANGS = ("en", "zh")
DEFAULT_LANG = "en"

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # ---------- 全局 / 顶部 ----------
        "app_caption": "AI-Powered Media Narrative Explorer",
        "positioning_md": (
            "**Research positioning**: explore news topics, keywords and text similarity "
            "with explainable text-mining methods (TF-IDF keywords, TextRank extractive "
            "summaries, KMeans topic clustering, cosine similarity), to help understand "
            "the structural features of news content.\n\n"
            "Text similarity only reflects surface/vector-level closeness — it does not "
            "indicate reprinting or causation; cluster IDs are exploratory, "
            "algorithm-generated groups, not verified news categories."
        ),
        # ---------- About This Research ----------
        "about_expander": "About This Research",
        "about_rq_md": (
            "**Research question**: How can explainable text-mining methods help users "
            "explore topic patterns and compare news coverage across media sources?"
        ),
        "about_motivation_md": (
            "**Why compare across sources**: coverage of the same event may differ in "
            "wording and topical emphasis across outlets. This app surfaces those "
            "differences as observable text phenomena (source keywords, source × topic "
            "distributions) to support further research questions; the differences "
            "themselves say nothing about which outlet is more objective."
        ),
        "about_data_md": (
            "**Current data status**: the project contains no real news data yet. "
            "The built-in example is a clearly labeled synthetic corpus for "
            "demonstration only; real data must be prepared and uploaded by the user "
            "(see docs/DATA_PREPARATION.md)."
        ),
        "about_methods_md": (
            "**Implemented methods**: TF-IDF keywords, TextRank extractive summaries, "
            "KMeans topic clustering, cosine similarity, source keyword comparison, "
            "and source × topic distributions."
        ),
        "about_cancannot_md": (
            "**What the methods support**: observing word-frequency structure, "
            "exploratory topic groups, retrieving textually similar articles, and "
            "observing content differences across sources — all within the current "
            "dataset.\n\n"
            "**What they cannot support**: identifying media stance or bias, tracing "
            "propagation chains or determining reprint relationships, drawing causal "
            "conclusions; extractive summaries are not fact-checks."
        ),
        "about_more_caption": (
            "Real news-data ingestion is future work, not a completed result. "
            "More background: docs/PROJECT_INTRO.md; verified example observations "
            "on synthetic data: docs/EXAMPLE_OBSERVATIONS.md."
        ),
        # ---------- 侧边栏 ----------
        "sb_import_header": "Data Import",
        "sb_upload_label": "Upload CSV file",
        "sb_upload_help": (
            "The CSV must contain the required columns: title, content, source."
        ),
        "sb_selected": "Selected: {name} ({size} bytes)",
        "sb_import_btn": "Import",
        "sb_demo_btn": "Load synthetic demo data",
        "status_synthetic": (
            "⚠ Current data: synthetic test data (not real news; demo only)"
        ),
        "status_user": "Current data: user-uploaded data ({name})",
        "status_none": "Status: no data imported yet",
        "status_other": "Current data: {label} ({name})",
        # ---------- 错误与状态 ----------
        "err_missing_cols": (
            "The CSV is missing required columns (title / content / source). "
            "Please check the column names and try again."
        ),
        "err_encoding": (
            "Could not detect the file encoding. Please save the CSV as UTF-8 "
            "or GBK and retry."
        ),
        "err_format": "Data format does not meet requirements: {msg}",
        "err_generic": "Import failed: {exc}",
        "err_import_kept_old": (
            "This import failed; the page still shows the previously imported "
            "dataset. Please fix the file and upload again."
        ),
        "info_no_data": (
            "No data imported yet. Upload a CSV file in the sidebar, or click "
            "'Load synthetic demo data' to try the features."
        ),
        "info_current_source": "Current data source: {label} (file: {filename})",
        "caption_synthetic_notice": (
            "Note: the current dataset is synthetic test data — it does not "
            "represent real news, real media sampling, or research findings."
        ),
        # ---------- 数据档案 ----------
        "prov_expander": "Data Provenance",
        "prov_metric_raw": "Raw records",
        "prov_metric_clean": "Records after cleaning",
        "prov_metric_fp": "Data fingerprint",
        "prov_dataset_name": "**Dataset name**: ",
        "prov_source_label": "**Source label**: ",
        "prov_imported_at": "**Imported at**: ",
        "prov_date_range": "**Publication date range**: ",
        "prov_cleaning_steps": "**Cleaning steps**: ",
        "prov_caption": (
            "The import time is kept only in this browser session and may reset "
            "after a refresh; this project does not yet implement a persistent "
            "audit log."
        ),
        # ---------- 数据质量概览 ----------
        "qo_title": "Data Quality Overview",
        "qo_metric_raw": "Raw records",
        "qo_metric_clean": "Records after cleaning",
        "qo_metric_removed": "Records removed by cleaning",
        "qo_dup": "**Raw data** duplicate rows: {n}",
        "qo_missing_header": "#### Missing values in required fields",
        "qo_col_field": "Field",
        "qo_col_raw": "Missing (raw)",
        "qo_col_clean": "Missing (cleaned)",
        "qo_date_header": "#### Date field (published_at) summary",
        "qo_valid": "Parseable",
        "qo_missing": "Missing (empty)",
        "qo_invalid": "Invalid format",
        "qo_range": "Valid date range",
        # ---------- 数据预览 ----------
        "dp_title": "Cleaned Data Preview",
        "dp_caption": "{n} rows in total; showing the first 20.",
        # ---------- 图表 ----------
        "chart_fallback": (
            "(No usable CJK font detected; falling back to the built-in chart.)"
        ),
        "chart_y_articles": "Articles",
        # ---------- 数据概览 ----------
        "ov_title": "Data Overview",
        "ov_empty": "No records to display after cleaning.",
        "ov_articles": "Articles (cleaned)",
        "ov_sources": "News sources",
        "ov_range": "Publication date range",
        "ov_no_date": "No parseable dates",
        "ov_completeness_header": "#### Key field completeness (non-empty counts)",
        "ov_col_field": "Field",
        "ov_col_nonempty": "Non-empty",
        "ov_col_total": "Total",
        "ov_no_required": "(no required fields)",
        "ov_len_header": "#### Body text length (characters)",
        "ov_min": "Min",
        "ov_max": "Max",
        "ov_mean": "Mean",
        "ov_median": "Median",
        "ov_no_content": "(no content field)",
        "ov_src_header": "#### Source distribution",
        "ov_src_none": "No usable source field; cannot show the source distribution.",
        "ov_src_single": (
            "All records come from a single source: {src} ({n} articles)."
        ),
        "ov_date_header": "#### Publication date distribution",
        "ov_date_none": "No parseable publication dates; cannot show the distribution.",
        "chart_src_title": "Source distribution",
        "chart_src_x": "Source",
        "chart_date_title": "Publication date distribution",
        "chart_date_x": "Date",
        # ---------- 主题聚类 ----------
        "cl_title": "Topic Clustering",
        "cl_caption": (
            "The clusters below are generated automatically by TF-IDF + KMeans. "
            "The IDs are exploratory groups — not verified news categories — and "
            "cannot be used directly to claim media bias or reporting intent."
        ),
        "cl_empty": "No records to analyze after cleaning; clustering is unavailable.",
        "cl_slider": "Number of clusters",
        "cl_slider_help": (
            "If too few valid texts remain, the cluster count is reduced automatically."
        ),
        "cl_fail": "Clustering failed: {e}",
        "cl_unclustered": (
            "{n} article(s) were excluded from clustering because their text "
            "became empty after preprocessing."
        ),
        "cl_no_result": "No valid clustering result was produced.",
        "cl_summary_header": "#### Topic overview",
        "cl_item": "**Topic {c}**: {n} articles ({r}), keywords: {kw}",
        "cl_dist_header": "#### Topic sizes",
        "chart_cl_title": "Topic sizes",
        "chart_cl_x": "Topic ID",
        "cl_select": "Select a topic to view articles",
        "cl_select_fmt": "Topic {x} ({n} articles)",
        "cl_articles_md": "**Articles in topic {c} ({n} in total)**",
        "cl_articles_empty": "(no articles in this topic yet)",
        # ---------- 多来源对比 ----------
        "sc_title": "Cross-Source Comparison",
        "sc_caption": (
            "This section compares keywords and topic distributions across news "
            "sources within the current sample. The differences only describe "
            "content-level variation — they do **not** prove media stance, bias, "
            "propagation paths, or causation; sources with few articles may be "
            "unstable, interpret with caution."
        ),
        "sc_empty": "No records to analyze after cleaning; comparison is unavailable.",
        "sc_kw_header": "#### Source keyword comparison",
        "sc_min_slider": "Minimum articles per source",
        "sc_min_help": (
            "Sources below this count are skipped (sample too small, unstable)."
        ),
        "sc_no_kw": "No source keywords to display.",
        "sc_source_md": "**{src}** ({n} articles)",
        "sc_kw_empty": "No keywords could be extracted from this source's text.",
        "sc_weight_caption": (
            "The weight column is the TF-IDF weight, indicating how distinctive a "
            "word is within that source's text — it is **not** an article count, "
            "a measure of influence, or an importance ranking; weights are only "
            "comparable within the current dataset."
        ),
        "sc_cross_header": "#### Source × topic distribution",
        "sc_no_cluster": (
            "No clustering result yet: please run clustering successfully in "
            "'Topic Clustering' first."
        ),
        "sc_counts_md": "**Article counts** (rows = sources, columns = topic IDs)",
        "sc_pct_md": (
            "**Row proportions** (denominator = all articles of the source, "
            "including unclustered ones)"
        ),
        "sc_chart_caption": (
            "The chart stacks article counts per topic by source. Topic IDs "
            "(0, 1, …) are exploratory KMeans groups, not verified news categories; "
            "distribution differences between sources cannot be read directly as "
            "stance or editorial intent. No cluster-quality metric is provided; "
            "with small samples the result is sensitive to the cluster count and "
            "random seed — interpret with caution."
        ),
        # ---------- 新闻详情与相似新闻 ----------
        "ae_title": "Article Detail & Similar Articles",
        "ae_caption": (
            "Text similarity only reflects surface/vector-level closeness — it "
            "does not imply factual agreement, reprinting, or shared stance."
        ),
        "ae_empty": "No articles to browse after cleaning.",
        "ae_select": "Select an article",
        "ae_no_title": "(no title)",
        "ae_unknown_source": "unknown source",
        "ae_unknown_date": "unknown date",
        "ae_no_content": "(no content)",
        "ae_source_line": "Source: {v}",
        "ae_date_line": "Published: {v}",
        "ae_body_expander": "Full text",
        "ae_analyze_fail": "Analysis failed: {e}",
        "ae_kw_header": "#### Keyword extraction",
        "ae_kw_caption": (
            "For a single article, TF-IDF weights degrade to term-frequency scale "
            "and only indicate frequent words in the text — not a statistically "
            "reliable importance ranking."
        ),
        "ae_kw_empty": "No keywords were extracted from this article.",
        "ae_sum_header": "#### Extractive summary (TextRank)",
        "ae_sum_caption": (
            "This summary is composed of sentences automatically selected from the "
            "original text and may omit important information. The existence of a "
            "summary does not prove the original text is true."
        ),
        "ae_sum_empty": "A summary could not be generated for this article.",
        "ae_sum_note": "Note: {note}",
        "ae_sim_header": "#### Similar articles",
        "ae_sim_slider": "Number of similar articles",
        "ae_sim_empty": "No articles with text similarity greater than 0 were found.",
        "ae_sim_row": "**{title}** | {source} | {date} | similarity: {sim}",
        "ae_view_btn": "View this article",
        "ae_sim_caption": (
            "Text similarity only reflects surface/vector closeness — it does not "
            "equal reprinting, causation, or shared stance."
        ),
        # ---------- AI Topic Recommendations (Phase 5.1, local rules) ----------
        "st_page_radio": "Page",
        "st_page_dashboard": "Dashboard",
        "st_page_strategist": "AI Topic Recommendations",
        # ---------- Dashboard tabs (visual grouping; no module is removed) ----------
        "dash_tab_profile": "Data Snapshot",
        "dash_tab_topics": "Distribution & Topics",
        "dash_tab_articles": "Article Explorer",
        "st_title": "AI Topic Recommendations",
        "st_caption": (
            "Topics are generated from clustering and keyword statistics of the "
            "current dataset, with a fully transparent ranking rule. They support "
            "topic brainstorming and are not trend predictions."
        ),
        "st_synthetic_notice": (
            "⚠ Current data: synthetic demo data — these recommendations are NOT "
            "real trends or hotspots."
        ),
        "st_rule_header": "#### Ranking rule (explicit and reproducible)",
        "st_rule_md": (
            "**Score = 0.5 × topic share + 0.3 × keyword strength + 0.2 × recency.** "
            "Topic share = topic articles / clustered articles; keyword strength = "
            "mean corpus-level TF-IDF weight of the topic's representative keywords, "
            "normalized by the largest topic; recency = closeness of the topic's "
            "latest date to the dataset's latest date. An unavailable factor is "
            "excluded and the remaining weights renormalized — no value is invented."
        ),
        "st_scope_caption": (
            "The score only describes statistical structure inside the current "
            "dataset. Article counts do not equal platform traffic or real user "
            "interest; no content performance is predicted."
        ),
        "st_empty": "No topic recommendations can be generated from the current data.",
        "st_unclustered": (
            "{n} article(s) were excluded from clustering (empty text after "
            "preprocessing) and do not belong to any topic."
        ),
        "st_note_no_dates": (
            "The dataset has no parsable dates, so the recency factor was excluded "
            "from ranking."
        ),
        "st_note_kw_na": (
            "Corpus-level keyword weights are unavailable, so the keyword-strength "
            "factor was excluded from ranking."
        ),
        "st_note_small_sample": (
            "Only {n} article(s) joined clustering — a small sample; topic grouping "
            "and ranking are unstable and for reference only."
        ),
        "st_option": "#{rank} {kw} ({n} articles · {ratio})",
        "st_topic_untitled": "(unnamed topic)",
        "st_reason": (
            "{n} article(s) ({ratio} of clustered corpus) share representative "
            "keywords: {kw}; latest article in this topic: {date}."
        ),
        "st_unknown_date": "unknown",
        "st_factor_na": "—",
        "st_factors_header": "#### Ranking factors",
        "st_col_topic": "Topic",
        "st_col_share": "Topic share",
        "st_col_kw": "Keyword strength",
        "st_col_recency": "Recency",
        "st_col_score": "Score",
        "st_articles_header": (
            "#### Related articles ({n} shown, up to {max} per topic; see Topic "
            "Clustering for the full list)"
        ),
        "st_col_title": "Title",
        "st_col_source": "Source",
        "st_col_date": "Date",
        # ---------- AI Copywriting (pluggable local backend) ----------
        "cp_title": "AI Copywriting",
        "cp_caption": (
            "Copy is generated through a pluggable backend, switchable in the UI. "
            "Mock sends nothing; Ollama runs on the local machine; Gemini sends the "
            "prompt to Google's online API and Groq to Groq's online API (both free "
            "tier). Each mode is labelled below."
        ),
        "cp_mock_notice": (
            "⚠ Mock mode: no local model is connected yet. The output below is "
            "FIXED PLACEHOLDER copy for UI testing only — it is NOT generated "
            "by any AI model and must not be used."
        ),
        "cp_provider_label": "Model backend",
        "cp_backend_mock": "Mock (placeholder copy, no model)",
        "cp_backend_ollama": "Ollama (local model)",
        "cp_backend_gemini": "Gemini (online API, free tier)",
        "cp_backend_groq": "Groq (online API, free tier)",
        "cp_model_label": "Local model name (e.g. qwen3:1.7b)",
        "cp_backend_online": "Local Ollama service detected — ready to generate.",
        "cp_backend_offline": (
            "Cannot reach the local Ollama service (127.0.0.1:11434). "
            "Start it with `ollama serve` before generating, or generation will fail."
        ),
        "cp_ollama_notice": (
            "⚠ Copy is generated by a local AI model running on this machine "
            "(Ollama, 127.0.0.1). Output may contain factual errors or omissions — "
            "please review it against the source articles before use."
        ),
        "cp_gemini_model_label": "Online model name (default gemini-2.0-flash)",
        "cp_gemini_ready": "API key detected — ready to generate.",
        "cp_gemini_no_key": (
            "No API key configured. Set the ECHOMAP_GEMINI_API_KEY secret in the "
            "deployment platform (or the environment variable) before generating, "
            "or generation will fail."
        ),
        "cp_gemini_notice": (
            "⚠ Copy is generated by an online AI model (Google Gemini, free tier). "
            "The prompt is sent to Google's API over the network. Output may contain "
            "factual errors or omissions — please review it against the source "
            "articles before use, and avoid pasting confidential material."
        ),
        "cp_groq_model_label": "Online model name (default llama-3.3-70b-versatile)",
        "cp_groq_ready": "API key detected — ready to generate.",
        "cp_groq_no_key": (
            "No API key configured. Set the ECHOMAP_GROQ_API_KEY secret in the "
            "deployment platform (or the environment variable) before generating, "
            "or generation will fail."
        ),
        "cp_groq_notice": (
            "⚠ Copy is generated by an online AI model (Groq, free tier). The prompt "
            "is sent to Groq's API over the network. Output may contain factual "
            "errors or omissions — please review it against the source articles "
            "before use, and avoid pasting confidential material."
        ),
        "cp_platform": "Content platform",
        "cp_audience": "Target audience",
        "cp_style": "Copy style",
        "cp_generate_btn": "Generate copy",
        "cp_generating": "Calling the model… (this may take a few seconds)",
        "cp_editor": "Copy preview & edit",
        "cp_copy_hint": (
            "Read-only view with a copy button (top-right of the block below); "
            "edits above are kept."
        ),
        "cp_prompt_expander": (
            "Preview prompt (mock: not sent anywhere; ollama: sent only to the local "
            "model; gemini: sent to Google's online API; groq: sent to Groq's online API)"
        ),
        "cp_empty_hint": "Select a topic above first.",
        "cp_fail": "Generation failed: {e}",
        "cp_platform_xiaohongshu": "Xiaohongshu (RED)",
        "cp_platform_wechat_mp": "WeChat Official Account",
        "cp_platform_douyin": "Douyin (short video)",
        "cp_platform_weibo": "Weibo",
        "cp_audience_general": "General readers",
        "cp_audience_students": "Students",
        "cp_audience_professionals": "Industry professionals",
        "cp_style_practical": "Practical tips",
        "cp_style_educational": "Educational explainer",
        "cp_style_casual": "Casual sharing",
        # ---------- Sensitive-content check (local rules, no network) ----------
        "safety_header": "#### Sensitive-content check (local rules, no network)",
        "safety_pass": (
            "PASSED — no sensitive terms or personal data detected. "
            "Export (the copy block below) is enabled."
        ),
        "safety_fail": (
            "NOT PASSED — {n} issue(s) detected. Export is DISABLED; "
            "please revise the copy above and it will be re-checked automatically."
        ),
        "safety_uncertain": (
            "INCONCLUSIVE — this copy could not be confirmed safe. Export is DISABLED."
        ),
        "safety_items_header": "Detected categories (masked):",
        "safety_masked_preview": "Masked preview:",
        "safety_export_disabled": (
            "Export disabled: revise the copy above; the check reruns on every render."
        ),
        "safety_cat_phone": "Phone number",
        "safety_cat_id_card": "ID card number",
        "safety_cat_email": "Email address",
        "safety_cat_sensitive_word": "Sensitive term (abuse / vulgar / death, etc.)",
    },
    "zh": {
        # ---------- 全局 / 顶部 ----------
        "app_caption": "AI-Powered Media Narrative Explorer · AI 驱动的媒体叙事探索平台",
        "positioning_md": (
            "**研究定位**：通过可解释的文本挖掘方法（TF-IDF 关键词、TextRank 抽取式摘要、"
            "KMeans 主题聚类、余弦相似度）探索新闻主题、关键词与文本相似性，"
            "辅助理解新闻内容的结构特征。\n\n"
            "文本相似性只反映词面/向量层面的接近程度，不代表传播关系或因果关系；"
            "聚类编号为算法生成的探索性分组，不代表已验证的新闻类别。"
        ),
        # ---------- About This Research ----------
        "about_expander": "About This Research / 关于本研究",
        "about_rq_md": (
            "**研究问题**：How can explainable text-mining methods help users "
            "explore topic patterns and compare news coverage across media sources？"
            "（可解释的文本挖掘方法如何帮助用户探索新闻主题模式、对比不同媒体的报道内容？）"
        ),
        "about_motivation_md": (
            "**为什么做多来源对比**：同一事件在不同媒体的报道，用词与主题侧重可能不同。"
            "本应用把这种差异作为可观察的文本现象来展示（来源关键词、来源×主题分布），"
            "供进一步研究提问使用；差异本身不能说明哪个媒体更客观。"
        ),
        "about_data_md": (
            "**当前数据状态**：项目尚无真实新闻数据。内置示例为明确标记的合成语料，"
            "仅用于演示功能；真实数据需使用者自行准备并上传"
            "（规范见 docs/DATA_PREPARATION.md）。"
        ),
        "about_methods_md": (
            "**已实现的方法**：TF-IDF 关键词、TextRank 抽取式摘要、KMeans 主题聚类、"
            "余弦相似度、来源关键词对比与来源×主题分布。"
        ),
        "about_cancannot_md": (
            "**方法能支持什么**：在当前数据集内观察词频结构、探索性主题分组、"
            "检索词面相似的文章、观察来源间的内容差异。\n\n"
            "**方法不能支持什么**：不能识别媒体立场或偏见，不能追踪传播链或判定"
            "转载关系，不能得出因果结论，抽取式摘要不构成事实核查。"
        ),
        "about_more_caption": (
            "真实新闻数据的接入是后续工作，不是当前已完成成果。"
            "更多背景见 docs/PROJECT_INTRO.md；合成数据上的示例观察见 "
            "docs/EXAMPLE_OBSERVATIONS.md。"
        ),
        # ---------- 侧边栏 ----------
        "sb_import_header": "数据导入",
        "sb_upload_label": "上传 CSV 文件",
        "sb_upload_help": "CSV 需包含必需列：title（标题）、content（正文）、source（来源）。",
        "sb_selected": "已选择：{name}（{size} 字节）",
        "sb_import_btn": "开始导入",
        "sb_demo_btn": "加载合成示例数据",
        "status_synthetic": "⚠ 当前数据：合成测试数据（非真实新闻，仅供演示）",
        "status_user": "当前数据：用户上传数据（{name}）",
        "status_none": "当前状态：尚未导入数据",
        "status_other": "当前数据：{label}（{name}）",
        # ---------- 错误与状态 ----------
        "err_missing_cols": "CSV 文件缺少必需列（title / content / source），请检查列名后重试。",
        "err_encoding": "无法识别文件编码，请尝试另存为 UTF-8 或 GBK 编码的 CSV。",
        "err_format": "数据格式不符合要求：{msg}",
        "err_generic": "导入失败：{exc}",
        "err_import_kept_old": (
            "本次导入失败，当前页面显示的仍是上一份成功导入的数据。"
            "请修正文件后重新上传。"
        ),
        "info_no_data": "尚未导入数据。请在左侧上传 CSV 文件，或点击「加载合成示例数据」体验功能。",
        "info_current_source": "当前数据来源：{label}（文件：{filename}）",
        "caption_synthetic_notice": (
            "注意：当前为合成测试数据（Synthetic test data），"
            "不代表真实新闻、真实媒体采样或研究结论。"
        ),
        # ---------- 数据档案 ----------
        "prov_expander": "数据档案（Data Provenance）",
        "prov_metric_raw": "原始记录数",
        "prov_metric_clean": "清洗后记录数",
        "prov_metric_fp": "数据指纹",
        "prov_dataset_name": "**数据集名称**：",
        "prov_source_label": "**数据来源标记**：",
        "prov_imported_at": "**导入时间**：",
        "prov_date_range": "**发布日期范围**：",
        "prov_cleaning_steps": "**清洗步骤**：",
        "prov_caption": (
            "导入时间仅保存在当前浏览器会话中，刷新或重新载入后可能重置；"
            "本项目尚未实现持久化的数据审计日志。"
        ),
        # ---------- 数据质量概览 ----------
        "qo_title": "数据质量概览",
        "qo_metric_raw": "原始记录数",
        "qo_metric_clean": "清洗后记录数",
        "qo_metric_removed": "被清洗掉的记录数",
        "qo_dup": "**原始数据**重复记录数：{n}",
        "qo_missing_header": "#### 必需字段缺失情况",
        "qo_col_field": "字段",
        "qo_col_raw": "原始数据缺失",
        "qo_col_clean": "清洗后数据缺失",
        "qo_date_header": "#### 日期字段（published_at）摘要",
        "qo_valid": "可解析",
        "qo_missing": "缺失（空）",
        "qo_invalid": "无效格式",
        "qo_range": "有效日期范围",
        # ---------- 数据预览 ----------
        "dp_title": "清洗后数据预览",
        "dp_caption": "共 {n} 行，仅展示前 20 行。",
        # ---------- 图表 ----------
        "chart_fallback": "（系统未检测到可用中文字体，已使用内置图表降级显示）",
        "chart_y_articles": "文章数量",
        # ---------- 数据概览 ----------
        "ov_title": "数据概览",
        "ov_empty": "清洗后没有可展示的数据记录。",
        "ov_articles": "清洗后新闻数量",
        "ov_sources": "新闻来源数量",
        "ov_range": "发布日期范围",
        "ov_no_date": "无可解析日期",
        "ov_completeness_header": "#### 关键字段完整性（非空数量）",
        "ov_col_field": "字段",
        "ov_col_nonempty": "非空数量",
        "ov_col_total": "总记录数",
        "ov_no_required": "（无必需字段）",
        "ov_len_header": "#### 正文长度统计（字符数）",
        "ov_min": "最短",
        "ov_max": "最长",
        "ov_mean": "平均",
        "ov_median": "中位数",
        "ov_no_content": "（无 content 字段）",
        "ov_src_header": "#### 新闻来源分布",
        "ov_src_none": "没有可用的来源字段，无法展示来源分布。",
        "ov_src_single": "全部记录来自同一来源：{src}（{n} 篇）。",
        "ov_date_header": "#### 发布日期分布",
        "ov_date_none": "没有可解析的发布日期，无法展示日期分布。",
        "chart_src_title": "新闻来源分布",
        "chart_src_x": "来源",
        "chart_date_title": "发布日期分布",
        "chart_date_x": "日期",
        # ---------- 主题聚类 ----------
        "cl_title": "主题聚类分析",
        "cl_caption": (
            "以下聚类结果由 TF-IDF + KMeans 算法自动生成，编号为探索性分组，"
            "不代表已验证的新闻类别，也不能直接据此断言媒体偏见或报道意图。"
        ),
        "cl_empty": "清洗后没有可分析的数据记录，无法聚类。",
        "cl_slider": "聚类数量",
        "cl_slider_help": "有效文本数不足时，聚类数会被自动下调。",
        "cl_fail": "聚类失败：{e}",
        "cl_unclustered": "{n} 篇文章因预处理后文本为空而未参与聚类。",
        "cl_no_result": "未产生有效聚类结果。",
        "cl_summary_header": "#### 各主题概况",
        "cl_item": "**主题 {c}**：{n} 篇（{r}），代表关键词：{kw}",
        "cl_dist_header": "#### 主题分布",
        "chart_cl_title": "主题分布",
        "chart_cl_x": "主题编号",
        "cl_select": "选择主题查看文章",
        "cl_select_fmt": "主题 {x}（{n} 篇）",
        "cl_articles_md": "**主题 {c} 的文章（共 {n} 篇）**",
        "cl_articles_empty": "（该主题下暂无文章）",
        # ---------- 多来源对比 ----------
        "sc_title": "多来源对比",
        "sc_caption": (
            "本区块比较不同新闻来源在当前样本中的关键词与主题分布差异。"
            "差异仅描述内容层面的不同，**不能证明**媒体立场、偏见、传播路径或因果关系；"
            "文章数少的来源结果可能不稳定，请谨慎解读。"
        ),
        "sc_empty": "清洗后没有可分析的数据记录，无法进行来源对比。",
        "sc_kw_header": "#### 来源关键词对比",
        "sc_min_slider": "每个来源至少包含的文章数",
        "sc_min_help": "低于该数量的来源会被跳过（样本过小、结果不稳定）。",
        "sc_no_kw": "没有可展示的来源关键词。",
        "sc_source_md": "**{src}**（{n} 篇）",
        "sc_kw_empty": "该来源文本未能提取出关键词。",
        "sc_weight_caption": (
            "表中 weight 为 TF-IDF 权重，表示词语在该来源文本中的相对区分能力，"
            "**不是**文章数量、媒体影响力或重要性排名；权重仅在当前数据集内可比。"
        ),
        "sc_cross_header": "#### 来源 × 主题分布",
        "sc_no_cluster": "暂无聚类结果：请先在「主题聚类分析」中成功执行聚类。",
        "sc_counts_md": "**文章数量**（行=来源，列=主题编号）",
        "sc_pct_md": "**行占比**（分母 = 该来源的全部文章数，含未参与聚类的文章）",
        "sc_chart_caption": (
            "上图按来源堆叠展示各主题的文章数量。主题编号（0、1、…）为 KMeans "
            "算法生成的探索性分组，不是已验证的新闻类别；来源间的分布差异不能"
            "直接解读为报道立场或编辑意图。当前实现未提供聚类质量指标，"
            "小样本下分布结果对聚类数与随机种子较敏感，请谨慎解释。"
        ),
        # ---------- 新闻详情与相似新闻 ----------
        "ae_title": "新闻详情与相似新闻",
        "ae_caption": (
            "文本相似度仅表示词面/向量层面的接近程度，"
            "不代表事实一致、转载关系或媒体立场一致。"
        ),
        "ae_empty": "清洗后没有可浏览的新闻。",
        "ae_select": "选择新闻",
        "ae_no_title": "（无标题）",
        "ae_unknown_source": "未知来源",
        "ae_unknown_date": "未知日期",
        "ae_no_content": "（无正文）",
        "ae_source_line": "来源：{v}",
        "ae_date_line": "发布时间：{v}",
        "ae_body_expander": "查看正文",
        "ae_analyze_fail": "分析失败：{e}",
        "ae_kw_header": "#### 关键词提取",
        "ae_kw_caption": (
            "单篇文章的 TF-IDF 权重退化为词频量级，仅可作为文内高频词参考，"
            "不构成具有统计可靠性的重要性排名。"
        ),
        "ae_kw_empty": "该文章没有提取到关键词。",
        "ae_sum_header": "#### 抽取式摘要（TextRank）",
        "ae_sum_caption": (
            "本摘要由模型从原文中自动抽取句子组成，可能遗漏重要信息。"
            "摘要存在不等于原文被证明为真。"
        ),
        "ae_sum_empty": "该文章无法生成摘要。",
        "ae_sum_note": "提示：{note}",
        "ae_sim_header": "#### 相似新闻",
        "ae_sim_slider": "相似新闻数量",
        "ae_sim_empty": "未找到文本相似度大于 0 的新闻。",
        "ae_sim_row": "**{title}** ｜ {source}｜ {date}｜ 相似度：{sim}",
        "ae_view_btn": "查看该新闻",
        "ae_sim_caption": (
            "文本相似度只反映词面/向量接近程度，"
            "不等于转载、因果关系或立场一致。"
        ),
        # ---------- AI 选题推荐（阶段 5.1，本地规则）----------
        "st_page_radio": "页面",
        "st_page_dashboard": "仪表板",
        "st_page_strategist": "AI 推荐选题",
        # ---------- 仪表板标签页（仅做视觉分组，不删除任何模块）----------
        "dash_tab_profile": "数据概况",
        "dash_tab_topics": "分布与主题",
        "dash_tab_articles": "文章探索",
        "st_title": "AI 推荐选题",
        "st_caption": (
            "选题由当前数据集的聚类主题与关键词统计生成，排序规则完全公开。"
            "推荐结果用于辅助选题思考，不代表热点预测。"
        ),
        "st_synthetic_notice": (
            "⚠ 当前数据：合成演示数据，非真实热点——推荐结果仅用于功能演示。"
        ),
        "st_rule_header": "#### 排序规则（明确、可复现）",
        "st_rule_md": (
            "**综合排序值 = 0.5 × 主题占比 + 0.3 × 关键词强度 + 0.2 × 时间新近度。**"
            "主题占比 = 主题文章数 / 参与聚类文章数；关键词强度 = 主题代表关键词的"
            "语料级 TF-IDF 平均权重（按各主题最大值归一化）；时间新近度 = 主题内"
            "最晚日期接近数据集最晚日期的程度。某因子不可用时按其余因子权重重新"
            "归一化，不虚构取值。"
        ),
        "st_scope_caption": (
            "排序值只描述当前数据集内部的统计结构；新闻数量 ≠ 平台流量 ≠ 用户真实"
            "兴趣，本功能不预测任何内容在平台上的表现。"
        ),
        "st_empty": "当前数据无法生成选题推荐。",
        "st_unclustered": (
            "{n} 篇文章未参与聚类（预处理后文本为空），不计入任何主题。"
        ),
        "st_note_no_dates": (
            "数据中没有可解析的日期，时间新近度因子未参与本次排序。"
        ),
        "st_note_kw_na": (
            "语料级关键词权重不可用，关键词强度因子未参与本次排序。"
        ),
        "st_note_small_sample": (
            "参与聚类的文章仅 {n} 篇，样本过小，主题分组与排序不稳定，仅供参考。"
        ),
        "st_option": "#{rank} {kw}（{n} 篇 · {ratio}）",
        "st_topic_untitled": "（未命名主题）",
        "st_reason": (
            "主题下共 {n} 篇文章（占参与聚类文章的 {ratio}），代表关键词：{kw}；"
            "主题内最新报道：{date}。"
        ),
        "st_unknown_date": "未知",
        "st_factor_na": "—",
        "st_factors_header": "#### 排序因子明细",
        "st_col_topic": "选题",
        "st_col_share": "主题占比",
        "st_col_kw": "关键词强度",
        "st_col_recency": "时间新近度",
        "st_col_score": "综合排序值",
        "st_articles_header": (
            "#### 相关新闻（显示 {n} 篇，每题最多 {max} 篇；完整列表见主题聚类区块）"
        ),
        "st_col_title": "标题",
        "st_col_source": "来源",
        "st_col_date": "日期",
        # ---------- AI 文案生成（可插拔本地后端）----------
        "cp_title": "AI 文案生成",
        "cp_caption": (
            "文案通过可插拔的后端生成，界面上可随时切换：模拟模式不发送任何请求；"
            "Ollama 只在本机运行；Gemini 与 Groq 会把提示词分别发送至对应厂商的"
            "在线接口（均为免费额度），任一家额度用尽可切到另一家。"
            "各模式的差异在下方明确标注。"
        ),
        "cp_mock_notice": (
            "⚠ 模拟模式：尚未接入本地模型。下方输出为界面联调用的固定占位文案，"
            "不是任何 AI 模型生成的结果，请勿直接使用。"
        ),
        "cp_provider_label": "模型后端",
        "cp_backend_mock": "模拟（占位文案，不调用模型）",
        "cp_backend_ollama": "Ollama（本地模型）",
        "cp_backend_gemini": "Gemini（在线接口，免费额度）",
        "cp_backend_groq": "Groq（在线接口，免费额度）",
        "cp_model_label": "本地模型名（如 qwen3:1.7b）",
        "cp_backend_online": "已检测到本机 Ollama 服务，可以生成。",
        "cp_backend_offline": (
            "无法连接本机 Ollama（127.0.0.1:11434），请先启动 `ollama serve` 再生成，"
            "否则生成会失败。"
        ),
        "cp_ollama_notice": (
            "⚠ 文案由本机运行的本地 AI 模型（Ollama，127.0.0.1）生成，"
            "可能存在事实错误或遗漏，使用前请对照来源新闻人工核查。"
        ),
        "cp_gemini_model_label": "在线模型名（默认 gemini-2.0-flash）",
        "cp_gemini_ready": "已检测到 API 密钥，可以生成。",
        "cp_gemini_no_key": (
            "未配置 API 密钥：请在部署平台的 Secrets（或环境变量）中设置 "
            "ECHOMAP_GEMINI_API_KEY 后再生成，否则生成会失败。"
        ),
        "cp_gemini_notice": (
            "⚠ 文案由在线 AI 模型（Google Gemini，免费额度）生成，提示词会经网络"
            "发送至 Google 接口。内容可能存在事实错误或遗漏，使用前请对照来源新闻"
            "人工核查；请勿粘贴机密材料。"
        ),
        "cp_groq_model_label": "在线模型名（默认 llama-3.3-70b-versatile）",
        "cp_groq_ready": "已检测到 API 密钥，可以生成。",
        "cp_groq_no_key": (
            "未配置 API 密钥：请在部署平台的 Secrets（或环境变量）中设置 "
            "ECHOMAP_GROQ_API_KEY 后再生成，否则生成会失败。"
        ),
        "cp_groq_notice": (
            "⚠ 文案由在线 AI 模型（Groq，免费额度）生成，提示词会经网络发送至 "
            "Groq 接口。内容可能存在事实错误或遗漏，使用前请对照来源新闻人工核查；"
            "请勿粘贴机密材料。"
        ),
        "cp_platform": "内容平台",
        "cp_audience": "目标受众",
        "cp_style": "文案风格",
        "cp_generate_btn": "生成文案",
        "cp_generating": "正在调用模型生成…（可能需要数秒）",
        "cp_editor": "文案预览与编辑",
        "cp_copy_hint": "只读视图（下方代码块右上角可一键复制）；上方编辑内容会保留。",
        "cp_prompt_expander": (
            "查看提示词（模拟模式不发送；Ollama 模式仅发送给本机模型；"
            "Gemini 模式发送至 Google 在线接口；Groq 模式发送至 Groq 在线接口）"
        ),
        "cp_empty_hint": "请先在上方选择选题。",
        "cp_fail": "生成失败：{e}",
        "cp_platform_xiaohongshu": "小红书",
        "cp_platform_wechat_mp": "微信公众号",
        "cp_platform_douyin": "抖音",
        "cp_platform_weibo": "微博",
        "cp_audience_general": "大众读者",
        "cp_audience_students": "学生群体",
        "cp_audience_professionals": "行业从业者",
        "cp_style_practical": "实用干货",
        "cp_style_educational": "知识科普",
        "cp_style_casual": "轻松分享",
        # ---------- 敏感信息检测（本地规则，不联网）----------
        "safety_header": "#### 敏感信息检测（本地规则，不联网）",
        "safety_pass": "已通过 —— 未检出敏感词或个人信息，可导出下方文案（复制块）。",
        "safety_fail": (
            "未通过 —— 检出 {n} 处问题，已禁用导出；"
            "请修改上方文案，系统会自动重新检测。"
        ),
        "safety_uncertain": "无法确定 —— 未能确认该文案安全，已禁用导出。",
        "safety_items_header": "检出的类别（已脱敏）：",
        "safety_masked_preview": "脱敏预览：",
        "safety_export_disabled": "导出已禁用：请修改上方文案，每次渲染都会自动重新检测。",
        "safety_cat_phone": "手机号",
        "safety_cat_id_card": "身份证号",
        "safety_cat_email": "邮箱",
        "safety_cat_sensitive_word": "敏感词（辱骂 / 低俗 / 负面伤亡等）",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    """按语言取界面文案；支持 {placeholder} 格式化。

    回退顺序：指定语言 → 默认语言（en）→ 键名本身（便于发现遗漏）。
    lang 非法时按默认语言处理，不抛异常。
    """
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    text = table.get(key)
    if text is None:
        text = STRINGS[DEFAULT_LANG].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
