"""HID report helpers for the COUGAR Revenger Pro 4K receiver.

Pairing and flash-write frames are derived from the Windows UIX 1.0.0.42
native HID DLL. The flash layout is for the Revenger Pro 4K's PixArt 3395.
"""

from __future__ import annotations

from dataclasses import dataclass, field

REPORT_OUT = 0x08
REPORT_FEATURE = 0x06
OUT_LEN = 17  # report id + 16 bytes
FEATURE_LEN = 8  # report id + 7 bytes

# UIX 1.0.0.42 identifies this mouse as CID 53 in Config.ini.
DEFAULT_PAIR_CID = 0x35

POLLING_CODES = {
    125: 0x08,
    250: 0x04,
    500: 0x02,
    1000: 0x01,
    2000: 0x10,
    4000: 0x20,
}
POLLING_FROM_CODE = {code: hz for hz, code in POLLING_CODES.items()}

DPI_MIN = 50
DPI_MAX = 26000
DPI_STEP = 50
STAGE_COUNT = 5
DEFAULT_STAGES = (800, 1200, 1600)


def _checksum(data: bytes) -> int:
    return sum(data) & 0xFF


def _out(cmd: int, args: bytes = b"") -> bytes:
    body = bytearray(16)
    body[0] = cmd
    body[1 : 1 + len(args)] = args[:15]
    pkt = bytes([REPORT_OUT]) + bytes(body)
    # Legacy experimental checksum. These non-pairing commands are unverified.
    chk = _checksum(pkt[1:16])
    return pkt[:16] + bytes([chk])


def _flash_write(address: int, data: bytes) -> bytes:
    """Build UIX WriteFlashData (0x07), including its 0x55 checksum."""
    if not 0 <= address <= 0xFFFF:
        raise ValueError("Flash address must fit in 16 bits")
    if not 1 <= len(data) <= 10:
        raise ValueError("Flash writes must contain 1-10 data bytes")
    body = bytearray(16)
    body[0] = REPORT_OUT
    body[1] = 0x07
    body[3:5] = address.to_bytes(2, "big")
    body[5] = len(data)
    body[6 : 6 + len(data)] = data
    return bytes(body) + bytes([(0x55 - sum(body)) & 0xFF])


def _flash_data_with_checksum(data: bytes) -> bytes:
    """Append the per-field checksum stored alongside UIX flash data."""
    return data + bytes([(0x55 - sum(data)) & 0xFF])


def _mouse_config_write(address: int, data: bytes) -> bytes:
    """Build UIX's two-byte MouseConfig flash record (address is little-endian)."""
    if not 0 <= address <= 0xFFFF:
        raise ValueError("Mouse config address must fit in 16 bits")
    if not 1 <= len(data) <= 10:
        raise ValueError("Mouse config writes must contain 1-10 data bytes")
    body = bytearray(16)
    body[0] = REPORT_OUT
    body[1] = 0x07
    body[4:6] = address.to_bytes(2, "little")
    body[6 : 6 + len(data)] = data
    return bytes(body) + bytes([(0x55 - sum(body)) & 0xFF])


def _usb_server_command(command: int, cid: int | None = None) -> bytes:
    """Build the 17-byte feature report used by UIX's dongle command queue."""
    body = bytearray(16)
    body[0] = REPORT_OUT
    body[1] = command
    if command == 0x05:  # EnterDonglePairOnlyCid
        if cid is None or not 0 <= cid <= 0xFF:
            raise ValueError("Pairing CID must be between 0 and 255")
        body[5] = 0x02
        body[8] = cid
    # HIDUsb.dll's checksum is 0x55 minus the sum of the first 16 bytes.
    return bytes(body) + bytes([(0x55 - sum(body)) & 0xFF])


def enter_dongle_pair(cid: int = DEFAULT_PAIR_CID) -> bytes:
    """UIX EnterDonglePairOnlyCid packet for the Revenger Pro 4K dongle."""
    return _usb_server_command(0x05, cid)


