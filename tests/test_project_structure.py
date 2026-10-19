"""阶段 0 结构冒烟测试。

验证项目骨架真实存在且源码包可导入。
本测试只使用 Python 标准库 unittest，无需额外安装依赖。

运行方式（在项目根目录执行任意一种）：
    py -m unittest discover -s tests -v
    py tests/test_project_structure.py
"""

import importlib
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 确保无论以哪种方式运行，项目根目录都在导入路径中
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_DIRS = [
    "app",
    "src",
    "src/data",
    "src/analysis",
    "src/visualization",
    "tests",
    "data/raw",
    "data/processed",
    "reports",
    "docs",
]

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    ".env.example",
    "docs/DEVELOPMENT_LOG.md",
    "app/app.py",
]

REQUIRED_PACKAGES = [
    "src",
    "src.data",
    "src.analysis",
    "src.visualization",
]


class TestProjectStructure(unittest.TestCase):
    def test_required_directories_exist(self):
        for rel in REQUIRED_DIRS:
            self.assertTrue(
                (PROJECT_ROOT / rel).is_dir(), f"缺少目录: {rel}"
            )

    def test_required_files_exist(self):
        for rel in REQUIRED_FILES:
            self.assertTrue(
                (PROJECT_ROOT / rel).is_file(), f"缺少文件: {rel}"
            )

    def test_source_packages_importable(self):
        for pkg in REQUIRED_PACKAGES:
            module = importlib.import_module(pkg)
            self.assertIsNotNone(module, f"无法导入包: {pkg}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
