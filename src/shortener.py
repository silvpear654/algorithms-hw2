"""URL shortening backed by a hand-written hash table."""

from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable


class Shortener:
    def __init__(
        self, table_type: type[HashTable] = HashTable, capacity: int = 101
    ):
        self._urls = table_type(capacity)
        self._codes = table_type(capacity)
        self._next_id = 0

    @property
    def table(self) -> HashTable:
        return self._urls

    def shorten(self, url: str) -> str:
        if not isinstance(url, str) or not url or any(
            character.isspace() for character in url
        ):
            raise ValueError("url must be a non-empty absolute HTTP(S) URL")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("url must be a valid absolute HTTP(S) URL") from error
        if parsed.scheme not in ("http", "https") or not hostname:
            raise ValueError("url must be a valid absolute HTTP(S) URL")

        existing_code = self._urls.search(url)
        if existing_code is not None:
            return existing_code

        code = encode(self._next_id)
        self._next_id += 1
        self._urls.insert(url, code)
        self._codes.insert(code, url)
        return code

    def expand(self, code: str) -> str:
        decode(code)
        url = self._codes.search(code)
        if url is None:
            raise KeyError(code)
        return url
