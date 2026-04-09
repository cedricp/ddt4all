import json

import ddt4all.options as options
from ddt4all.core.ecu.ecu_file import EcuFile



def test_ecu_file_loads_xml_and_exercises_main_paths(dummy_ecu_file):

    ecu = EcuFile(str(dummy_ecu_file(type="xml")), isfile=True)

    assert ecu.ecuname == "TEST_ECU"
    assert ecu.ecu_protocol == "CAN"
    assert ecu.baudrate == 250000
    assert ecu.ecu_send_id == "7E0"
    assert ecu.ecu_recv_id == "7E8"
    assert ecu.funcaddr == "1A"
    assert ecu.funcname == "Injection"
    assert ecu.endianness == "Little"

    assert ecu.projects == ["PROJECT_A", "PROJECT_B"]
    assert ecu.autoidents == [
        {
            "diagversion": "10",
            "supplier": "ABC",
            "soft": "1234",
            "version": "01",
        },
        {
            "diagversion": "11",
            "supplier": "XYZ",
            "soft": "5678",
            "version": "02",
        },
    ]

    assert "DEVICE_1" in ecu.devices
    device = ecu.devices["DEVICE_1"]
    assert device.name == "DEVICE_1"
    assert device.dtc == 4660
    assert device.dtctype == 2
    assert device.devicedata == {"State": "FF"}

    assert "ReadVIN" in ecu.requests
    

    assert "VIN" in ecu.data
    assert "Mode" in ecu.data

    vin_data = ecu.data["VIN"]
    assert vin_data.name == "VIN"
    assert vin_data.description == "Vehicle identification"
    assert vin_data.comment == "<b>VIN comment</b>"
    assert vin_data.byte is True
    assert vin_data.bytesascii is True
    assert vin_data.bytescount == 17
    assert vin_data.bitscount == 136

    mode_data = ecu.data["Mode"]
    assert mode_data.name == "Mode"
    assert mode_data.bitscount == 8
    assert mode_data.bytescount == 1
    assert mode_data.lists == {1: "ON", 2: "OFF"}
    assert mode_data.items == {"ON": 1, "OFF": 2}


############""


    dumped_json = ecu.dumpJson()
    dumped = json.loads(dumped_json)

    assert dumped["ecuname"] == "TEST_ECU"
    assert dumped["autoidents"] == ecu.autoidents
    assert dumped["obd"]["protocol"] == "CAN"
    assert dumped["obd"]["send_id"] == "7E0"
    assert dumped["obd"]["recv_id"] == "7E8"
    assert dumped["obd"]["baudrate"] == 250000
    assert dumped["obd"]["funcaddr"] == "1A"
    assert dumped["obd"]["funcname"] == "Injection"
    assert dumped["endian"] == "Little"

    assert dumped["devices"] == [
        {
            "dtc": 4660,
            "dtctype": 2,
            "devicedata": {"State": "FF"},
            "name": "DEVICE_1",
        }
    ]

    assert dumped["requests"] == [
        {
            "minbytes": 3,
            "shiftbytescount": 1,
            "replybytes": "62F190",
            "manualsend": True,
            "sentbytes": "22F190",
            "name": "ReadVIN",
            "deny_sds": ["engineering", "supplier"],
            "sendbyte_dataitems": {
                "VIN": {
                    "firstbyte": 1,
                    "ref": False,
                }
            },
            "receivebyte_dataitems": {
                "VIN": {
                    "firstbyte": 1,
                    "ref": False,
                }
            },
        }
    ]

    assert dumped["data"]["VIN"]["bytescount"] == 17
    assert dumped["data"]["VIN"]["comment"] == "VIN comment"
    assert dumped["data"]["Mode"]["lists"] == {"1": "ON", "2": "OFF"}


def test_ecu_file_get_requests(dummy_ecu_file):

    ecu = EcuFile(str(dummy_ecu_file(type="xml")), isfile=True)


    request = ecu.get_request("ReadVIN")

    assert request is ecu.get_request("readvin")
    assert ecu.get_request("unknown") is None

    assert request.name == "ReadVIN"
    assert request.manualsend is True
    assert request.shiftbytescount == 1
    assert request.replybytes == "62F190"
    assert request.sentbytes == "22F190"
    assert request.minbytes == 3
    assert sorted(request.dataitems.keys()) == ["VIN"]
    assert sorted(request.sendbyte_dataitems.keys()) == ["VIN"]
    assert request.sds["supplier"] is False
    assert request.sds["engineering"] is False
    assert request.sds["nosds"] is True
    assert request.sds["plant"] is True
    assert request.sds["aftersales"] is True


