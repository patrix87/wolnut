# WolNut

A simplified fork of [hardwarehaven/wolnut](https://github.com/hardwarehaven/wolnut)
— a lightweight service that monitors a [NUT](https://networkupstools.org/) UPS
and sends Wake-on-LAN packets to bring clients back online after a power outage.

This version strips the project down to the bare essentials: state is defined
as code in the config file, no runtime state file, no CLI framework, no MAC
auto-resolution — just UPS monitoring, ping checks, and WOL packets.

## What It Does

- On startup: checks all enabled clients and WOLs any that are offline
- Continuously monitors UPS status via `upsc`
- When power is restored after a battery event: waits `restore_delay_sec`,
  then WOLs offline clients
- Retries up to 5 times per client with `wol_retry_delay_sec` between attempts
- Sends a Discord notification if a client fails to come back online

## Configuration

Copy `config.example.yaml` to `/config/config.yaml`
(or set `WOLNUT_CONFIG_FILE` env var):

```yaml
log_level: INFO
nut:
  ups: "ups@localhost"
poll_interval: 15
restore_delay_sec: 30
wol_retry_delay_sec: 30
discord_webhook: ""  # optional
clients:
  - name: "server1"
    host: 192.168.0.100
    mac: "38:f7:cd:c5:87:6b"
    enabled: true
```

## Docker Compose

```yaml
services:
  wolnut:
    build: .
    container_name: wolnut
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./config:/config
```

## Maintenance

Update pinned dependency versions:

```sh
uv lock --upgrade
```
