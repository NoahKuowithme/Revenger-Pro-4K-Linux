#!/usr/bin/env python3
"""GTK 4 + libadwaita companion for the Revenger Pro 4K."""

from __future__ import annotations

import subprocess
import sys
import threading
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
from revengerctl.device import FOUR_K_PID, ONE_K_PID, list_revenger_interfaces  # noqa: E402
from revengerctl.profiles import save_profile  # noqa: E402
from revengerctl.protocol import DPI_MAX, DPI_MIN, DPI_STEP, MouseState, STAGE_COUNT  # noqa: E402

CSS = b"""
window {
  background-color: alpha(#18181b, 0.85);
  color: #f4f4f5;
}
.hero-title {
  font-weight: 750;
  font-size: 24px;
}
.stat-value {
  font-weight: 700;
  font-size: 20px;
}
.surface-card {
  background-color: #27272a;
  border: 1px solid alpha(#f97316, 0.42);
  border-radius: 12px;
  padding: 14px;
}
.receiver-name {
  font-weight: 700;
  font-size: 15px;
}
.pair-result {
  padding: 8px;
}
.pair-failure {
  color: #ffb4ab;
  background-color: alpha(#b3261e, 0.24);
  border-radius: 8px;
}
.device-path {
  font-family: monospace;
  font-weight: 650;
}
button.primary-action {
  background-color: #f97316;
  color: #18181b;
  font-weight: 750;
  min-height: 42px;
}
button.primary-action:hover {
  background-color: #fb923c;
}
button.primary-action:disabled {
  background-color: alpha(#f97316, 0.42);
}
button.preset:checked, button.poll-rate:checked {
  background-color: #f97316;
  color: #18181b;
  border-color: #ff6600;
  box-shadow: 0 0 8px alpha(#f97316, 0.38);
}
.section-title {
  font-weight: 700;
  font-size: 17px;
}
.stage-row {
  padding: 4px 0;
}
"""

