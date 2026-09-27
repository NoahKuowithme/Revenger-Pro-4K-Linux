#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
RULE_SRC="$ROOT/udev/99-revenger-pro-4k.rules"
RULE_DST="/etc/udev/rules.d/99-revenger-pro-4k.rules"

if [[ $EUID -ne 0 ]]; then
  echo "Installing udev rule (needs sudo)…"
  exec sudo "$0" "$@"
fi

install -m 644 "$RULE_SRC" "$RULE_DST"
udevadm control --reload-rules
udevadm trigger --subsystem-match=hidraw --subsystem-match=usb
echo "Installed $RULE_DST"
echo "Unplug and replug the Revenger Pro 4K dongle, then run: ./revengerctl-cli status"
