import pytest
from wolnut.config import load_config, _validate, WolnutConfig


def _write_config(tmp_path, content):
    path = tmp_path / "config.yaml"
    path.write_text(content)
    return str(path)


MINIMAL_CONFIG = """\
nut:
  ups: "ups@localhost"
clients:
  - name: "server1"
    host: "10.0.0.1"
    mac: "aa:bb:cc:dd:ee:ff"
"""

FULL_CONFIG = """\
log_level: DEBUG
nut:
  ups: "myups@10.0.0.2"
poll_interval: 5
restore_delay_sec: 10
wol_retry_delay_sec: 15
discord_webhook: "https://discord.com/api/webhooks/test"
clients:
  - name: "server1"
    host: "10.0.0.1"
    mac: "aa:bb:cc:dd:ee:ff"
    enabled: true
  - name: "server2"
    host: "10.0.0.2"
    mac: "11:22:33:44:55:66"
    enabled: false
"""


def test_load_minimal_config(tmp_path):
    path = _write_config(tmp_path, MINIMAL_CONFIG)
    config = load_config(path)
    assert config is not None
    assert config.nut.ups == "ups@localhost"
    assert len(config.clients) == 1
    assert config.clients[0].enabled is True
    assert config.poll_interval == 10
    assert config.restore_delay_sec == 30
    assert config.wol_retry_delay_sec == 30
    assert config.discord_webhook == ""
    assert config.log_level == "INFO"


def test_load_full_config(tmp_path):
    path = _write_config(tmp_path, FULL_CONFIG)
    config = load_config(path)
    assert config is not None
    assert config.nut.ups == "myups@10.0.0.2"
    assert config.poll_interval == 5
    assert config.restore_delay_sec == 10
    assert config.wol_retry_delay_sec == 15
    assert config.discord_webhook == "https://discord.com/api/webhooks/test"
    assert config.log_level == "DEBUG"
    assert len(config.clients) == 2
    assert config.clients[0].enabled is True
    assert config.clients[1].enabled is False


def test_wol_broadcast_defaults_to_global_broadcast(tmp_path):
    path = _write_config(tmp_path, MINIMAL_CONFIG)
    config = load_config(path)
    assert config is not None
    assert config.clients[0].wol_broadcast == "255.255.255.255"


def test_wol_broadcast_override(tmp_path):
    content = """\
nut:
  ups: "ups@localhost"
clients:
  - name: "nas"
    host: "192.168.1.7"
    mac: "aa:bb:cc:dd:ee:ff"
    wol_broadcast: "10.0.0.255"
"""
    path = _write_config(tmp_path, content)
    config = load_config(path)
    assert config is not None
    assert config.clients[0].wol_broadcast == "10.0.0.255"


def test_load_config_file_not_found():
    assert load_config("/nonexistent/config.yaml") is None


def test_load_config_invalid_yaml(tmp_path):
    path = _write_config(tmp_path, "{{invalid yaml")
    assert load_config(path) is None


def test_enabled_defaults_to_true(tmp_path):
    path = _write_config(tmp_path, MINIMAL_CONFIG)
    config = load_config(path)
    assert config is not None
    assert config.clients[0].enabled is True


@pytest.mark.parametrize(
    "raw,error_match",
    [
        ({}, "nut.ups"),
        ({"nut": {}}, "nut.ups"),
        ({"nut": {"ups": "x"}}, "clients"),
        ({"nut": {"ups": "x"}, "clients": "not-a-list"}, "clients"),
        (
            {
                "nut": {"ups": "x"},
                "clients": [{"host": "h", "mac": "aa:bb:cc:dd:ee:ff"}],
            },
            "name",
        ),
        (
            {
                "nut": {"ups": "x"},
                "clients": [{"name": "n", "mac": "aa:bb:cc:dd:ee:ff"}],
            },
            "host",
        ),
        ({"nut": {"ups": "x"}, "clients": [{"name": "n", "host": "h"}]}, "mac"),
        (
            {
                "nut": {"ups": "x"},
                "clients": [{"name": "n", "host": "h", "mac": "bad"}],
            },
            "MAC",
        ),
    ],
)
def test_validate_rejects_bad_config(raw, error_match):
    with pytest.raises(ValueError, match=error_match):
        _validate(raw)


def test_validate_accepts_good_config():
    _validate(
        {
            "nut": {"ups": "ups@localhost"},
            "clients": [{"name": "n", "host": "h", "mac": "aa:bb:cc:dd:ee:ff"}],
        }
    )
