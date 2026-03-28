import argparse

from ddt4all.cli.cmd_handlers.doip import cmd_doip


def test_cmd_doip_success_flow(mocker, capsys):
    mock_doip_device_class = mocker.patch(
        "ddt4all.cli.cmd_handlers.doip.DoIPDevice"
    )
    mock_doip_device = mock_doip_device_class.return_value

    mock_doip_device.connect.return_value = True
    mock_doip_device.init_can.return_value = True
    mock_doip_device.request.return_value = "62 F1 90 56 49 4E"

    result = cmd_doip(argparse.Namespace())
    captured = capsys.readouterr()

    assert result is None

    mock_doip_device.connect.assert_called_once()
    mock_doip_device.init_can.assert_called_once()
    mock_doip_device.disconnect.assert_called_once()

    assert mock_doip_device.set_can_addr.call_count == 7
    assert mock_doip_device.request.call_count == 8

    mock_doip_device.request.assert_called_with("22 F1 90")

    assert "DoIP device connected successfully" in captured.out
    assert "DoIP CAN initialized with Electric ECU support" in captured.out
    assert "Testing Electric ECU: EVC" in captured.out
    assert "Testing Electric ECU: GWM" in captured.out
    assert "DoIP response:" in captured.out


def test_cmd_doip_connect_failure(mocker, capsys):
    mock_doip_device_class = mocker.patch(
        "ddt4all.cli.cmd_handlers.doip.DoIPDevice"
    )
    mock_doip_device = mock_doip_device_class.return_value

    mock_doip_device.connect.return_value = False

    result = cmd_doip(argparse.Namespace())
    captured = capsys.readouterr()

    assert result is None

    mock_doip_device.connect.assert_called_once()
    mock_doip_device.init_can.assert_not_called()
    mock_doip_device.request.assert_not_called()
    mock_doip_device.set_can_addr.assert_not_called()
    mock_doip_device.disconnect.assert_not_called()

    assert "Failed to connect to DoIP device" in captured.out


def test_cmd_doip_first_request_failure_does_not_stop_ecu_loop(mocker, capsys):
    mock_doip_device_class = mocker.patch(
        "ddt4all.cli.cmd_handlers.doip.DoIPDevice"
    )
    mock_doip_device = mock_doip_device_class.return_value

    mock_doip_device.connect.return_value = True
    mock_doip_device.init_can.return_value = True
    mock_doip_device.request.side_effect = [
        RuntimeError("boom"),
        "62 F1 90 56 49 4E",
        "62 F1 90 56 49 4E",
        "62 F1 90 56 49 4E",
        "62 F1 90 56 49 4E",
        "62 F1 90 56 49 4E",
        "62 F1 90 56 49 4E",
        "62 F1 90 56 49 4E",
    ]

    result = cmd_doip(argparse.Namespace())
    captured = capsys.readouterr()

    assert result is None

    mock_doip_device.connect.assert_called_once()
    mock_doip_device.init_can.assert_called_once()
    mock_doip_device.disconnect.assert_called_once()

    assert mock_doip_device.set_can_addr.call_count == 7
    assert mock_doip_device.request.call_count == 8

    assert "DoIP request failed: boom" in captured.out
    assert "Testing Electric ECU: EVC" in captured.out
    assert "Testing Electric ECU: GWM" in captured.out