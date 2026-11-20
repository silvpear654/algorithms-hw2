"""A small standard-library HTTP interface for the URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, quote, unquote, urlsplit

from src.hash_table import HashTable, LinearProbingHashTable
from src.shortener import Shortener

MAX_FORM_BYTES = 16_384


def _hash_explanation(key: str, capacity: int) -> str:
    value = 0
    expression = "0"
    for character in key:
        value = value * 31 + ord(character)
        expression = f"({expression} * 31 + {ord(character)})"
    return f"{expression} = {value}; {value} % {capacity} = {value % capacity}"


class ShortenerHandler(BaseHTTPRequestHandler):
    def _send_html(self, status: int, document: str) -> None:
        body = document.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _page(self, title: str, content: str) -> str:
        return (
            "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
            f"<title>{escape(title)}</title><body><h1>{escape(title)}</h1>"
            f"{content}<p><a href=\"/\">Shorten another URL</a> | "
            "<a href=\"/table\">Inspect table</a></p></body></html>"
        )

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            content = (
                '<form action="/shorten" method="post">'
                '<label>URL <input name="url" type="url" required></label> '
                '<button type="submit">Shorten</button></form>'
            )
            self._send_html(200, self._page("URL shortener", content))
            return
        if path == "/table":
            self._render_table()
            return
        if path.startswith("/") and "/" not in path[1:]:
            code = unquote(path[1:])
            try:
                url = self.server.shortener.expand(code)
            except ValueError:
                self._send_html(400, self._page("Invalid code", "<p>Invalid short code.</p>"))
                return
            except KeyError:
                self._send_html(404, self._page("Not found", "<p>Unknown short code.</p>"))
                return
            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_html(404, self._page("Not found", "<p>Unknown path.</p>"))

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/shorten":
            self._send_html(404, self._page("Not found", "<p>Unknown path.</p>"))
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_html(400, self._page("Invalid form", "<p>Invalid content length.</p>"))
            return
        if length < 0:
            self._send_html(400, self._page("Invalid form", "<p>Invalid content length.</p>"))
            return
        if length > MAX_FORM_BYTES:
            self._send_html(413, self._page("Form too large", "<p>URL form is too large.</p>"))
            return
        try:
            body = self.rfile.read(length).decode("utf-8")
            fields = parse_qsl(body, keep_blank_values=True, max_num_fields=16)
        except (UnicodeDecodeError, ValueError):
            self._send_html(400, self._page("Invalid form", "<p>Could not read the URL form.</p>"))
            return
        urls = [value for name, value in fields if name == "url"]
        if len(urls) != 1:
            self._send_html(400, self._page("Invalid URL", "<p>Submit exactly one URL.</p>"))
            return
        try:
            code = self.server.shortener.shorten(urls[0])
            if self.server.linear_shortener is not None:
                linear_code = self.server.linear_shortener.shorten(urls[0])
                if linear_code != code:
                    raise RuntimeError("shortener tables generated different codes")
        except ValueError:
            self._send_html(400, self._page("Invalid URL", "<p>Enter a valid HTTP(S) URL.</p>"))
            return

        link = f"/{quote(code)}"
        content = (
            f"<p>Short link: <a href=\"{escape(link, quote=True)}\">"
            f"{escape(link)}</a></p><p>Original URL: "
            f"<code>{escape(urls[0])}</code></p>"
        )
        self._send_html(200, self._page("URL shortened", content))

    def _render_table(self) -> None:
        tables = [self.server.shortener.table]
        if self.server.linear_shortener is not None:
            tables.append(self.server.linear_shortener.table)
        styles = (
            "<style>"
            ".chain{display:flex;align-items:center;gap:.5rem;list-style:none;"
            "margin:.25rem 0;padding:.75rem;overflow-x:auto;background:#f5f7fa}"
            ".chain-node{flex:0 0 18rem;overflow-wrap:anywhere;border:1px solid "
            "#9aa7b5;border-radius:.35rem;padding:.75rem;background:white}"
            ".chain-arrow{font-size:1.5rem;color:#526579}"
            "</style>"
        )
        sections = []
        for table in tables:
            linear_probing = isinstance(table, LinearProbingHashTable)
            strategy = "Linear probing" if linear_probing else "Separate chaining"
            location_label = "Slot" if linear_probing else "Bucket"
            rows = []
            for index in range(table.capacity):
                entries = table.items_at(index)
                if entries:
                    nodes = []
                    for position, (key, value) in enumerate(entries):
                        calculation = _hash_explanation(key, table.capacity)
                        home = table.hash_details(key)[1]
                        code = str(value)
                        short_link = f"/{quote(code, safe='')}"
                        if linear_probing:
                            probe_path = table.probe_path(key)
                            path = " -> ".join(str(slot) for slot in probe_path)
                            inspection = (
                                f"Home slot: {home}; inspected slots: "
                                f"<code>{escape(path)}</code> "
                                f"({len(probe_path)} probes)"
                            )
                        else:
                            inspection = (
                                f"Bucket: {home}; chain position: "
                                f"{position + 1} of {len(entries)}; nodes inspected: "
                                f"{position + 1}"
                            )
                        nodes.append(
                            '<li class="chain-node">'
                            f"<strong>URL key:</strong> <code>{escape(key)}</code><br>"
                            f"<strong>Short code:</strong> <code>{escape(code)}</code><br>"
                            f'<strong>Short link:</strong> <a href="{escape(short_link, quote=True)}">'
                            f"{escape(short_link)}</a><details>"
                            f"<summary>Horner hash calculation</summary>"
                            f"<code>{escape(calculation)}</code><br>"
                            f"{inspection}</details></li>"
                        )
                        if position + 1 < len(entries):
                            nodes.append(
                                '<li class="chain-arrow" aria-hidden="true">&rarr;</li>'
                            )
                    contents = (
                        '<ol class="chain" aria-label="Linked-list nodes">'
                        + "".join(nodes)
                        + "</ol>"
                    )
                else:
                    contents = "<span>empty</span>"
                rows.append(
                    f"<tr><th scope=\"row\">{index}</th><td>{contents}</td></tr>"
                )
            sections.append(
                f"<section><h2>{strategy} table</h2>"
                f"<p>Each populated cell shows its "
                f"{'probe path' if linear_probing else 'linked list'} "
                "and Horner hash calculation.</p>"
                + f"<table border=\"1\"><thead><tr><th>{location_label}</th>"
                "<th>Entries</th></tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table></section>"
            )
        content = styles + "".join(sections)
        self._send_html(200, self._page("Hash table inspection", content))


class ShortenerHTTPServer(HTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        shortener: Shortener | None = None,
        linear_shortener: Shortener | None = None,
    ):
        super().__init__(address, ShortenerHandler)
        self.shortener = shortener if shortener is not None else Shortener()
        self.linear_shortener = linear_shortener


def create_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    shortener: Shortener | None = None,
    linear_shortener: Shortener | None = None,
) -> ShortenerHTTPServer:
    return ShortenerHTTPServer((host, port), shortener, linear_shortener)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--strategy", choices=("chaining", "linear", "both"), default="both"
    )
    args = parser.parse_args()
    linear_shortener = None
    if args.strategy == "both":
        shortener = Shortener(table_type=HashTable)
        linear_shortener = Shortener(table_type=LinearProbingHashTable)
    else:
        table_type = (
            HashTable if args.strategy == "chaining" else LinearProbingHashTable
        )
        shortener = Shortener(table_type=table_type)
    server = create_server(
        port=args.port,
        shortener=shortener,
        linear_shortener=linear_shortener,
    )
    print(f"Serving on http://127.0.0.1:{args.port} ({args.strategy})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