TEXT = {
    "en": {
        "settings_tab": "Mouse settings",
        "connection_tab": "Receiver connection",
        "rescan": "Rescan USB",
        "language": "Interface language",
        "cancel": "Cancel",
        "hero_subtitle": "The Ultimate Gaming Mouse — Linux companion",
        "app_subtitle": "Linux companion · built by AI",
        "connected": "USB control · {name} · {vid_pid} · {hidraw}\n{access}",
        "not_connected": "No receiver control interface detected.",
        "device_title": "USB device",
        "device_connected": "Connected",
        "device_disconnected": "Not connected",
        "device_access": "HID access available",
        "access_ok": "HID access OK",
        "connection_title": "Wireless connection",
        "connection_description": "The mouse pairs with one receiver at a time. USB detection does not confirm pairing; disconnect the other receiver before switching.",
        "receiver_1k": "2.4 GHz · 1K",
        "receiver_4k": "4K receiver",
        "receiver_detected": "USB receiver detected",
        "receiver_absent": "Not connected",
        "target_receiver": "Target receiver",
        "target_1k": "2.4 GHz (1K receiver)",
        "target_4k": "4K receiver",
        "pair_title": "Pair mouse",
        "pair_subtitle": "Before starting, hold the middle-wheel + right + left buttons together until the yellow pairing light flashes rapidly.",
        "pair_button": "Start pairing",
        "pair_initial": "Select a receiver. Put the mouse in pairing mode before starting.",
        "pair_multiple": "Unplug the other receiver before pairing.",
        "pair_none": "No supported receiver detected.",
        "pair_wrong_receiver": "Plug in the selected receiver, then start pairing.",
        "pair_preparing": "Starting receiver pairing…",
        "pair_heading": "Pair with {receiver}?",
        "pair_instructions": "Disconnect the other receiver; leave only the selected receiver connected. Turn the mouse on and place it within 10 cm. Before clicking Start pairing, hold the middle-wheel + right + left buttons together for about 3 seconds until the yellow pairing light flashes rapidly.",
        "pair_started": "Pairing request sent to {path}. The mouse should already be in pairing mode (rapid yellow light).",
        "pair_pending": "Receiver is waiting for the mouse…",
        "pair_succeeded": "Pairing succeeded.",
        "pair_failed": "Pairing failure (Status 3). Hold the middle-wheel + right + left buttons until the yellow light flashes rapidly, then retry.",
        "pair_timeout": "No pairing result before timeout. Check the mouse pairing mode and try again.",
        "stat_polling": "Polling",
        "stat_weight": "Weight",
        "stat_battery": "Battery",
        "specs": "PixArt 26,000 DPI optical sensor  ·  4K wireless receiver (up to 4000 Hz)  ·  up to 150 hours  ·  PTFE feet + grip tape",
        "dpi_title": "DPI stages",
        "dpi_description": "Select a stage, choose a preset or enter a custom DPI. The mouse has five physical slots; unused slots repeat the last configured value.",
        "stage": "Stage",
        "dpi_presets": "DPI presets",
        "add_stage": "Add stage",
        "remove_stage": "Remove selected stage",
        "stage_limit": "The mouse supports up to five DPI slots.",
        "stage_minimum": "Keep at least one DPI stage.",
        "polling_title": "Polling rate",
        "polling_description": "Use 1000 Hz on the 1K receiver. 2000 / 4000 Hz need the 4K receiver.",
        "apply_title": "Apply current settings",
        "apply_subtitle": "Write DPI, polling rate, lift-off distance and sensor toggles to the mouse.",
        "apply_button": "Apply to mouse",
        "sensor_pending": "UIX 1.0.0.42 confirms these settings for the PixArt 3395. Changes are written with Apply to mouse.",
        "angle_title": "Angle snapping",
        "motion_title": "Motion sync",
        "calibrate_title": "Surface calibration",
        "calibrate_button": "Calibrate",
        "calibration_wait": "UIX status timer: {seconds}s",
        "calibration_done": "UIX 3-second status flow finished. No calibration HID command was found in the reference app.",
        "sensor_title": "Sensor tuning",
        "sensor_description": "Supported by the 3395 sensor. Apply to mouse writes these values; readback is not yet available.",
        "lod_title": "Lift-off distance",
        "lod_subtitle": "Applied with the main button",
        "debounce_title": "Debounce",
        "debounce_subtitle": "Not currently applied to the mouse",
        "permission_error": "HID permission needed. Run ./install-udev.sh, then replug the receiver.",
        "settings_sent": "Settings sent to {path}; verify them on the mouse.",
    },
    "zh": {
        "settings_tab": "滑鼠設定",
        "connection_tab": "接收器連線",
        "rescan": "重新掃描 USB",
        "language": "介面語言",
        "cancel": "取消",
        "hero_subtitle": "頂級電競滑鼠 — Linux 控制程式",
        "app_subtitle": "Linux 控制程式 · AI 製作",
        "connected": "USB 控制介面 · {name} · {vid_pid} · {hidraw}\n{access}",
        "not_connected": "沒有偵測到接收器控制介面。",
        "device_title": "USB 裝置",
        "device_connected": "已連線",
        "device_disconnected": "未連線",
        "device_access": "HID 權限正常",
        "access_ok": "HID 權限正常",
        "connection_title": "無線連線",
        "connection_description": "滑鼠一次只能配對一個接收器。偵測到 USB 不代表已配對；切換前請拔除另一個接收器。",
        "receiver_1k": "2.4 GHz · 1K",
        "receiver_4k": "4K 接收器",
        "receiver_detected": "已偵測到 USB 接收器",
        "receiver_absent": "未連接",
        "target_receiver": "配對目標",
        "target_1k": "2.4 GHz（1K 接收器）",
        "target_4k": "4K 接收器",
        "pair_title": "配對滑鼠",
        "pair_subtitle": "開始前，請同時按住滾輪＋右鍵＋左鍵，直到黃色配對燈快速閃爍。",
        "pair_button": "開始配對",
        "pair_initial": "選擇接收器；開始前先讓滑鼠進入配對模式。",
        "pair_multiple": "配對前請拔除另一個接收器。",
        "pair_none": "未偵測到支援的接收器。",
        "pair_wrong_receiver": "請先接上所選的接收器，再開始配對。",
        "pair_preparing": "正在啟動接收器配對…",
        "pair_heading": "配對至{receiver}？",
        "pair_instructions": "請拔除另一個接收器，只保留所選接收器。開啟滑鼠並放在接收器 10 公分內。按下「開始配對」前，先同時按住滾輪、右鍵與左鍵約 3 秒，直到黃色配對燈快速閃爍。",
        "pair_started": "已向 {path} 傳送配對請求。滑鼠應已進入配對模式（黃燈快速閃爍）。",
        "pair_pending": "接收器正在等待滑鼠…",
        "pair_succeeded": "配對成功。",
        "pair_failed": "配對失敗（狀態 3）。請先同時按住滾輪、右鍵與左鍵，直到黃燈快速閃爍，再重試。",
        "pair_timeout": "等待配對結果逾時。請確認滑鼠已進入配對模式後重試。",
        "stat_polling": "輪詢率",
        "stat_weight": "重量",
        "stat_battery": "電量",
        "specs": "PixArt 26,000 DPI 光學感應器  ·  4K 無線接收器（最高 4000 Hz）  ·  最長 150 小時  ·  PTFE 鼠腳與止滑貼",
        "dpi_title": "DPI 段數",
        "dpi_description": "選擇 DPI 段、套用快速預設或輸入自訂數值。滑鼠有五個實體槽位；未使用的槽位會重複最後一段數值。",
        "stage": "第",
        "dpi_presets": "DPI 快速預設",
        "add_stage": "新增段數",
        "remove_stage": "移除所選段數",
        "stage_limit": "滑鼠最多支援五個 DPI 槽位。",
        "stage_minimum": "至少保留一個 DPI 段數。",
        "polling_title": "輪詢率",
        "polling_description": "1K 接收器使用 1000 Hz；2000 / 4000 Hz 需搭配 4K 接收器。",
        "apply_title": "套用目前設定",
        "apply_subtitle": "將 DPI、輪詢率、抬升高度與感測器開關寫入滑鼠。",
        "apply_button": "套用至滑鼠",
        "sensor_pending": "官方 UIX 1.0.0.42 確認這些設定適用於 PixArt 3395；按「套用至滑鼠」後寫入。",
        "angle_title": "直線修正",
        "motion_title": "Motion Sync",
        "calibrate_title": "表面校準",
        "calibrate_button": "開始校準",
        "calibration_wait": "UIX 狀態計時：{seconds} 秒",
        "calibration_done": "UIX 三秒狀態流程已結束。參考程式沒有送出感測器校準 HID 命令。",
        "sensor_title": "感應器調整",
        "sensor_description": "3395 感測器支援這些設定。按「套用至滑鼠」寫入；目前尚無法讀回確認值。",
        "lod_title": "抬升高度",
        "lod_subtitle": "按主按鈕後寫入",
        "debounce_title": "按鍵去抖",
        "debounce_subtitle": "目前不會套用至滑鼠",
        "permission_error": "需要 HID 權限。請執行 ./install-udev.sh，然後重新插拔接收器。",
        "settings_sent": "設定已傳送至 {path}；請在滑鼠上確認是否生效。",
    },
}


class CompanionWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title=APP_TITLE)
        self.set_default_size(820, 640)
        self.state = MouseState()
        self._syncing = False
        self._pairing = False
        self._changing_language = False
        self.language = "en"
        self._localized_text: list[tuple[object, str, str]] = []
        self._last_pair_output: str | None = None
        self._pair_notice_key = "pair_initial"

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.view_stack = Adw.ViewStack()
        view_switcher = Adw.ViewSwitcher.new()
        view_switcher.set_stack(self.view_stack)
        view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(view_switcher)
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        self.bind_text(refresh_btn, "set_tooltip_text", "rescan")
        refresh_btn.connect("clicked", lambda *_: self.reload())
        header.pack_start(refresh_btn)
        self.language_drop = Gtk.DropDown.new(
            Gtk.StringList.new(["English", "繁體中文"]), None
        )
        self.bind_text(self.language_drop, "set_tooltip_text", "language")
        self.language_drop.connect("notify::selected", self.on_language_selected)
        header.pack_end(self.language_drop)
        toolbar.add_top_bar(header)

        self.settings_page = self._make_page()
        settings_scroller = Gtk.ScrolledWindow()
        settings_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        settings_scroller.set_child(self.settings_page)
        self.settings_stack_page = self.view_stack.add_titled(
            settings_scroller, "settings", self.tr("settings_tab")
        )

        self.connection_page = self._make_page()
        connection_scroller = Gtk.ScrolledWindow()
        connection_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        connection_scroller.set_child(self.connection_page)
        self.connection_stack_page = self.view_stack.add_titled(
            connection_scroller, "connection", self.tr("connection_tab")
        )
        toolbar.set_content(self.view_stack)

        page = self.settings_page

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title = Gtk.Label(label="REVENGER PRO 4K")
        title.add_css_class("hero-title")
        title.set_xalign(0)
        sub = Gtk.Label(label="The Ultimate Gaming Mouse — Linux companion")
        self.bind_text(sub, "set_text", "hero_subtitle")
        sub.add_css_class("hero-sub")
        sub.set_xalign(0)
        built = Gtk.Label(label=APP_SUBTITLE)
        self.bind_text(built, "set_text", "app_subtitle")
        built.set_xalign(0)
        built.add_css_class("dim-label")
        hero.append(title)
        hero.append(sub)
        hero.append(built)
        page.append(hero)

        self.device_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.device_card.add_css_class("surface-card")
        self.device_card.set_margin_top(4)
        device_icon = Gtk.Image.new_from_icon_name("drive-removable-media-symbolic")
        device_icon.set_pixel_size(24)
        self.device_card.append(device_icon)
        device_details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        device_title = Gtk.Label(xalign=0)
        self.bind_text(device_title, "set_text", "device_title")
        device_title.add_css_class("heading")
        device_details.append(device_title)
        self.device_status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.device_status_icon = Gtk.Image.new_from_icon_name("process-stop-symbolic")
        self.device_status_label = Gtk.Label(xalign=0)
        self.device_status_row.append(self.device_status_icon)
        self.device_status_row.append(self.device_status_label)
        self.device_path_label = Gtk.Label(xalign=0)
        self.device_path_label.add_css_class("device-path")
        self.device_access_label = Gtk.Label(xalign=0)
        self.device_access_label.add_css_class("dim-label")
        device_details.append(self.device_status_row)
        device_details.append(self.device_path_label)
        device_details.append(self.device_access_label)
        self.device_card.append(device_details)
        self.connection_page.append(self.device_card)

        pair_group = Adw.PreferencesGroup(title="Wireless connection")
        self.bind_text(pair_group, "set_title", "connection_title")
        self.bind_text(pair_group, "set_description", "connection_description")
        receiver_cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        receiver_cards.set_homogeneous(True)
        self.receiver_state_labels: dict[int, Gtk.Label] = {}
        self.receiver_name_labels: dict[int, Gtk.Label] = {}
        for pid, title_key in ((ONE_K_PID, "receiver_1k"), (FOUR_K_PID, "receiver_4k")):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("surface-card")
            card.set_margin_top(4)
            card.set_margin_bottom(4)
            name = Gtk.Label(xalign=0)
            self.bind_text(name, "set_text", title_key)
            name.add_css_class("receiver-name")
            self.receiver_name_labels[pid] = name
            state = Gtk.Label(xalign=0)
            self.bind_text(state, "set_text", "receiver_absent")
            state.add_css_class("receiver-state")
            self.receiver_state_labels[pid] = state
            card.append(name)
            card.append(state)
            receiver_cards.append(card)
        pair_group.add(receiver_cards)
        self.receiver_row = Adw.ComboRow(
            title="Target receiver",
            model=Gtk.StringList.new(["2.4 GHz (1K receiver)", "4K receiver"]),
        )
        self.bind_text(self.receiver_row, "set_title", "target_receiver")
        self.receiver_row.set_selected(1)
        self.receiver_row.connect("notify::selected", self.on_receiver_selected)
        pair_group.add(self.receiver_row)
        pair_row = Adw.ActionRow(
            title="Pair mouse",
            subtitle="Before starting, hold left + right + wheel until the yellow pairing light flashes rapidly.",
        )
        self.bind_text(pair_row, "set_title", "pair_title")
        self.bind_text(pair_row, "set_subtitle", "pair_subtitle")
        self.pair_button, self.pair_button_label = self._action_button(
            "bluetooth-active-symbolic", "pair_button"
        )
        self.pair_button.add_css_class("primary-action")
        self.pair_button.set_size_request(180, 46)
        self.pair_button.connect("clicked", self.on_pair)
        pair_row.add_suffix(self.pair_button)
        pair_row.set_activatable_widget(self.pair_button)
        pair_group.add(pair_row)
        self.pair_result_label = Gtk.Label(xalign=0)
        self.bind_text(self.pair_result_label, "set_text", "pair_initial")
        self.pair_result_label.set_wrap(True)
        self.pair_result_label.add_css_class("pair-result")
        pair_group.add(self.pair_result_label)
        self.connection_page.append(pair_group)

        stats = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats.set_homogeneous(True)
        self.stat_dpi = self._stat_card("DPI")
        self.stat_poll = self._stat_card("Polling", "stat_polling")
        self.stat_weight = self._stat_card("Weight", "stat_weight")
        self.stat_weight[1].set_text("55 g")
        self.stat_battery = self._stat_card("Battery", "stat_battery")
        for card in (self.stat_dpi, self.stat_poll, self.stat_weight, self.stat_battery):
            stats.append(card[0])
        page.append(stats)

        specs = Gtk.Label()
        self.bind_text(specs, "set_text", "specs")
        specs.set_wrap(True)
        specs.set_xalign(0)
        specs.add_css_class("dim-label")
        page.append(specs)

        performance = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        performance.add_css_class("surface-card")
        performance_title = Gtk.Label(xalign=0)
        self.bind_text(performance_title, "set_text", "dpi_title")
        performance_title.add_css_class("section-title")
        performance.append(performance_title)
        performance_description = Gtk.Label(xalign=0)
        self.bind_text(performance_description, "set_text", "dpi_description")
        performance_description.set_wrap(True)
        performance_description.add_css_class("dim-label")
        performance.append(performance_description)

        poll_title = Gtk.Label(xalign=0)
        self.bind_text(poll_title, "set_text", "polling_title")
        poll_title.add_css_class("heading")
        performance.append(poll_title)
        poll_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        poll_box.set_homogeneous(True)
        poll_box.set_hexpand(True)
        self.poll_buttons: dict[int, Gtk.ToggleButton] = {}
        first = None
        for hz in (125, 500, 1000, 2000, 4000):
            btn = Gtk.ToggleButton(label=f"{hz} Hz")
            btn.add_css_class("poll-rate")
            if first is None:
                first = btn
            else:
                btn.set_group(first)
            btn.connect("toggled", self.on_poll_toggled, hz)
            self.poll_buttons[hz] = btn
            poll_box.append(btn)
        performance.append(poll_box)

        preset_title = Gtk.Label(xalign=0)
        self.bind_text(preset_title, "set_text", "dpi_presets")
        preset_title.add_css_class("heading")
        performance.append(preset_title)
        preset_box = Gtk.FlowBox()
        preset_box.set_selection_mode(Gtk.SelectionMode.NONE)
        preset_box.set_max_children_per_line(7)
        preset_box.set_row_spacing(4)
        preset_box.set_column_spacing(4)
        self.preset_buttons: list[Gtk.ToggleButton] = []
        preset_first = None
        for dpi in (800, 1200, 1600, 2000, 2400, 2800, 3200):
            preset = Gtk.ToggleButton(label=str(dpi))
            preset.add_css_class("preset")
            if preset_first is None:
                preset_first = preset
            else:
                preset.set_group(preset_first)
            preset.connect("clicked", self.on_dpi_preset, dpi)
            self.preset_buttons.append(preset)
            preset_box.insert(preset, -1)
        performance.append(preset_box)

        self.dpi_spins: list[Gtk.SpinButton] = []
        self.stage_checks: list[Gtk.CheckButton] = []
        self.stage_rows: list[Gtk.Box] = []
        self.stage_labels: list[Gtk.Label] = []
        self.dpi_rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        performance.append(self.dpi_rows_box)
        stage_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.add_stage_button = Gtk.Button(label="＋")
        self.bind_text(self.add_stage_button, "set_tooltip_text", "add_stage")
        self.add_stage_button.connect("clicked", self.on_add_stage)
        self.remove_stage_button = Gtk.Button(label="−")
        self.bind_text(self.remove_stage_button, "set_tooltip_text", "remove_stage")
        self.remove_stage_button.connect("clicked", self.on_remove_stage)
        stage_controls.append(self.add_stage_button)
        stage_controls.append(self.remove_stage_button)
        stage_controls.append(Gtk.Box(hexpand=True))
        performance.append(stage_controls)

        self.apply_button, self.apply_button_label = self._action_button(
            "emblem-ok-symbolic", "apply_button"
        )
        self.apply_button.add_css_class("primary-action")
        self.apply_button.set_halign(Gtk.Align.FILL)
        self.apply_button.set_hexpand(True)
        self.apply_button.set_size_request(-1, 46)
        self.apply_button.connect("clicked", lambda *_: self.on_apply())
        performance.append(self.apply_button)
        page.append(performance)
        self._render_dpi_rows()

        extra = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        extra.add_css_class("surface-card")
        sensor_title = Gtk.Label(xalign=0)
        self.bind_text(sensor_title, "set_text", "sensor_title")
        sensor_title.add_css_class("section-title")
        extra.append(sensor_title)
        sensor_description = Gtk.Label(xalign=0)
        self.bind_text(sensor_description, "set_text", "sensor_description")
        sensor_description.set_wrap(True)
        sensor_description.add_css_class("dim-label")
        extra.append(sensor_description)
        lod_row = Adw.ComboRow(
            title="Lift-off distance",
            subtitle=self.tr("lod_subtitle"),
            model=Gtk.StringList.new(["1 mm", "2 mm"]),
        )
        self.bind_text(lod_row, "set_title", "lod_title")
        self.bind_text(lod_row, "set_subtitle", "lod_subtitle")
        lod_row.connect("notify::selected", lambda *_: self.collect())
        self.lod_row = lod_row
        extra.append(lod_row)
        angle_row = Adw.ActionRow(title="Angle snapping")
        self.bind_text(angle_row, "set_title", "angle_title")
        self.angle_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.angle_switch.connect("notify::active", lambda *_: self.collect())
        angle_row.add_suffix(self.angle_switch)
        angle_row.set_activatable_widget(self.angle_switch)
        extra.append(angle_row)
        motion_row = Adw.ActionRow(title="Motion sync")
        self.bind_text(motion_row, "set_title", "motion_title")
        self.motion_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.motion_switch.connect("notify::active", lambda *_: self.collect())
        motion_row.add_suffix(self.motion_switch)
        motion_row.set_activatable_widget(self.motion_switch)
        extra.append(motion_row)
        calibration_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        calibration_label = Gtk.Label(xalign=0, hexpand=True)
        self.bind_text(calibration_label, "set_text", "calibrate_title")
        calibration_row.append(calibration_label)
        self.calibrate_button = Gtk.Button()
        self.bind_text(self.calibrate_button, "set_label", "calibrate_button")
        self.calibrate_button.add_css_class("primary-action")
        self.calibrate_button.connect("clicked", self.on_calibrate)
        calibration_row.append(self.calibrate_button)
        extra.append(calibration_row)
        self.calibration_progress = Gtk.ProgressBar(show_text=True)
        self.calibration_progress.set_visible(False)
        extra.append(self.calibration_progress)
        self.calibration_status = Gtk.Label(xalign=0, wrap=True)
        self.calibration_status.add_css_class("dim-label")
        extra.append(self.calibration_status)
        deb_row = Adw.ComboRow(
            title="Debounce",
            subtitle="Not currently applied to the mouse",
            model=Gtk.StringList.new(["0 ms", "1 ms", "2 ms", "4 ms", "8 ms"]),
        )
        self.bind_text(deb_row, "set_title", "debounce_title")
        self.bind_text(deb_row, "set_subtitle", "debounce_subtitle")
        deb_row.connect("notify::selected", lambda *_: self.collect())
        deb_row.set_sensitive(False)
        self.deb_row = deb_row
        extra.append(deb_row)
        page.append(extra)

        # ToolbarView as window content; wrap with overlay
        overlay = Adw.ToastOverlay()
        overlay.set_child(toolbar)
        self.toast = overlay
        self.set_content(overlay)

        self.apply_language()
        GLib.timeout_add_seconds(3, self.reload)
        self.reload()

    def _make_page(self) -> Gtk.Box:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(16)
        page.set_margin_bottom(20)
        page.set_margin_start(20)
        page.set_margin_end(20)
        return page

    def _render_dpi_rows(self) -> None:
        was_syncing = self._syncing
        self._syncing = True
        self.dpi_rows_box.remove_all()
        self.dpi_spins.clear()
        self.stage_checks.clear()
        self.stage_rows.clear()
        self.stage_labels.clear()
        self.state.active_stage = min(
            max(0, self.state.active_stage), len(self.state.dpi_stages) - 1
        )
        root_check = None
        for index, dpi in enumerate(self.state.dpi_stages):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.add_css_class("stage-row")
            check = Gtk.CheckButton()
            if root_check is None:
                root_check = check
            else:
                check.set_group(root_check)
            check.connect("toggled", self.on_stage_toggled, index)
            check.set_active(index == self.state.active_stage)
            row.append(check)
            stage_label = Gtk.Label(xalign=0)
            stage_label.set_hexpand(True)
            row.append(stage_label)
            spin = Gtk.SpinButton.new_with_range(DPI_MIN, DPI_MAX, DPI_STEP)
            spin.set_width_chars(7)
            spin.set_value(dpi)
            spin.connect("value-changed", self.on_dpi_value_changed)
            row.append(spin)
            self.dpi_rows_box.append(row)
            self.stage_rows.append(row)
            self.stage_labels.append(stage_label)
            self.stage_checks.append(check)
            self.dpi_spins.append(spin)
        self.add_stage_button.set_sensitive(len(self.state.dpi_stages) < STAGE_COUNT)
        self.remove_stage_button.set_sensitive(len(self.state.dpi_stages) > 1)
        self._update_stage_labels()
        self._update_preset_selection()
        self._syncing = was_syncing

    def _update_stage_labels(self) -> None:
        for index, label in enumerate(self.stage_labels, start=1):
            label.set_text(
                f"{self.tr('stage')} {index}"
                if self.language == "en"
                else f"{self.tr('stage')}{index} 段"
            )

    def _update_preset_selection(self) -> None:
        if not self.dpi_spins:
            return
        current = int(self.dpi_spins[self.state.active_stage].get_value())
        presets = (800, 1200, 1600, 2000, 2400, 2800, 3200)
        for value, button in zip(presets, self.preset_buttons):
            button.set_active(value == current)

    def on_add_stage(self, *_args) -> None:
        self.collect()
        if len(self.state.dpi_stages) >= STAGE_COUNT:
            self.toast_msg(self.tr("stage_limit"))
            return
        self.state.dpi_stages.append(self.state.dpi_stages[-1])
        self.state.active_stage = len(self.state.dpi_stages) - 1
        self._syncing = True
        self._render_dpi_rows()
        self._syncing = False
        self.collect()

    def on_remove_stage(self, *_args) -> None:
        self.collect()
        if len(self.state.dpi_stages) <= 1:
            self.toast_msg(self.tr("stage_minimum"))
            return
        selected = self.state.active_stage
        self.state.dpi_stages.pop(selected)
        self.state.active_stage = min(selected, len(self.state.dpi_stages) - 1)
        self._syncing = True
        self._render_dpi_rows()
        self._syncing = False
        self.collect()

    def on_dpi_value_changed(self, *_args) -> None:
        self.collect()
        self._update_preset_selection()

    def on_dpi_preset(self, _button, dpi: int) -> None:
        if not self.dpi_spins:
            return
        self.dpi_spins[self.state.active_stage].set_value(dpi)
        self.collect()
        self._update_preset_selection()

    def _action_button(self, icon_name: str, text_key: str):
        button = Gtk.Button()
        button.set_halign(Gtk.Align.END)
        button.add_css_class("pill")
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        content.append(Gtk.Image.new_from_icon_name(icon_name))
        label = Gtk.Label()
        self.bind_text(label, "set_text", text_key)
        content.append(label)
        button.set_child(content)
        return button, label

    def tr(self, key: str, **values: object) -> str:
        return TEXT[self.language][key].format(**values)

    def bind_text(self, widget, setter: str, key: str) -> None:
        self._localized_text.append((widget, setter, key))
        getattr(widget, setter)(self.tr(key))

    def on_language_selected(self, dropdown, _param) -> None:
        self.language = "zh" if dropdown.get_selected() == 1 else "en"
        self.apply_language()

    def apply_language(self) -> None:
        selected_receiver = self.receiver_row.get_selected()
        selected_lod = self.lod_row.get_selected()
        selected_debounce = self.deb_row.get_selected()
        self._changing_language = True
        self._syncing = True
        for widget, setter, key in self._localized_text:
            getattr(widget, setter)(self.tr(key))
        self.settings_stack_page.set_title(self.tr("settings_tab"))
        self.connection_stack_page.set_title(self.tr("connection_tab"))
        self.receiver_row.set_model(
            Gtk.StringList.new([self.tr("target_1k"), self.tr("target_4k")])
        )
        lod_values = ["1 毫米", "2 毫米"] if self.language == "zh" else ["1 mm", "2 mm"]
        self.lod_row.set_model(Gtk.StringList.new(lod_values))
        debounce_values = (
            ["0 毫秒", "1 毫秒", "2 毫秒", "4 毫秒", "8 毫秒"]
            if self.language == "zh"
            else ["0 ms", "1 ms", "2 ms", "4 ms", "8 ms"]
        )
        self.deb_row.set_model(Gtk.StringList.new(debounce_values))
        self.receiver_row.set_selected(selected_receiver)
        self.lod_row.set_selected(selected_lod)
        self.deb_row.set_selected(selected_debounce)
        self._update_stage_labels()
        self._changing_language = False
        self._syncing = True
        self.push_ui()
        self._syncing = False
        if self._last_pair_output:
            self.show_pair_message(self._last_pair_output)

    def _translated_pair_output(self, line: str) -> str:
        if line.startswith("Pairing started via "):
            fields = line.split()
            path = fields[3] if len(fields) > 3 else "the receiver"
            return self.tr("pair_started", path=path)
        if "Dongle reports pairing pending" in line:
            return self.tr("pair_pending")
        if "Pairing succeeded" in line:
            return self.tr("pair_succeeded")
        if "status 3" in line:
            return self.tr("pair_failed")
        if "No success/failure report before timeout" in line:
            return self.tr("pair_timeout")
        if "receiver control HID interface not found" in line:
            return self.tr("pair_wrong_receiver")
        if line.startswith("Could not start pairing:"):
            return line if self.language == "en" else f"無法啟動配對：{line.partition(':')[2].strip()}"
        return line

    def show_pair_message(self, line: str) -> None:
        self._last_pair_output = line
        self.pair_result_label.set_text(self._translated_pair_output(line))
        if "status 3" in line.lower():
            self.pair_result_label.add_css_class("pair-failure")
        else:
            self.pair_result_label.remove_css_class("pair-failure")

    def _stat_card(self, caption: str, key: str | None = None) -> tuple[Gtk.Box, Gtk.Label]:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("surface-card")
        box.set_margin_top(3)
        box.set_margin_bottom(3)
        value = Gtk.Label(label="—")
        value.add_css_class("stat-value")
        value.set_xalign(0)
        cap = Gtk.Label(label=caption)
        if key:
            self.bind_text(cap, "set_text", key)
        cap.set_xalign(0)
        cap.add_css_class("dim-label")
        box.append(value)
        box.append(cap)
        return box, value

    def toast_msg(self, text: str) -> None:
        self.toast.add_toast(Adw.Toast(title=text))

    def reload(self) -> bool:
        self.receiver_interfaces = list_revenger_interfaces()
        self.state = refresh()
        self.push_ui()
        return True

    def push_ui(self) -> None:
        self._syncing = True
        st = self.state
        if len(self.dpi_spins) != len(st.dpi_stages):
            self._render_dpi_rows()
        connected = bool(st.connected)
        self.device_status_icon.set_from_icon_name(
            "emblem-ok-symbolic" if connected else "process-stop-symbolic"
        )
        self.device_status_icon.set_css_classes(
            ["success" if connected else "dim-label"]
        )
        self.device_status_label.set_text(
            self.tr("device_connected" if connected else "device_disconnected")
        )
        self.device_path_label.set_text(st.hidraw if connected and st.hidraw else "—")
        self.device_path_label.set_visible(connected)
        self.device_access_label.set_text(
            self.tr("access_ok") if st.access_ok else (st.access_error or "")
        )
        self.device_access_label.set_visible(connected and not st.access_ok)
        self.stat_dpi[1].set_text(f"{st.dpi:,}")
        self.stat_poll[1].set_text(f"{st.polling_hz} Hz")
        self.stat_battery[1].set_text(f"{st.battery}%" if st.battery is not None else "—")
        for i, spin in enumerate(self.dpi_spins):
            spin.set_value(st.dpi_stages[i])
        if 0 <= st.active_stage < len(self.stage_checks):
            self.stage_checks[st.active_stage].set_active(True)
        btn = self.poll_buttons.get(st.polling_hz)
        if btn is None and 250 not in self.poll_buttons:
            self.state.polling_hz = 500
            btn = self.poll_buttons.get(500)
        if btn:
            btn.set_active(True)
        self.lod_row.set_selected(0 if st.lod_mm <= 1 else 1)
        self.angle_switch.set_active(st.angle_snapping)
        self.motion_switch.set_active(st.motion_sync)
        mapping = {0: 0, 1: 1, 2: 2, 4: 3, 8: 4}
        self.deb_row.set_selected(mapping.get(st.debounce_ms, 0))
        self._syncing = False
        self.update_pair_availability()

    def update_pair_availability(self) -> None:
        connected = {
            iface.product
            for iface in getattr(self, "receiver_interfaces", [])
            if iface.is_control and iface.product in self.receiver_state_labels
        }
        for pid, label in self.receiver_state_labels.items():
            label.set_text(self.tr("receiver_detected" if pid in connected else "receiver_absent"))
        selected_pid = ONE_K_PID if self.receiver_row.get_selected() == 0 else FOUR_K_PID
        can_pair = len(connected) == 1 and selected_pid in connected and not self._pairing
        self.pair_button.set_sensitive(can_pair)
        if len(connected) > 1:
            self._pair_notice_key = "pair_multiple"
        elif not connected:
            self._pair_notice_key = "pair_none"
        elif selected_pid not in connected:
            self._pair_notice_key = "pair_wrong_receiver"
        else:
            self._pair_notice_key = "pair_initial"
        if self._last_pair_output and len(connected) == 1 and selected_pid in connected:
            self.show_pair_message(self._last_pair_output)
        else:
            self.pair_result_label.remove_css_class("pair-failure")
            self.pair_result_label.set_text(self.tr(self._pair_notice_key))

    def on_receiver_selected(self, *_args) -> None:
        if self._changing_language:
            return
        self._last_pair_output = None
        self.update_pair_availability()

    def on_stage_toggled(self, button: Gtk.CheckButton, index: int) -> None:
        if self._syncing or not button.get_active():
            return
        self.state.active_stage = index
        self.collect()
        self._update_preset_selection()

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
        self.state.angle_snapping = self.angle_switch.get_active()
        self.state.motion_sync = self.motion_switch.get_active()
        debounce_index = int(self.deb_row.get_selected())
        debounce = [0, 1, 2, 4, 8][debounce_index] if debounce_index < 5 else 0
        self.state.debounce_ms = debounce
        self.stat_dpi[1].set_text(f"{self.state.dpi:,}")
        self.stat_poll[1].set_text(f"{self.state.polling_hz} Hz")
        save_profile(self.state)

    def on_calibrate(self, *_args) -> None:
        """Show UIX's three-second calibration status flow, without claiming HID calibration."""
        self.calibrate_button.set_sensitive(False)
        self.calibration_progress.set_visible(True)
        self.calibration_progress.set_fraction(0)
        start_time = GLib.get_monotonic_time()

        def tick() -> bool:
            elapsed = (GLib.get_monotonic_time() - start_time) / 1_000_000
            fraction = min(elapsed / 3.0, 1.0)
            remaining = max(0, 3 - int(elapsed))
            self.calibration_progress.set_fraction(fraction)
            self.calibration_progress.set_text(
                self.tr("calibration_wait", seconds=remaining)
            )
            if fraction >= 1.0:
                self.calibration_status.set_text(self.tr("calibration_done"))
                self.calibration_button.set_sensitive(True)
                return False
            return True

        GLib.timeout_add(50, tick)


    def on_apply(self) -> None:
        self.collect()
        try:
            path = apply(self.state)
        except PermissionError:
            self.toast_msg(self.tr("permission_error"))
            return
        except Exception as exc:
            self.toast_msg(str(exc))
            return
        self.toast_msg(self.tr("settings_sent", path=path))
        self.reload()

    def on_pair(self, *_args) -> None:
        receiver = "4k" if self.receiver_row.get_selected() == 1 else "1k"
        receiver_label = self.tr("receiver_4k" if receiver == "4k" else "receiver_1k")
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=self.tr("pair_heading", receiver=receiver_label),
            body=self.tr("pair_instructions"),
        )
        dialog.add_response("cancel", self.tr("cancel"))
        dialog.add_response("pair", self.tr("pair_button"))
        dialog.set_response_appearance("pair", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("pair")
        dialog.set_close_response("cancel")
        dialog.connect("response", self.on_pair_confirmed, receiver)
        dialog.present()

    def on_pair_confirmed(self, _dialog, response: str, receiver: str) -> None:
        if response != "pair" or self._pairing:
            return
        self._pairing = True
        self.pair_button.set_sensitive(False)
        self._last_pair_output = None
        self._pair_notice_key = "pair_preparing"
        self.pair_result_label.set_text(self.tr(self._pair_notice_key))

        def run_pair() -> None:
            command = [
                sys.executable,
                "-u",
                str(ROOT / "revengerctl-cli"),
                "pair",
                "--receiver",
                receiver,
                "--yes",
            ]
            try:
                process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert process.stdout is not None
                for line in process.stdout:
                    message = line.strip()
                    if message:
                        GLib.idle_add(self.show_pair_message, message)
                process.wait()
            except OSError as exc:
                GLib.idle_add(self.show_pair_message, f"Could not start pairing: {exc}")
            finally:
                GLib.idle_add(self.pairing_finished)

        threading.Thread(target=run_pair, daemon=True).start()

    def pairing_finished(self) -> bool:
        self._pairing = False
        self.pair_button.set_sensitive(True)
        self.reload()
        return GLib.SOURCE_REMOVE


class CompanionApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, _app) -> None:
        windows = self.get_windows()
        if windows:
            windows[0].present()
            return
        CompanionWindow(self).present()


def main() -> int:
    Adw.init()
    return CompanionApp().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
