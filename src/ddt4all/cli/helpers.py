from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Callable, Any

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
