#!/usr/bin/env python3
"""CLI for Revenger Pro 4K on Linux."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from revengerctl.apply import apply, refresh  # noqa: E402
from revengerctl.device import list_revenger_interfaces  # noqa: E402
from revengerctl.profiles import save_profile  # noqa: E402
from revengerctl.protocol import POLLING_CODES  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="revengerctl", description="Revenger Pro 4K Linux companion")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show connection and last-known settings")
    sub.add_parser("probe", help="List hidraw interfaces for this mouse")
    sub.add_parser("apply", help="Write current profile to the mouse")

    p_dpi = sub.add_parser("dpi", help="Set one DPI stage (1-5) and save")
    p_dpi.add_argument("stage", type=int)
    p_dpi.add_argument("value", type=int)

    p_poll = sub.add_parser("polling", help="Set polling rate and save")
    p_poll.add_argument("hz", type=int, choices=sorted(POLLING_CODES))

    args = parser.parse_args(argv)
    state = refresh()

    if args.cmd == "probe":
        ifaces = list_revenger_interfaces()
        if not ifaces:
            print("No Revenger Pro 4K hidraw nodes found.")
            return 1
        for iface in ifaces:
            kind = "control" if iface.is_control else ("mouse" if iface.is_mouse else "other")
            print(f"{iface.path}  {iface.id_str}  {iface.name}  desc={iface.report_len}B  [{kind}]")
        return 0

    if args.cmd == "status":
        print(f"connected: {state.connected}")
        print(f"name:      {state.name}")
        print(f"usb:       {state.vid_pid or '-'}")
        print(f"hidraw:    {state.hidraw or '-'}")
        print(f"access:    {'ok' if state.access_ok else state.access_error or 'no'}")
        print(f"dpi:       {state.dpi_stages}  (stage {state.active_stage + 1})")
        print(f"polling:   {state.polling_hz} Hz")
        print(f"lod:       {state.lod_mm} mm")
        print(f"debounce:  {state.debounce_ms} ms")
        print(f"battery:   {state.battery if state.battery is not None else 'n/a'}")
        if state.feature06:
            print(f"feature06: {state.feature06.hex()}")
        return 0 if state.connected else 1

    if args.cmd == "dpi":
        if not 1 <= args.stage <= 5:
            print("Stage must be 1-5", file=sys.stderr)
            return 2
        state.dpi_stages[args.stage - 1] = args.value
        save_profile(state)
        if state.access_ok:
            apply(state)
            print(f"Set DPI stage {args.stage} to {args.value} and wrote to device.")
        else:
            print(f"Saved DPI stage {args.stage}={args.value}. Device access: {state.access_error}")
        return 0

    if args.cmd == "polling":
        state.polling_hz = args.hz
        save_profile(state)
        if state.access_ok:
            apply(state)
            print(f"Set polling to {args.hz} Hz and wrote to device.")
        else:
            print(f"Saved polling {args.hz} Hz. Device access: {state.access_error}")
        return 0

    if args.cmd == "apply":
        save_profile(state)
        path = apply(state)
        print(f"Wrote settings to {path}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