def test_ecu_file_dump_idents(dummy_ecu_file):

    ecu = EcuFile(str(dummy_ecu_file(type="xml")), isfile=True)

    dumped_idents = ecu.dump_idents()

    assert dumped_idents == {
        "address": "1A",
        "group": "Injection",
        "protocol": "CAN",
        "projects": ["PROJECT_A", "PROJECT_B"],
        "ecuname": "TEST_ECU",
        "autoidents": [
            {
                "diagnostic_version": "10",
                "supplier_code": "ABC",
                "soft_version": "1234",
                "version": "01",
            },
            {
                "diagnostic_version": "11",
                "supplier_code": "XYZ",
                "soft_version": "5678",
                "version": "02",
            },
        ],
    }

def test_ecu_file_dump_json(dummy_ecu_file):

    ecu = EcuFile(str(dummy_ecu_file(type="xml")), isfile=True)


    dumped_json = ecu.dumpJson()
    dumped = json.loads(dumped_json)

    assert dumped["ecuname"] == "TEST_ECU"
    assert dumped["autoidents"] == ecu.autoidents
    assert dumped["obd"]["protocol"] == "CAN"
    assert dumped["obd"]["send_id"] == "7E0"
    assert dumped["obd"]["recv_id"] == "7E8"
    assert dumped["obd"]["baudrate"] == 250000
    assert dumped["obd"]["funcaddr"] == "1A"
    assert dumped["obd"]["funcname"] == "Injection"
    assert dumped["endian"] == "Little"

    assert dumped["devices"] == [
        {
            "dtc": 4660,
            "dtctype": 2,
            "devicedata": {"State": "FF"},
            "name": "DEVICE_1",
        }
    ]

    assert dumped["requests"] == [
        {
            "minbytes": 3,
            "shiftbytescount": 1,
            "replybytes": "62F190",
            "manualsend": True,
            "sentbytes": "22F190",
            "name": "ReadVIN",
            "deny_sds": ["engineering", "supplier"],
            "sendbyte_dataitems": {
                "VIN": {
                    "firstbyte": 1,
                    "ref": False,
                }
            },
            "receivebyte_dataitems": {
                "VIN": {
                    "firstbyte": 1,
                    "ref": False,
                }
            },
        }
    ]

    assert dumped["data"]["VIN"]["bytescount"] == 17
    assert dumped["data"]["VIN"]["comment"] == "VIN comment"
    assert dumped["data"]["Mode"]["lists"] == {"1": "ON", "2": "OFF"}


def test_ecu_file_connect_to_hardware(dummy_ecu_file, mocker):

    ecu = EcuFile(str(dummy_ecu_file(type="xml")), isfile=True)

    mock_elm = mocker.Mock()
    mocker.patch.object(options, "simulation_mode", False)
    mocker.patch.object(options, "elm", mock_elm)
    mocker.patch(
        "ddt4all.core.ecu.ecu_file.elm.get_can_addr",
        return_value="26",
    )

    result = ecu.connect_to_hardware(canline=1)

    assert result is True
    mock_elm.init_can.assert_called_once_with()
    mock_elm.set_can_addr.assert_called_once_with(
        "26",
        {
            "idTx": "7E0",
            "idRx": "7E8",
            "ecuname": "b'TEST_ECU'",
            "brp": "1",
        },
        1,
    )


def test_ecu_file_init_with_no_data_keeps_defaults():
    ecu = EcuFile(None)

    assert ecu.requests == {}
    assert ecu.devices == {}
    assert ecu.data == {}
    assert ecu.endianness == ""
    assert ecu.ecu_protocol == ""
    assert ecu.ecu_send_id == "00"
    assert ecu.ecu_recv_id == "00"
    assert ecu.fastinit is False
    assert ecu.kw1 == ""
    assert ecu.kw2 == ""
    assert ecu.funcname == ""
    assert ecu.funcaddr == "00"
    assert ecu.ecuname == ""
    assert ecu.projects == []
    assert ecu.autoidents == []
    assert ecu.baudrate == 0


def test_ecu_file_missing_xml_file_keeps_default_state(tmp_path):

    missing_file = tmp_path / "missing_ecu.xml"

    ecu = EcuFile(str(missing_file), isfile=True)

    assert ecu.ecuname == ""
    assert ecu.ecu_protocol == ""
    assert ecu.requests == {}
    assert ecu.devices == {}
    assert ecu.data == {}


def test_ecu_file_connect_to_hardware_can_simulation_mode_skips_elm_calls(dummy_ecu_file, mocker):

    ecu = EcuFile(str(dummy_ecu_file(type="xml")), isfile=True)
    mock_elm = mocker.Mock()
    mocker.patch.object(options, "simulation_mode", True)
    mocker.patch.object(options, "elm", mock_elm)

    result = ecu.connect_to_hardware(canline=1)

    assert result is True
    mock_elm.init_can.assert_not_called()
    mock_elm.set_can_addr.assert_not_called()


