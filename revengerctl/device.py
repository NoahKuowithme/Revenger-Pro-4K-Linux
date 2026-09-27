"""Find the Revenger Pro 4K control hidraw node and talk HID reports."""

from __future__ import annotations

import array
import fcntl
import os
from dataclasses import dataclass
from pathlib import Path

VID = 0x3554
PIDS = {0xF5DC, 0xF5DE, 0xF5DF}
ONE_K_PID = 0xF5DC
FOUR_K_PID = 0xF5DF

# hidraw ioctl: _IOC(_IOC_READ|_IOC_WRITE, 'H', 0x06/0x07, len)
def _hidioc_feature(set_not_get: bool, length: int) -> int:
    nr = 0x06 if set_not_get else 0x07
    return 0xC0004800 | (length << 16) | nr


@dataclass(frozen=True)
class HidInterface:
    path: str
    index: int
    vendor: int
    product: int
    name: str
    phys: str
    report_len: int

    @property
    def is_control(self) -> bool:
        # Vendor collection with feature 0x06 (7 bytes) + output 0x08 (16 bytes).
        return self.report_len >= 140

    @property
    def is_mouse(self) -> bool:
        return 70 <= self.report_len <= 100

    @property
    def id_str(self) -> str:
        return f"{self.vendor:04x}:{self.product:04x}"


def _parse_uevent(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = value
    return data


def list_revenger_interfaces() -> list[HidInterface]:
    found: list[HidInterface] = []
    hidraw = Path("/sys/class/hidraw")
    if not hidraw.exists():
        return found
    for node in sorted(hidraw.iterdir(), key=lambda item: int(item.name[6:])):
        uevent = node / "device" / "uevent"
        desc = node / "device" / "report_descriptor"
        if not uevent.exists() or not desc.exists():
            continue
        info = _parse_uevent(uevent)
        hid_id = info.get("HID_ID", "")
        parts = hid_id.split(":")
        if len(parts) != 3:
            continue
        vendor = int(parts[1], 16)
        product = int(parts[2], 16)
        name = info.get("HID_NAME", "")
        if vendor != VID or product not in PIDS:
            if "revenger" not in name.lower():
                continue
        found.append(
            HidInterface(
                path=f"/dev/{node.name}",
                index=int(node.name.replace("hidraw", "")),
                vendor=vendor,
                product=product,
                name=name,
                phys=info.get("HID_PHYS", ""),
                report_len=len(desc.read_bytes()),
            )
        )
    return found


def find_control() -> HidInterface | None:
    matches = [iface for iface in list_revenger_interfaces() if iface.is_control]
    if not matches:
        return None
    return next((iface for iface in matches if iface.product == FOUR_K_PID), matches[0])


def find_4k_control() -> HidInterface | None:
    return next(
        (
            iface
            for iface in list_revenger_interfaces()
            if iface.product == FOUR_K_PID and iface.is_control
        ),
        None,
    )


def find_1k_control() -> HidInterface | None:
    return next(
        (
            iface
            for iface in list_revenger_interfaces()
            if iface.product == ONE_K_PID and iface.is_control
        ),
        None,
    )


def find_any() -> HidInterface | None:
    ifaces = list_revenger_interfaces()
    return find_control() or (ifaces[0] if ifaces else None)


class HidRaw:
    def __init__(self, path: str) -> None:
        self.path = path
        self._fd = os.open(path, os.O_RDWR)

    def close(self) -> None:
        if self._fd >= 0:
            os.close(self._fd)
            self._fd = -1

    def __enter__(self) -> "HidRaw":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def get_feature(self, report_id: int, length: int) -> bytes:
        buf = array.array("B", [report_id] + [0] * (length - 1))
        fcntl.ioctl(self._fd, _hidioc_feature(False, length), buf, True)
        return bytes(buf)

    def set_feature(self, payload: bytes) -> None:
        buf = array.array("B", payload)
        fcntl.ioctl(self._fd, _hidioc_feature(True, len(buf)), buf, True)

    def write_output(self, payload: bytes) -> int:
        return os.write(self._fd, payload)

    def read(self, length: int = 64) -> bytes:
        return os.read(self._fd, length)

    def fileno(self) -> int:
        return self._fd
