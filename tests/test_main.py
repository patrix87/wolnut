from unittest.mock import patch
from wolnut.__main__ import wake_clients, send_discord_notification
from wolnut.config import WolnutConfig, NutConfig, ClientConfig


def _make_config(**overrides) -> WolnutConfig:
    return WolnutConfig(
        nut=overrides.get("nut", NutConfig(ups="ups@localhost")),
        clients=overrides.get(
            "clients",
            [
                ClientConfig(name="srv1", host="10.0.0.1", mac="aa:bb:cc:dd:ee:ff"),
            ],
        ),
        poll_interval=overrides.get("poll_interval", 10),
        restore_delay_sec=overrides.get("restore_delay_sec", 0),
        wol_retry_delay_sec=overrides.get("wol_retry_delay_sec", 0),
        wol_max_retries=overrides.get("wol_max_retries", 5),
        discord_webhook=overrides.get("discord_webhook", ""),
        log_level=overrides.get("log_level", "INFO"),
    )


@patch("wolnut.__main__.time.sleep", return_value=None)
@patch("wolnut.__main__.send_wol_packet", return_value=True)
@patch("wolnut.__main__.is_client_online")
def test_wake_clients_already_online(mock_ping, mock_wol, mock_sleep):
    mock_ping.return_value = True
    config = _make_config()
    wake_clients(config)
    mock_wol.assert_not_called()


@patch("wolnut.__main__.time.sleep", return_value=None)
@patch("wolnut.__main__.send_wol_packet", return_value=True)
@patch("wolnut.__main__.is_client_online")
def test_wake_clients_comes_online_after_wol(mock_ping, mock_wol, mock_sleep):
    # offline (initial check) → WOL → offline (retry check) → WOL → online (retry check)
    mock_ping.side_effect = [False, False, True]
    config = _make_config()
    wake_clients(config)
    assert mock_wol.call_count == 2


@patch("wolnut.__main__.send_discord_notification")
@patch("wolnut.__main__.time.sleep", return_value=None)
@patch("wolnut.__main__.send_wol_packet", return_value=True)
@patch("wolnut.__main__.is_client_online", return_value=False)
def test_wake_clients_retries_5_times(mock_ping, mock_wol, mock_sleep, mock_discord):
    config = _make_config()
    wake_clients(config)
    assert mock_wol.call_count == 5


@patch("wolnut.__main__.send_discord_notification")
@patch("wolnut.__main__.time.sleep", return_value=None)
@patch("wolnut.__main__.send_wol_packet", return_value=True)
@patch("wolnut.__main__.is_client_online", return_value=False)
def test_wake_clients_sends_discord_on_failure(
    mock_ping, mock_wol, mock_sleep, mock_discord
):
    config = _make_config(discord_webhook="https://discord.com/api/webhooks/test")
    wake_clients(config)
    mock_discord.assert_called_once()
    assert "srv1" in mock_discord.call_args[0][1]


@patch("wolnut.__main__.send_discord_notification")
@patch("wolnut.__main__.time.sleep", return_value=None)
@patch("wolnut.__main__.send_wol_packet", return_value=True)
@patch("wolnut.__main__.is_client_online", return_value=False)
def test_wake_clients_no_discord_without_webhook(
    mock_ping, mock_wol, mock_sleep, mock_discord
):
    config = _make_config(discord_webhook="")
    wake_clients(config)
    mock_discord.assert_not_called()


@patch("wolnut.__main__.time.sleep", return_value=None)
@patch("wolnut.__main__.send_wol_packet", return_value=True)
@patch("wolnut.__main__.is_client_online")
def test_wake_clients_skips_disabled(mock_ping, mock_wol, mock_sleep):
    config = _make_config(
        clients=[
            ClientConfig(
                name="srv1", host="10.0.0.1", mac="aa:bb:cc:dd:ee:ff", enabled=False
            ),
        ]
    )
    wake_clients(config)
    mock_ping.assert_not_called()
    mock_wol.assert_not_called()


@patch("wolnut.__main__.urlopen")
def test_send_discord_notification_success(mock_urlopen):
    send_discord_notification("https://discord.com/api/webhooks/test", "hello")
    mock_urlopen.assert_called_once()


@patch("wolnut.__main__.urlopen", side_effect=Exception("network error"))
def test_send_discord_notification_failure(mock_urlopen):
    # Should not raise
    send_discord_notification("https://discord.com/api/webhooks/test", "hello")
