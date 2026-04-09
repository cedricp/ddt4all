from PyQt5.QtCore import Qt

from ddt4all.ui.main_window.utils import (
    set_theme_style,
    isWritable,
    set_socket_timeout,
)

def test_set_theme_style_does_not_crash(qapp):
    set_theme_style(qapp, Qt.Checked)  # dark
    set_theme_style(qapp, Qt.Unchecked)  # light


class TestIsWritable:
    def test_isWritable_on_writatable_dir(self):
        assert isWritable(".")

    def test_isWritable_on_missing_dir(self):
        assert not isWritable("/missing/directory")

class TestSetSocketTimeout:
    def test_set_stocket_timeout_on(self):
        set_socket_timeout(Qt.Checked)

    def test_set_stocket_timeout_off(self):
        set_socket_timeout(Qt.Unchecked)

