# -*- coding: utf-8 -*-
"""
cmd_macros.py — ddt4all **master** plugin (>= 3.1)
====================================================

Runs the **DDT2000 macros** (``.txt`` and ``.cmd`` files, format **compatible
with the pyren3 macros**) from the ddt4all GUI, on the ELM connection ddt4all
already has open — no serial port is reopened.

The name is deliberately **neutral**: the ``.cmd`` format comes from DDT2000
(Renault + Dacia), the bundled macros target Renault ECUs, and the engine
imposes no brand — the addressing follows the tables of the vehicle loaded in
ddt4all. A macro is only playable if its ECU exists on that vehicle.
"""

import os
import sys

#: folder of this file (root of the ddt4all "plugins" folder)
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

#: shared modules: either next to this file ("flat" installation), or in the
#: cmd_macros_lib/ sub-folder (default installation)
LIB_DIR = PLUGIN_DIR
for _candidate in (PLUGIN_DIR, os.path.join(PLUGIN_DIR, 'cmd_macros_lib')):
    if os.path.isfile(os.path.join(_candidate, 'cmd_ui.py')):
        LIB_DIR = _candidate
        break
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

try:
    from cmd_ui import run_dialog
except ImportError as _err:
    raise ImportError(
        "cmd_ui not found. Copy cmd_engine.py, "
        "ddt4all_adapter.py, can_addressing.py, elm_log.py and "
        "cmd_ui.py into %s or %s (cause: %s)"
        % (PLUGIN_DIR, os.path.join(PLUGIN_DIR, 'cmd_macros_lib'), _err))

try:
    from ddt4all_adapter import Ddt4allContext
    _CONTEXT = Ddt4allContext()
    _ = (_CONTEXT.options.translator('ddt4all')
         if _CONTEXT.options is not None and hasattr(_CONTEXT.options, 'translator')
         else (lambda text: text))
except ImportError:
    _ = lambda text: text


plugin_name = _("DDT2000 command macros (.cmd)")
category = _("Macros")
# an ELM connection is required: ddt4all asks for it before running
need_hw = True


def plugin_entry():
    """Called by ddt4all when the user clicks the plugin."""
    run_dialog(LIB_DIR, title=_("DDT2000 command macros (.cmd)"))
