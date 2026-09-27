"""Compx vendor HID used by the Revenger Pro 4K dongle.

The control interface (hidraw, report descriptor ~150 bytes) exposes:

* Feature report 0x06 — 7-byte payload (status / battery-style reads)
* Output/input report 0x08 — 16-byte payload (configuration)

Packet layout matches other Compx PAW3395 4K OEM mice (same VID 0x3554
family). Commands are original builders for this app, sized to the HID
descriptor captured from Noah's dongle (3554:f5de).
"""

from __future__ import annotations

from dataclasses import dataclass, field

REPORT_OUT = 0x08
REPORT_FEATURE = 0x06
OUT_LEN = 17  # report id + 16 bytes
FEATURE_LEN = 8  # report id + 7 bytes

POLLING_CODES = {
    125: 0x08,
    250: 0x04,
    500: 0x02,
    1000: 0x01,
    2000: 0x11,
    4000: 0x12,
}
POLLING_FROM_CODE = {code: hz for hz, code in POLLING_CODES.items()}

DPI_MIN = 50
DPI_MAX = 26000
DPI_STEP = 50
STAGE_COUNT = 5
DEFAULT_STAGES = (400, 800, 1600, 3200, 6400)


def _checksum(data: bytes) -> int:
    return sum(data) & 0xFF


def _out(cmd: int, args: bytes = b"") -> bytes:
    body = bytearray(16)
    body[0] = cmd
    body[1 : 1 + len(args)] = args[:15]
    pkt = bytes([REPORT_OUT]) + bytes(body)
    # Last byte is a simple additive checksum over the 16-byte body
    # excluding itself (common Compx pattern).
    chk = _checksum(pkt[1:16])
    return pkt[:16] + bytes([chk])


def encode_dpi(dpi: int) -> tuple[int, int]:
    dpi = max(DPI_MIN, min(DPI_MAX, int(dpi)))
    dpi -= dpi % DPI_STEP
    return dpi & 0xFF, (dpi >> 8) & 0xFF


def decode_dpi(lo: int, hi: int) -> int:
    return int(lo | (hi << 8))


def set_polling(hz: int) -> bytes:
    if hz not in POLLING_CODES:
        raise ValueError(f"Unsupported polling rate: {hz}")
    return _out(0x04, bytes([POLLING_CODES[hz]]))


def set_dpi_stage(stage: int, dpi: int) -> bytes:
    if not 0 <= stage < STAGE_COUNT:
        raise ValueError("DPI stage must be 0-4")
    lo, hi = encode_dpi(dpi)
    return _out(0x07, bytes([stage + 1, lo, hi]))


def set_active_stage(stage: int) -> bytes:
    if not 0 <= stage < STAGE_COUNT:
        raise ValueError("DPI stage must be 0-4")
    return _out(0x0A, bytes([stage + 1]))


def set_lod(mm: int) -> bytes:
    # 1 mm or 2 mm lift-off, typical Pixart 3395.
    code = 0x01 if mm <= 1 else 0x02
    return _out(0x0B, bytes([code]))


def set_debounce_ms(ms: int) -> bytes:
    allowed = (0, 1, 2, 4, 8)
    if ms not in allowed:
        raise ValueError("Debounce must be 0, 1, 2, 4, or 8 ms")
    return _out(0x0C, bytes([ms]))


def request_status() -> bytes:
    return bytes([REPORT_FEATURE] + [0] * (FEATURE_LEN - 1))


@dataclass
class MouseState:
    connected: bool = False
    name: str = "Revenger Pro 4K"
    vid_pid: str = ""
    hidraw: str = ""
    access_ok: bool = False
    access_error: str = ""
    dpi_stages: list[int] = field(default_factory=lambda: list(DEFAULT_STAGES))
    active_stage: int = 1
    polling_hz: int = 1000
    lod_mm: int = 1
    debounce_ms: int = 0
    battery: int | None = None
    feature06: bytes = b""

    @property
    def dpi(self) -> int:
        if 0 <= self.active_stage < len(self.dpi_stages):
            return self.dpi_stages[self.active_stage]
        return self.dpi_stages[0]


def parse_feature06(raw: bytes, state: MouseState) -> MouseState:
    state.feature06 = raw
    if len(raw) >= 8:
        # Heuristic: some Compx firmwares put battery in byte 6 or 7.
        for index in (6, 7, 5, 4):
            value = raw[index]
            if 1 <= value <= 100:
                state.battery = value
                break
        code = raw[3] if len(raw) > 3 else 0
        if code in POLLING_FROM_CODE:
            state.polling_hz = POLLING_FROM_CODE[code]
    return state


def parse_input08(raw: bytes, state: MouseState) -> MouseState:
    if len(raw) < 8 or raw[0] != REPORT_OUT:
        return state
    cmd = raw[1]
    if cmd == 0x0A:
        stage = raw[6] if len(raw) > 6 else raw[2]
        if 1 <= stage <= STAGE_COUNT:
            state.active_stage = stage - 1
    return state