def read_dongle_pair_status() -> bytes:
    """UIX ReadDonglePairStatus request."""
    return _usb_server_command(0x06)


def parse_dongle_pair_status(report: bytes) -> int | None:
    """Return UIX pairing status (1=pending, 2=success, 3=failure).

    UIX's callback receives the response data separately from the six-byte
    command header, so hidraw's corresponding first data byte is report[6].
    Ignore unrelated, short, or checksum-invalid input reports.
    """
    if len(report) < OUT_LEN or report[0] != REPORT_OUT or report[1] != 0x06:
        return None
    frame = report[:OUT_LEN]
    if (sum(frame[:16]) + frame[16]) & 0xFF != 0x55:
        return None
    return frame[6]


def encode_dpi(dpi: int) -> tuple[int, int, int]:
    """Encode a 3395 DPI value as UIX xDPI, yDPI, and DPIex bytes."""
    dpi = int(dpi)
    if not DPI_MIN <= dpi <= DPI_MAX or dpi % DPI_STEP:
        raise ValueError(f"DPI must be {DPI_MIN}-{DPI_MAX} in steps of {DPI_STEP}")
    units = dpi // DPI_STEP - 1
    high = units >> 8
    # UIX stores the quotient's high bits in duplicated DPIex bit fields.
    dpi_ex = ((high & 0x03) << 2) | ((high & 0x03) << 6)
    low = units & 0xFF
    return low, low, dpi_ex


def decode_dpi(x_dpi: int, y_dpi: int, dpi_ex: int) -> int:
    """Decode the standard 3395 DPI representation (without special modes)."""
    if x_dpi != y_dpi:
        raise ValueError("X and Y DPI encodings differ")
    high = ((dpi_ex >> 2) & 0x03) | ((dpi_ex >> 6) & 0x03)
    units = (high << 8) | x_dpi
    return (units + 1) * DPI_STEP


def set_polling(hz: int) -> bytes:
    if hz not in POLLING_CODES:
        raise ValueError(f"Unsupported polling rate: {hz}")
    # UIX stores MouseConfig fields at 0x0200 + 2 * field index; each one-byte
    # value is followed by its field checksum. For reportRate, the resulting
    # frame also matches the zero-address/two-byte generic record on the wire.
    value = bytes([POLLING_CODES[hz]])
    return _mouse_config_write(0x0200, _flash_data_with_checksum(value))


def set_dpi_stage(stage: int, dpi: int) -> bytes:
    if not 0 <= stage < STAGE_COUNT:
        raise ValueError("DPI stage must be 0-4")
    # Each DPIConfig's xDPI/yDPI/DPIex occupies a four-byte flash record.
    encoded = bytes(encode_dpi(dpi))
    address = 0x000C + stage * 4
    return _flash_write(address, _flash_data_with_checksum(encoded))


def set_active_stage(stage: int) -> bytes:
    if not 0 <= stage < STAGE_COUNT:
        raise ValueError("DPI stage must be 0-4")
    # MouseConfig.currentDPI is a zero-based index at UIX flash address 0x0204.
    return _mouse_config_write(0x0204, _flash_data_with_checksum(bytes([stage])))


def set_lod(mm: int) -> bytes:
    """Set the UIX 3395 lift-detection selection (0=1 mm, 1=2 mm)."""
    if mm not in (1, 2):
        raise ValueError("Lift-off distance must be 1 or 2 mm")
    return _mouse_config_write(0x020A, _flash_data_with_checksum(bytes([mm - 1])))


def set_motion_sync(enabled: bool) -> bytes:
    return _mouse_config_write(0x020E, _flash_data_with_checksum(bytes([int(enabled)])))


def set_angle_snapping(enabled: bool) -> bytes:
    """Set UIX's linearCorrectionEnable (labelled Angle snapping)."""
    return _mouse_config_write(0x0212, _flash_data_with_checksum(bytes([int(enabled)])))


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
    angle_snapping: bool = False
    motion_sync: bool = False
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
