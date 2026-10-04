#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
elm_log.py
==========

Journal ELM of the plugin — **the ddt4all one**, not a re-implementation.

ddt4all already records the traffic of its ELM in two files
(``src/ddt4all/core/elm/elm.py``, ``ELM.__init__``)::

    Path(get_logs_dir()).mkdir(parents=True, exist_ok=True)

    if len(options.log) > 0:
        self.lf = open(os.path.join(get_logs_dir(), "elm_" + options.log + ".txt"), "at", encoding="utf-8")
        self.vf = open(os.path.join(get_logs_dir(), "ecu_" + options.log + ".txt"), "at", encoding="utf-8")
        self.vf.write("# TimeStamp;Address;Command;Response;Error\\n")

With the default ``options.log`` (``"ddt"``) the files are
``<logs>/elm_ddt.txt`` and ``<logs>/ecu_ddt.txt``.

Every ``if self.lf != 0`` / ``if self.vf != 0`` of ddt4all then records the
traffic itself — in ``send_raw``, ``cmd``, ``request``, ``set_can_addr``,
``init_can``, ``init_iso``... — so **everything** is logged, the frames of the
macro *and* the AT commands ddt4all issues on its own, in the format and in the
folder of the application.

This module only (re)opens those two handles for the duration of a macro run:

* ddt4all opens them once, when the connection is created — a macro played
  later, or a connection opened with an empty ``options.log``, leaves them
  closed (``lf``/``vf`` stay ``0``);
* :meth:`ElmLog.close` restores the previous state, so the plugin never leaves
  ddt4all writing files behind its back.

Usage (outside ddt4all, e.g. a test without vehicle and without ddt4all: the
folder and the name are then passed explicitly)::

    from elm_log import ElmLog

    with ElmLog(elm, 'ddt', folder) as log:
        print(log.elm_path, log.ecu_path)

Nothing here ever breaks a macro: a log that cannot be opened degrades to a
no-op (:attr:`ElmLog.error` tells why).
"""

import os

#: Base name used when ``options.log`` is empty (same default as ddt4all's
#: ``options.py``: ``log = "ddt"``).
DEFAULT_LOG_NAME = 'ddt'

#: Header ddt4all writes at the top of the request-level file.
ECU_HEADER = '# TimeStamp;Address;Command;Response;Error\n'
def _ddt4all_options(options_module=None):
    """The ``options`` module of ddt4all (None outside ddt4all)."""
    if options_module is not None:
        return options_module
    try:                                       # ddt4all master (>= 3.1)
        import ddt4all.options as module
    except ImportError:                        # ddt4all legacy (2.x / 3.0.x)
        try:
            import options as module           # noqa: F401
        except ImportError:
            return None
    return module


def default_log_name(options_module=None):
    """``options.log`` of ddt4all, or :data:`DEFAULT_LOG_NAME`.

    The name is used **as ddt4all uses it**: the plugin adds no extension
    either (``options.log`` is ``"ddt"``, not ``"ddt.txt"``).
    """
    module = _ddt4all_options(options_module)
    return safe_name(getattr(module, 'log', None))


def logs_folder(options_module=None):
    """ddt4all ``get_logs_dir()``, or ``<ddt4all>/logs`` outside ddt4all."""
    try:
        try:                                   # ddt4all master (>= 3.1)
            from ddt4all.file_manager import get_logs_dir
        except ImportError:                    # ddt4all legacy
            from file_manager import get_logs_dir
        return os.fspath(get_logs_dir())
    except Exception:
        # outside ddt4all (console, tests): keep the files next to the plugin
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


#: characters that cannot appear in a file name (Windows rules, stricter)
_FORBIDDEN = ('/', '\\', ':', '*', '?', '"', '<', '>', '|')


def safe_name(name=DEFAULT_LOG_NAME):
    """Base name usable as a file name.

    What the user types is never trusted as a path: the separators become
    ``_`` and a leading dot is removed, so the files always land in the logs
    folder (``..`` cannot escape it).
    """
    text = str(name or '').strip()
    for char in _FORBIDDEN:
        text = text.replace(char, '_')
    return text.strip('. ') or DEFAULT_LOG_NAME
class ElmLog(object):
    """Turns the ddt4all ELM journal on for the duration of a macro.

    :param elm:    the live ELM (``ddt4all.options.elm``).
    :param name:   base name of the files (default: ``options.log``).
    :param folder: destination (default: ddt4all ``get_logs_dir()``).

    :attr:`elm_path` / :attr:`ecu_path` are the two files really written; they
    can be shown to the user as soon as the object is built.
    """

    def __init__(self, elm, name=None, folder=None, options_module=None):
        self.elm = elm
        self.name = safe_name(name if name is not None
                              else default_log_name(options_module))
        self.folder = os.path.abspath(
            folder if folder is not None else logs_folder(options_module))
        self.elm_path = os.path.join(self.folder, 'elm_%s.txt' % self.name)
        self.ecu_path = os.path.join(self.folder, 'ecu_%s.txt' % self.name)
        self.error = None
        self._lf = None
        self._vf = None
        self._previous = None
        self._owned = True
        self._open()

    # ------------------------------------------------------------------ #
    #  open / close                                                        #
    # ------------------------------------------------------------------ #
    def _open(self):
        """Opens the two files and hands them to the ELM (``elm.lf``/``vf``).

        Exactly what ``ELM.__init__`` does, same names, same header: ddt4all
        then writes the traffic by itself, no interception involved.

        When ddt4all already writes **these** files (the connection was opened
        with the same ``options.log``), its handles are reused as they are: no
        second handle on the same file, and no second header.
        """
        if self.elm is None:
            self.error = 'no ELM connection'
            return
        if self._reuse_existing():
            return
        try:
            os.makedirs(self.folder, exist_ok=True)
            self._lf = open(self.elm_path, 'at', encoding='utf-8')
            self._vf = open(self.ecu_path, 'at', encoding='utf-8')
            self._vf.write(ECU_HEADER)
            self._vf.flush()
        except OSError as err:
            # never break a macro because of the journal
            self.error = str(err)
            self._close_files()
            return
        # remember the state of ddt4all, to restore it on close
        self._previous = (getattr(self.elm, 'lf', 0),
                          getattr(self.elm, 'vf', 0))
        self.elm.lf = self._lf
        self.elm.vf = self._vf

    def _reuse_existing(self):
        """True when ddt4all already writes exactly these two files."""
        for attr, path in (('lf', self.elm_path), ('vf', self.ecu_path)):
            handle = getattr(self.elm, attr, 0)
            if not getattr(handle, 'name', None):
                return False
            if os.path.abspath(handle.name) != os.path.abspath(path):
                return False
        self._owned = False
        self._lf = getattr(self.elm, 'lf', 0)
        self._vf = getattr(self.elm, 'vf', 0)
        return True

    def _close_files(self):
        """Closes the files, **only if the plugin opened them**."""
        if not self._owned:
            self._lf = self._vf = None
            return
        for attr in ('_lf', '_vf'):
            handle = getattr(self, attr, None)
            if handle is not None:
                try:
                    handle.close()
                except (OSError, ValueError):
                    pass
                setattr(self, attr, None)

    @property
    def active(self):
        """True when ddt4all is really writing the two files."""
        return self._lf is not None and self._vf is not None

    def close(self):
        """Gives ddt4all its previous handles back and closes ours."""
        if self._previous is not None and self.elm is not None:
            self.elm.lf, self.elm.vf = self._previous
            self._previous = None
        self._close_files()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
        return False

    def __repr__(self):
        return '<ElmLog %s>' % self.elm_path