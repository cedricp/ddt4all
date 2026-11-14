"""Initialize writable application data paths for a frozen macOS app."""

import os
from pathlib import Path
import shutil
import sys


if sys.platform == "darwin" and getattr(sys, "frozen", False):
    resources_dir = Path(sys.executable).resolve().parent.parent / "Resources"
    if not resources_dir.is_dir():
        raise RuntimeError("DDT4ALL application Resources directory is missing.")

    from platformdirs import PlatformDirs

    data_dir = Path(PlatformDirs("ddt4all").user_data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    bundled_vehicles = resources_dir / "vehicles"
    user_vehicles = data_dir / "vehicles"
    if bundled_vehicles.is_dir() and not user_vehicles.exists():
        shutil.copytree(str(bundled_vehicles), str(user_vehicles))
    elif bundled_vehicles.is_dir() and user_vehicles.is_dir() and not any(user_vehicles.iterdir()):
        shutil.copytree(
            str(bundled_vehicles),
            str(user_vehicles),
            dirs_exist_ok=True,
        )

    for directory in ("ecus", "graphics", "json"):
        (data_dir / directory).mkdir(exist_ok=True)
    os.chdir(str(data_dir))
