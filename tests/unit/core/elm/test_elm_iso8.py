"""Regression tests for ELM ISO8 initialization (issue #1928).

Verifies that set_iso8_addr programs the slow-init address with AT IIA
before issuing AT SI, so an ECU sitting at an address other than the ELM
default (33 / 0x21) can answer the 5 baud init.
"""

from types import SimpleNamespace


class FakeELM:
    """Minimal stand-in for ELM capturing the AT command sequence."""

    def __init__(self):
        self.currentprotocol = ""
        self.currentaddress = ""
        self.currentsubprotocol = ""
        self.lf = 0  # matches ELM.lf class default (0 == no log file)
        self.cmd_log = []

    def cmd(self, command, serviceDelay="0"):
        self.cmd_log.append(command.upper())
        return "OK"


def test_set_iso8_addr_sends_at_iia_before_at_si():
    """AT IIA <addr> must precede AT SI for ISO8 slow init."""
    from ddt4all.core.elm.elm import ELM

    elm = FakeELM()
    # Bind the real method onto the fake instance.
    ELM.set_iso8_addr(elm, "7A", {"protocol": "ISO8", "ecuname": "SAFIR"})

    # Address tracking must be updated.
    assert elm.currentprotocol == "iso8"
    assert elm.currentaddress == "7A"
    assert elm.currentsubprotocol == "ISO8"

    # The command sequence must contain AT IIA 7A before AT SI.
    assert "AT IIA 7A" in elm.cmd_log, elm.cmd_log
    iia_index = elm.cmd_log.index("AT IIA 7A")
    si_index = elm.cmd_log.index("AT SI")
    assert iia_index < si_index, (
        "AT IIA must come before AT SI: %s" % elm.cmd_log
    )


def test_set_iso8_addr_early_return_when_already_configured():
    """No commands are emitted when protocol/address/subprotocol already match."""
    from ddt4all.core.elm.elm import ELM

    elm = FakeELM()
    elm.currentprotocol = "iso8"
    elm.currentaddress = "7A"
    elm.currentsubprotocol = "ISO8"
    ELM.set_iso8_addr(elm, "7A", {"protocol": "ISO8", "ecuname": "SAFIR"})
    assert elm.cmd_log == [], elm.cmd_log


def test_safe_commands_contains_service_33():
    """SID 0x33 must be in safe_commands so plain read requests (e.g. Safir
    live data 33 50 / 33 51) are not blocked outside expert mode."""
    import ddt4all.options as options

    assert "33" in options.safe_commands, options.safe_commands