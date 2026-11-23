# tests how the tester tells our own system from another: the target_url normalisation and the three sources

import pytest

from Tester.own_system import REGISTRY_SYSTEM_URL, is_own, normalise

RAILWAY = {"RAILWAY_PROJECT_ID": "p1", "RAILWAY_PUBLIC_DOMAIN": "drifter-test.up.railway.app"}
TEAM16 = "https://doc-tracker-team16.onrender.com/system"


@pytest.fixture
def off_railway(monkeypatch):
    # clears the Railway variables, as on a laptop
    for name in RAILWAY:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def on_railway(monkeypatch):
    # sets the Railway variables, as in the hosted service
    for name, value in RAILWAY.items():
        monkeypatch.setenv(name, value)


def test_normalise_lowercases_the_scheme():
    assert normalise("HTTPS://host.example/system") == "https://host.example/system"


def test_normalise_lowercases_the_host():
    assert normalise("https://Host.EXAMPLE/system") == "https://host.example/system"


def test_normalise_drops_a_default_port():
    assert normalise("https://host.example:443/system") == "https://host.example/system"
    assert normalise("http://host.example:80/system") == "http://host.example/system"
    assert normalise("http://host.example:443/system") == "http://host.example:443/system"


def test_normalise_strips_a_trailing_slash():
    assert normalise("https://host.example/system/") == "https://host.example/system"


def test_normalise_compares_the_path_exactly():
    assert normalise("https://host.example/System") != normalise("https://host.example/system")


def test_railway_public_url_is_own(on_railway):
    assert is_own("https://drifter-test.up.railway.app/system")


def test_registry_url_is_own(on_railway):
    assert is_own(REGISTRY_SYSTEM_URL)
    assert REGISTRY_SYSTEM_URL == "https://documentationmodeldrifter-production.up.railway.app/system"


def test_localhost_off_railway_is_own(off_railway):
    assert is_own("http://localhost/system")
    assert is_own("http://localhost:8000/system")


def test_127_0_0_1_off_railway_is_own(off_railway):
    assert is_own("http://127.0.0.1:8000/system")


def test_ipv6_loopback_off_railway_is_own(off_railway):
    assert is_own("http://[::1]:8000/system")


def test_localhost_on_railway_is_not_own(on_railway):
    assert not is_own("http://localhost:8000/system")


def test_team16_url_is_not_own(on_railway):
    assert not is_own(TEAM16)
