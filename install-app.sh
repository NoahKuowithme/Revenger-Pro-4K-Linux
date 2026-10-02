#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPLICATIONS="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"

printf 'Revenger Pro 4K — desktop setup\n\n'
printf '[1/4] Preparing your application folders…\n'
mkdir -p "$APPLICATIONS" "$ICON_DIR"

DESKTOP_TMP="$(mktemp)"
trap 'rm -f "$DESKTOP_TMP"' EXIT
sed \
  -e "s|^Exec=.*|Exec=$ROOT/revenger-pro-4k|" \
  -e "s|^TryExec=.*|TryExec=$ROOT/revenger-pro-4k|" \
  -e "s|^Icon=.*|Icon=$ICON_DIR/io.github.noahkuowithme.Revenger-Pro-4K-Linux.svg|" \
  "$ROOT/revenger-pro-4k.desktop" \
  > "$DESKTOP_TMP"
install -Dm644 "$DESKTOP_TMP" "$APPLICATIONS/io.github.noahkuowithme.Revenger-Pro-4K-Linux.desktop"
printf '[2/4] Installing launcher and icon…\n'
install -Dm644 "$ROOT/icons/io.github.noahkuowithme.Revenger-Pro-4K-Linux.svg" \
  "$ICON_DIR/io.github.noahkuowithme.Revenger-Pro-4K-Linux.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
  printf '[3/4] Refreshing the desktop application database…\n'
  update-desktop-database "$APPLICATIONS"
else
  printf '[3/4] update-desktop-database not found; skipping MIME database refresh.\n'
fi

if command -v kbuildsycoca6 >/dev/null 2>&1; then
  printf '[4/4] Refreshing KDE Plasma 6 service and icon caches…\n'
  if ! kbuildsycoca6 --noincremental; then
    printf '[Warning] KDE cache refresh failed; the installed shortcut is still available.\n'
  fi
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
  printf '[4/4] Refreshing KDE Plasma 5 service and icon caches…\n'
  if ! kbuildsycoca5 --noincremental; then
    printf '[Warning] KDE cache refresh failed; the installed shortcut is still available.\n'
  fi
else
  printf '[4/4] KDE cache tool not found; GNOME and other desktops refresh automatically.\n'
fi

printf '\nDone. Revenger Pro 4K is available in your application menu.\n'
