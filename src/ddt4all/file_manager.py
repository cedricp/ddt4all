from pathlib import Path

from platformdirs import PlatformDirs

BASE_DIR = Path(__file__).resolve().parent
icons_base_dir = BASE_DIR / "resources" / "icons"

_dirs = PlatformDirs("ddt4all")


def is_run_from_src():
    return (
            BASE_DIR.name == "ddt4all" and
            BASE_DIR.parent.name == "src"
    )


def _legacy_exists():
    return Path("config.json").exists() or Path("json").exists()


def get_dir(dir_name):
    if is_run_from_src():
        path = Path(BASE_DIR / ".." / ".." / dir_name)
    elif _legacy_exists():
        path = Path(dir_name)
    else:
        if dir_name == ".":
            path = Path(_dirs.user_config_dir)
        else:
            path = Path(_dirs.user_data_dir) / dir_name
    return path.resolve()


def get_json_dir():
    return get_dir("json")


def get_logs_dir():
    return get_dir("logs")


def get_vehicles_dir():
    return get_dir("vehicles")


def get_config_dir():
    return get_dir(".")


def get_projects_path():
    user_path = Path(_dirs.user_data_dir) / "projects.json"
    if user_path.exists():
        return user_path
    return BASE_DIR / "resources" / "projects.json"


def is_not_package_file(path):
    return not path.endswith("__init__.py")
