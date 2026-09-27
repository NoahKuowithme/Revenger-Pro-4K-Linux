#!/usr/bin/env python3
"""GTK 4 + libadwaita companion for the Revenger Pro 4K."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from revengerctl import APP_ID, APP_SUBTITLE, APP_TITLE  # noqa: E402
from revengerctl.apply import apply, refresh  # noqa: E402
from revengerctl.profiles import save_profile  # noqa: E402
from revengerctl.protocol import DPI_MAX, DPI_MIN, DPI_STEP, MouseState, POLLING_CODES  # noqa: E402

CSS = b"""
window {
  background-color: #0b0c10;
}
.hero-title {
  font-weight: 800;
  font-size: 28px;
  letter-spacing: 2px;
}
.hero-sub {
  color: #c5c6c7;
}
.stat-value {
  font-weight: 700;
  font-size: 22px;
  color: #66fcf1;
}
.accent-card {
  background: #1f2833;
  border-radius: 16px;
  padding: 16px;
  border: 1px solid #45a29e;
}
"""


class CompanionWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title=APP_TITLE)
        self.set_default_size(920, 720)
        self.state = MouseState()
        self._syncing = False

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=APP_TITLE))
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.set_tooltip_text("Rescan USB")
        refresh_btn.connect("clicked", lambda *_: self.reload())
        header.pack_start(refresh_btn)
        apply_btn = Gtk.Button(label="Apply to mouse")
        apply_btn.add_css_class("suggested-action")
        apply_btn.connect("clicked", lambda *_: self.on_apply())
        header.pack_end(apply_btn)
        toolbar.add_top_bar(header)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        page.set_margin_top(24)
        page.set_margin_bottom(32)
        page.set_margin_start(28)
        page.set_margin_end(28)
        scroller.set_child(page)
        toolbar.set_content(scroller)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title = Gtk.Label(label="REVENGER PRO 4K")
        title.add_css_class("hero-title")
        title.set_xalign(0)
        sub = Gtk.Label(label="The Ultimate Gaming Mouse — Linux companion")
        sub.add_css_class("hero-sub")
        sub.set_xalign(0)
        built = Gtk.Label(label=APP_SUBTITLE)
        built.set_xalign(0)
        built.add_css_class("dim-label")
        hero.append(title)
        hero.append(sub)
        hero.append(built)
        page.append(hero)

        self.status_label = Gtk.Label(xalign=0)
        self.status_label.set_wrap(True)
        page.append(self.status_label)

        stats = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats.set_homogeneous(True)
        self.stat_dpi = self._stat_card("DPI")
        self.stat_poll = self._stat_card("Polling")
        self.stat_weight = self._stat_card("Weight")
        self.stat_weight[1].set_text("55 g")
        self.stat_battery = self._stat_card("Battery")
        for card in (self.stat_dpi, self.stat_poll, self.stat_weight, self.stat_battery):
            stats.append(card[0])
        page.append(stats)

        specs = Gtk.Label(
            label=(
                "PixArt 26,000 DPI optical sensor  ·  4K wireless dongle (up to 4000 Hz)  ·  "
                "up to 150 hours  ·  PTFE feet + grip tape"
            )
        )
        specs.set_wrap(True)
        specs.set_xalign(0)
        specs.add_css_class("dim-label")
        page.append(specs)

        dpi_group = Adw.PreferencesGroup(title="DPI stages")
        dpi_group.set_description("Five onboard stages, 50–26,000 DPI in steps of 50.")
        self.dpi_spins: list[Gtk.SpinButton] = []
        self.stage_checks: list[Gtk.CheckButton] = []
        group_root = None
        for i in range(5):
            row = Adw.ActionRow(title=f"Stage {i + 1}")
            check = Gtk.CheckButton()
            if group_root is None:
                group_root = check
            else:
                check.set_group(group_root)
            check.connect("toggled", self.on_stage_toggled, i)
            self.stage_checks.append(check)
            spin = Gtk.SpinButton.new_with_range(DPI_MIN, DPI_MAX, DPI_STEP)
            spin.set_width_chars(6)
            spin.connect("value-changed", lambda *_: self.collect())
            self.dpi_spins.append(spin)
            row.add_prefix(check)
            row.add_suffix(spin)
            dpi_group.add(row)
        page.append(dpi_group)

        poll_group = Adw.PreferencesGroup(title="Polling rate")
        poll_group.set_description("Use 1000 Hz on the 1K dongle. 2000 / 4000 Hz need the 4K dongle.")
        poll_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        poll_box.set_margin_top(8)
        poll_box.set_margin_bottom(8)
        self.poll_buttons: dict[int, Gtk.ToggleButton] = {}
        first = None
        for hz in sorted(POLLING_CODES):
            btn = Gtk.ToggleButton(label=f"{hz} Hz")
            if first is None:
                first = btn
            else:
                btn.set_group(first)
            btn.connect("toggled", self.on_poll_toggled, hz)
            self.poll_buttons[hz] = btn
            poll_box.append(btn)
        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        wrap.append(poll_box)
        page.append(poll_group)
        page.append(wrap)

        extra = Adw.PreferencesGroup(title="Sensor")
        lod_row = Adw.ComboRow(title="Lift-off distance", model=Gtk.StringList.new(["1 mm", "2 mm"]))
        lod_row.connect("notify::selected", lambda *_: self.collect())
        self.lod_row = lod_row
        extra.add(lod_row)
        deb_row = Adw.ComboRow(
            title="Debounce",
            subtitle="Lower is snappier; 0 ms is optical-switch default.",
            model=Gtk.StringList.new(["0 ms", "1 ms", "2 ms", "4 ms", "8 ms"]),
        )
        deb_row.connect("notify::selected", lambda *_: self.collect())
        self.deb_row = deb_row
        extra.add(deb_row)
        page.append(extra)

        # ToolbarView as window content; wrap with overlay
        overlay = Adw.ToastOverlay()
        overlay.set_child(toolbar)
        self.toast = overlay
        self.set_content(overlay)

        GLib.timeout_add_seconds(3, self.reload)
        self.reload()

    def _stat_card(self, caption: str) -> tuple[Gtk.Box, Gtk.Label]:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("accent-card")
        value = Gtk.Label(label="—")
        value.add_css_class("stat-value")
        value.set_xalign(0)
        cap = Gtk.Label(label=caption)
        cap.set_xalign(0)
        cap.add_css_class("dim-label")
        box.append(value)
        box.append(cap)
        return box, value

    def toast_msg(self, text: str) -> None:
        self.toast.add_toast(Adw.Toast(title=text))

    def reload(self) -> bool:
        self.state = refresh()
        self.push_ui()
        return True

    def push_ui(self) -> None:
        self._syncing = True
        st = self.state
        if st.connected:
            access = "HID access OK" if st.access_ok else st.access_error
            self.status_label.set_text(f"Connected · {st.name} · {st.vid_pid} · {st.hidraw}\n{access}")
        else:
            self.status_label.set_text("Dongle not found. Plug in the Revenger Pro 4K 2.4 GHz receiver.")
        self.stat_dpi[1].set_text(f"{st.dpi:,}")
        self.stat_poll[1].set_text(f"{st.polling_hz} Hz")
        self.stat_battery[1].set_text(f"{st.battery}%" if st.battery is not None else "—")
        for i, spin in enumerate(self.dpi_spins):
            spin.set_value(st.dpi_stages[i])
        if 0 <= st.active_stage < len(self.stage_checks):
            self.stage_checks[st.active_stage].set_active(True)
        btn = self.poll_buttons.get(st.polling_hz)
        if btn:
            btn.set_active(True)
        self.lod_row.set_selected(0 if st.lod_mm <= 1 else 1)
        mapping = {0: 0, 1: 1, 2: 2, 4: 3, 8: 4}
        self.deb_row.set_selected(mapping.get(st.debounce_ms, 0))
        self._syncing = False

    def on_stage_toggled(self, button: Gtk.CheckButton, index: int) -> None:
        if self._syncing or not button.get_active():
            return
        self.state.active_stage = index
        self.collect()

    def on_poll_toggled(self, button: Gtk.ToggleButton, hz: int) -> None:
        if self._syncing or not button.get_active():
            return
        self.state.polling_hz = hz
        self.collect()

    def collect(self) -> None:
        if self._syncing:
            return
        self.state.dpi_stages = [int(s.get_value()) for s in self.dpi_spins]
        self.state.lod_mm = 1 if self.lod_row.get_selected() == 0 else 2
        debounce_index = int(self.deb_row.get_selected())
        debounce = [0, 1, 2, 4, 8][debounce_index] if debounce_index < 5 else 0
        self.state.debounce_ms = debounce
        self.stat_dpi[1].set_text(f"{self.state.dpi:,}")
        self.stat_poll[1].set_text(f"{self.state.polling_hz} Hz")
        save_profile(self.state)

    def on_apply(self) -> None:
        self.collect()
        try:
            path = apply(self.state)
        except PermissionError:
            self.toast_msg("Need hidraw permission. Run ./install-udev.sh then replug the dongle.")
            return
        except Exception as exc:
            self.toast_msg(str(exc))
            return
        self.toast_msg(f"Settings written to {path}")
        self.reload()


class CompanionApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, _app) -> None:
        win = CompanionWindow(self)
        win.present()


def main() -> int:
    Adw.init()
    return CompanionApp().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
