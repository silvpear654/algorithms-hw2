import unittest

from src.hash_table import HashTable, LinearProbingHashTable
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

    def test_shortener_works_with_both_table_implementations(self):
        for table_type in (HashTable, LinearProbingHashTable):
            with self.subTest(table_type=table_type.__name__):
                shortener = Shortener(table_type=table_type, capacity=8)
                url = "https://example.com"
                code = shortener.shorten(url)
                self.assertEqual(code, "0")
                self.assertEqual(shortener.shorten(url), code)
                self.assertEqual(shortener.expand(code), url)


if __name__ == "__main__":
    unittest.main()
