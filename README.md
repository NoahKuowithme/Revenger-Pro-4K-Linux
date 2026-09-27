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

CLI:

```bash
./revengerctl-cli probe
./revengerctl-cli status
./revengerctl-cli polling 1000
./revengerctl-cli dpi 2 1600
./revengerctl-cli apply
```

Needs GTK 4 and libadwaita (already typical on Ubuntu/GNOME).

## Allow HID access (once)

`/dev/hidraw*` is root-only until you install the udev rule:

```bash
./install-udev.sh
```

Then unplug and replug the dongle. After that, **Apply to mouse** can write DPI, polling, lift-off, and debounce.

## Notes

- The mouse still works as a normal pointer without this app.
- 2000 Hz / 4000 Hz only apply when the **4K** receiver is plugged in.
- Compx firmware variants exist. If a setting does not stick, check `./revengerctl-cli status` after applying.
- Not affiliated with COUGAR / Compucase.
