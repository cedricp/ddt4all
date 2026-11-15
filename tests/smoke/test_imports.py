from importlib import import_module


def test_import_package():
    import ddt4all

def test_import_main():
    import ddt4all.main

def test_import_core():
    import ddt4all.core

def test_import_ui():
    import ddt4all.ui


def test_import_plugins():
    from ddt4all.plugins import PLUGIN_MODULES

    for module_name in PLUGIN_MODULES:
        plugin = import_module("ddt4all.plugins." + module_name)
        assert callable(plugin.plugin_entry)
        assert plugin.plugin_name
        assert plugin.category
