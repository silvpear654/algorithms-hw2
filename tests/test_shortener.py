import unittest

from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def test_codes_start_at_zero_and_repeated_urls_are_idempotent(self):
        shortener = Shortener()
        url = "https://example.com/a?b=c"
        code = shortener.shorten(url)

        self.assertEqual(code, "0")
        self.assertEqual(shortener.shorten(url), code)
        self.assertEqual(shortener.expand(code), url)

    def test_invalid_urls_are_rejected(self):
        shortener = Shortener()
        for url in ("", "ftp://example.com", "https:///path", "not a URL", None):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_invalid_and_unknown_codes_are_distinct(self):
        shortener = Shortener()
        with self.assertRaises(ValueError):
            shortener.expand("bad!")
        with self.assertRaises(KeyError):
            shortener.expand("1")


if __name__ == "__main__":
    unittest.main()
