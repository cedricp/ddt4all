# tests/conftest.py
from pathlib import Path
import pytest
import sys

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(autouse=True)
def force_english_locale():
    """Force English locale for all tests to ensure consistent output.
    
    This fixture automatically applies to all tests and ensures that
    translated strings are always in English, preventing test failures
    when the system is configured with different languages (e.g., French).
    """
    # Import and patch all CLI command handlers that use translation
    try:
        import ddt4all.cli.cmd_handlers.doip as doip_module
        doip_module._ = lambda x: x  # Force English for DoIP tests
    except ImportError:
        pass
    
    # Add more modules here as they start using translation
    # Example:
    # try:
    #     import ddt4all.cli.cmd_handlers.some_module as some_module
    #     some_module._ = lambda x: x
    # except ImportError:
    #     pass


@pytest.fixture
def resources_path():
    return Path(__file__).resolve().parent / "resources"


@pytest.fixture
def dummy_ecu_file(resources_path):
    def _factory(protocol="can", type="json"):
        return resources_path / "chatgpt_generated" / f"dummy_ecu_{protocol}.{type}"
    return _factory