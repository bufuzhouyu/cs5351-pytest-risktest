"""Shared fixtures for the pytest-risktest test suite.

The package is used from ``src/`` directly (no installation required), which is
also how the benchmark harness invokes it.
"""

from __future__ import annotations

import os
import sys

# Child pytest processes must emit UTF-8 even on a GBK console, otherwise
# pytester cannot decode their output when the workspace path contains CJK text.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytest_plugins = ["pytester"]


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_project(root: Path, *, failing: bool = False, extra_lines: int = 0) -> Path:
    """Create a small two-module/two-test project used by several test modules."""
    _write(
        root,
        "app/__init__.py",
        "from . import calc, text\n\n__all__ = ['calc', 'text']\n",
    )
    _write(
        root,
        "app/calc.py",
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "\n"
        "def is_even(value):\n"
        "    return value % 2 == 0\n"
        + "".join(f"\n\ndef filler_{i}():\n    return {i}\n" for i in range(extra_lines)),
    )
    _write(
        root,
        "app/text.py",
        "def shout(text):\n"
        "    return text.upper() + ('!' if text else '')\n"
        + ("\n\ndef broken():\n    return 1 / 0\n" if failing else ""),
    )
    _write(
        root,
        "tests/test_calc.py",
        "from app.calc import add, is_even\n"
        "\n"
        "\n"
        "def test_add():\n"
        "    assert add(1, 2) == 3\n"
        "\n"
        "\n"
        "def test_is_even():\n"
        "    assert is_even(4)\n",
    )
    _write(
        root,
        "tests/test_text.py",
        "from app.text import shout\n"
        "\n"
        "\n"
        "def test_shout():\n"
        "    assert shout('hi') == 'HI!'\n",
    )
    return root

