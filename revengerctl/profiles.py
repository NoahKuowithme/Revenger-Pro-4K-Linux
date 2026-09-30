from __future__ import annotations

import json
from pathlib import Path

from .protocol import DEFAULT_STAGES, MouseState

CONFIG_DIR = Path.home() / ".config" / "revenger-pro-4k"
PROFILE_PATH = CONFIG_DIR / "profile.json"


def load_profile(state: MouseState) -> MouseState:
    if not PROFILE_PATH.exists():
        return state
    try:
        data = json.loads(PROFILE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return state
    stages = data.get("dpi_stages")
    if isinstance(stages, list) and 1 <= len(stages) <= 5:
        state.dpi_stages = [int(x) for x in stages]
    else:
        state.dpi_stages = list(DEFAULT_STAGES)
    state.active_stage = int(data.get("active_stage", state.active_stage))
    state.polling_hz = int(data.get("polling_hz", state.polling_hz))
    state.lod_mm = int(data.get("lod_mm", state.lod_mm))
    state.angle_snapping = bool(data.get("angle_snapping", state.angle_snapping))
    state.motion_sync = bool(data.get("motion_sync", state.motion_sync))
    state.debounce_ms = int(data.get("debounce_ms", state.debounce_ms))
    return state


def save_profile(state: MouseState) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "dpi_stages": state.dpi_stages,
        "active_stage": state.active_stage,
        "polling_hz": state.polling_hz,
        "lod_mm": state.lod_mm,
        "angle_snapping": state.angle_snapping,
        "motion_sync": state.motion_sync,
        "debounce_ms": state.debounce_ms,
    }
    PROFILE_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    return PROFILE_PATH
