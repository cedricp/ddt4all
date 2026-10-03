#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macro_ui.py
===========
GUI **shared** by the ddt4all plugins (``master/renault_macros.py`` and
``legacy/renault_macros.py``).

It allows to:

* pick the macro folder (``*.txt`` + ``*.cmd``) ;
* run a ``.cmd`` file (left list) or a named macro from the ``*.txt`` files
  (right list) ;
* inject a key for the interactive macros (``if_key``) ;
* follow/interrupt the execution in a ``QThread`` (the GUI never freezes).

Every access to ddt4all goes through :mod:`macro_adapter`.
"""

import os
import time
import traceback

import PyQt5.QtCore as core
import PyQt5.QtGui as qtgui
import PyQt5.QtWidgets as gui

#: window icon — same Qt resource as the other ddt4all plugins
APP_ICON = ":icons/obd.png"


def app_icon_path():
    """Icon path used by the installed ddt4all version.

    The master defines ``ddt4all.ui.main_window.icons_paths.ICON_OBD``; we
    reuse it as-is to stay in sync, otherwise we fall back to the plugin
    convention (``:icons/obd.png``).
    """
    try:
        from ddt4all.ui.main_window.icons_paths import ICON_OBD
        return ICON_OBD
    except Exception:                               # pragma: no cover
        return APP_ICON

try:
    from macro_engine import MacroEngine, MacroError, MacroExit
    from macro_adapter import (Ddt4allContext, describe_macro_dir,
                               installed_macro_dir, macro_dir_origin,
                               scan_macro_dir)
except ImportError:  # package imported without the folder in sys.path
    from ddt4all.plugins.macro_plugin.macro_engine import (
        MacroEngine, MacroError, MacroExit)
    from ddt4all.plugins.macro_plugin.macro_adapter import (
        Ddt4allContext, describe_macro_dir, installed_macro_dir,
        macro_dir_origin, scan_macro_dir)


# --------------------------------------------------------------------------- #
#  translation
# --------------------------------------------------------------------------- #
# Same convention as the ddt4all modules and plugins: the strings marked with
# _("...") are translated by the ddt4all catalog
# ``<ddt4all>/generated/locales/<lang>/LC_MESSAGES/ddt4all.mo`` (sources in
# ``<ddt4all>/locales/<lang>/LC_MESSAGES/ddt4all.po``).
#
# Only **literals** are wrapped: gettext extracts literals, so a computed string
# would never match a catalog entry.
#
# Resolved **once** at import: calling translator() per string would re-read the
# ddt4all configuration and replace its global translation. Outside ddt4all
# (tests, console) we fall back to the identity function.
try:                                       # ddt4all master (>= 3.1)
    import ddt4all.options as options
except ImportError:                        # ddt4all legacy (2.x / 3.0.x)
    try:
        import options                     # noqa: F401  (flat ddt4all module)
    except ImportError:
        options = None                     # outside ddt4all (tests, console)

#: ddt4all translates the _("...") strings through its own catalog
_ = options.translator('ddt4all') if hasattr(options, 'translator') \
    else (lambda text: text)

#: ELM connection state, as translatable literals (the adapter returns the
#: technical value, the GUI owns the wording).
ELM_LABELS = {
    True: _("ELM connected"),
    False: _("ELM not connected"),
}

#: Origin of the macro folder, as translatable literals.
MACRO_DIR_LABELS = {
    'installed': _("installed copy (macro_plugin/macros)"),
    'custom': _("manually chosen folder"),
}


def addressing_label(book):
    """Translated **effective** addressing source of ``book``.

    Only the source actually in use is named: with the ddt4all tables loaded,
    the ``LEGACY_*`` fallback is not mentioned (it stays in memory, but serves
    no purpose).
    """
    live = len(book.dnat) + len(book.dnat_ext)
    if live:
        return _("ddt4all tables (%d addresses)") % live
    if book.legacy_dnat:
        return _("pyren3 fallback (%d addresses)") % len(book.legacy_dnat)
    return _("no table")


def legacy_label(book):
    """Translated ``LEGACY_*`` (pyren3) fallback of ``book``: count, real role.

    In the *master* layout the ddt4all tables are fed by the loaded vehicle,
    so the fallback is only consulted for the addresses missing from them. The
    line reports it anyway, so one knows what is available and what serves.
    """
    if not book.use_legacy:
        return _("pyren3 fallback: disabled")
    count = len(book.legacy_dnat)
    if not count:
        return _("pyren3 fallback: no entry")
    if book.dnat or book.dnat_ext:
        return _("pyren3 fallback: %d addresses as a fallback, used only "
                 "for the addresses missing from the ddt4all tables") % count
    return _("pyren3 fallback: %d addresses (source in use)") % count


def natural_key(text):
    """"Natural alphabetical" sort key.

    * case insensitive (``RadNav`` before ``rlink2``, like a human would) ;
    * punctuation insensitive (``rlink2_acoustic`` before
      ``rlink2-enable``) ;
    * ties broken by the original name, so the sort is deterministic.
    """
    name = str(text)
    letters = ''.join(char for char in name.lower() if char.isalnum())
    return (letters, name)


class NaturalItem(gui.QTreeWidgetItem):
    """Tree node sorted alphabetically (case and punctuation ignored).

    ``weight`` puts the **standalone files** (macro at the root of the macro
    folder, without an ECU sub-folder) after every ECU group.
    """

    def __init__(self, *args, **kwargs):
        weight = kwargs.pop('weight', 0)
        super(NaturalItem, self).__init__(*args, **kwargs)
        self.weight = weight

    def __lt__(self, other):
        return self.sort_key() < other.sort_key()

    def sort_key(self):
        return (self.weight, natural_key(self.text(0)))


class MacroWorker(core.QThread):
    """Runs the engine in a dedicated thread (the GUI stays responsive)."""

    log_line = core.pyqtSignal(str)
    done = core.pyqtSignal(str)

    def __init__(self, engine, kind, target, name='', parent=None):
        super(MacroWorker, self).__init__(parent)
        self.engine = engine
        self.kind = kind            # 'cmd' or 'macro'
        self.target = target        # lines (.cmd) or macro name
        self.name = name or str(target)
        self._abort = False
        # the engine writes to the GUI through a signal (thread-safe)
        self.engine.set_log(self.log_line.emit)

    def abort(self):
        self._abort = True

    def is_aborted(self):
        return self._abort

    def run(self):
        try:
            if self.kind == 'cmd':
                self.engine.play_lines(self.target, self.name)
            else:
                self.engine.play_macro(self.target)
            self.done.emit(_("OK"))
        except MacroExit:
            self.done.emit(_("Done"))
        except MacroError as err:
            self.log_line.emit(_("ERROR: %s") % err)
            self.done.emit(_("Error"))
        except Exception:
            self.log_line.emit(traceback.format_exc())
            self.done.emit(_("Error"))


class MacroRunnerDialog(gui.QDialog):
    """Plugin window: folder selection, macro selection, execution."""

    def __init__(self, plugin_dir, context=None, parent=None, title=None):
        super(MacroRunnerDialog, self).__init__(parent)

        self.plugin_dir = os.path.abspath(plugin_dir)
        self.ctx = context or Ddt4allContext()
        self.engine = None
        self.worker = None

        self.setWindowTitle(title or _("Macros DDT2000"))
        appIcon = qtgui.QIcon(app_icon_path())   # like the other ddt4all plugins
        self.setWindowIcon(appIcon)
        self.resize(820, 600)

        # --- short status bar -------------------------------------------
        # The full details (host, folder, addressing tables) are written to
        # the log on load: the header keeps only the essentials.
        self.info = gui.QLabel()
        self.info.setTextInteractionFlags(core.Qt.TextSelectableByMouse)

        # --- macro folder ------------------------------------------------
        # the bundled macros ship with the plugin (macro_plugin/macros);
        # the field stays editable to point at another macro set.
        self.folder_edit = gui.QLineEdit()
        self.folder, self.origin = installed_macro_dir(self.plugin_dir)
        self.folder_edit.setText(self.folder or '')
        self.folder_edit.setToolTip(_("Macro folder (.cmd and *.txt)"))
        self.browse_btn = gui.QPushButton(_("Browse"))
        self.browse_btn.clicked.connect(self.browse)
        self.refresh_btn = gui.QPushButton(_("Refresh"))
        self.refresh_btn.clicked.connect(self.reload_macros)

        folder_row = gui.QHBoxLayout()
        folder_row.addWidget(gui.QLabel(_("Macro folder:")))
        folder_row.addWidget(self.folder_edit)
        folder_row.addWidget(self.browse_btn)
        folder_row.addWidget(self.refresh_btn)

        # --- trees: .cmd per ECU + named macros per *.txt ---------------
        # both trees start collapsed (the user opens what he needs).
        self.cmd_tree = self._new_tree(_(".cmd files (by ECU)"))
        self.cmd_tree.itemDoubleClicked.connect(lambda _i: self.run_cmd())
        self.macro_tree = self._new_tree(_("Named macros (by *.txt)"))
        self.macro_tree.itemDoubleClicked.connect(lambda _i: self.run_macro())

        lists = gui.QHBoxLayout()
        left = gui.QVBoxLayout()
        left.addWidget(gui.QLabel(_("Macros by ECU (.cmd)")))
        left.addWidget(self.cmd_tree)
        right = gui.QVBoxLayout()
        right.addWidget(gui.QLabel(_("Named macros (*.txt)")))
        right.addWidget(self.macro_tree)
        lists.addLayout(left)
        lists.addLayout(right)

        # --- if_key key --------------------------------------------------
        self.key_edit = gui.QLineEdit()
        self.key_edit.setMaxLength(1)
        self.key_edit.setFixedWidth(40)
        self.key_edit.returnPressed.connect(self.send_key)
        self.key_btn = gui.QPushButton(_("Send key"))
        self.key_btn.clicked.connect(self.send_key)
        key_row = gui.QHBoxLayout()
        key_row.addWidget(gui.QLabel(_("Key for 'if_key':")))
        key_row.addWidget(self.key_edit)
        key_row.addWidget(self.key_btn)
        key_row.addStretch(1)

        # --- buttons -----------------------------------------------------
        self.run_cmd_btn = gui.QPushButton(_("Execute .cmd"))
        self.run_cmd_btn.clicked.connect(self.run_cmd)
        self.run_macro_btn = gui.QPushButton(_("Execute macro"))
        self.run_macro_btn.clicked.connect(self.run_macro)
        self.stop_btn = gui.QPushButton(_("Stop"))
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        self.close_btn = gui.QPushButton(_("Close"))
        self.close_btn.clicked.connect(self.close)
        buttons = gui.QHBoxLayout()
        buttons.addWidget(self.run_cmd_btn)
        buttons.addWidget(self.run_macro_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.close_btn)

        # --- log ---------------------------------------------------------
        self.log_view = gui.QPlainTextEdit()
        self.log_view.setReadOnly(True)

        layout = gui.QVBoxLayout(self)
        layout.addWidget(self.info)
        layout.addLayout(folder_row)
        layout.addLayout(lists)
        layout.addLayout(key_row)
        layout.addLayout(buttons)
        layout.addWidget(gui.QLabel(_("Log")))
        layout.addWidget(self.log_view, 1)

        self.reload_macros()

    # ------------------------------------------------------------------ #
    #  selection                                                        #
    # ------------------------------------------------------------------ #
    def _new_tree(self, header):
        """Creates a **collapsed**, alphabetically sorted ``QTreeWidget``.

        ``setSortingEnabled`` is deliberately disabled: Qt uses
        ``QTreeWidgetItem::operator<`` (not virtual in C++), which ignores
        :class:`NaturalItem`. Sorting is therefore done by
        :meth:`sort_tree`, on a header click.

        No alternating row colours: the ddt4all stylesheets
        (``resources/styles/qstyle*.qss``) have no ``alternate-background-color``
        rule, so the stripes would be painted with the **system** palette
        (near-white) over the dark theme. ddt4all's own ``QTreeWidget``
        (``ui/main_window/ecu_list.py``) does the same.
        """
        tree = gui.QTreeWidget()
        tree.setHeaderLabels([header])
        tree.setUniformRowHeights(True)
        tree.setSortingEnabled(False)
        tree.header().setSectionsClickable(True)
        tree.header().sectionClicked.connect(
            lambda col: self.sort_tree(tree, col))
        return tree

    def sort_tree(self, tree, column=0):
        """Sorts the children of every tree level alphabetically.

        Uses :meth:`NaturalItem.sort_key` (weight, then natural order), so
        standalone files stay after the groups.
        """
        def key(item):
            if hasattr(item, 'sort_key'):
                return item.sort_key()
            return (0, natural_key(item.text(column)))

        def recurse(parent):
            items = [parent.takeChild(0) for _ in range(parent.childCount())]
            for child in sorted(items, key=key):
                parent.insertChild(parent.childCount(), child)
                recurse(child)

        recurse(tree.invisibleRootItem())

    def browse(self):
        folder = gui.QFileDialog.getExistingDirectory(
            self, _("Macro folder"), self.folder_edit.text() or '.')
        if folder:
            self.folder_edit.setText(folder)
            self.origin = 'custom'
            self.reload_macros()

    def fill_cmd_tree(self, folder, cmds):
        """Fills the ``.cmd`` tree: one node per ECU folder.

        The macro folders are named after the ECU or the targeted platform
        (``rlink2``, ``qr25``, ``UCL4.1``, ``Megane3Scenic3``…), not after a
        vehicle model.

        Natural alphabetical order (see :func:`natural_key`) **inside** each
        node ; the files sitting at the root of the macro folder are shown
        **after** every group. The tree is **collapsed**.

        :returns: ``(number_of_groups, number_of_files)``.
        """
        tree = self.cmd_tree
        tree.clear()
        groups = {}
        leaves = 0

        def sort_key(path):
            rel = os.path.relpath(path, folder).replace(os.sep, '/')
            return tuple(natural_key(part) for part in rel.split('/'))

        for path in sorted(cmds, key=sort_key):
            rel = os.path.relpath(path, folder).replace(os.sep, '/')
            parts = rel.split('/')
            parent = tree.invisibleRootItem()
            prefix = []
            for name in parts[:-1]:
                prefix.append(name)
                key = '/'.join(prefix)
                if key not in groups:
                    node = NaturalItem(parent, [name])
                    node.setToolTip(0, os.path.join(folder, *prefix))
                    groups[key] = node
                parent = groups[key]
            # a macro at the root belongs to no ECU: weight 1 so that it
            # is displayed after every group.
            leaf = NaturalItem(parent, [parts[-1]],
                               weight=0 if len(parts) > 1 else 1)
            leaf.setData(0, core.Qt.UserRole, path)
            leaf.setData(0, core.Qt.UserRole + 1, rel)
            leaf.setToolTip(0, rel)
            leaves += 1

        tree.collapseAll()
        self.sort_tree(tree)
        return len(groups), leaves

    def fill_macro_tree(self, folder, txts):
        """Fills the named-macro tree: one node per ``*.txt`` file.

        :returns: ``(number_of_groups, number_of_macros)``.
        """
        tree = self.macro_tree
        tree.clear()
        groups = 0
        seen = set()

        for path in sorted(txts, key=natural_key):
            rel = os.path.relpath(path, folder).replace(os.sep, '/')
            engine = MacroEngine(None, log=lambda _m: None)
            try:
                engine.parse_file(path)
            except MacroError as err:
                self.append_log(_("Parsing error %s: %s") % (rel, err))
                continue
            except OSError as err:
                self.append_log(_("Cannot read %s: %s") % (rel, err))
                continue

            names = [name for name in engine.macro if name not in seen]
            if not names:
                continue
            seen.update(names)
            node = NaturalItem(tree, [rel])
            node.setToolTip(0, path)
            for name in sorted(names, key=natural_key):
                leaf = NaturalItem(node, [name])
                leaf.setData(0, core.Qt.UserRole, name)
                leaf.setData(0, core.Qt.UserRole + 1, rel)
                leaf.setToolTip(0, _("%s (defined in %s)") % (name, rel))
            groups += 1

        tree.collapseAll()
        self.sort_tree(tree)
        return groups, len(seen)

    def reload_macros(self):
        """Reloads both trees (``.cmd`` and named ``*.txt`` macros)."""
        folder = self.folder_edit.text().strip()
        if not self.origin or folder != self.folder:
            # the user changed the folder -> work out where it comes from
            self.origin = macro_dir_origin(folder, self.plugin_dir) or 'custom'
        cmds, txts = scan_macro_dir(folder)
        groups, leaves = self.fill_cmd_tree(folder, cmds)
        mgroups, macros = self.fill_macro_tree(folder, txts)

        self.append_log(_("Host: %s") % self.host_line())
        self.append_log(_("Addresses: %s") % self.legacy_label())
        self.append_log(_("Format: macros DDT2000 (pyren3); the bundled macros "
                          "target Renault ECUs, address resolution follows "
                          "the vehicle loaded in ddt4all."))
        self.append_log(_("Folder: %s") % (folder or _("(none)")))
        self.append_log(_("Source: %s") % self.origin_label(self.origin))
        self.append_log(_("%d ECU group(s), %d .cmd file(s), "
                          "%d named macro(s) in %d .txt file(s)")
                        % (groups, leaves, macros, mgroups))
        self.update_status(groups, leaves, macros)

    def origin_label(self, origin):
        """Translated label of a macro folder origin (see MACRO_DIR_LABELS)."""
        return MACRO_DIR_LABELS.get(origin, origin or _("(none)"))

    def elm_label(self):
        """Translated ELM connection label (see ELM_LABELS)."""
        return ELM_LABELS[self.ctx.elm is not None]

    def addressing_label(self):
        """Translated **effective** addressing source (see module function)."""
        return addressing_label(self.ctx.address_book())

    def legacy_label(self):
        """Translated pyren3 fallback count and role (see module function)."""
        return legacy_label(self.ctx.address_book())

    def host_line(self):
        """Translated one-line summary of the host (status bar / log)."""
        if not self.ctx.is_available():
            return _("ddt4all not found (console mode only)")
        return _("ddt4all %s | %s | addressing: %s") % (
            self.ctx.flavor, self.elm_label(), self.addressing_label())

    def update_status(self, groups=0, leaves=0, macros=0):
        """Short header + detailed tooltip (the rest lives in the log)."""
        book = self.ctx.address_book()
        self.info.setText(_("%s | %d .cmd (%d ECU) | %d named macro(s)")
                          % (self.elm_label(), leaves, groups, macros))
        self.info.setToolTip(
            _("%s\nAddresses: %s\n%s\nFolder: %s\nSource: %s")
            % (self.host_line(), self.legacy_label(), book.detail(),
               self.folder_edit.text().strip() or _("(none)"),
               self.origin_label(self.origin)))

    # ------------------------------------------------------------------ #
    #  execution                                                          #
    # ------------------------------------------------------------------ #
    def append_log(self, text):
        self.log_view.appendPlainText(str(text))

    def safe_wait(self, seconds):
        """``wait``, interruptible (otherwise a macro could not be stopped)."""
        end = time.time() + float(seconds)
        while time.time() < end:
            if self.worker is not None and self.worker.is_aborted():
                raise MacroExit()
            time.sleep(0.05)

    def start_worker(self, kind, target, name):
        if self.worker is not None and self.worker.isRunning():
            self.append_log(_("A macro is already running."))
            return

        self.ctx = Ddt4allContext()          # re-detect (late connection)
        if not self.ctx.is_available() and not self.ctx.simulation:
            self.append_log(_("ddt4all is not available: this plugin must be "
                              "started from ddt4all."))
            return
        if self.ctx.elm is None and not self.ctx.simulation:
            self.append_log(_("No ELM connection: connect ddt4all to the ELM "
                              "before running a macro."))
            return

        engine = self.ctx.make_engine(
            log=self.append_log,
            wait_hook=self.safe_wait,
            clear_hook=self.log_view.clear,
            abort_hook=lambda: (self.worker is not None
                                and self.worker.is_aborted()),
            interactive=True)
        if kind == 'macro':
            engine.load_macro_dir(self.folder_edit.text().strip())

        self.engine = engine
        self.worker = MacroWorker(engine, kind, target, name, self)
        self.worker.log_line.connect(self.append_log)
        self.worker.done.connect(self.on_done)
        self.set_running(True)
        self.append_log(_("--- START %s: %s ---") % (kind, name))
        self.worker.start()

    def run_cmd(self):
        item = self.cmd_tree.currentItem()
        path = item.data(0, core.Qt.UserRole) if item is not None else None
        if not path:
            self.append_log(_("Select a .cmd file (double-click to run)."))
            return
        try:
            with open(path, 'rt', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except OSError as err:
            self.append_log(_("Cannot read %s: %s") % (path, err))
            return
        self.start_worker('cmd', lines,
                          item.data(0, core.Qt.UserRole + 1)
                          or os.path.basename(path))

    def run_macro(self):
        item = self.macro_tree.currentItem()
        name = item.data(0, core.Qt.UserRole) if item is not None else None
        if not name:
            self.append_log(_("Select a named macro (double-click to run)."))
            return
        self.start_worker('macro', name, name)

    def send_key(self):
        """Injects a key for the interactive macros (``if_key``)."""
        if self.engine is None:
            return
        text = self.key_edit.text().strip()
        if text:
            self.engine.set_key(text[0])
            self.append_log(_("# key '%s' sent") % text[0])
        self.key_edit.clear()

    def stop(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.abort()
            self.append_log(_("# stop requested..."))

    def on_done(self, status):
        self.append_log(_("--- END: %s ---") % status)
        self.report_addressing_conflicts()
        self.set_running(False)

    def report_addressing_conflicts(self):
        """Warn when ddt4all and pyren3 resolve an address differently.

        The bundled macros come from pyren3, so a macro would talk to another
        id than in pyren3 if the vehicle tables differ: say so explicitly.
        """
        book = self.engine.addresses if self.engine is not None else None
        for addr, current, legacy in getattr(book, 'conflicts', ()):
            self.append_log(
                _("WARNING: address %s resolves to %s/%s (ddt4all) but "
                  "pyren3 uses %s/%s") % (addr, current[0], current[1],
                                          legacy[0], legacy[1]))

    def set_running(self, running):
        self.run_cmd_btn.setEnabled(not running)
        self.run_macro_btn.setEnabled(not running)
        self.cmd_tree.setEnabled(not running)
        self.macro_tree.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def showEvent(self, event):
        """On display: both trees stay collapsed."""
        super(MacroRunnerDialog, self).showEvent(event)

    def closeEvent(self, event):
        self.stop()
        if self.worker is not None:
            self.worker.wait(3000)
        super(MacroRunnerDialog, self).closeEvent(event)


def run_dialog(plugin_dir, title=None):
    """Common entry point of the two ddt4all plugins."""
    MacroRunnerDialog(plugin_dir, title=title).exec_()
