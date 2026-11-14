from types import SimpleNamespace

import usb.backend.libusb1

from ddt4all.core.usbdevice import usb_can


def test_frozen_macos_app_uses_bundled_libusb(monkeypatch, tmp_path):
    executable = tmp_path / "DDT4ALL.app" / "Contents" / "MacOS" / "DDT4ALL"
    libusb = tmp_path / "DDT4ALL.app" / "Contents" / "Frameworks" / "libusb-1.0.0.dylib"
    libusb.parent.mkdir(parents=True)
    libusb.touch()

    calls = {}
    monkeypatch.setattr(
        usb_can,
        "sys",
        SimpleNamespace(platform="darwin", frozen=True, executable=str(executable)),
    )
    monkeypatch.setattr(
        usb.backend.libusb1,
        "get_backend",
        lambda **kwargs: calls.update(kwargs) or "backend",
    )

    assert usb_can._get_libusb_backend() == "backend"
    assert calls["find_library"]("usb-1.0") == str(libusb)
