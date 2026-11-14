import pytest

from ddt4all.core.ecu.data_item import DataItem
from ddt4all.core.ecu.ecu_data import EcuData


@pytest.mark.parametrize(
    ("response", "bitscount", "expected"),
    [
        ("72 0B", 16, "0b72"),
        ("11 22 33", 24, "332211"),
        ("11 22 33 44", 32, "44332211"),
    ],
)
def test_get_hex_value_little_endian_reverses_bytes(response, bitscount, expected):
    data = EcuData({"bitscount": bitscount})
    item = DataItem({"firstbyte": 1, "endian": "Little"}, "")

    assert data.getHexValue(response, item, "Big") == expected


def test_get_hex_value_data_item_endian_overrides_request_endian():
    data = EcuData({"bitscount": 16})
    little_item = DataItem({"firstbyte": 1, "endian": "Little"}, "")
    big_item = DataItem({"firstbyte": 1, "endian": "Big"}, "")

    assert data.getHexValue("72 0B", little_item, "Big") == "0b72"
    assert data.getHexValue("72 0B", big_item, "Little") == "720b"


def test_get_display_value_decodes_signed_little_endian_sensor_value():
    data = EcuData({"bitscount": 16, "bytescount": 2, "scaled": True, "signed": True})
    item = DataItem({"firstbyte": 1, "endian": "Little"}, "Atmospheric_pressure")

    assert data.getDisplayValue("D9 03", item, "Big") == "985"


def test_get_hex_value_decodes_demo_21a2_value_at_byte_seven():
    data = EcuData({"bitscount": 16})
    item = DataItem({"firstbyte": 7, "endian": "Little"}, "")
    response = "61 A2 00 00 00 00 72 0B" + " 00" * 62

    assert data.getHexValue(response, item, "Big") == "0b72"


def test_get_hex_value_little_endian_respects_bit_offset():
    data = EcuData({"bitscount": 8})
    item = DataItem(
        {"firstbyte": 1, "bitoffset": 7, "endian": "Little"},
        "",
    )

    assert data.getHexValue("FF 01", item, "Big") == "fe"
    assert data.getHexValue("FF", item, "Big") is None
