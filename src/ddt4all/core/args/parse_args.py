from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Callable, Any

VERSION = "1.0.0"


# ---------- Handlers ----------

def cmd_add(args: argparse.Namespace) -> int:
    result = args.a + args.b
    if args.verbose:
        print(f"[DEBUG] a={args.a}, b={args.b}")
    print(f"Résultat: {result}")
    return 0


def cmd_echo(args: argparse.Namespace) -> int:
    text = args.text
    if args.upper:
        text = text.upper()
    print(text)
    return 0


def cmd_rm(args: argparse.Namespace) -> int:
    print(f"Suppression de: {args.path} (force={args.force})")
    return 0


def cmd_doip(args: argparse.Namespace) -> int:
    print(f"Suppression de: {args.path} (force={args.force})")
    return 0

# ---------- Description factorisée ----------

@dataclass
class ArgumentSpec:
    flags: tuple[str, ...]
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandSpec:
    name: str
    help: str
    handler: Callable[[argparse.Namespace], int]
    arguments: list[ArgumentSpec] = field(default_factory=list)


COMMANDS: list[CommandSpec] = [
    CommandSpec(
        name="add",
        help="Additionne deux entiers",
        handler=cmd_add,
        arguments=[
            ArgumentSpec(("a",), {"type": int, "help": "Premier entier"}),
            ArgumentSpec(("b",), {"type": int, "help": "Deuxième entier"}),
        ],
    ),
    CommandSpec(
        name="echo",
        help="Affiche du texte",
        handler=cmd_echo,
        arguments=[
            ArgumentSpec(("text",), {"help": "Texte à afficher"}),
            ArgumentSpec(("--upper",), {"action": "store_true", "help": "Met en majuscules"}),
        ],
    ),
    CommandSpec(
        name="rm",
        help="Supprime une ressource",
        handler=cmd_rm,
        arguments=[
            ArgumentSpec(("path",), {"help": "Chemin à supprimer"}),
            ArgumentSpec(("-f", "--force"), {"action": "store_true", "help": "Force la suppression"}),
        ],
    ),
]


# Program arguments
ARGUMENTS = [
    ArgumentSpec(("path",), {"help": "Chemin à supprimer"}),
]

# ---------- Construction du parser ----------

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser()

    # options globales
    parser.add_argument(
        '-z', '--zipconvert',
        action="store_true",
        default=None,
        help="Convert all XML to JSON in a Zip archive"
    )
    parser.add_argument(
        '-d', '--dumpprojects',
        action="store_true",
        default=None,
        help="Dump Vehicles"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
class ArgsParser():

    parser = argparse.ArgumentParser()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', 
        '--convert', 
        action="store_true", 
        default=None, 
        help="Convert all XML to JSON"
    )
    parser.add_argument('-z', '--zipconvert', action="store_true", default=None, help="Convert all XML to JSON in a Zip archive")
    parser.add_argument('-d', '--dumpprojects', action="store_true", default=None, help="Dump Vehicles")
    args = parser.parse_args()

    if args.zipconvert:
        zipConvertXML()

    if args.convert:
        convertXML()

    if args.dumpprojects:
        dumpVehicles()