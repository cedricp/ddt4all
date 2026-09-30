"""Tests for the "Clear DDT4ALL History" action (Tools menu).

The action must reset the live widgets (ECU / Screen windows) and not only the
saved configuration, otherwise the windows stay filled until DDT4ALL restarts.
"""

import ddt4all.options as options
import ddt4all.ui.main_window.main_widget as main_widget
from ddt4all.ui.main_window.main_widget import MainWidget

_ = options.translator('ddt4all')


def _fake_main_window(mocker, paramview_opened=True, vehicle_count=2):
    """Build a mock standing in for MainWidget.

    Only the attributes used by clearHistory() and clearHistoryWindows() are
    needed, which allows testing the logic without building the whole GUI.
    """
    window = mocker.MagicMock()
    window.paramview = mocker.MagicMock() if paramview_opened else None
    window.eculistwidget.vehicle_combo.count.return_value = vehicle_count
    return window


class TestClearHistoryWindows:
    def test_empties_ecu_and_screen_windows(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker)

        MainWidget.clearHistoryWindows(window)

        window.treeview_ecu.clear.assert_called_once_with()
        window.treeview_params.clear.assert_called_once_with()
        assert window.ecunamemap == {}
        assert window.screennames == []

    def test_unloads_the_opened_ecu(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker)
        paramview = window.paramview

        MainWidget.clearHistoryWindows(window)

        paramview.tester_timer.stop.assert_called_once_with()
        paramview.setParent.assert_called_once_with(None)
        paramview.close.assert_called_once_with()
        paramview.destroy.assert_called_once_with()
        assert window.paramview is None
        window.scrollview.setWidget.assert_called_once_with(
            main_widget.widgets.QWidget.return_value)

    def test_works_without_any_opened_ecu(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker, paramview_opened=False)

        MainWidget.clearHistoryWindows(window)  # must not raise

        assert window.paramview is None
        window.treeview_ecu.clear.assert_called_once_with()
        window.treeview_params.clear.assert_called_once_with()

    def test_disables_the_actions_that_need_an_ecu(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker)

        MainWidget.clearHistoryWindows(window)

        window.diagaction.setEnabled.assert_called_once_with(False)
        window.hexinput.setEnabled.assert_called_once_with(False)
        window.cominput.setEnabled.assert_called_once_with(False)
        window.sdscombo.setEnabled.assert_called_once_with(False)
        window.expert.setChecked.assert_called_once_with(False)
        assert options.promode is False
        assert options.auto_refresh is False

    def test_resets_the_vehicle_filter(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker)

        MainWidget.clearHistoryWindows(window)

        window.eculistwidget.vehicle_combo.setCurrentIndex.assert_called_once_with(0)
        window.eculistwidget.filterProject.assert_called_once_with()

    def test_keeps_the_vehicle_filter_when_list_is_empty(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker, vehicle_count=0)

        MainWidget.clearHistoryWindows(window)

        window.eculistwidget.vehicle_combo.setCurrentIndex.assert_not_called()
        window.eculistwidget.filterProject.assert_not_called()


class TestClearHistory:
    def test_resets_windows_before_clearing_saved_history(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker)
        calls = []
        window.clearHistoryWindows.side_effect = lambda: calls.append("windows")
        mocker.patch.object(main_widget.options, "clear_history",
                            side_effect=lambda: calls.append("config"))

        MainWidget.clearHistory(window)

        # The widgets may save the history again, so it must be cleared last
        assert calls == ["windows", "config"]

    def test_informs_the_user(self, mocker):
        mocker.patch.object(main_widget, "widgets")
        window = _fake_main_window(mocker)
        mocker.patch.object(main_widget.options, "clear_history")

        MainWidget.clearHistory(window)

        msgbox = main_widget.widgets.QMessageBox.return_value
        msgbox.setWindowTitle.assert_called_once_with(_("History cleared"))
        msgbox.setText.assert_called_once_with(
            _("Last selected vehicle and ECU history has been cleared."))
        msgbox.exec_.assert_called_once_with()
