#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macro_engine.py
=================
Execution engine for **DDT2000 macros** (``*.txt`` and ``*.cmd`` files,
mod_term-compatible format): usable from a ddt4all plugin or outside a GUI.

Faithful port of ``pyren3/mod_term.py``:
``pars_macro``, ``play_macro``, ``proc_line``, ``bit_cmd``, ``term_cmd``,
``run_init_function``, ``wait_kb``.

**Mandatory** adaptations to run inside a graphical application (every other
part of the language is preserved as-is):

======================  =================================================
mod_term.py             here
======================  =================================================
``sys.exit()``          ``raise MacroExit()``  (otherwise ddt4all quits!)
``print()``             ``log`` callback  (default ``print``)
``wait_kb()``           ``wait_hook`` callback + injected keys
``input()``             removed (no console in a GUI)
``os.chdir()``          removed (done on mod_term import: forbidden here)
``readline``/``pip``/    removed
``colorama``/``android``
``mod_globals``         injected ``globals_`` object (shim, see the adapter)
``mod_elm.dnat/snat``   injected ``AddressBook`` (see can_addressing +
                        the live ddt4all tables)
``mod_elm.pyren_time``  local ``pyren_time()``
``mod_utils.KBHit``     replaced by ``set_key()`` / ``interactive``
======================  =================================================

Minimal usage (without ddt4all)::

    from macro_engine import MacroEngine
    engine = MacroEngine(elm)                 # elm = mod_elm.ELM-like object
    engine.load_macro_dir('./macro')          # *.txt  (init.txt, can500, ...)
    engine.play_lines(open('mac.tmp.cmd').readlines())
"""

import inspect
import os
import re
import string
import sys
import time

#: The modules live side by side in the plugin folder. Putting that folder on
#: ``sys.path`` keeps the imports below valid whether the plugin is installed
#: flat (``<plugins>/macro_*.py``) or in the ``macro_plugin`` sub-folder, and
#: whether it is imported as a plain module or as part of the
#: ``ddt4all.plugins.macro_plugin`` package.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from can_addressing import (DNAT, DNAT_EXT, LEGACY_DNAT, LEGACY_SNAT,
                            SNAT, SNAT_EXT, is_ext, normalize)

# ddt4all translates the _("...") strings through its own catalog; outside
# ddt4all (console, tests) we fall back to the identity function.
try:                                       # ddt4all master (>= 3.1)
    import ddt4all.options as options
except ImportError:                        # ddt4all legacy (2.x / 3.0.x)
    try:
        import options                     # noqa: F401  (flat ddt4all module)
    except ImportError:
        options = None                     # outside ddt4all (tests, console)

_ = options.translator('ddt4all') if hasattr(options, 'translator') \
    else (lambda text: text)


class MacroExit(Exception):
    """Normal end of a macro (``exit``, ``q``, ``exit_if`` ...).

    Replaces the ``sys.exit()`` of ``mod_term.py``: inside ddt4all an
    ``sys.exit()`` would close the whole application.
    """


class MacroError(Exception):
    """Syntax / execution error of a macro."""


def pyren_time():
    """Equivalent of ``mod_elm.pyren_time()``."""
    return time.perf_counter()


def _accepts(func, param):
    """True if ``func`` accepts the ``param`` keyword (signature compatibility)."""
    try:
        return param in inspect.signature(func).parameters
    except (TypeError, ValueError):
        return True


#: Maximum number of ``$variable`` substitutions in a single macro line.
#: A substitution that does not consume the variable (or a value that
#: reintroduces one) would otherwise loop forever, as in ``mod_term.py``.
MAX_VARIABLES_PER_LINE = 100


#: ``bit_cmd`` guard messages (translated like every other UI string)
BIT_CMD_ERROR_1 = _("""ERROR: command should have 5 parameters: 
    <command> <lid> <rsp_len> <offset> <hex mask> <hex value>
        <lid> - ECUs local identifier. Length should be 2 simbols for KWP or 4 for CAN
        <rsp_len> - lengt of command response including positive response bytes, equals MinBytes from ddt db
        <offset> - offeset in bytes to first changed byte (starts from 1 not 0) 
        <hex mask> - bit mask for changed bits, 1 - changable, 0 - untachable
        <hex value> - bit value
    <hex mask> and <hex value> should have equal length
