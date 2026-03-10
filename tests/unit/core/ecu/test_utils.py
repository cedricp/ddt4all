# tests/unit/core/ecu/test_utils.py
from __future__ import annotations

import xml.dom.minidom

from ddt4all.core.ecu.utils import cleanhtml, getChildNodesByName, hex16_tosigned, hex8_tosigned


def test_hex8_tosigned():
    assert hex8_tosigned(0x00) == 0
    assert hex8_tosigned(0x7F) == 127
    assert hex8_tosigned(0x80) == -128
    assert hex8_tosigned(0xFF) == -1


def test_hex16_tosigned():
    assert hex16_tosigned(0x0000) == 0
    assert hex16_tosigned(0x7FFF) == 32767
    assert hex16_tosigned(0x8000) == -32768
    assert hex16_tosigned(0xFFFF) == -1


def test_cleanhtml_strips_tags():
    assert cleanhtml("<b>Hello</b> <i>world</i>") == "Hello world"


def test_getChildNodesByName_filters_elements():
    doc = xml.dom.minidom.parseString("<root><Target/><Other/><Target/><Target><Child/></Target></root>")
    root = doc.documentElement
    found = getChildNodesByName(root, "Target")
    assert len(found) == 3
    assert all(n.localName == "Target" for n in found)