def test_ecu_file_connect_to_hardware_can_address_not_found_returns_false(dummy_ecu_file, mocker):

    ecu = EcuFile(str(dummy_ecu_file(type="xml")), isfile=True)
    mock_elm = mocker.Mock()
    mocker.patch.object(options, "simulation_mode", False)
    mocker.patch.object(options, "elm", mock_elm)
    mocker.patch(
        "ddt4all.core.ecu.ecu_file.elm.get_can_addr",
        return_value=None,
    )

    result = ecu.connect_to_hardware()

    assert result is False
    mock_elm.init_can.assert_not_called()
    mock_elm.set_can_addr.assert_not_called()


def test_ecu_file_connect_to_hardware_extended_can_uses_get_can_addr_ext(mocker, dummy_ecu_file):

    ecu = EcuFile(str(dummy_ecu_file(protocol="can_ext", type="xml")), isfile=True)
    mock_elm = mocker.Mock()
    get_can_addr = mocker.patch("ddt4all.core.ecu.ecu_file.elm.get_can_addr")
    get_can_addr_ext = mocker.patch(
        "ddt4all.core.ecu.ecu_file.elm.get_can_addr_ext",
        return_value="AB",
    )

    mocker.patch.object(options, "simulation_mode", False)
    mocker.patch.object(options, "elm", mock_elm)

    result = ecu.connect_to_hardware(canline=2)

    assert result is True
    get_can_addr.assert_not_called()
    get_can_addr_ext.assert_called_once_with(ecu.ecu_send_id)
    mock_elm.init_can.assert_called_once_with()
    mock_elm.set_can_addr.assert_called_once_with(
        "AB",
        {
            "idTx": ecu.ecu_send_id,
            "idRx": ecu.ecu_recv_id,
            "ecuname": "b'EXT_CAN_ECU'",
        },
        2,
    )


def test_ecu_file_loads_json_file(dummy_ecu_file):

    ecu = EcuFile(str(dummy_ecu_file(type="json")), isfile=True)

    assert ecu.ecuname == "JSON_ECU"
    assert ecu.ecu_protocol == "CAN"
    assert ecu.ecu_send_id == "7E0"
    assert ecu.ecu_recv_id == "7E8"
    assert ecu.baudrate == 250000
    assert ecu.funcaddr == "1A"
    assert ecu.funcname == "Injection"
    assert ecu.endianness == "Little"
    assert "DEVICE_1" in ecu.devices
    assert "ReadVIN" in ecu.requests
    assert "VIN" in ecu.data


def test_ecu_file_connect_to_hardware_kwp2000_fastinit(dummy_ecu_file, mocker):

    ecu = EcuFile(str(dummy_ecu_file(protocol="kwp", type="xml")), isfile=True)

    assert ecu.ecu_protocol == "KWP2000"
    assert ecu.fastinit is True
    assert ecu.kw1 == "81"
    assert ecu.kw2 == "82"

    mock_elm = mocker.Mock()
    mocker.patch.object(options, "simulation_mode", False)
    mocker.patch.object(options, "elm", mock_elm)
    mocker.patch.object(options, "opt_si", None)

    result = ecu.connect_to_hardware()

    assert result is True
    assert options.opt_si is False
    mock_elm.init_iso.assert_called_once_with()
    mock_elm.set_iso_addr.assert_called_once_with(
        "26",
        {
            "idTx": "",
            "idRx": "",
            "ecuname": "b'KWP_ECU'",
            "protocol": "KWP2000",
        },
    )


def test_ecu_file_connect_to_hardware_iso8(dummy_ecu_file, mocker):

    ecu = EcuFile(str(dummy_ecu_file(protocol="iso8", type="xml")), isfile=True)


    assert ecu.ecu_protocol == "ISO8"
    assert ecu.fastinit is False
    assert ecu.kw1 == "91"
    assert ecu.kw2 == "92"

    mock_elm = mocker.Mock()
    mocker.patch.object(options, "simulation_mode", False)
    mocker.patch.object(options, "elm", mock_elm)

    result = ecu.connect_to_hardware()

    assert result is True
    mock_elm.init_iso.assert_called_once_with()
    mock_elm.set_iso8_addr.assert_called_once_with(
        "27",
        {
            "idTx": "",
            "idRx": "",
            "ecuname": "b'ISO8_ECU'",
            "protocol": "ISO8",
        },
    )


def test_ecu_file_connect_to_hardware_unknown_protocol_returns_false():
    ecu = EcuFile(None)
    ecu.ecu_protocol = "UNKNOWN"

    assert ecu.connect_to_hardware() is False