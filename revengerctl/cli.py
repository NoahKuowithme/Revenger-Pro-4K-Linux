#!/usr/bin/env python3
"""CLI for Revenger Pro 4K on Linux."""

from __future__ import annotations

import argparse
import select
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from revengerctl.apply import apply, apply_dpi_stage, apply_polling, refresh  # noqa: E402
from revengerctl.device import (  # noqa: E402
    HidRaw,
    find_1k_control,
    find_4k_control,
    list_revenger_interfaces,
)
from revengerctl.profiles import save_profile  # noqa: E402
from revengerctl.protocol import (  # noqa: E402
    DEFAULT_PAIR_CID,
    POLLING_CODES,
    encode_dpi,
    enter_dongle_pair,
    parse_dongle_pair_status,
    read_dongle_pair_status,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="revengerctl", description="Revenger Pro 4K Linux companion")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show connection and last-known settings")
    sub.add_parser("probe", help="List hidraw interfaces for this mouse")
    sub.add_parser("apply", help="Write current profile to the mouse")

    p_pair = sub.add_parser("pair", help="Pair the mouse with a selected wireless receiver")
    p_pair.add_argument(
        "--receiver",
        choices=("1k", "4k"),
        default="4k",
        help="target receiver: 1k is 2.4 GHz (3554:f5dc); 4k is high-polling (3554:f5df, default)",
    )
    p_pair.add_argument(
        "--cid",
        type=lambda value: int(value, 0),
        default=DEFAULT_PAIR_CID,
        help="mouse CID (default: UIX Revenger Pro 4K value 0x35)",
    )
    p_pair.add_argument("--timeout", type=float, default=60, help="pairing wait limit in seconds (default: 60)")
    p_pair.add_argument("--debug", action="store_true", help="print received HID reports as hex for diagnosis")
    p_pair.add_argument(
        "--yes",
        action="store_true",
        help="skip the prompt; put the mouse in pairing mode before starting this command",
    )

    p_dpi = sub.add_parser("dpi", help="Set and activate one DPI stage (1-5), then save")
    p_dpi.add_argument("stage", type=int)
    p_dpi.add_argument("value", type=int)

    p_poll = sub.add_parser("polling", help="Set polling rate and save")
    p_poll.add_argument("hz", type=int, choices=sorted(POLLING_CODES))

    args = parser.parse_args(argv)
    if args.cmd == "probe":
        ifaces = list_revenger_interfaces()
        if not ifaces:
            print("No Revenger Pro 4K hidraw nodes found.")
            return 1
        for iface in ifaces:
            kind = "control" if iface.is_control else ("mouse" if iface.is_mouse else "other")
            print(f"{iface.path}  {iface.id_str}  {iface.name}  desc={iface.report_len}B  [{kind}]")
        return 0

    if args.cmd == "pair":
        if args.timeout <= 0:
            print("Timeout must be greater than zero.", file=sys.stderr)
            return 2
        control = find_4k_control() if args.receiver == "4k" else find_1k_control()
        receiver_name = "4K" if args.receiver == "4k" else "2.4 GHz (1K)"
        receiver_pid = "3554:f5df" if args.receiver == "4k" else "3554:f5dc"
        if control is None:
            print(f"{receiver_name} receiver control HID interface not found ({receiver_pid}).", file=sys.stderr)
            return 1
        if not args.yes:
            if not sys.stdin.isatty():
                print("Interactive pairing needs a terminal; use --yes to start the receiver without prompting.", file=sys.stderr)
                return 2
            print(
                f"Leave only the {receiver_name} receiver connected. Turn the mouse on and place it "
                "within 10 cm. Hold middle-wheel + right + left together for about 3 seconds until the "
                "yellow pairing light flashes rapidly."
            )
            try:
                input("After the mouse light is flashing rapidly, press Enter to start receiver pairing (Ctrl-C cancels): ")
            except EOFError:
                print("Pairing cancelled before sending a command.", file=sys.stderr)
                return 2
        try:
            with HidRaw(control.path) as hid:
                hid.set_feature(enter_dongle_pair(args.cid))
                print(
                    f"Pairing started via {control.path} (CID 0x{args.cid:02x}); "
                    "the mouse should already be in pairing mode with its yellow light flashing rapidly. "
                    "Keep it within 10 cm of the receiver."
                )
                deadline = time.monotonic() + args.timeout
                next_status_request = time.monotonic() + 1.0
                pending_reported = False
                while time.monotonic() < deadline:
                    now = time.monotonic()
                    if now >= next_status_request:
                        hid.set_feature(read_dongle_pair_status())
                        next_status_request = now + 1.0

                    wait = max(
                        0.0,
                        min(
                            0.2,
                            next_status_request - time.monotonic(),
                            deadline - time.monotonic(),
                        ),
                    )
                    ready, _, _ = select.select([hid.fileno()], [], [], wait)
                    if not ready:
                        continue
                    report = hid.read()
                    if args.debug:
                        print(f"hidraw: {report.hex(' ')}")
                    status = parse_dongle_pair_status(report)
                    if status == 1 and not pending_reported:
                        print("Dongle reports pairing pending.")
                        pending_reported = True
                    elif status == 2:
                        print("Pairing succeeded.")
                        return 0
                    elif status == 3:
                        print(
                            "Dongle reports pairing failure (status 3). This is an explicit failure, "
                            "not a timeout. Before starting receiver pairing, put the mouse in "
                            "pairing mode by holding middle-wheel + right + left together until the yellow "
                            "light flashes rapidly; keep it within 10 cm and leave only the "
                            f"{receiver_name} receiver connected.",
                            file=sys.stderr,
                        )
                        return 1
                print(
                    "No success/failure report before timeout. The pairing-start request was sent; "
                    "check that the mouse was already in pairing mode before the receiver request, "
                    "then retry.",
                    file=sys.stderr,
                )
                return 1
        except PermissionError:
            print(
                f"Cannot open {control.path}; install the udev rule and replug the dongle.",
                file=sys.stderr,
            )
            return 1
        except (OSError, ValueError) as exc:
            print(f"Could not start pairing: {exc}", file=sys.stderr)
            return 1
        return 1

    state = refresh()

    if args.cmd == "status":
        print(f"connected: {state.connected}")
        print(f"name:      {state.name}")
        print(f"usb:       {state.vid_pid or '-'}")
        print(f"hidraw:    {state.hidraw or '-'}")
        print(f"access:    {'ok' if state.access_ok else state.access_error or 'no'}")
        print(
            f"dpi:       {state.dpi_stages}  "
            f"(profile active stage {state.active_stage + 1}; not read from mouse)"
        )
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
        try:
            encode_dpi(args.value)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        state.dpi_stages[args.stage - 1] = args.value
        state.active_stage = args.stage - 1
        if state.access_ok:
            try:
                apply_dpi_stage(args.stage - 1, args.value)
            except (OSError, RuntimeError, ValueError) as exc:
                print(f"Could not write DPI stage: {exc}", file=sys.stderr)
                return 1
        save_profile(state)
        if state.access_ok:
            print(
                f"Sent DPI stage {args.stage}={args.value} and active-stage write "
                f"requests to {state.hidraw}; verify the pointer speed changed."
            )
        else:
            print(f"Saved DPI stage {args.stage}={args.value}. Device access: {state.access_error}")
        return 0

    if args.cmd == "polling":
        state.polling_hz = args.hz
        if state.access_ok:
            try:
                apply_polling(args.hz)
            except (OSError, RuntimeError, ValueError) as exc:
                print(f"Could not write polling rate: {exc}", file=sys.stderr)
                return 1
        save_profile(state)
        if state.access_ok:
            print(
                f"Sent polling {args.hz} Hz write request to {state.hidraw}; "
                "confirm with a polling-rate measurement."
            )
        else:
            print(f"Saved polling {args.hz} Hz. Device access: {state.access_error}")
        return 0

    if args.cmd == "apply":
        save_profile(state)
        path = apply(state)
        print(f"Sent profile settings to {path}; verify them on the mouse.")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
