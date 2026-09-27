import unittest

from revengerctl.protocol import (
    OUT_LEN,
    decode_dpi,
    encode_dpi,
    set_dpi_stage,
    set_polling,
)


class ProtocolTests(unittest.TestCase):
    def test_dpi_roundtrip(self):
        lo, hi = encode_dpi(1600)
        self.assertEqual(decode_dpi(lo, hi), 1600)
        lo, hi = encode_dpi(26000)
        self.assertEqual(decode_dpi(lo, hi), 26000)

    def test_packets_are_17_bytes(self):
        pkt = set_polling(4000)
        self.assertEqual(len(pkt), OUT_LEN)
        self.assertEqual(pkt[0], 0x08)
        dpi = set_dpi_stage(1, 800)
        self.assertEqual(len(dpi), OUT_LEN)
        self.assertEqual(dpi[1], 0x07)
        self.assertEqual(dpi[2], 2)


if __name__ == "__main__":
    unittest.main()
