"""CSV 导入模块的单元测试（标准库 unittest）。"""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import (  # noqa: E402
    REQUIRED_COLUMNS,
    DataValidationError,
    find_csv_files,
    load_csv,
)

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_sample_news.csv"


class TestLoader(unittest.TestCase):
    def test_load_valid_fixture(self):
        df = load_csv(FIXTURE)
        self.assertEqual(len(df), 5)
        for col in REQUIRED_COLUMNS:
            self.assertIn(col, df.columns)

    def test_empty_cells_are_empty_string(self):
        df = load_csv(FIXTURE)
        # 第 4 行 content 为空，应读成空字符串而不是 NaN
        self.assertEqual(df.loc[3, "content"], "")

    def test_missing_required_column_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.csv"
            bad.write_text("id,title\n1,只有标题\n", encoding="utf-8")
            with self.assertRaises(DataValidationError):
                load_csv(bad)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_csv(PROJECT_ROOT / "tests" / "fixtures" / "no_such_file.csv")

    def test_find_csv_files(self):
        files = find_csv_files(PROJECT_ROOT / "tests" / "fixtures")
        self.assertIn(FIXTURE, files)
        self.assertEqual(find_csv_files(PROJECT_ROOT / "no_such_dir"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
