"""Thin entry point at repo root — delegates to app/app.py.

Streamlit Cloud defaults to running the root app.py. This wrapper preserves
that convention while keeping all real code in app/app.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.app import main

if __name__ == "__main__":
    main()
