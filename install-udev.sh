#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
RULE_SRC="$ROOT/udev/72-revenger-pro-4k.rules"
RULE_DST="/etc/udev/rules.d/72-revenger-pro-4k.rules"

printf 'Revenger Pro 4K — USB access setup\n\n'

if [[ $EUID -ne 0 ]]; then
  printf '[Permission] Administrator access is needed to install a USB access rule.\n'
  exec sudo "$0" "$@"
fi

printf '[1/3] Installing the USB access rule…\n'
install -m 644 "$RULE_SRC" "$RULE_DST"
printf '[2/3] Reloading device rules…\n'
udevadm control --reload-rules
printf '[3/3] Applying the rules to connected devices…\n'
udevadm trigger --subsystem-match=hidraw --subsystem-match=usb
printf '\nDone. Unplug and reconnect the Revenger Pro 4K receiver.\n'
printf 'Then check access with: ./revengerctl-cli status\n'
