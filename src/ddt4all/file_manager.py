from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
icons_base_dir = BASE_DIR / "resources" / "icons"

def is_run_from_src():
    return (
        BASE_DIR.name == "ddt4all" and
        BASE_DIR.parent.name == "src"
    )

def get_dir(dir_name):

    if is_run_from_src():

        return BASE_DIR / ".." / ".." / dir_name

    else:
        return dir_name

def get_json_dir():
    return get_dir("json")

def get_logs_dir():
    return get_dir("logs")

def get_vehicles_dir():
    return get_dir("vehicles")

def get_config_dir():
    return get_dir(".")