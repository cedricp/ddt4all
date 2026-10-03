# -*- coding: utf-8 -*-
"""
renault_macros.py — ddt4all **master** plugin (>= 3.1)
====================================================

ddt4all plugin running the **DDT2000 macros** (``.txt`` and ``.cmd`` files),
**compatible with the pyren3 macros**, straight from the ddt4all GUI and
**without** reopening the serial port: the engine works on the ELM connection
already open in ddt4all (``ddt4all.options.elm``).

The name is deliberately **neutral**: the ``.cmd`` format comes from DDT2000
(Renault + Dacia), the bundled macros target Renault ECUs, and the engine
imposes no brand — the addressing follows the tables of the vehicle loaded in
ddt4all. A macro is only playable if its ECU exists on that vehicle.

Installation (refactored master layout)::

    <ddt4all>/src/ddt4all/plugins/
        renault_macros.py            <- THIS file (only .py at the root)
        macro_plugin/                <- plugin modules
            macro_ui.py
            macro_engine.py
            macro_adapter.py
            can_addressing.py
            macros/                  <- macro folder (copied by default)

(or: ``python ddt4all/plugin/install.py --target <ddt4all> --layout master``)

``install.py --flat`` puts the modules next to this file instead of the
``macro_plugin/`` sub-folder. ``install.py --no-macros`` installs the code
only.

The macro folder is the copy shipped with the plugin (``<macro_plugin>/macros``),
always present after installation; it stays editable in the GUI to work on
another macro set.
"""

import os
import sys

#: folder of this file (root of the ddt4all "plugins" folder)
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

#: shared modules: either next to this file ("flat" installation), or in the
#: macro_plugin/ sub-folder (default installation)
LIB_DIR = PLUGIN_DIR
for _candidate in (PLUGIN_DIR, os.path.join(PLUGIN_DIR, 'macro_plugin')):
    if os.path.isfile(os.path.join(_candidate, 'macro_ui.py')):
        LIB_DIR = _candidate
        break
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

try:
    from macro_ui import run_dialog
except ImportError as _err:
    raise ImportError(
        "macro_ui not found. Copy macro_engine.py, "
        "macro_adapter.py, can_addressing.py and macro_ui.py "
        "into %s or %s (cause: %s)"
        % (PLUGIN_DIR, os.path.join(PLUGIN_DIR, 'macro_plugin'), _err))

try:
    from macro_adapter import Ddt4allContext
    _CONTEXT = Ddt4allContext()
    _ = (_CONTEXT.options.translator('ddt4all')
         if _CONTEXT.options is not None and hasattr(_CONTEXT.options, 'translator')
         else (lambda text: text))
except ImportError:
    _ = lambda text: text


plugin_name = _("Macros DDT2000 (.cmd)")
# compatible with the pyren3 / DDT2000 macros (mod_term engine)
category = _("Macros")
# an ELM connection is required: ddt4all asks for it before running
need_hw = True


def plugin_entry():
    """Called by ddt4all when the user clicks the plugin."""
    run_dialog(LIB_DIR, title=_("Macros DDT2000 (.cmd)"))
