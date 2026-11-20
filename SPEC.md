# URL shortener specification

## 1. Purpose

The program accepts an absolute HTTP or HTTPS URL and returns a short code. The
code can later be expanded to the original URL. The implementation uses
hand-written hash tables to store the mapping.

## 2. Base62 encoding

`src/base62.py` provides `encode(number: int) -> str` and
`decode(code: str) -> int`. The alphabet is `0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`,
in that order. Zero encodes as `"0"`. Negative, non-integer, empty, and
non-alphabet inputs raise `ValueError`.

## 3. Hash tables

`HashTable(capacity=...)` uses separate chaining and a fixed positive capacity.
`LinearProbingHashTable(capacity=...)` uses open addressing with linear probing
and the same interface. Both use a polynomial Horner hash with multiplier 31
over Unicode code points; the table index is the hash value modulo capacity.
Neither implementation uses Python's `dict`, `set`, or built-in `hash()`.

`insert(key, value)` adds a key or replaces its value. `search(key)` returns
the value or `None` when absent. `delete(key)` returns whether a key existed.
`len(table)` is the number of stored keys. Every search/insert/delete records
the number of inspected nodes or slots in `last_probes`; an unsuccessful
chained search in an empty bucket inspects zero nodes. A linear-probing table
raises `OverflowError` when inserting a new key into a full table. Both reject
non-string keys with `TypeError`; capacity must be a positive integer.

## 4. Shortener

`Shortener` provides `shorten(url) -> str` and `expand(code) -> str`. It accepts
only absolute `http` and `https` URLs with a hostname. Re-shortening the same
URL returns its original code. Codes are assigned from an increasing integer
sequence encoded in base62, not derived from a hash value. Invalid URLs or
codes raise `ValueError`; an unknown but syntactically valid code raises
`KeyError`.

## 5. Web server

`make serve` runs an HTTP server on port 8000 by default; `PORT` can override
the port. `GET /` serves the URL input form. `POST /shorten` accepts a
form-encoded `url` and returns a page containing its short link. `GET /<code>`
redirects to the expanded URL, and `GET /table` renders the current chained
table including bucket contents, inspected cells, and the Horner-hash
calculation. Unknown routes return 404 and invalid input returns 400.

## 6. Boundary cases

- Base62 zero, alphabet boundary values, large integers, negative values,
  empty strings, and invalid characters.
- Hash table capacity validation, collisions, updates, absent keys, deletion,
  wraparound from the final slot to slot zero, and a full linear-probing table.
- Shortening repeated URLs, invalid URL schemes/hosts, generated code zero,
  invalid codes, and unknown valid codes.
- Server form input validation, redirects, table inspection, and unknown paths.

## Decisions recorded from reviewing the draft

- Codes come from a monotonic counter rather than hash values, so collisions in
  the storage table do not affect short-code uniqueness.
- The tables have fixed capacities, making load factor and probe counts
  observable and allowing the linear-probing full-table boundary to be tested.
- Duplicate URLs are idempotent, while malformed URLs and unknown codes have
  distinct error behavior.
