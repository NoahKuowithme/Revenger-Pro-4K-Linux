import unittest
from unittest.mock import patch

from revengerctl.device import HidInterface, find_1k_control, find_4k_control, find_control


def _interface(path: str, product: int, report_len: int = 150) -> HidInterface:
    return HidInterface(
        path=path,
        index=int(path.removeprefix("/dev/hidraw")),
        vendor=0x3554,
        product=product,
        name="Compx Revenger Pro Wireless",
        phys="",
        report_len=report_len,
    )


class ReceiverSelectionTests(unittest.TestCase):
    def test_control_prefers_4k_receiver_when_2_4ghz_receiver_appears_first(self):
        receiver_24g = _interface("/dev/hidraw10", 0xF5DC)
        receiver_4k = _interface("/dev/hidraw7", 0xF5DF, 266)
        with patch(
            "revengerctl.device.list_revenger_interfaces",
            return_value=[receiver_24g, receiver_4k],
        ):
            self.assertIs(find_control(), receiver_4k)
            self.assertIs(find_4k_control(), receiver_4k)

    def test_pair_target_is_not_fallback_2_4ghz_receiver(self):
        receiver_24g = _interface("/dev/hidraw10", 0xF5DC)
        with patch(
            "revengerctl.device.list_revenger_interfaces",
            return_value=[receiver_24g],
        ):
            self.assertIsNone(find_4k_control())

    def test_1k_pair_target_selects_only_2_4ghz_receiver(self):
        receiver_24g = _interface("/dev/hidraw10", 0xF5DC)
        receiver_4k = _interface("/dev/hidraw7", 0xF5DF, 266)
        with patch(
            "revengerctl.device.list_revenger_interfaces",
            return_value=[receiver_4k, receiver_24g],
        ):
            self.assertIs(find_1k_control(), receiver_24g)


if __name__ == "__main__":
    unittest.main()
