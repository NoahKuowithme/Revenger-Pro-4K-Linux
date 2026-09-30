#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPLICATIONS="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"

printf 'Revenger Pro 4K — desktop setup\n\n'
printf '[1/3] Preparing your application folders…\n'
mkdir -p "$APPLICATIONS" "$ICON_DIR"

DESKTOP_TMP="$(mktemp)"
trap 'rm -f "$DESKTOP_TMP"' EXIT
sed \
  -e "s|^Exec=.*|Exec=$ROOT/revenger-pro-4k|" \
  -e "s|^Icon=.*|Icon=$ICON_DIR/io.noah.revengerpro4k.svg|" \
  "$ROOT/revenger-pro-4k.desktop" \
  > "$DESKTOP_TMP"
install -Dm644 "$DESKTOP_TMP" "$APPLICATIONS/io.noah.revengerpro4k.desktop"
printf '[2/3] Installing launcher and icon…\n'
install -Dm644 "$ROOT/icons/io.noah.revengerpro4k.svg" \
  "$ICON_DIR/io.noah.revengerpro4k.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
  printf '[3/3] Refreshing the application menu…\n'
  update-desktop-database "$APPLICATIONS"
else
  printf '[3/3] Desktop database updater not found; the menu will refresh automatically.\n'
fi

printf '\nDone. Revenger Pro 4K is available in your application menu.\n'
