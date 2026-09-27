#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPLICATIONS="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"

DESKTOP_TMP="$(mktemp)"
trap 'rm -f "$DESKTOP_TMP"' EXIT
sed \
  -e "s|^Exec=.*|Exec=$ROOT/revenger-pro-4k|" \
  -e "s|^Icon=.*|Icon=$ICON_DIR/io.noah.revengerpro4k.svg|" \
  "$ROOT/revenger-pro-4k.desktop" \
  > "$DESKTOP_TMP"
install -Dm644 "$DESKTOP_TMP" "$APPLICATIONS/io.noah.revengerpro4k.desktop"
install -Dm644 "$ROOT/icons/io.noah.revengerpro4k.svg" \
  "$ICON_DIR/io.noah.revengerpro4k.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPLICATIONS"
fi

echo "Installed Revenger Pro 4K launcher and icon for this user."
