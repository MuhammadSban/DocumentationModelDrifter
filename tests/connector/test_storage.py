# checks the durable store (D6): run files on the Railway volume, no start on Railway without
# one, and /health saying which store the runs land in

import pytest
from fastapi.testclient import TestClient

from GitHub_Connector import api, runs
from GitHub_Connector.settings import get_settings

ID = "an-" + "0" * 32


@pytest.fixture
def env(monkeypatch):
    # clears the Railway variables and the settings cache around each test
    for name in ("RAILWAY_PROJECT_ID", "RAILWAY_VOLUME_MOUNT_PATH"):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def test_runs_are_saved_on_the_volume(env, tmp_path):
    env.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path))

    runs.save(ID, b"{}")

    assert (tmp_path / f"{ID}.json").read_bytes() == b"{}"
    assert runs.load(ID) == b"{}"


def test_the_app_refuses_to_start_on_railway_without_a_volume(env):
    env.setenv("RAILWAY_PROJECT_ID", "p")

    with pytest.raises(RuntimeError, match="volume"), TestClient(api.app):
        pass


def test_the_app_starts_on_railway_with_a_volume(env, tmp_path):
    env.setenv("RAILWAY_PROJECT_ID", "p")
    env.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path))

    with TestClient(api.app) as client:
        assert client.get("/system/health").json()["storage"] == "volume"


def test_health_says_ephemeral_without_a_volume(env):
    assert api.health()["storage"] == "ephemeral"
