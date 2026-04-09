import logging
import re

import yaml
from dataclasses import dataclass, field

logger = logging.getLogger("wolnut")

_MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")


@dataclass
class NutConfig:
    ups: str


@dataclass
class ClientConfig:
    name: str
    host: str
    mac: str
    enabled: bool = True


@dataclass
class WolnutConfig:
    nut: NutConfig
    clients: list[ClientConfig] = field(default_factory=list)
    poll_interval: int = 10
    restore_delay_sec: int = 30
    wol_retry_delay_sec: int = 30
    wol_max_retries: int = 5
    discord_webhook: str = ""
    log_level: str = "INFO"


def load_config(config_path: str):
    try:
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("Config file not found: %s", config_path)
        return None
    except Exception:
        logger.exception("Failed to load config: %s", config_path)
        return None

    try:
        _validate(raw)
    except ValueError as e:
        logger.error("Invalid config: %s", e)
        return None

    clients = []
    for c in raw["clients"]:
        clients.append(ClientConfig(
            name=c["name"],
            host=c["host"],
            mac=c["mac"],
            enabled=c.get("enabled", True),
        ))

    config = WolnutConfig(
        nut=NutConfig(ups=raw["nut"]["ups"]),
        clients=clients,
        poll_interval=raw.get("poll_interval", 10),
        restore_delay_sec=raw.get("restore_delay_sec", 30),
        wol_retry_delay_sec=raw.get("wol_retry_delay_sec", 30),
        wol_max_retries=raw.get("wol_max_retries", 5),
        discord_webhook=raw.get("discord_webhook", ""),
        log_level=raw.get("log_level", "INFO").upper(),
    )

    logger.info("Config loaded from %s", config_path)
    for client in config.clients:
        status = "enabled" if client.enabled else "disabled"
        logger.info("  %s — %s (%s)", client.name, client.mac, status)

    return config


def _validate(raw: dict):
    if not isinstance(raw, dict):
        raise ValueError("Config must be a YAML mapping")
    if "nut" not in raw or not isinstance(raw.get("nut"), dict) or "ups" not in raw["nut"]:
        raise ValueError("Missing required field: nut.ups")
    if "clients" not in raw or not isinstance(raw["clients"], list):
        raise ValueError("Missing or invalid 'clients' list")
    for i, c in enumerate(raw["clients"]):
        if "name" not in c:
            raise ValueError(f"Client #{i}: missing 'name'")
        if "host" not in c:
            raise ValueError(f"Client '{c.get('name', '?')}': missing 'host'")
        if "mac" not in c:
            raise ValueError(f"Client '{c['name']}': missing 'mac'")
        if not _MAC_PATTERN.match(c["mac"]):
            raise ValueError(f"Client '{c['name']}': invalid MAC format: {c['mac']}")

