# Revenger Pro 4K for Linux

Linux companion for the **COUGAR Revenger Pro 4K** (Compx OEM, USB `3554:f5de` / `3554:f5df`). Official UIX is Windows-only; this app talks to the dongle over HID on Linux.

Built by AI for Noah.

## Specs (hardware)

- Ultra-light ergonomic shell, **55 g**
- **4K wireless dongle**, up to **4000 Hz** polling
- **26,000 DPI** PixArt optical sensor
- Up to **150 hours** (1000 Hz)
- PTFE feet and grip tape in the box

## Run the app

```bash
cd ~/Desktop/Revenger-Pro-4K-Linux
./revenger-pro-4k
```

The GUI has **Mouse settings** and **Receiver connection** pages; choose English
or Traditional Chinese from the header. **Apply to mouse** is in the polling-rate
section beside the DPI controls.

### Customize the GUI

The GUI layout and behavior are in [`revengerctl/app.py`](revengerctl/app.py).
Edit the `TEXT` dictionary near the top of that file to change English or
Traditional Chinese labels and messages. The `MainWindow` class builds the
header and the **Mouse settings** / **Receiver connection** pages; look there to
rearrange controls or adjust the layout. Restart the app to see your changes.

CLI:

```bash
./revengerctl-cli probe
./revengerctl-cli status
./revengerctl-cli dpi 2 1600
./revengerctl-cli polling 4000
./revengerctl-cli apply
./revengerctl-cli pair
./revengerctl-cli pair --receiver 1k
```

`pair` defaults to the 4K receiver; use `--receiver 1k` to target the 2.4 GHz
receiver. Disconnect the other receiver, turn on the mouse, place it within
10 cm, then hold middle-wheel + right + left together for about 3 seconds until the
yellow pairing light flashes rapidly. Only then start receiver pairing. Add
`--debug` to print input reports as hex if pairing fails.

To add the app to the desktop application menu with its icon, run:

```bash
./install-app.sh
```

Flatpak packaging for a future Flathub submission is documented in
[`FLATPAK.md`](FLATPAK.md). The Flatpak needs host udev access to the receiver;
the sandbox cannot install the project's udev rule itself.

Needs GTK 4 and libadwaita (already typical on Ubuntu/GNOME).

## Allow HID access (once)

`/dev/hidraw*` is root-only until you install the udev rule. The rule uses
`uaccess` for the active desktop session and does not depend on Ubuntu's
`plugdev` group, so it also works on Arch-based systems such as CachyOS:

```bash
./install-udev.sh
```

Then unplug and replug the dongle. This grants the app permission to open the HID interface.
If the app still reports an access error, check that you launched it from your
logged-in desktop session and inspect the node's ACL with
`getfacl /dev/hidrawN` (replace `N` with the path shown by `./revengerctl-cli probe`).

## Notes

- The mouse still works as a normal pointer without this app.
- `dpi` and `polling` use UIX 1.0.0.42-derived flash-write frames sent using
  HID SetFeature, matching UIX's native route for command reports. The `dpi`
  command writes the requested stage and activates it; `apply` writes polling,
  all five DPI stages, and the selected active stage with a short gap between
  reports. DPI changes still need physical validation.
- Lift-off and debounce are not implemented; the GUI shows their saved profile
  values but disables the controls and labels them as unapplied.
- `status` does not yet read the five DPI values back from mouse flash, so its
  displayed DPI stages and active-stage selection come from the local profile.
  The polling-rate field is also not yet confirmed as a reliable hardware
  readback.
- Pair-status decoding is based on UIX's native callback layout and still needs
  a hardware run to confirm the Linux report offset.
- Not affiliated with COUGAR / Compucase.
- Licensed under the GNU General Public License v3.0 or later; see [LICENSE](LICENSE).

## Reference files

The `references/` folder documents local research material. The extracted
Windows UIX DLLs/resources and the old desktop launcher are intentionally
ignored by Git; they are not needed to run the Linux app. The active launcher
is `revenger-pro-4k.desktop`.
