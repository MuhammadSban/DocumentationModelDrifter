# tells our own system from another, so the suite report carries coverage.model only for our own (W4-8)

from __future__ import annotations

import os
from urllib.parse import urlsplit

# names the system URL in our course registry row
REGISTRY_SYSTEM_URL = "https://documentationmodeldrifter-production.up.railway.app/system"

DEFAULT_PORTS = {"http": 80, "https": 443}
LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def normalise(url: str) -> str:
    # lowercases scheme and host, drops a default port and a trailing slash, keeps the path as given
    parts = urlsplit(url.strip())
    scheme, host, port = parts.scheme.lower(), (parts.hostname or "").lower(), parts.port
    netloc = f"[{host}]" if ":" in host else host
    if port is not None and port != DEFAULT_PORTS.get(scheme):
        netloc += f":{port}"
    return f"{scheme}://{netloc}{parts.path.rstrip('/')}"


def is_own(target_url: str) -> bool:
    # answers whether target_url is the Railway public URL, the registry URL, or localhost off Railway
    try:
        target = normalise(target_url)
        host = (urlsplit(target).hostname or "").lower()
    except ValueError:
        return False
    own = {normalise(REGISTRY_SYSTEM_URL)}
    domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if domain:
        own.add(normalise(f"https://{domain}/system"))
    if target in own:
        return True
    on_railway = bool(os.environ.get("RAILWAY_PROJECT_ID"))
    return not on_railway and host in LOOPBACK and urlsplit(target).path == "/system"
