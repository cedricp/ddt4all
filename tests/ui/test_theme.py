from PyQt5.QtCore import Qt

from ddt4all.ui.main_window.utils import set_theme_style

def test_set_theme_style_does_not_crash(qapp):
    set_theme_style(qapp, Qt.Checked)  # dark
    set_theme_style(qapp, Qt.Unchecked)  # light