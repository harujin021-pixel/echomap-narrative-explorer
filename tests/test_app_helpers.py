"""app/app.py 中可独立测试的辅助函数测试（标准库 unittest）。

仅测试不依赖 Streamlit 运行时的纯函数（如 _friendly_error、sidebar_data_status）。
Streamlit 交互逻辑（按钮、session_state 流转）通过人工验收验证。
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.app import _friendly_error, sidebar_data_status  # noqa: E402
from src.data.loader import DataValidationError  # noqa: E402


class TestFriendlyError(unittest.TestCase):
    def test_missing_required_column_message(self):
        exc = DataValidationError("CSV 文件缺少必需列 ['title']")
        msg = _friendly_error(exc)
        self.assertIn("缺少必需列", msg)
        self.assertIn("title / content / source", msg)

    def test_encoding_error_message(self):
        exc = DataValidationError("无法用候选编码解码文件")
        msg = _friendly_error(exc)
        self.assertIn("编码", msg)

    def test_other_validation_error_message(self):
        exc = DataValidationError("其他格式问题")
        msg = _friendly_error(exc)
        self.assertIn("数据格式不符合要求", msg)
        self.assertIn("其他格式问题", msg)

    def test_generic_exception_message(self):
        exc = RuntimeError("未知错误")
        msg = _friendly_error(exc)
        self.assertIn("导入失败", msg)
        self.assertIn("未知错误", msg)


class TestSidebarDataStatus(unittest.TestCase):
    """数据来源标注文案：按实际加载标记动态生成，不猜测来源。"""

    def test_synthetic_label_warns_not_real_news(self):
        msg = sidebar_data_status("合成测试数据", "synthetic_news_corpus.csv")
        self.assertIn("合成测试数据", msg)
        self.assertIn("非真实新闻", msg)

    def test_user_upload_shows_filename(self):
        msg = sidebar_data_status("用户上传数据", "my_news.csv")
        self.assertIn("用户上传数据", msg)
        self.assertIn("my_news.csv", msg)
        self.assertNotIn("合成", msg)  # 用户数据不得被标为合成

    def test_user_upload_missing_filename_fallback(self):
        msg = sidebar_data_status("用户上传数据", None)
        self.assertIn("用户上传数据", msg)
        self.assertIn("未知文件", msg)

    def test_none_label_shows_not_imported(self):
        msg = sidebar_data_status(None, None)
        self.assertIn("尚未导入数据", msg)

    def test_unknown_label_does_not_invent_source(self):
        msg = sidebar_data_status("异常标记", None)
        self.assertIn("异常标记", msg)
        self.assertNotIn("合成", msg)
        self.assertNotIn("用户上传", msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
