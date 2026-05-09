import codecs
import json
import os
from pathlib import Path
import sys

import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

from ddt4all.cli.cli_args_parser import build_parser
import ddt4all.core.ecu.ecu_database as ecu_db
import ddt4all.core.elm.elm as elm
from ddt4all.file_manager import (
    get_config_dir,
    get_json_dir,
    get_logs_dir,
)
import ddt4all.generated.resources_rc  # noqa: F401
import ddt4all.options as options
from ddt4all.ui.main_window.main_widget import MainWidget
from ddt4all.ui.main_window.main_window_options import MainWindowOptions
from ddt4all.ui.main_window.utils import (
    set_socket_timeout,
    set_theme_style
)
import ddt4all.version as version

_ = options.translator('ddt4all')

# Optional WebEngine import for enhanced features
try:
    import PyQt5.QtWebEngineWidgets as webkitwidgets
    HAS_WEBENGINE = True
except ImportError:
    print(_("Warning: PyQtWebEngine not available. Some features may be limited."))
    webkitwidgets = None
    HAS_WEBENGINE = False

BASE_DIR = Path(__file__).resolve().parent
icons_base_dir = BASE_DIR / "resources" / "icons"

# remove Warning: Ignoring XDG_SESSION_TYPE=wayland on Gnome. Use QT_QPA_PLATFORM=wayland to run on Wayland anyway 
if sys.platform[:3] == "lin":
    os.environ["XDG_SESSION_TYPE"] = "xcb"


def load_this():
    try:
        with open(BASE_DIR / "resources" / "projects.json", "r", encoding="UTF-8") as f:
            vehicles_loc = json.loads(f.read())
        ecu_db.addressing = vehicles_loc["projects"]["All"]["addressing"]
        ecu_db.doip_addressing = vehicles_loc["projects"]["All"]["DoIP"]
        elm.snat = vehicles_loc["projects"]["All"]["snat"]
        elm.snat_ext = vehicles_loc["projects"]["All"]["snat_ext"]
        elm.dnat = vehicles_loc["projects"]["All"]["dnat"]
        elm.dnat_ext = vehicles_loc["projects"]["All"]["dnat_ext"]
        return vehicles_loc
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(_("resources/projects.json not found or invalid.") + f" Error: {e}")
        exit(-1) # TODO raise ?


def main(argv=None) -> int:

    parser = build_parser()
    args = parser.parse_args()

    # If subcommand : run then exit
    if hasattr(args, "handler"):
        result = args.handler(args)
        # Potential return code propagation
        raise SystemExit(result if isinstance(result, int) else 0)

    # For InnoSetup version.h auto generator
    if os.path.isdir('setup_tools/inno-win-setup'):
        try:
            with open("setup_tools/inno-win-setup/version.h", "w", encoding="UTF-8") as f:
                f.write(f'#define __appname__ "{version.__appname__}"\n')
                f.write(f'#define __author__ "{version.__author__}"\n')
                f.write(f'#define __copyright__ "{version.__copyright__}"\n')
                f.write(f'#define __version__ "{version.__version__}"\n')
                f.write(f'#define __email__ "{version.__email__}"\n')
                f.write(f'#define __status__ "{version.__status__}"')
        except (OSError, IOError) as e:
            print(f"Warning: Could not write version.h: {e}")

    try:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
    except (OSError, ValueError):
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)


    vehicles = load_this()

    options.simulation_mode = True
    options.socket_timeout = False

    app = widgets.QApplication(sys.argv)

    try:
        with open(get_config_dir() / "config.json", "r", encoding="UTF-8") as f:
            configuration = json.loads(f.read())
        set_theme_style(app, 2 if configuration.get("dark") else 0)
        set_socket_timeout(1 if configuration.get("socket_timeout") else 0)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        set_theme_style(app, 0)

    app.setStyle("plastic")

    if os.path.exists(options.ecus_dir + '/eculist.xml'):
        print(_("Using custom DDT database"))

    if not os.path.exists(get_json_dir()):
        os.mkdir(get_json_dir())
    if not os.path.exists(get_logs_dir()):
        os.mkdir(get_logs_dir())

    pc = MainWindowOptions(app)
    nok = True
    while nok:
        pcres = pc.exec_()

        if pc.mode == 0 or pcres == widgets.QDialog.Rejected:
            return 0

        if pc.mode == 1:
            options.promode = False
            options.simulation_mode = False
        if pc.mode == 2:
            options.promode = False
            options.simulation_mode = True
            break

        options.port = str(pc.port)
        port_speed = pc.selectedportspeed

        if not options.port:
            msgbox = widgets.QMessageBox()
            msgbox.setWindowIcon(gui.QIcon(":icons/obd.png"))
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setText(_("No COM port selected"))
            msgbox.exec_()

        print(_("Initializing ELM with speed %i...") % port_speed)
        options.elm = elm.ELM(options.port, port_speed, pc.adapter, pc.raise_port_speed)

        if options.elm_failed:
            pc.show()
            pc.logview.append(options.get_last_error())
            msgbox = widgets.QMessageBox()
            msgbox.setWindowIcon(gui.QIcon(":icons/obd.png"))
            msgbox.setWindowTitle(version.__appname__)
            msgbox.setText(_("No ELM327 or OBDLINK-SX detected on COM port ") + options.port)
            msgbox.exec_()
        else:
            nok = False
            # Initialize device with enhanced features (STPX, pin swapping, etc.)
            if options.elm and options.elm.connectionStatus:
                print(_("Initializing device features..."))
                elm.DeviceManager.initialize_device(options.elm)
                # Mark as initialized to avoid re-initialization during scan
                options.elm._device_initialized = True

    w = MainWidget(app, vehicles)
    options.main_window = w
    w.show()
    app.exec_()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())