import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.hash_table import LinearProbingHashTable
from src.server import create_server
from src.shortener import Shortener


class ShortenerServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_form_shortening_and_redirect(self):
        self.connection.request(
            "GET", "/"
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b'name="url"', response.read())

        url = "https://example.com/a"
        self.connection.request(
            "POST",
            "/shorten",
            body=urlencode({"url": url}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b'href="/0"', response.read())

        self.connection.request("GET", "/0")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), url)
        response.read()

    def test_table_view_shows_chaining_and_hash_calculation(self):
        self.server.shortener.shorten("https://example.com")
        self.connection.request("GET", "/table")
        response = self.connection.getresponse()
        body = response.read()

        self.assertEqual(response.status, 200)
        self.assertIn(b"Separate chaining table", body)
        self.assertIn(b"Horner hash calculation", body)
        self.assertIn(b"chain position:", body)
        self.assertIn(b"nodes inspected:", body)
        self.assertIn(b"https://example.com", body)

    def test_table_view_shows_linear_probe_path(self):
        self.server.shortener = Shortener(
            table_type=LinearProbingHashTable, capacity=5
        )
        self.server.shortener.shorten("https://example.com")
        self.connection.request("GET", "/table")
        response = self.connection.getresponse()
        body = response.read()

        self.assertEqual(response.status, 200)
        self.assertIn(b"Linear probing table", body)
        self.assertIn(b"probe path", body)
        self.assertIn(b"inspected slots:", body)

    def test_invalid_input_and_unknown_codes_have_error_statuses(self):
        self.connection.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "ftp://example.com"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 400)
        response.read()

        self.connection.request("GET", "/1")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 404)
        response.read()


if __name__ == "__main__":
    unittest.main()
