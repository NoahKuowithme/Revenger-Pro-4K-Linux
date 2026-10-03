# Revenger Pro 4K Linux companion

This guide covers native installation and development on Ubuntu/Debian and
Arch/CachyOS. The application is a Python 3 GTK 4 + libadwaita program. It does
not have a CMake build or a native compile step.

## System requirements

### Runtime dependencies

- Python 3
- PyGObject (`gi`)
- GTK 4 introspection bindings
- libadwaita introspection bindings
- A running graphical session (Wayland or X11)
- `udev` and systemd-logind for session based device permissions

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
  desktop-file-utils acl
```

### Arch Linux / CachyOS

```bash
sudo pacman -Syu --needed python python-gobject gtk4 libadwaita \
  desktop-file-utils acl
```

`pkg-config`/`pkgconf`, CMake, compilers, and GTK development headers are not
needed to run or build this Python-only project. Install them only if you add
native C/C++ components.

## Get the source

Open a terminal in the project directory. If you have not checked out the
project yet, use the project's published Git repository and select the branch
or commit you intend to work on.

```bash
cd ~/Desktop/Revenger-Pro-4K-Linux
```

On localized desktops, the directory may be shown as `~/桌面`; use the actual
path where you checked out the repository.

## Install and run

There is no compilation step. Run the Python launcher from the repository root:

```bash
python3 ./revenger-pro-4k
```

The launcher adds the project directory to Python's import path and starts the
GTK application. Do not use `sudo` to launch the GUI.

For Debian/Ubuntu, install the downloadable `.deb` with
`sudo apt install ./revenger-pro-4k.deb`. For Arch/CachyOS, install the
downloadable package with `sudo pacman -U ./revenger-pro-4k.pkg.tar.zst`, or
install `base-devel` and run `makepkg -si` from a checkout. The packages install
the menu entry and udev rule in standard system paths.

Install receiver permissions once on the host:

```bash
./install-udev.sh
```

Approve the administrator prompt, unplug and reconnect the receiver, then
check access:

```bash
./revengerctl-cli probe
./revengerctl-cli status
```

The udev rule uses `TAG+="uaccess"` and is named `72-...` so the tag is applied
before systemd's `73-seat-late.rules` processes device ACLs. A listed
`/dev/hidrawN` node proves detection only; `Permission: Ready` confirms that
the current user can open the control interface.

## Desktop menu shortcut and updates

The repository contains `revenger-pro-4k.desktop` as the native desktop-entry
template. Install or refresh the menu shortcut and icon with:

```bash
./install-app.sh
```

The script overwrites the per-user installed entry, points it to the current
checkout, installs the icon, refreshes the desktop application database, and
refreshes KDE's service/icon cache when the KDE cache utility is present.
The generated entry has both `Exec` and `TryExec` set to the current Python
launcher.

If you edit the desktop entry manually, refresh the caches with:

```bash
update-desktop-database ~/.local/share/applications/
kbuildsycoca6 --noincremental
```

On Plasma 5, use `kbuildsycoca5 --noincremental`. GNOME normally discovers
updated per-user application entries automatically after the desktop database
refresh. The script skips a cache tool that is not installed.

## Troubleshooting

### The GUI opens, but the receiver cannot be opened

Use the node printed by `./revengerctl-cli status` rather than assuming the
hidraw number. Inspect its permissions and udev tags:

```bash
NODE="$(./revengerctl-cli status | sed -n 's/^HID device[[:space:]]*:[[:space:]]*//p')"
ls -l "$NODE"
getfacl -p "$NODE"
udevadm info --query=property --name="$NODE" | grep -E '^(ID_VENDOR_ID|ID_MODEL_ID|TAGS|CURRENT_TAGS)='
```

If the rule was just installed, reconnect the receiver so udev reprocesses its
hidraw interfaces.

### Pairing status 3 while USB control still works

Status 3 is returned by the receiver's HID pairing-status report. It describes
the pairing attempt; it is not a NetworkManager or D-Bus connection status.
The GUI therefore explains that this response does not itself mean that USB
control is disconnected. If the mouse already works with the receiver, continue
using it; otherwise follow the pairing instructions and retry. The CLI keeps a
nonzero exit status for an unsuccessful or unconfirmed pairing attempt.

## Project layout

- `revengerctl/app.py`: GTK 4/libadwaita interface and English/Traditional
  Chinese text.
- `revengerctl/device.py`: HID interface discovery and hidraw access.
- `revengerctl/protocol.py`: HID report encoding and parsing.
- `revengerctl/apply.py`, `profiles.py`: device operations and local settings.
- `revenger-pro-4k`, `revengerctl-cli`: GUI and command-line launchers.
- `install-app.sh`, `install-udev.sh`: desktop-entry and host permission setup.
- `udev/`: host udev rule source.
- `reference/`: legacy launcher and local protocol/research materials. Windows
  installer extracts are ignored and must never be committed or packaged.
- `tests/`: protocol, device-discovery, and settings tests.

## Licensing

This project is licensed under **GNU General Public License v3.0 or later**
(`GPL-3.0-or-later`). See [`LICENSE`](LICENSE). Third-party reference materials
may have separate terms and are not bundled with the Linux application.
