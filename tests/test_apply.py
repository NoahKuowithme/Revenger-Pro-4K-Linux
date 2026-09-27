import unittest
from types import SimpleNamespace
from unittest.mock import patch

from revengerctl.apply import apply, apply_dpi_stage, apply_polling
from revengerctl.protocol import MouseState, set_active_stage, set_dpi_stage, set_polling


class ApplyTests(unittest.TestCase):
    def _assert_one_report(self, apply_one, expected):
        with (
            patch(
                "revengerctl.apply.find_control",
                return_value=SimpleNamespace(path="/dev/hidraw-test"),
            ),
            patch("revengerctl.apply.HidRaw") as hidraw,
        ):
            hid = hidraw.return_value.__enter__.return_value

            self.assertEqual(apply_one(), "/dev/hidraw-test")

        hid.set_feature.assert_called_once_with(expected)

    def test_dpi_command_writes_and_activates_the_selected_stage(self):
        with (
            patch(
                "revengerctl.apply.find_control",
                return_value=SimpleNamespace(path="/dev/hidraw-test"),
            ),
            patch("revengerctl.apply.HidRaw") as hidraw,
            patch("revengerctl.apply.time.sleep"),
        ):
            hid = hidraw.return_value.__enter__.return_value
            self.assertEqual(apply_dpi_stage(2, 1600), "/dev/hidraw-test")

        self.assertEqual(
            [call.args[0] for call in hid.set_feature.call_args_list],
            [set_dpi_stage(2, 1600), set_active_stage(2)],
        )

    def test_polling_command_writes_only_the_rate(self):
        expected = set_polling(4000)
        self._assert_one_report(lambda: apply_polling(4000), expected)

    def test_apply_sends_rate_dpi_stages_and_active_stage(self):
        state = MouseState(polling_hz=500, dpi_stages=[400, 800, 1600, 3200, 6400])
        with (
            patch(
                "revengerctl.apply.find_control",
                return_value=SimpleNamespace(path="/dev/hidraw-test"),
            ),
            patch("revengerctl.apply.HidRaw") as hidraw,
            patch("revengerctl.apply.time.sleep") as sleep,
        ):
            hid = hidraw.return_value.__enter__.return_value

            self.assertEqual(apply(state), "/dev/hidraw-test")

        self.assertEqual(hid.set_feature.call_count, 7)
        self.assertEqual(
            [call.args[0] for call in hid.set_feature.call_args_list],
            [
                set_polling(500),
                *(set_dpi_stage(i, dpi) for i, dpi in enumerate(state.dpi_stages)),
                set_active_stage(state.active_stage),
            ],
        )
        self.assertEqual(sleep.call_count, 6)


if __name__ == "__main__":
    unittest.main()
