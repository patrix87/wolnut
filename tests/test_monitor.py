from unittest.mock import patch, MagicMock
from wolnut.monitor import get_ups_status, is_client_online


def test_get_ups_status_parses_output():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "battery.charge: 100\nups.status: OL\ndevice.model: CPS\n"

    with patch("wolnut.monitor.subprocess.run", return_value=mock_result):
        status = get_ups_status("ups@localhost")

    assert status["battery.charge"] == "100"
    assert status["ups.status"] == "OL"
    assert status["device.model"] == "CPS"


def test_get_ups_status_returns_empty_on_error():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error: Connection failure"

    with patch("wolnut.monitor.subprocess.run", return_value=mock_result):
        status = get_ups_status("ups@localhost")

    assert status == {}


def test_get_ups_status_returns_empty_on_exception():
    with patch("wolnut.monitor.subprocess.run", side_effect=Exception("timeout")):
        status = get_ups_status("ups@localhost")

    assert status == {}


def test_is_client_online_returns_true():
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("wolnut.monitor.subprocess.run", return_value=mock_result):
        assert is_client_online("10.0.0.1") is True


def test_is_client_online_returns_false():
    mock_result = MagicMock()
    mock_result.returncode = 1

    with patch("wolnut.monitor.subprocess.run", return_value=mock_result):
        assert is_client_online("10.0.0.1") is False


def test_is_client_online_returns_false_on_exception():
    with patch("wolnut.monitor.subprocess.run", side_effect=Exception("error")):
        assert is_client_online("10.0.0.1") is False
