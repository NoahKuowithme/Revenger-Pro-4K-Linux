# Agent Instructions

## Project
- This repository is the Linux companion app for the COUGAR Revenger Pro 4K mouse. The GTK application and HID implementation live in `revengerctl/`.
- Preserve the project's `GPL-3.0-or-later` license and existing English / Traditional Chinese support.

## HID and hardware accuracy
- Treat protocol details as evidence-based. Clearly label inferred behavior, and do not claim a setting works until validated on the physical mouse/receiver.
- Do not run the Windows UIX executable on Linux. Windows installer extracts under `Windows referrence/` or `references/uix-windows-extract/` are research material: never commit or package them.
- Keep the UI honest about device readback and sensor support. A calibration progress timer is not proof that hardware calibration ran.
- A discovered `/dev/hidraw*` node does not prove it is writable. Check device permissions/ACLs and the host udev rule when diagnosing access.

## GTK behavior
- Keep English and Traditional Chinese UI strings in sync when changing user-facing text.
- The permission guide should help users install the host udev rule when a receiver is detected but inaccessible. Flatpak cannot install host rules; do not make the app silently execute host scripts or commands.

## Flatpak and release source
- Keep `io.noah.revengerpro4k.yml` pinned to the intended published Git commit. Before asking for a clean build, verify the pin includes the changes being built.
- Runtime and SDK currently use GNOME branch `50`; preserve a matching pair unless intentionally updating both.
- Flatpak cannot install the host udev rule. Keep host setup and required sandbox permissions documented in `FLATPAK.md`; do not describe the package as Flathub-ready without the relevant build, metadata, sandbox, and hardware checks.
- Do not bundle Windows reference files, local build caches, or generated artifacts in the release.

## Scripts and validation
- Keep shell scripts readable, with clear status/error messages; request elevated privileges only for host operations that need them, such as installing a udev rule.
- When reporting validation, distinguish static checks, Flatpak build/launch, and physical hardware testing. Never imply one proves another.
- For user-facing instructions, prefer short, copyable commands and respond in Traditional Chinese when the user writes in Chinese.
