import pytest
from pathlib import Path


def test_import_placeholder():
    from src.cli.state import AppState
    assert AppState is not None


def test_display_imports():
    from src.cli.display import header, table, pick, prompt, separator
    assert callable(header)
    assert callable(table)
    assert callable(pick)
