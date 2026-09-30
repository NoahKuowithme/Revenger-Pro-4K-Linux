# Flatpak / Flathub packaging

The initial manifest is `io.noah.revengerpro4k.yml`. It builds the Python GTK
app against the GNOME 50 runtime and installs its desktop entry and SVG icon
under `/app/share`, where Flatpak exports them to desktop environments.

## Hardware access

This app communicates directly with `/dev/hidrawN` and reads receiver
descriptors and uevent data from `/sys/class/hidraw`. The manifest requests
`--device=all` and read-only `/sys` access because Flatpak does not currently
provide a per-hidraw device permission. The device permission is broader than
the app needs and must be justified during Flathub review.

The host udev rule is not installed by a Flatpak. On systems where the logged-in
user does not already have access to the receiver's hidraw node, install the
project's `udev/99-revenger-pro-4k.rules` on the host and reconnect the
receiver. This requires administrator access and is a significant installation
prerequisite to disclose in the Flathub listing.

The app includes a first-run guide that copies the exact host setup command for
the user to paste into a terminal. It does not spawn host commands or request
administrator access itself.

## Local build

After installing `flatpak-builder` and the Flathub remote, build and install
with:

```sh
flatpak-builder --user --install --force-clean build-dir io.noah.revengerpro4k.yml
```

The release manifest builds a pinned Git commit. To build uncommitted local
changes, use a temporary copy of the manifest with its Git source replaced by
`type: dir` and `path: .`, then run the same command against that copy. Keep the
release manifest pinned to a reviewed, published commit for Flathub.

## Before submitting to Flathub

- Build and launch the Flatpak on both supported architectures, then verify
  receiver detection, settings writes, and pairing inside the sandbox.
- Confirm whether Flathub reviewers will accept the broad device permission and
  the host-side udev installation requirement for this hardware-control app.
- Update the pinned Git commit whenever a new source release is submitted.
