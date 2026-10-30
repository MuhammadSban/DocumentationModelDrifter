# serves the console and forwards /system/* to the v1 API, so the page and the API share one origin

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB = Path(__file__).resolve().parent

# forwards only what the API needs, hop-by-hop headers never cross a proxy
PASS_REQUEST = ("content-type", "accept")
PASS_RESPONSE = ("content-type",)


class Handler(SimpleHTTPRequestHandler):
    # serves the console from this folder, proxying /system/* so the browser stays same-origin

    def __init__(self, *args, api: str, **kwargs) -> None:
        self.api = api.rstrip("/")
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self) -> None:
        # splits the two jobs: API calls go upstream, everything else is a file
        if self.path.startswith("/system/") or self.path == "/system":
            self._forward("GET")
        else:
            super().do_GET()

    def do_POST(self) -> None:
        # only the API takes POST, a static file never does
        if self.path.startswith("/system/"):
            self._forward("POST")
        else:
            self.send_error(405, "POST is only forwarded to /system/")

    def _forward(self, method: str) -> None:
        # relays one request upstream and copies the answer back verbatim
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items() if k.lower() in PASS_REQUEST}
        request = urllib.request.Request(self.api + self.path, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=180) as answer:
                self._relay(answer.status, answer.headers, answer.read())
        except urllib.error.HTTPError as exc:
            # passes the contract's own error body through, the page reads its code
            self._relay(exc.code, exc.headers, exc.read())
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            self._fail(f"cannot reach the API at {self.api}: {reason}")

    def _relay(self, status: int, headers, payload: bytes) -> None:
        # writes an upstream answer back to the browser
        self.send_response(status)
        for name in PASS_RESPONSE:
            if headers.get(name):
                self.send_header(name, headers[name])
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _fail(self, message: str) -> None:
        # answers in the contract's error shape, so the page shows it like any other failure
        payload = json.dumps({"code": "TIMEOUT", "message": message}).encode("utf-8")
        self.send_response(502)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args) -> None:
        # keeps the console readable, one line per request without the date prefix
        print(f"  {fmt % args}")


def main() -> None:
    # starts the console in front of a running API
    parser = argparse.ArgumentParser(description="Serve the DocumentationDrifter console.")
    parser.add_argument("--port", type=int, default=5173, help="port to serve the console on")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="base URL of the v1 API")
    args = parser.parse_args()

    if not (WEB / "index.html").is_file():
        raise SystemExit(f"no console found at {WEB / 'index.html'}")

    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, api=args.api))
    print(f"console  http://127.0.0.1:{args.port}")
    print(f"api      {args.api}  (proxied at /system/*)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
