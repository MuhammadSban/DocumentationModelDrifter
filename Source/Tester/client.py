# sends the tester's HTTP calls with the standard library, each sent once (contract §6: no retries)

from __future__ import annotations

import ipaddress
import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

# caps one call to the target, contract §6
CALL_TIMEOUT = 90.0


@dataclass
class Reply:
    # holds one answer from the target: its status, the parsed JSON body (None if not JSON) and the raw text
    status: int
    body: object
    text: str
    new_url: str | None = None  # names a 3xx's Location, made absolute; the tester never follows it


class NoReply(Exception):
    # reports a call the target never answered: refused, unreachable or past its timeout
    pass


class Refused(NoReply):
    # reports a target the hosted tester will not call, an internal or not globally routable address
    pass


def check_target(url: str) -> None:
    # refuses, on Railway only, an internal name or a host with any address that is not global,
    # so the hosted tester cannot be pointed at Railway's private network or the metadata address
    if not os.environ.get("RAILWAY_PROJECT_ID"):
        return
    # drops a trailing dot, so x.railway.internal. is the same internal name
    host = (urlsplit(url).hostname or "").rstrip(".")
    if host.endswith(".internal"):
        raise Refused(f"{host} is an internal name, which the hosted tester does not call")
    try:
        found = socket.getaddrinfo(host, None)
    except (OSError, UnicodeError) as err:
        raise NoReply(f"{host} does not resolve: {err}") from None
    for *_, sockaddr in found:
        address = ipaddress.ip_address(str(sockaddr[0]).split("%")[0])
        # unwraps ::ffff:a.b.c.d itself, so the verdict does not depend on the Python version
        if address.version == 6 and address.ipv4_mapped is not None:
            address = address.ipv4_mapped
        if not address.is_global:
            raise Refused(f"{host} resolves to {address}, which is not a public address the hosted tester calls")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # follows no redirect on any host, so a 3xx comes back as the answer and no unchecked URL is called
    def redirect_request(self, *args, **kwargs):
        return None


# sends every call through the handler above
OPENER = urllib.request.build_opener(_NoRedirect)


def call(method: str, url: str, payload: object = None, raw: bytes | None = None,
         timeout: float | None = None) -> Reply:
    # sends one request, JSON-encoding payload unless raw bytes are given; any HTTP status is a Reply.
    # The target is checked first, so a refused one receives nothing
    check_target(url)
    data = raw if raw is not None else None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    start = time.monotonic()
    new_url = None
    try:
        with OPENER.open(request, timeout=CALL_TIMEOUT if timeout is None else timeout) as resp:
            status, text = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status, text = err.code, err.read().decode("utf-8", "replace")
        location = err.headers.get("Location") if 300 <= status < 400 and err.headers else None
        new_url = urljoin(url, location) if location else None
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as err:
        _log(method, url, "no-reply", start)
        raise NoReply(str(getattr(err, "reason", err))) from None
    _log(method, url, status, start)
    try:
        body = json.loads(text)
    except ValueError:
        body = None
    return Reply(status, body, text, new_url)


def _log(method: str, url: str, status: int | str, start: float) -> None:
    # prints one line per call with its time, so a full run can be timed call by call in the host's logs
    print(f"tester call {method} {url} {status} {time.monotonic() - start:.2f} s", flush=True)
