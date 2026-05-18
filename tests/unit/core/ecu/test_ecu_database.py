import json
import zipfile

from ddt4all.core.ecu.ecu_database import EcuDatabase


def test_vehiclemap_keeps_full_project_codes_from_json_targets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    (json_dir / "test.json.targets").write_text(
        json.dumps(
            [
                {
                    "diagnostic_version": "01",
                    "supplier_code": "SUPPLIER",
                    "soft_version": "SOFT",
                    "version": "0001",
                    "group": "UCH",
                    "projects": ["X95PH2"],
                    "protocol": "CAN",
                    "address": "26",
                }
            ]
        )
    )

    database = EcuDatabase()

    assert database.vehiclemap == {"X95PH2": [("CAN", "26")]}


def test_vehiclemap_keeps_full_project_codes_from_zip_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dbdict = {
        "test.json": {
            "group": "UCH",
            "protocol": "CAN",
            "projects": ["X95PH2"],
            "address": "26",
            "ecuname": "Test ECU",
            "autoidents": [
                {
                    "diagnostic_version": "01",
                    "supplier_code": "SUPPLIER",
                    "soft_version": "SOFT",
                    "version": "0001",
                }
            ],
        }
    }
    with zipfile.ZipFile("ecu.zip", mode="w") as zf:
        zf.writestr("db.json", json.dumps(dbdict))

    database = EcuDatabase()

    assert database.vehiclemap == {"X95PH2": [("CAN", "26")]}


def test_vehiclemap_keeps_full_project_codes_from_xml_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ecus_dir = tmp_path / "ecus"
    ecus_dir.mkdir()
    (ecus_dir / "eculist.xml").write_text(
        """\
<ECUlist>
  <Function Address="38">
    <Target group="UCH" href="test.xml" Name="Test ECU">
      <Protocol>CAN</Protocol>
      <Projects>
        <X95PH2/>
      </Projects>
      <AutoIdents>
        <AutoIdent
          DiagVersion="01"
          Supplier="SUPPLIER"
          Soft="SOFT"
          Version="0001"
        />
      </AutoIdents>
    </Target>
  </Function>
</ECUlist>
"""
    )

    database = EcuDatabase()

    assert database.vehiclemap == {"X95PH2": [("CAN", "26")]}


def test_vehiclemap_does_not_truncate_project_codes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    database = EcuDatabase()
    database.vehiclemap = {}

    database.addVehicleMapEntry("X95PH2", "CAN", "26")

    assert database.vehiclemap == {"X95PH2": [("CAN", "26")]}
