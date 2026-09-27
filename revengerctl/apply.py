"""Apply settings to the mouse and refresh live status."""

from __future__ import annotations

from .device import HidRaw, find_any, find_control, list_revenger_interfaces
from .protocol import (
    FEATURE_LEN,
    MouseState,
    parse_feature06,
    request_status,
    set_active_stage,
    set_debounce_ms,
    set_dpi_stage,
    set_lod,
    set_polling,
)
from .profiles import load_profile


def refresh() -> MouseState:
    state = MouseState()
    ifaces = list_revenger_interfaces()
    control = find_control() or find_any()
    if not control:
        state.connected = False
        return load_profile(state)
    state.connected = True
    state.name = control.name or state.name
    state.vid_pid = control.id_str
    state.hidraw = control.path
    load_profile(state)
    try:
        with HidRaw(control.path) as hid:
            state.access_ok = True
            try:
                raw = hid.get_feature(request_status()[0], FEATURE_LEN)
                parse_feature06(raw, state)
            except OSError:
                pass
    except PermissionError:
        state.access_ok = False
        state.access_error = (
            f"Cannot open {control.path}. Install the udev rule so your user can use hidraw."
        )
    except OSError as exc:
        state.access_ok = False
        state.access_error = str(exc)
    return state


def apply(state: MouseState) -> str:
    control = find_control()
    if control is None:
        raise RuntimeError("Revenger Pro 4K control interface not found. Plug in the 4K dongle.")
    with HidRaw(control.path) as hid:
        hid.write_output(set_polling(state.polling_hz))
        for index, dpi in enumerate(state.dpi_stages):
            hid.write_output(set_dpi_stage(index, dpi))
        hid.write_output(set_active_stage(state.active_stage))
        hid.write_output(set_lod(state.lod_mm))
        hid.write_output(set_debounce_ms(state.debounce_ms))
        try:
            hid.set_feature(request_status())
        except OSError:
            pass
    return control.path
