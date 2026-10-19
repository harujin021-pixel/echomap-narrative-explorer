"""数据清洗模块的单元测试（标准库 unittest）。"""

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_csv  # noqa: E402
from src.data.cleaning import clean_news_data  # noqa: E402

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_sample_news.csv"


class TestCleaning(unittest.TestCase):
    def setUp(self):
        self.raw = load_csv(FIXTURE)

    def test_row_count_after_cleaning(self):
        # 原始 5 行：删除 1 个空正文、1 个空标题、1 个重复行 -> 剩 2 行
        clean = clean_news_data(self.raw)
        self.assertEqual(len(clean), 2)

    def test_does_not_mutate_input(self):
        clean_news_data(self.raw)
        self.assertEqual(len(self.raw), 5)

    def test_strips_whitespace(self):
        clean = clean_news_data(self.raw)
        self.assertEqual(clean.loc[0, "title"], "合成示例：城市交通新政策")

    def test_no_empty_required_fields(self):
        clean = clean_news_data(self.raw)
        for col in ("title", "content", "source"):
            self.assertTrue((clean[col] != "").all(), f"{col} 仍存在空值")

    def test_no_duplicate_rows(self):
        clean = clean_news_data(self.raw)
        self.assertEqual(int(clean.duplicated().sum()), 0)

    def test_date_column_parsed(self):
        clean = clean_news_data(self.raw)
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(clean["published_at"])
        )
        # 清洗后第 1 行日期有效，第 2 行日期无效（NaT）
        self.assertFalse(pd.isna(clean.loc[0, "published_at"]))
        self.assertTrue(pd.isna(clean.loc[1, "published_at"]))


class TestHtmlStripping(unittest.TestCase):
    """HTML 残留清洗：抓取网页正文常混入 <p style="text-indent:2em"> 等标记，
    不剥离会被 TF-IDF 当成高频词，产生按排版格式聚类的伪主题。"""

    @staticmethod
    def _df(content: str, title: str = "标题", source: str = "来源") -> pd.DataFrame:
        return pd.DataFrame(
            {"title": [title], "content": [content], "source": [source]}
        )

    def test_html_tags_removed_from_content(self):
        clean = clean_news_data(self._df('<p style="text-indent:2em">正文内容</p>'))
        self.assertEqual(clean.loc[0, "content"], "正文内容")

    def test_html_tags_removed_from_title_and_source(self):
        clean = clean_news_data(
            self._df("正文", title="<b>标题</b>", source='<span class="s">来源</span>')
        )
        self.assertEqual(clean.loc[0, "title"], "标题")
        self.assertEqual(clean.loc[0, "source"], "来源")

    def test_html_entities_unescaped(self):
        clean = clean_news_data(self._df("甲&nbsp;乙&amp;丙"))
        # &nbsp; 还原后归一为普通空格，&amp; 还原为 &
        self.assertEqual(clean.loc[0, "content"], "甲 乙&丙")

    def test_tag_only_content_becomes_empty_and_row_removed(self):
        df = pd.DataFrame(
            {
                "title": ["有效标题", "空壳标题"],
                "content": ["有效正文", "<p></p>"],
                "source": ["来源", "来源"],
            }
        )
        clean = clean_news_data(df)
        # 第二行 content 只剩标签，剥离后为空 -> 按“必需列为空”规则删除
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean.loc[0, "title"], "有效标题")

    def test_plain_text_unchanged(self):
        clean = clean_news_data(self._df("不含任何标记的普通正文。"))
        self.assertEqual(clean.loc[0, "content"], "不含任何标记的普通正文。")

    def test_comparison_operators_in_text_not_treated_as_tags(self):
        # “2<3 且 5>1” 中的 <> 是文本比较符而非标签；<...> 配对会被当作标签剥除，
        # 此处如实记录当前（简单正则）行为边界：未配对的 < 或 > 原样保留
        clean = clean_news_data(self._df("增速 5>1 倍"))
        self.assertEqual(clean.loc[0, "content"], "增速 5>1 倍")


if __name__ == "__main__":
    unittest.main(verbosity=2)
