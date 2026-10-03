# Revenger Pro 4K for Linux

A community-maintained Linux companion app for the **COUGAR Revenger Pro 4K**.
It provides a GTK desktop interface and command-line tools for communicating
with the mouse receiver over USB HID.

> This project is not affiliated with COUGAR or Compucase. Some settings still
> need confirmation on physical hardware; see [Known limitations](#known-limitations).

## Features

- GTK 4 and libadwaita interface in English and Traditional Chinese.
- Command-line tools for device status, DPI, polling rate, and receiver pairing.
- Per-user settings stored in `~/.config/revenger-pro-4k/`.
- Host udev rule for session-based access to supported receiver IDs.

## Install

Prebuilt Debian and Arch packages are attached to the
[GitHub Release v2](https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/tag/v2).
You can also create a native package from a source checkout.

### Debian and Ubuntu

```bash
./packaging/build-deb.sh
curl -LO https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/download/v2/revenger-pro-4k.deb
sudo apt install ./revenger-pro-4k.deb
```

The package installs the app, desktop menu entry, icon, and udev rule. GTK and
Python runtime dependencies are declared by the package manager.

### Arch Linux and CachyOS

Download the Arch package from the [v2 release](https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/tag/v2), then install it:

```bash
curl -LO https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/download/v2/revenger-pro-4k.pkg.tar.zst
sudo pacman -U ./revenger-pro-4k.pkg.tar.zst
```

To build it yourself, install `base-devel` and run `makepkg -si` from the project directory.

### Run from a checkout

Install GTK 4, libadwaita, and PyGObject for your distribution, then run:

```bash
./revenger-pro-4k
```

To add a desktop menu shortcut for the checkout, run `./install-app.sh`.
Detailed distro dependencies and troubleshooting steps are in
[`INSTRUCTIONS.md`](INSTRUCTIONS.md).

## Receiver access

The app needs permission to open the receiver's `/dev/hidraw*` interface. Native
packages install the udev rule automatically. For a source checkout, install it
once on the host:

```bash
./install-udev.sh
```

Approve the administrator prompt, then unplug and reconnect the receiver. The
rule uses `TAG+="uaccess"` for the active desktop session; it does not rely on
the `plugdev` group. Device discovery alone does not confirm that the HID node
is writable. See [`INSTRUCTIONS.md`](INSTRUCTIONS.md) if access is still denied.

## Command-line examples

```bash
./revengerctl-cli probe
./revengerctl-cli status
./revengerctl-cli dpi 2 1600
./revengerctl-cli polling 4000
./revengerctl-cli apply
./revengerctl-cli pair --receiver 1k
```

Pairing defaults to the 4K receiver. For 2.4 GHz pairing, use `--receiver 1k`.
Disconnect the other receiver, turn on the mouse, place it within 10 cm, then
hold the middle wheel, right button, and left button together for about three
seconds until the yellow light flashes rapidly. Start pairing only after that.
Add `--debug` to print input reports as hex when diagnosing a pairing attempt.

## Known limitations

- DPI and polling commands send UIX-derived HID write requests. Their behavior
  and persistence still need physical mouse validation.
- `status` uses the local profile for DPI stages and active stage; it does not
  read those values back from mouse flash. Polling readback is also unconfirmed.
- LOD, angle snapping, and Motion Sync can be sent with **Apply to mouse**, but
  the app cannot read them back yet. Confirm their effect on the mouse.
- The calibration control mirrors UIX's three-second timer. It does not send a
  hardware calibration command. Debounce is not applied.
- Pairing status decoding follows the UIX callback layout; the Linux report
  offset still needs hardware confirmation.

## Development and license

The GTK interface and translations are in [`revengerctl/app.py`](revengerctl/app.py).
Protocol and device code live in `revengerctl/`. The project is licensed under
**GPL-3.0-or-later**; see [`LICENSE`](LICENSE).

<details>
<summary>繁體中文</summary>

這是 COUGAR Revenger Pro 4K 的社群維護 Linux 控制程式，提供 GTK 桌面介面
和命令列工具，透過 USB HID 與接收器通訊。本專案與 COUGAR／Compucase 無關。

### 安裝套件

預編譯套件已附在 [GitHub Release v2](https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/tag/v2)。也可以在專案目錄自行建置。

**Debian／Ubuntu**

```bash
curl -LO https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/download/v2/revenger-pro-4k.deb
sudo apt install ./revenger-pro-4k.deb
```

**Arch／CachyOS**：下載 [v2 release](https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/tag/v2) 的套件後安裝：

```bash
curl -LO https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux/releases/download/v2/revenger-pro-4k.pkg.tar.zst
sudo pacman -U ./revenger-pro-4k.pkg.tar.zst
```

套件會安裝程式、桌面選單項目、圖示和 udev 規則。也可以直接從原始碼目錄執行
`./revenger-pro-4k`；詳細相依套件請看 [`INSTRUCTIONS.md`](INSTRUCTIONS.md)。

### 接收器權限

原生套件會安裝 udev 規則。若直接從原始碼執行，請在主機執行一次：

```bash
./install-udev.sh
```

核准管理員提示後，拔除並重新接上接收器。偵測到 `/dev/hidraw*` 不代表程式已有
讀寫權限；若仍無法連線，請依照安裝說明檢查 ACL。

### 已知限制

- DPI／回報率寫入行為仍需在實體滑鼠上驗證。
- DPI 狀態來自本機設定檔，尚未從滑鼠 flash 讀回；回報率讀回也未確認。
- LOD、角度修正和 Motion Sync 可送出設定，但目前無法讀回確認。
- 校正按鈕只顯示三秒計時，不會送出硬體校正命令；Debounce 尚未套用。
- 配對狀態的 Linux HID 報告位置仍待實機確認。

本專案採用 **GPL-3.0-or-later**，詳見 [`LICENSE`](LICENSE)。

</details>
