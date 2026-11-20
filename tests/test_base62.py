import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_zero_encodes_as_zero(self):
        self.assertEqual(encode(0), "0")

    def test_digits_follow_the_specified_alphabet_order(self):
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for value, digit in enumerate(alphabet):
            with self.subTest(value=value):
                self.assertEqual(encode(value), digit)
                self.assertEqual(decode(digit), value)
        self.assertEqual(encode(62), "10")
        self.assertEqual(decode("10"), 62)

    def test_round_trip(self):
        for number in (1, 61, 62, 3844, 2**128):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_invalid_numbers_are_rejected(self):
        for number in (-1, True, 1.5, "12"):
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    encode(number)

    def test_empty_or_invalid_codes_are_rejected(self):
        for code in ("", "a?", "é", None):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)


if __name__ == "__main__":
    unittest.main()
