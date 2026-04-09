import pytest

from ddt4all.cli.cli_args_parser import build_parser
from ddt4all.cli.cmd_handlers.doip import cmd_doip
from ddt4all.cli.cmd_handlers.parameters import cmd_parameters
from ddt4all.cli.cmd_handlers.usbdevice import cmd_usbdevice


def test_parse_without_subcommand():
    parser = build_parser()

    args = parser.parse_args([])

    assert args.command is None
    assert not hasattr(args, "handler")


def test_parse_doip_command_sets_expected_handler():
    parser = build_parser()

    args = parser.parse_args(["doip"])

    assert args.command == "doip"
    assert args.handler is cmd_doip


def test_parse_usbdevice_command_sets_expected_handler():
    parser = build_parser()

    args = parser.parse_args(["usbdevice"])

    assert args.command == "usbdevice"
    assert args.handler is cmd_usbdevice


def test_parse_parameters_command_sets_expected_handler():
    parser = build_parser()

    args = parser.parse_args(["parameters"])

    assert args.command == "parameters"
    assert args.handler is cmd_parameters
    assert args.zipconvert is False
    assert args.dumpprojects is False


def test_parse_parameters_command_with_zipconvert_option():
    parser = build_parser()

    args = parser.parse_args(["parameters", "--zipconvert"])

    assert args.command == "parameters"
    assert args.handler is cmd_parameters
    assert args.zipconvert is True
    assert args.dumpprojects is False


def test_parse_parameters_command_with_dumpprojects_option():
    parser = build_parser()

    args = parser.parse_args(["parameters", "--dumpprojects"])

    assert args.command == "parameters"
    assert args.handler is cmd_parameters
    assert args.zipconvert is False
    assert args.dumpprojects is True


def test_parse_parameters_command_with_both_options():
    parser = build_parser()

    args = parser.parse_args(["parameters", "--zipconvert", "--dumpprojects"])

    assert args.command == "parameters"
    assert args.handler is cmd_parameters
    assert args.zipconvert is True
    assert args.dumpprojects is True


def test_unknown_subcommand_exits_with_error():
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["unknown-command"])

    assert exc_info.value.code == 2