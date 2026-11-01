# checks that /system/health answers the contract's Health shape

from GitHub_Connector import api, rules
from GitHub_Connector.settings import build_label


def test_health_lists_model_drift_and_the_required_fields():
    body = api.health()

    assert body["status"] == "ok"
    assert body["tool_version"] == build_label()
    assert body["config_version"] == rules.config_version()
    assert body["features"] == ["model_drift"]
