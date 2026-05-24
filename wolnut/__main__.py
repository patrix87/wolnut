import logging
import os
import sys
import time
import json
from urllib.request import Request, urlopen

from wolnut.config import load_config
from wolnut.monitor import get_ups_status, is_client_online
from wolnut.wol import send_wol_packet

logger = logging.getLogger("wolnut")

def send_discord_notification(webhook_url: str, message: str):
    try:
        data = json.dumps({"content": message}).encode()
        # Discord returns 403 to the default Python-urllib User-Agent.
        # Any non-default UA passes.
        req = Request(webhook_url, data=data, headers={
            "Content-Type": "application/json",
            "User-Agent": "wolnut/1.0 (+https://github.com/patrix87/wolnut)",
        })
        urlopen(req, timeout=10)
        logger.info("Discord notification sent.")
    except Exception as e:
        logger.error("Failed to send Discord notification: %s", e)


def wake_clients(config):
    for client in config.clients:
        if not client.enabled:
            logger.debug("Skipping disabled client: %s", client.name)
            continue

        if is_client_online(client.host):
            logger.info("%s is already online.", client.name)
            continue

        success = False
        for attempt in range(1, config.wol_max_retries + 1):
            logger.info(
                "Sending WOL to %s (%s) — attempt %d/%d",
                client.name, client.mac, attempt, config.wol_max_retries,
            )
            send_wol_packet(client.mac)
            time.sleep(config.wol_retry_delay_sec)

            if is_client_online(client.host):
                logger.info("%s is now online.", client.name)
                success = True
                break

        if not success:
            msg = f"Failed to wake {client.name} ({client.host}) after {config.wol_max_retries} attempts."
            logger.error(msg)
            if config.discord_webhook:
                send_discord_notification(config.discord_webhook, msg)


def main():
    config_path = os.environ.get("WOLNUT_CONFIG_FILE", "/config/config.yaml")
    config = load_config(config_path)
    if config is None:
        sys.exit(1)

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logger.info("WolNut started. Monitoring UPS: %s", config.nut.ups)

    was_on_battery = False
    wol_needed = True  # Check hosts on startup

    while True:
        ups_status = get_ups_status(config.nut.ups)
        power_status = ups_status.get("ups.status", "OL")
        logger.debug("UPS status: %s", power_status)

        if "OB" in power_status:
            if not was_on_battery:
                logger.warning("UPS is on battery power.")
                was_on_battery = True
            time.sleep(2)
            continue

        if wol_needed or was_on_battery:
            if was_on_battery:
                logger.info(
                    "Power restored. Waiting %ds before waking clients...",
                    config.restore_delay_sec,
                )
                time.sleep(config.restore_delay_sec)
            was_on_battery = False
            wol_needed = False
            wake_clients(config)

        time.sleep(config.poll_interval)


if __name__ == "__main__":
    main()
