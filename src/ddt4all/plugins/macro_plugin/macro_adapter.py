#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macro_adapter.py
=================
Adaptation layer between the macro engine (:mod:`macro_engine`) and
**ddt4all**.

It automatically detects the installed ddt4all variant:

* **master** (>= 3.1): ``ddt4all`` package, ``ddt4all.options``,
  ``ddt4all.core.elm.elm`` ;
* **legacy** (2.x / 3.0.x): flat modules ``options``, ``elm``, ``ecu`` ;
* **none**: the module stays usable (tests, console).

It then builds the objects the engine expects:

* ``elm``       : ``options.elm`` (connection **already open** by ddt4all) ;
* ``globals_``  : ``mod_globals`` shim (``opt_demo``, ``opt_rate`` ...) ;
* ``addresses`` : :class:`AddressBook` (embedded tables + ddt4all tables) ;
* ``log``       : callback wired to the ddt4all log.
"""

import os
import sys

try:
    from macro_engine import AddressBook, MacroEngine
except ImportError:  # package imported without the folder in sys.path
    from ddt4all.plugins.macro_engine import AddressBook, MacroEngine


OPTIONS_CANDIDATES = ('ddt4all.options', 'options')
ELM_CANDIDATES = ('ddt4all.core.elm.elm', 'elm')


def _import_first(names, required_attr):
    """Imports the first module of ``names`` owning ``required_attr``."""
    for name in names:
        try:
            __import__(name)
        except ImportError:
            continue
        module = sys.modules.get(name)
        if module is not None and hasattr(module, required_attr):
            return module
    return None


class ModGlobalsShim(object):
    """``pyren3.mod_globals`` shim built from ``ddt4all.options``.

    It is not used by the ddt4all ELM (which reads its own options), but the
    engine needs it to know the simulation mode and for the ``wait`` command.
    """

    def __init__(self, options=None):
        self.os = os.name
        self.opt_demo = bool(getattr(options, 'simulation_mode', False))
        self.opt_rate = getattr(options, 'port_speed', 38400)
        self.opt_speed = self.opt_rate
        self.opt_obdlink = False
        self.opt_caf = bool(getattr(options, 'opt_caf', False))
        self.opt_can2 = bool(getattr(options, 'opt_can2', False))
        self.opt_cfc0 = bool(getattr(options, 'opt_cfc0', False))
        self.opt_n1c = bool(getattr(options, 'opt_n1c', True))
        self.opt_stn = bool(getattr(options, 'opt_stn_basic', False)
                            or getattr(options, 'opt_stpx_full', False))
        self.opt_port = getattr(options, 'port_name', '')
        self.opt_log = ''

    def __repr__(self):
        return '<ModGlobalsShim demo=%s rate=%s>' % (self.opt_demo, self.opt_rate)


class Ddt4allContext(object):
    """Detection + access to the host application (ddt4all or bare env)."""

    def __init__(self, options_module=None, elm_module=None):
        self.options = options_module or _import_first(OPTIONS_CANDIDATES, 'elm')
        self.elm_module = elm_module or _import_first(ELM_CANDIDATES, 'ELM')
        self._mod_globals = None

    # ------------------------------------------------------------------ #
    #  detection                                                          #
    # ------------------------------------------------------------------ #
    @property
    def flavor(self):
        """``'master'``, ``'legacy'`` or ``'none'``."""
        if self.options is None:
            return 'none'
        return 'master' if self.options.__name__.startswith('ddt4all') \
            else 'legacy'

    def is_available(self):
        return self.options is not None

    # ------------------------------------------------------------------ #
    #  application access                                                 #
    # ------------------------------------------------------------------ #
    @property
    def elm(self):
        return getattr(self.options, 'elm', None) if self.options else None

    def set_elm(self, elm):
        if self.options is not None:
            self.options.elm = elm

    @property
    def simulation(self):
        return bool(getattr(self.options, 'simulation_mode', False)) \
            if self.options else False

    @property
    def main_window(self):
        return getattr(self.options, 'main_window', None) if self.options else None

    @property
    def mod_globals(self):
        if self._mod_globals is None:
            self._mod_globals = ModGlobalsShim(self.options)
        return self._mod_globals

    def log(self, msg):
        """Logs into ddt4all when possible, otherwise to the console."""
        window = self.main_window
        view = getattr(window, 'logview', None) if window is not None else None
        if view is not None:
            try:
                view.append(str(msg))
                return
            except Exception:
                pass
        print(msg)

    # ------------------------------------------------------------------ #
    #  engine construction                                                #
    # ------------------------------------------------------------------ #
    def address_book(self):
        """Embedded tables + tables of the ddt4all ``elm`` module (if not empty)."""
        return AddressBook.from_elm_module(self.elm_module)

    def make_engine(self, elm=None, log=None, addresses=None, **kwargs):
        """Creates a :class:`MacroEngine` ready to play the macros."""
        kwargs.setdefault('globals_', self.mod_globals)
        return MacroEngine(elm if elm is not None else self.elm,
                           log=log if log is not None else self.log,
                           addresses=addresses or self.address_book(),
                           **kwargs)


#: Readable label of each possible origin. The **translatable** wording lives
#: in ``macro_ui.MACRO_DIR_LABELS`` (only literals can be extracted by gettext);
#: this mapping is the plain English fallback for non-GUI callers.
MACRO_DIR_ORIGINS = {
    'installed': 'installed copy (macro_plugin/macros)',
    'custom': 'manually chosen folder',
}

#: name of the macro sub-folder installed next to the shared modules
MACRO_SUBDIR = 'macros'


def installed_macro_dir(plugin_dir):
    """Macro folder shipped with the plugin: ``(path, origin)``.

    The macros live in ``<plugin>/macro_plugin/macros``, so they are part of
    the plugin: no lookup in a pyren checkout and no environment variable is
    needed, which makes the installation self-contained and deterministic.
    """
    path = os.path.join(os.path.abspath(plugin_dir), MACRO_SUBDIR)
    return (path, 'installed') if os.path.isdir(path) else (None, None)


def macro_dir_origin(folder, plugin_dir):
    """Origin of a macro folder: installed or manually chosen."""
    if folder and os.path.abspath(folder) == \
            os.path.abspath(os.path.join(plugin_dir, MACRO_SUBDIR)):
        return 'installed'
    return 'custom' if folder else None


def describe_macro_dir(origin):
    """Readable label of the origin of a macro folder."""
    return MACRO_DIR_ORIGINS.get(origin, origin or 'unknown')


def scan_macro_dir(folder):
    """Recursively lists the content of a macro folder.

    :returns: ``(cmd_files, txt_files)`` sorted (absolute paths).
    """
    cmds, txts = [], []
    if not folder or not os.path.isdir(folder):
        return cmds, txts
    for root, _dirs, files in os.walk(folder):
        for name in sorted(files):
            path = os.path.join(root, name)
            low = name.lower()
            if low.endswith('.cmd'):
                cmds.append(path)
            elif low.endswith('.txt'):
                txts.append(path)
    return sorted(cmds), sorted(txts)
