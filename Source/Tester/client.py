# sends the tester's HTTP calls with the standard library, each sent once (contract §6: no retries)

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

# caps one call to the target, contract §6
CALL_TIMEOUT = 90.0


@dataclass
class Reply:
    # holds one answer from the target: its status, the parsed JSON body (None if not JSON) and the raw text
    status: int
    body: object
    text: str


class NoReply(Exception):
    # reports a call the target never answered: refused, unreachable or past its timeout
    pass


def call(method: str, url: str, payload: object = None, raw: bytes | None = None,
         timeout: float | None = None) -> Reply:
    # sends one request, JSON-encoding payload unless raw bytes are given; any HTTP status is a Reply
    data = raw if raw is not None else None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=CALL_TIMEOUT if timeout is None else timeout) as resp:
            status, text = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status, text = err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as err:
        _log(method, url, "no-reply", start)
        raise NoReply(str(getattr(err, "reason", err))) from None
    _log(method, url, status, start)
    try:
        body = json.loads(text)
    except ValueError:
        body = None
    return Reply(status, body, text)


def _log(method: str, url: str, status: int | str, start: float) -> None:
    # prints one line per call with its time, so a full run can be timed call by call in the host's logs
    print(f"tester call {method} {url} {status} {time.monotonic() - start:.2f} s", flush=True)
