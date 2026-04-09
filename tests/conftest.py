# tests/conftest.py
from pathlib import Path
import pytest


@pytest.fixture
def resources_path():
    return Path(__file__).resolve().parent / "resources"


@pytest.fixture
def dummy_ecu_file(resources_path):
    def _factory(protocol="can", type="json"):
        return resources_path / "chatgpt_generated" / f"dummy_ecu_{protocol}.{type}"
    return _factory