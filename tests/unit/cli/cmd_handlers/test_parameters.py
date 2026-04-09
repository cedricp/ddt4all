import argparse

from ddt4all.cli.cmd_handlers.parameters import cmd_parameters


def test_cmd_parameters_no_flags_calls_nothing(mocker):
    mock_zip = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.zipConvertXML"
    )
    mock_convert = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.convertXML"
    )
    mock_dump = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.dumpVehicles"
    )

    args = argparse.Namespace(
        zipconvert=False,
        convert=False,
        dumpprojects=False,
    )

    result = cmd_parameters(args)

    assert result is None

    mock_zip.assert_not_called()
    mock_convert.assert_not_called()
    mock_dump.assert_not_called()


def test_cmd_parameters_zipconvert_only(mocker):
    mock_zip = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.zipConvertXML"
    )
    mock_convert = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.convertXML"
    )
    mock_dump = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.dumpVehicles"
    )

    args = argparse.Namespace(
        zipconvert=True,
        convert=False,
        dumpprojects=False,
    )

    cmd_parameters(args)

    mock_zip.assert_called_once_with()
    mock_convert.assert_not_called()
    mock_dump.assert_not_called()


def test_cmd_parameters_convert_only(mocker):
    mock_zip = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.zipConvertXML"
    )
    mock_convert = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.convertXML"
    )
    mock_dump = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.dumpVehicles"
    )

    args = argparse.Namespace(
        zipconvert=False,
        convert=True,
        dumpprojects=False,
    )

    cmd_parameters(args)

    mock_zip.assert_not_called()
    mock_convert.assert_called_once_with()
    mock_dump.assert_not_called()


def test_cmd_parameters_dumpprojects_only(mocker):
    mock_zip = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.zipConvertXML"
    )
    mock_convert = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.convertXML"
    )
    mock_dump = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.dumpVehicles"
    )

    args = argparse.Namespace(
        zipconvert=False,
        convert=False,
        dumpprojects=True,
    )

    cmd_parameters(args)

    mock_zip.assert_not_called()
    mock_convert.assert_not_called()
    mock_dump.assert_called_once_with()


def test_cmd_parameters_all_flags(mocker):
    mock_zip = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.zipConvertXML"
    )
    mock_convert = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.convertXML"
    )
    mock_dump = mocker.patch(
        "ddt4all.cli.cmd_handlers.parameters.dumpVehicles"
    )

    args = argparse.Namespace(
        zipconvert=True,
        convert=True,
        dumpprojects=True,
    )

    cmd_parameters(args)

    mock_zip.assert_called_once_with()
    mock_convert.assert_called_once_with()
    mock_dump.assert_called_once_with()