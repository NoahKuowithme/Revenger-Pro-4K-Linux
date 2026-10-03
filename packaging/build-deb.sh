#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=${VERSION:-2.0.0-1}
OUTPUT=${1:-"$ROOT/dist/revenger-pro-4k.deb"}
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT HUP INT TERM

if ! command -v dpkg-deb >/dev/null 2>&1; then
  printf 'Error: dpkg-deb is required to build the Debian package.\n' >&2
  exit 1
fi

install -d "$STAGE/usr/lib/revenger-pro-4k/revengerctl" \
  "$STAGE/usr/bin" \
  "$STAGE/usr/share/applications" \
  "$STAGE/usr/share/icons/hicolor/scalable/apps" \
  "$STAGE/usr/share/doc/revenger-pro-4k" \
  "$STAGE/usr/lib/udev/rules.d" \
  "$STAGE/usr/lib/revenger-pro-4k/udev" \
  "$STAGE/DEBIAN"
cp -a "$ROOT/revengerctl/." "$STAGE/usr/lib/revenger-pro-4k/revengerctl/"
find "$STAGE/usr/lib/revenger-pro-4k" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$STAGE/usr/lib/revenger-pro-4k" -type f -name '*.py[co]' -delete
install -m 755 "$ROOT/revenger-pro-4k" "$ROOT/revengerctl-cli" \
  "$STAGE/usr/lib/revenger-pro-4k/"
install -m 755 "$ROOT/packaging/bin/revenger-pro-4k" \
  "$ROOT/packaging/bin/revengerctl-cli" "$STAGE/usr/bin/"
install -m 644 "$ROOT/revenger-pro-4k.desktop" \
  "$STAGE/usr/share/applications/io.github.noahkuowithme.Revenger-Pro-4K-Linux.desktop"
install -m 644 "$ROOT/icons/io.github.noahkuowithme.Revenger-Pro-4K-Linux.svg" \
  "$STAGE/usr/share/icons/hicolor/scalable/apps/io.github.noahkuowithme.Revenger-Pro-4K-Linux.svg"
install -m 644 "$ROOT/udev/72-revenger-pro-4k.rules" \
  "$STAGE/usr/lib/udev/rules.d/72-revenger-pro-4k.rules"
install -m 644 "$ROOT/udev/72-revenger-pro-4k.rules" \
  "$STAGE/usr/lib/revenger-pro-4k/udev/72-revenger-pro-4k.rules"
install -m 644 "$ROOT/README.md" "$ROOT/INSTRUCTIONS.md" "$ROOT/LICENSE" \
  "$STAGE/usr/share/doc/revenger-pro-4k/"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: revenger-pro-4k
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, udev
Maintainer: Revenger Pro 4K Linux contributors
Description: Linux companion app for the COUGAR Revenger Pro 4K mouse
 GTK 4 application and command-line tools for configuring the receiver.
EOF
cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v udevadm >/dev/null 2>&1; then
  udevadm control --reload-rules || true
fi
printf '%s\n' 'Revenger Pro 4K installed. Unplug and reconnect the receiver to apply its udev rule.'
EOF
chmod 755 "$STAGE/DEBIAN/postinst"
find "$STAGE" -type d -exec chmod 755 {} +

mkdir -p "$(dirname -- "$OUTPUT")"
dpkg-deb --root-owner-group --build "$STAGE" "$OUTPUT"
printf 'Built package: %s\n' "$OUTPUT"
