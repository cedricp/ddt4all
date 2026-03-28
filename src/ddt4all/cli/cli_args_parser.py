import argparse

from ddt4all.cli.helpers import (
    ArgumentSpec,
    CommandSpec
)
from ddt4all.cli.cmd_handlers.doip import cmd_doip
from ddt4all.cli.cmd_handlers.parameters import cmd_parameters
from ddt4all.cli.cmd_handlers.usbdevice import cmd_usbdevice


# program sub commands
COMMANDS: list[CommandSpec] = [

    CommandSpec(
        name="doip",
        help="Test DoIP implementation with Electric ECU support",
        handler=cmd_doip,
        arguments=[
        ],
    ),
    CommandSpec(
        name="usbdevice",
        help="",
        handler=cmd_usbdevice,
        arguments=[
        ],
    ),
    CommandSpec(
        name="parameters",
        help="",
        handler=cmd_parameters,
        arguments=[
            ArgumentSpec(
                ("-c", "--convert"),
                {"action": "store_true", "help": "Convert XML to JSON"}
            ),
            ArgumentSpec(
                ("-z", "--zipconvert"),
                {"action": "store_true", "help": "Convert all XML to JSON in a Zip archive"}
            ),
            ArgumentSpec(
                ("-d", "--dumpprojects"),
                {"action": "store_true", "help": "Dump Vehicles"}
            ),
        ],
    ),
]


# Program arguments
ARGUMENTS = [
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    # global arguments
    for arg in ARGUMENTS:
        parser.add_argument(*arg.flags, **arg.kwargs)
    subparsers = parser.add_subparsers(dest="command", required=False)

    # sub commands & arguments
    for cmd in COMMANDS:
        sub = subparsers.add_parser(cmd.name, help=cmd.help)
        for arg in cmd.arguments:
            sub.add_argument(*arg.flags, **arg.kwargs)
        sub.set_defaults(handler=cmd.handler)

    return parser

