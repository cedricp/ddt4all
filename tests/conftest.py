# tests/conftest.py
from pathlib import Path
import pytest


@pytest.fixture
def resources_path():
    return Path(__file__).resolve().parent / "resources"