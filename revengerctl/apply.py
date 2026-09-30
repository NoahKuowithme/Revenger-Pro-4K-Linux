"""Apply settings to the mouse and refresh live status."""

from __future__ import annotations

import time

from .device import HidRaw, find_any, find_control, list_revenger_interfaces
from .protocol import (
    FEATURE_LEN,
    MouseState,
    parse_feature06,
    request_status,
    set_active_stage,
    set_dpi_stage,
    set_angle_snapping,
    set_lod,
    set_motion_sync,
    set_polling,
)
from .profiles import load_profile

_REPORT_INTERVAL_SECONDS = 0.02


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


def _write_reports(reports: list[bytes]) -> str:
    control = find_control()
    if control is None:
        raise RuntimeError("Revenger Pro 4K control interface not found. Plug in the 4K dongle.")
    with HidRaw(control.path) as hid:
        for index, report in enumerate(reports):
            # UIX routes nonzero command reports (including WriteFlashData 0x07)
            # through HID SetFeature, not the interrupt-OUT WriteFile path.
            hid.set_feature(report)
            if index + 1 < len(reports):
                # Leave the receiver time to commit each flash record before
                # issuing the next one (the GUI's Apply sends several records).
                time.sleep(_REPORT_INTERVAL_SECONDS)
    return control.path


def apply_dpi_stage(stage: int, dpi: int) -> str:
    """Write a DPI stage and select it so the change is immediately testable."""
    return _write_reports([set_dpi_stage(stage, dpi), set_active_stage(stage)])


def apply_polling(hz: int) -> str:
    return _write_reports([set_polling(hz)])


def apply(state: MouseState) -> str:
    """Write performance and verified 3395 sensor settings.

    The device has five physical DPI slots. Unconfigured trailing slots repeat
    the last visible stage because the currently verified protocol does not
    expose an active-stage-count setting.
    """
    reports = [set_polling(state.polling_hz)]
    stages = list(state.dpi_stages[:5])
    if not stages:
        raise ValueError("At least one DPI stage is required")
    stages.extend([stages[-1]] * (5 - len(stages)))
    reports.extend(
        set_dpi_stage(index, dpi) for index, dpi in enumerate(stages)
    )
    reports.append(set_active_stage(state.active_stage))
    reports.extend([
        set_lod(state.lod_mm),
        set_angle_snapping(state.angle_snapping),
        set_motion_sync(state.motion_sync),
    ])
    return _write_reports(reports)