""")

BIT_CMD_ERROR_2 = _("""ERROR: command should have 6 parameters: 
    <command> <lid> <rsp_len> <offset> <hex mask> <hex value> <label>
        <lid> - ECUs local identifier. Length should be 2 simbols for KWP or 4 for CAN
        <rsp_len> - lengt of command response including positive response bytes, equals MinBytes from ddt db
        <offset> - offeset in bytes to first changed byte (starts from 1 not 0) 
        <hex mask> - bit mask for changed bits, 1 - changable, 0 - untachable
        <hex value> - bit value
        <label> - label to go
    <hex mask> and <hex value> should have equal length
""")

BIT_CMD_ERROR_3 = _("""ERROR: command should have 4 or 7 parameters: 
    <command> <lid> <rsp_len> <offset> <hex mask> <hex value> <label>
        <lid> - ECUs local identifier. Length should be 2 simbols for KWP or 4 for CAN
        <rsp_len> - lengt of command response including positive response bytes, equals MinBytes from ddt db
        <offset> - offeset in bytes to first changed byte (starts from 1 not 0) 
        <hex mask> - bit mask for changed bits, 1 - changable, 0 - untachable
        <val step> - value step
        <val offset> - value offset
        <val divider> - value divider

""")


class AddressBook(object):
    """Resolution of the CAN addresses used by the macros (``$addr``).

    Sources, **in decreasing priority order**:

    1. live ddt4all tables: ``elm.dnat``, ``elm.snat``, ``elm.dnat_ext``,
       ``elm.snat_ext`` (plus the ``dnat_entries`` / ``snat_entries``
       aliases) ;
    2. embedded tables, extracted from the **same** ddt4all code
       (``can_addressing.DNAT``/``SNAT``/``DNAT_EXT``/``SNAT_EXT``) ;
    3. ``LEGACY_*`` tables (fallback), last resort and disableable
       (``use_legacy=False``): useful because the ddt4all master declares its
       four tables empty (the addressing comes from the ECU XML there).

    Extended identifiers (29 bits) are taken from the ``*_ext`` tables.
    """

    def __init__(self, dnat=None, snat=None, dnat_ext=None, snat_ext=None,
                 legacy_dnat=None, legacy_snat=None, use_legacy=True):
        self.dnat = normalize(dnat or {})
        self.snat = normalize(snat or {})
        self.dnat_ext = normalize(dnat_ext or {})
        self.snat_ext = normalize(snat_ext or {})
        self.use_legacy = bool(use_legacy)
        self.legacy_dnat = normalize(legacy_dnat or {}) if use_legacy else {}
        self.legacy_snat = normalize(legacy_snat or {}) if use_legacy else {}
        #: ``(addr, (idTx, idRx), (legacy_idTx, legacy_idRx))`` where the ddt4all
        #: tables and the pyren3 ones disagree — reported by the GUI after a run
        self.conflicts = []

    # ------------------------------------------------------------------ #
    #  construction                                                       #
    # ------------------------------------------------------------------ #
    @classmethod
    def from_elm_module(cls, elm_module, use_legacy=True):
        """Builds an AddressBook from the ddt4all ``elm`` module."""
        live = {}
        if elm_module is not None:
            for name in ('dnat', 'snat', 'dnat_ext', 'snat_ext',
                         'dnat_entries', 'snat_entries'):
                data = getattr(elm_module, name, None)
                if isinstance(data, dict) and data:
                    live.setdefault(name, normalize(data))

        def merged(live_name, embedded):
            """Embedded table, enriched by the live ddt4all table."""
            out = dict(embedded)
            out.update(live.get(live_name, {}))
            return out

        return cls(dnat=merged('dnat', DNAT),
                   snat=merged('snat', SNAT),
                   dnat_ext=merged('dnat_ext', DNAT_EXT),
                   snat_ext=merged('snat_ext', SNAT_EXT),
                   legacy_dnat=LEGACY_DNAT, legacy_snat=LEGACY_SNAT,
                   use_legacy=use_legacy)

    # ------------------------------------------------------------------ #
    #  resolution                                                         #
    # ------------------------------------------------------------------ #
    def resolve(self, addr):
        """Returns ``(idTx, idRx, extended)`` for a logical address.

        :raises KeyError: if the address is unknown in every table.
        """
        key = str(addr).upper()
        resolved = self._resolve(key)
        self._record_conflict(key, resolved)
        return resolved

    def _record_conflict(self, key, resolved):
        """Store where ddt4all and pyren3 disagree, so the GUI can warn."""
        if not self.use_legacy or key not in self.legacy_dnat \
                or key not in self.legacy_snat:
            return
        legacy = (self.legacy_dnat[key], self.legacy_snat[key])
        if (resolved[0], resolved[1]) != legacy:
            entry = (key, (resolved[0], resolved[1]), legacy)
            if entry not in self.conflicts:
                self.conflicts.append(entry)

    def _resolve(self, key):
        if key in self.dnat and key in self.snat:
            return self.dnat[key], self.snat[key], False
        if key in self.dnat_ext and key in self.snat_ext:
            return self.dnat_ext[key], self.snat_ext[key], True
        if self.use_legacy:
            if key in self.legacy_dnat and key in self.legacy_snat:
                return (self.legacy_dnat[key], self.legacy_snat[key],
                        is_ext(self.legacy_dnat[key]))
        # ddt4all also accepts a direct CAN identifier (reverse lookup)
        addr = self.addr_for_txa(key)
        if addr is not None:
            return key, self.snat.get(addr, ''), is_ext(key)
        raise KeyError(addr)

    def has(self, addr):
        try:
            self.resolve(addr)
            return True
        except KeyError:
            return False

    def txa(self, addr):
        """Transmit identifier (idTx), or '' if unknown."""
        try:
            return self.resolve(addr)[0]
        except KeyError:
            return ''

    def rxa(self, addr):
        """Receive identifier (idRx), or '' if unknown."""
        try:
            return self.resolve(addr)[1]
        except KeyError:
            return ''

    def addr_for_txa(self, txa):
        """Reverse lookup (like ``elm.get_can_addr`` of ddt4all)."""
        target = str(txa).upper()
        for dnat, snat in ((self.dnat, self.snat), (self.dnat_ext, self.snat_ext),
                           (self.legacy_dnat, self.legacy_snat)):
            for key, value in dnat.items():
                if value == target:
                    return key
        return None

    def ecu_dict(self, addr, brp=None, ecuname='macro-plugin', **extra):
        """``ecu`` dictionary for ``ELM.set_can_addr``.

        ``idTx``/``idRx`` are only set when the address is known; otherwise
        ddt4all gets a minimal dictionary and resolves the addressing as it
        does for its own screens. 29-bit identifiers are accepted as-is by
        both drivers (test ``len(idRx) > 4``).
        """
        res = {'ecuname': ecuname}
        try:
            tx, rx, _ext = self.resolve(addr)
        except KeyError:
            tx = rx = ''
        if tx:
            res['idTx'] = tx
        if rx:
            res['idRx'] = rx
        if brp is not None:
            res['brp'] = str(brp)
        res.update(extra)
        return res

    def detail(self):
        """Raw count of each table (tooltip).

        Plain ``key=value`` data, not prose: the wording lives in
        ``macro_ui`` so that it can be translated (see
        :meth:`macro_ui.MacroRunnerDialog.addressing_label`).
        """
        return ('dnat=%d snat=%d dnat_ext=%d snat_ext=%d legacy=%d'
                % (len(self.dnat), len(self.snat), len(self.dnat_ext),
                   len(self.snat_ext),
                   len(self.legacy_dnat) if self.use_legacy else 0))


class MacroEngine(object):
    """DDT2000 macro interpreter (mod_term format).

    :param elm:         ELM instance (``ddt4all.options.elm`` or ``mod_elm.ELM``).
    :param log:         ``log(str)`` callback (default: ``print``).
    :param wait_hook:   ``wait_hook(seconds)`` callback (default: ``time.sleep``).
    :param clear_hook:  ``clear_hook()`` callback for the ``cls`` command.
    :param addresses:   :class:`AddressBook` (default: embedded tables).
    :param globals_:    ``mod_globals`` shim (``opt_demo`` above, see adapter).
    :param abort_hook:  boolean callback: True => interrupts the macro
                        (the "Stop" button of the GUI).
    :param interactive: False => the ``if_key`` are ignored (batch mode).
    :param canline:     CAN line (0 = CAN1) passed to ``set_can_addr``
                        when the ddt4all ELM supports it.
    :param max_steps:   anti-infinite-loop guard (``goto`` without ``if_key``).
    """

    def __init__(self, elm, log=None, wait_hook=None, clear_hook=None,
                 addresses=None, globals_=None, abort_hook=None,
                 interactive=True, canline=0, max_steps=200000):

        self.elm = elm
        self.addresses = addresses or AddressBook.from_elm_module(None)
        self.globals_ = globals_
        self.wait_hook = wait_hook
        self.clear_hook = clear_hook
        self.abort_hook = abort_hook
        self.interactive = interactive
        self.canline = canline
        self.max_steps = max_steps

        self._log = log if log is not None else print
        self.macro = {}
        self.var = {}
        self.cmd_delay = 0
        self.stack = []
        self.key_pressed = ''
        self.steps = 0

        self.init_var()

    # ------------------------------------------------------------------ #
    #  utilities                                                          #
    # ------------------------------------------------------------------ #
    def log(self, msg=''):
        self._log(str(msg))

    def set_log(self, callback):
        """Replaces the logging callback (e.g. a Qt signal)."""
        self._log = callback if callback is not None else print

    def init_var(self):
        """Predefined variables (same as ``mod_term.init_var``)."""
        self.var = {}
        self.var['$addr'] = '7A'
        self.var['$txa'] = '7E0'
        self.var['$rxa'] = '7E8'
        self.var['$prompt'] = 'ELM'

    def set_key(self, key):
        """Injects a key for the ``if_key`` command (GUI)."""
        self.key_pressed = str(key)

    def _require_elm(self):
        if self.elm is None:
            raise MacroError(_("No ELM connection (plugin need_hw=True ?)"))

    def _tick(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise MacroError(_("guard: %(limit)d steps exceeded (infinite loop?)")
                             % {"limit": self.max_steps})
        if self.abort_hook is not None and self.abort_hook():
            self.log(_("# abort requested"))
            raise MacroExit()

    # ------------------------------------------------------------------ #
    #  parsing (port of pars_macro / load_macro)                          #
    # ------------------------------------------------------------------ #
    def parse_file(self, filename):
        """Loads a ``*.txt`` macro file."""
        with open(filename, 'rt', encoding='utf-8', errors='replace') as f:
            text = f.read()
        self.log(_("openning file: %(file)s") % {"file": filename})
        self.parse_text(text, filename)

    def parse_text(self, text, filename='<text>'):
        """Port of ``mod_term.pars_macro`` (same behaviour)."""
        macroname = ''
        macrostrings = []
        for line_num, raw in enumerate(str(text).splitlines(), 1):
            l = raw.split('#')[0]          # remove comments
            l = l.strip()
            if l == '':
                continue
            if '{' in l:
                if macroname == '':
                    literals = l.split('{')
                    macroname = literals[0].strip()
                    macroname = macroname.replace(' ', '_').replace('\t', '_')
                    macrostrings = []
                    if len(literals) > 1 and literals[1] != '':
                        macrostrings.append(literals[1])
                    continue
                else:
                    raise MacroError(_("%(file)s:%(line)d: empty macro name")
                                     % {"file": filename, "line": line_num})
            if '}' in l:
                if macroname != '':
                    literals = l.split('}')
                    cmd = literals[0].strip()
                    if cmd != '':
                        macrostrings.append(cmd)
                    self.macro[macroname] = macrostrings
                    macroname = ''
                    macrostrings = []
                    continue
                else:
                    raise MacroError(_("%(file)s:%(line)d: unexpected end of macro")
                                     % {"file": filename, "line": line_num})
            m = re.search(r'\$\S+\s*=\s*\S+', l)
            if m and macroname == '':
                # variable definition
                r = m.group(0).replace(' ', '').replace('\t', '')
                rl = r.split('=')
                self.var[rl[0]] = rl[1]
            else:
                macrostrings.append(l)
        return self.macro

    def load_macro_dir(self, folder):
        """Loads every ``*.txt`` of a folder (and its sub-folders).

        ``mod_term.load_macro`` only walked ``./macro`` and forgot the
        sub-folder in the ``join``: fixed here.
        """
        count = 0
        for root, _dirs, files in os.walk(folder):
            for mfile in sorted(files):
                if mfile.lower().endswith('.txt'):
                    self.parse_file(os.path.join(root, mfile))
                    count += 1
        return count

    def load_commands(self, filename):
        """Reads a ``*.cmd`` (or ``*.tmp``) file and returns its lines."""
        with open(filename, 'rt', encoding='utf-8', errors='replace') as f:
            return f.readlines()

    def help_text(self):
        """Translated help of the macro language (``h`` command)."""
        variables = ''.join(_("  %(name)s = %(value)s") % {"name": v, "value": self.var[v]}
                           for v in sorted(self.var))
        macros = ''.join(_("  %(macro)s") % {"macro": m} for m in sorted(self.macro))
        return '\n'.join((_("[h]elp                 - this help"),
                          _("[q]uit, [e]xit, end    - exit from terminal"),
                          _("wait|sleep x           - wait x seconds"),
                          '',
                          _("Variables:"), variables,
                          '',
                          _("Macros:"), macros))

    # ------------------------------------------------------------------ #
    #  execution                                                          #
    # ------------------------------------------------------------------ #
    def play_macro(self, mname):
        """Port of ``mod_term.play_macro`` (recursion forbidden)."""
        if mname not in self.macro:
            self.log(_("Error: unknown macro name: %(macro)s") % {"macro": mname})
            return
        if mname in self.stack:
            self.log(_("Error: recursion prohibited: %(macro)s") % {"macro": mname})
            return
        self.stack.append(mname)
        try:
            for l in self.macro[mname]:
                self._tick()
                if l in self.macro:
                    self.play_macro(l)
                    continue
                self.proc_line(l)
        finally:
            self.stack.remove(mname)

    def play_lines(self, lines, name='<cmd>'):
        """Port of the ``mod_term.main`` loop for a ``.cmd`` file.

        Handles the ``:label`` labels and the ``goto`` / ``goto_if`` jumps.
        Stops cleanly at the end of the file (no ``input()`` in a GUI).
        """
        cmd_lines = [str(x).rstrip('\r\n') for x in lines]
        cmd_ref = 0
        self.log(_("### %(file)s : %(count)d lines")
                     % {"file": name, "count": len(cmd_lines)})
        while True:
            self._tick()
            if cmd_ref < len(cmd_lines):
                l = cmd_lines[cmd_ref].strip()
                cmd_ref += 1
            else:
                self.log(_("# end of command file"))
                return

            self.log(_("> %(line)s") % {"line": l})
            goto = self.proc_line(l)

            if goto:
                found = False
                for c_str, c in enumerate(cmd_lines):
                    if c.startswith(':') and goto == c[1:].strip():
                        cmd_ref = c_str
                        found = True
                        break
                if not found:
                    self.log(_("Error: unknown label '%(label)s'") % {"label": goto})
                    return

    def proc_line(self, l):
        """Port of ``mod_term.proc_line`` (same commands, same syntax)."""
        if '#' in l:
            l = l.split('#')[0]
        l = l.strip()

        if l.startswith(':'):
            self.log(l)
            return

        if len(l) == 0:
            return

        if l in ('q', 'quit', 'e', 'exit', 'end'):
            raise MacroExit()

        if l in ('h', 'help', '?'):
            self.log(self.help_text())
            return

        if l in ('var',):
            self.log(_("###### Variables #####"))
            for v in sorted(self.var):
                self.log(_("# %(name)20s = %(value)s")
                         % {"name": v, "value": self.var[v]})
            return

        if l in ('cls',):
            if self.clear_hook is not None:
                self.clear_hook()
            return

        if len(l) > 2 and l[0:3] in ('ini', 'can', 'slo', 'fas'):
            self.run_init_function(l)
            return
        elif l in self.macro:
            self.play_macro(l)
            return

        # find variable usage
        m = re.search(r'.+(\$\S+)', l)
        if m:
            for _attempt in range(MAX_VARIABLES_PER_LINE):
                vu = m.group(1)
                if vu not in self.var:
                    self.log(_("Error: unknown variable %(name)s")
                             % {"name": vu})
                    return
                # ``re.escape`` matches the variable name literally (``$txa``)
                # and a **function** as the replacement inserts the value as-is:
                # a value holding a backslash or ``\1`` is not read as a
                # replacement template.
                l = re.sub(re.escape(vu),
                           lambda _match, value=self.var[vu]: value, l)
                m = re.search(r'.+(\$\S+)', l)
                if m is None:
                    break
            else:
                self.log(_("Error: too many variables in one line"))
                return
            self.log(_("#(subst)") + l)

        m = re.search(r'\$\S+\s*=\s*\S+', l)
        if m:
            # find variable definition
            r = m.group(0).replace(' ', '').replace('\t', '')
            rl = r.split('=')
            self.var[rl[0]] = rl[1]
            if rl[0] == '$addr':
                if self.addresses.has(self.var['$addr']):
                    self.var['$txa'] = self.addresses.txa(self.var['$addr'])
                    self.var['$rxa'] = self.addresses.rxa(self.var['$addr'])
                    if self.elm is not None:
                        self.elm.currentaddress = self.var['$addr'].upper()
            return

        l_parts = l.split()

        if len(l_parts) > 0 and l_parts[0] in ('wait', 'sleep'):
            try:
                self.wait(float(l_parts[1]))
                return
            except (IndexError, ValueError):
                pass

        if len(l_parts) > 0 and l_parts[0] in ('ses', 'session'):
            try:
                if self.elm is not None:
                    self.elm.startSession = l_parts[1]
                l = l_parts[1]
            except IndexError:
                pass

        if len(l_parts) > 0 and l_parts[0] in ('delay',):
            try:
                self.cmd_delay = float(l_parts[1])
            except (IndexError, ValueError):
                pass
            return

        if l.lower().startswith('set_bits'):
            self.bit_cmd(l.lower()[8:], fnc='set_bits')
            return

        if l.lower().startswith('xor_bits'):
            self.bit_cmd(l.lower()[8:], fnc='xor_bits')
            return

        if l.lower().startswith('exit_if_not'):
            self.bit_cmd(l.lower()[11:], fnc='exit_if_not')
            return

        if l.lower().startswith('exit_if'):
            self.bit_cmd(l.lower()[7:], fnc='exit_if')
            return

        if l.lower().startswith('goto_if_not'):
            return self.bit_cmd(l.lower()[11:], fnc='goto_if_not')

        if l.lower().startswith('goto_if'):
            return self.bit_cmd(l.lower()[7:], fnc='goto_if')

        if l.lower().startswith('if_key'):
            if not self.interactive:
                # mode batch : aucune touche ne peut arriver
                return
            if len(l_parts) != 3 or l_parts[1] != self.key_pressed:
                return
            self.key_pressed = ''
            return l_parts[2]

        if l.lower().startswith('value'):
            self.bit_cmd(l.lower()[5:], fnc='value')
            return

        if len(l_parts) > 0 and l_parts[0] in ('go', 'goto'):
            self.log(l)
            return l_parts[1]

        if len(l_parts) > 0 and l_parts[0] in ('var', 'variable'):
            self.log(l)
            return

        if l.startswith('_'):
            self._require_elm()
            self.log(self.elm.send_raw(l[1:]))
        else:
            self.log(self.term_cmd(l))

        if self.cmd_delay > 0:
            self.log(_("# delay: %(seconds)s") % {"seconds": self.cmd_delay})
            self.wait(self.cmd_delay)

    # ------------------------------------------------------------------ #
    #  ELM access                                                          #
    # ------------------------------------------------------------------ #
    def term_cmd(self, c):
        """Port of ``mod_term.term_cmd``: sends a diagnostic request."""
        self._require_elm()
        rsp = self._elm_request(c, cache=False)
        self.var['$lastResponse'] = rsp
        return rsp

    def _elm_request(self, cmd, cache=False):
        """``elm.request()``, tolerant to both ELM signatures."""
        if _accepts(self.elm.request, 'cache'):
            return self.elm.request(cmd, cache=cache)
        return self.elm.request(cmd)

    def _set_can_addr(self, addr, brp=None, **extra):
        """``elm.set_can_addr()``, 2 or 3 parameters."""
        self._require_elm()
        ecu = self.addresses.ecu_dict(addr, brp=brp, **extra)
        if _accepts(self.elm.set_can_addr, 'canline'):
            return self.elm.set_can_addr(addr, ecu, self.canline)
        return self.elm.set_can_addr(addr, ecu)

    def _set_iso_addr(self, addr, **extra):
        """``elm.set_iso_addr()`` (KWP / ISO)."""
        self._require_elm()
        ecu = self.addresses.ecu_dict(addr, **extra)
        return self.elm.set_iso_addr(addr, ecu)

    def run_init_function(self, mname):
        """Port of ``mod_term.run_init_function``."""
        if mname in ('init_can_250', 'can250', 'init_can_500', 'can500'):
            self._require_elm()
            self.elm.init_can()
            if mname in ('init_can_250', 'can250'):
                self._set_can_addr(self.var['$addr'], brp='1')
            else:
                self._set_can_addr(self.var['$addr'])
        elif mname in ('init_iso_slow', 'slow', 'init_iso_fast', 'fast'):
            self._require_elm()
            self.elm.init_iso()
            if mname in ('init_iso_slow', 'slow'):
                self._set_iso_addr(self.var['$addr'], protocol='PRNA2000')
            else:
                self._set_iso_addr(self.var['$addr'])
        elif mname in ('init_can', 'init_iso'):
            # mod_term.py did not recognise those two forms; we accept them
            # because init.txt defines them as macros
            self._require_elm()
            getattr(self.elm, mname)()
        else:
            self.log(_("Unrecognized init command: %(name)s") % {"name": mname})

    def wait(self, seconds):
        """Wait (``wait``/``sleep``/``delay``).

        In simulation (``globals_.opt_demo``) the wait is skipped so the tests
        do not block outside a vehicle.
        """
        if self.globals_ is not None and getattr(self.globals_, 'opt_demo', False):
            return
        if self.wait_hook is not None:
            self.wait_hook(seconds)
            return
        time.sleep(seconds)

    # ------------------------------------------------------------------ #
    #  bit_cmd : set_bits / xor_bits / exit_if / goto_if / value          #
    # ------------------------------------------------------------------ #
    def bit_cmd(self, l, fnc='set_bits'):
        """Port of ``mod_term.bit_cmd`` (bit read/write).

        Syntaxes ::

            set_bits     <lid> <rsp_len> <offset> <mask> <value>
            xor_bits     <lid> <rsp_len> <offset> <mask> <value>
            exit_if      <lid> <rsp_len> <offset> <mask> <value>
            exit_if_not  <lid> <rsp_len> <offset> <mask> <value>
            goto_if      <lid> <rsp_len> <offset> <mask> <value> <label>
            goto_if_not  <lid> <rsp_len> <offset> <mask> <value> <label>
            value        <lid> <rsp_len> <offset> <mask> [step offset divider]
        """
        if fnc not in ('set_bits', 'xor_bits', 'exit_if', 'exit_if_not',
                       'goto_if', 'goto_if_not', 'value'):
            self.log(_("ERROR: Unknown function"))
            return

        error_msg = ''
        par = l.strip().split(' ')

        if fnc in ('set_bits', 'xor_bits', 'exit_if', 'exit_if_not'):
            error_msg = BIT_CMD_ERROR_1
            if len(par) != 5:
                self.log(error_msg)
                return

        if fnc in ('goto_if', 'goto_if_not'):
            error_msg = BIT_CMD_ERROR_2
            if len(par) != 6:
                self.log(error_msg)
                return

        if fnc in ('value',):
            error_msg = BIT_CMD_ERROR_3
            if len(par) == 4:
                par = par + ['1', '0', '1']
            if len(par) != 7:
                self.log(error_msg)
                return

        go = ''
        stp = ofs = div = '1'
        try:
            lid = par[0].strip()
            lng = int(par[1].strip())
            off = int(par[2].strip()) - 1
            mask = par[3].strip()
            val = par[4].strip()
            if fnc in ('goto_if', 'goto_if_not'):
                go = par[5].strip()
            if fnc in ('value',):
                val = '0' * len(mask)
                stp = par[4].strip()
                ofs = par[5].strip()
                div = par[6].strip()
        except (IndexError, ValueError):
            self.log(error_msg)
            return

        if len(lid) in (2, 4) and 0 <= off <= lng:
            if fnc not in ('value',) and (len(mask) != len(val)):
                self.log(error_msg)
                return
        else:
            self.log(error_msg)
            return

        if len(lid) == 2:      # KWP
            rcmd = '21' + lid
        else:                  # CAN
            rcmd = '22' + lid

        rsp = self.term_cmd(rcmd)
        rsp = rsp.replace(' ', '')[:lng * 2].upper()

        if fnc not in ('value',):
            self.log(_("read  value: ") + rsp)

        if len(rsp) != lng * 2:
            self.log(_("ERROR: Length is unexpected"))
            if fnc.startswith('exit'):
                raise MacroExit()
            return

        if not all(c in string.hexdigits for c in rsp):
            if fnc.startswith('exit'):
                raise MacroExit()
            self.log(_("ERROR: Wrong simbol in response"))
            return

        pos_rsp = ('6' + rcmd[1:]).upper()
        if not rsp.startswith(pos_rsp):
            if fnc.startswith('exit'):
                raise MacroExit()
            self.log(_("ERROR: Not positive response"))
            return

        diff = 0
        i = 0
        int_val = 0
        while i < len(mask) // 2:
            c_by = int(rsp[(off + i) * 2:(off + i) * 2 + 2], 16)
            c_ma = int(mask[i * 2:i * 2 + 2], 16)
            c_va = int(val[i * 2:i * 2 + 2], 16)

            if fnc == 'xor_bits':
                n_by = c_by ^ (c_va & c_ma)
            elif fnc == 'set_bits':
                n_by = (c_by & ~c_ma) | c_va
            else:
                n_by = c_by & c_ma
                int_val = int_val * 256 + n_by
                if (c_by & c_ma) != (c_va & c_ma):
                    diff += 1
                i += 1
                continue

            str_n_by = hex(n_by & 0xFF).upper()[2:].zfill(2)

            n_rsp = rsp[0:(off + i) * 2] + str_n_by + rsp[(off + i + 1) * 2:]
            rsp = n_rsp
            i += 1

        if fnc == 'exit_if':
            if diff == 0:
                self.log(_("Match. Exit"))
                raise MacroExit()
            self.log(_("Not match. Continue"))
            return

        if fnc == 'exit_if_not':
            if diff != 0:
                self.log(_("Not match. Exit"))
                raise MacroExit()
            self.log(_("Match. Continue"))
            return

        if fnc == 'goto_if':
            if diff == 0:
                self.log(_("Match. goto: ") + go)
                return go
            self.log(_("Not match. Continue"))
            return

        if fnc == 'goto_if_not':
            if diff != 0:
                self.log(_("Not match. goto: ") + go)
                return go
            self.log(_("Match. Continue"))
            return

        if fnc == 'value':
            res = (int_val * float(stp) + float(ofs)) / float(div)
            self.var['$rawValue'] = str(int_val)
            self.var['$scaledValue'] = str(res)
            self.var['$hexValue'] = hex(int_val)[2:].upper()
            self.log(_("# LID(%(lid)s) $rawValue = %(raw)s  $scaledValue = %(scaled)s  "
                      "$hexValue = %(hex)s")
                     % {"lid": lid, "raw": self.var['$rawValue'],
                        "scaled": self.var['$scaledValue'],
                        "hex": self.var['$hexValue']})
            return

        if rsp[:2] == '61':
            wcmd = '3B' + rsp[2:]
        elif rsp[:2] == '62':
            wcmd = '2E' + rsp[2:]
        else:
            # mod_term.py left wcmd undefined here (UnboundLocalError)
            self.log(_("ERROR: unexpected positive response: %(rsp)s") % {"rsp": rsp})
            return

        self.log(_("write value: ") + wcmd)
        self.log(self.term_cmd(wcmd))
