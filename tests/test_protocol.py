import unittest

from revengerctl.protocol import (
    DEFAULT_PAIR_CID,
    OUT_LEN,
    POLLING_CODES,
    decode_dpi,
    enter_dongle_pair,
    encode_dpi,
    parse_dongle_pair_status,
    read_dongle_pair_status,
    set_active_stage,
    set_dpi_stage,
    set_polling,
)


class ProtocolTests(unittest.TestCase):
    def test_dpi_roundtrip(self):
        for dpi in (50, 400, 1600, 13000, 26000):
            encoded = encode_dpi(dpi)
            self.assertEqual(encoded[0], encoded[1])
            self.assertEqual(decode_dpi(*encoded), dpi)

    def test_dpi_encoding_matches_uix_3395_format(self):
        self.assertEqual(encode_dpi(1600), (0x1F, 0x1F, 0x00))
        self.assertEqual(encode_dpi(13000), (0x03, 0x03, 0x44))
        self.assertEqual(encode_dpi(26000), (0x07, 0x07, 0x88))
        for invalid in (0, 49, 51, 26001):
            with self.subTest(dpi=invalid), self.assertRaises(ValueError):
                encode_dpi(invalid)

    def test_polling_codes_match_uix(self):
        self.assertEqual(POLLING_CODES, {
            125: 0x08,
            250: 0x04,
            500: 0x02,
            1000: 0x01,
            2000: 0x10,
            4000: 0x20,
        })
        self.assertEqual(
            set_polling(4000),
            bytes.fromhex("08 07 00 00 00 02 20 35 00 00 00 00 00 00 00 00 ef"),
        )

    def test_active_stage_uses_uix_mouse_config_record(self):
        self.assertEqual(
            set_active_stage(1),
            bytes.fromhex("08 07 00 00 04 02 01 54 00 00 00 00 00 00 00 00 eb"),
        )
        with self.assertRaises(ValueError):
            set_active_stage(5)

    def test_dpi_flash_packets_match_uix(self):
        self.assertEqual(
            set_dpi_stage(0, 800),
            bytes.fromhex("08 07 00 00 0c 04 0f 0f 00 37 00 00 00 00 00 00 e1"),
        )
        self.assertEqual(
            set_dpi_stage(4, 26000),
            bytes.fromhex("08 07 00 00 1c 04 07 07 88 bf 00 00 00 00 00 00 d1"),
        )
        self.assertEqual(len(set_polling(4000)), OUT_LEN)

    def test_uix_pair_packets_match_native_builders(self):
        # Derived from HIDUsb.dll's EnterDonglePairOnlyCid and
        # ReadDonglePairStatus builders, including its 0x55 checksum.
        self.assertEqual(
            enter_dongle_pair(DEFAULT_PAIR_CID),
            bytes.fromhex("08 05 00 00 00 02 00 00 35 00 00 00 00 00 00 00 11"),
        )
        self.assertEqual(
            read_dongle_pair_status(),
            bytes.fromhex("08 06 00 00 00 00 00 00 00 00 00 00 00 00 00 00 47"),
        )

    def test_pair_cid_must_fit_one_byte(self):
        with self.assertRaises(ValueError):
            enter_dongle_pair(256)

    def test_parse_uix_pairing_status(self):
        report = bytearray(read_dongle_pair_status()[:16])
        report[6] = 2
        report.append((0x55 - sum(report)) & 0xFF)
        self.assertEqual(parse_dongle_pair_status(bytes(report)), 2)
        self.assertIsNone(parse_dongle_pair_status(bytes(report[:-1])))
        report[-1] ^= 1
        self.assertIsNone(parse_dongle_pair_status(bytes(report)))


if __name__ == "__main__":
    unittest.main()
