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
  ups: "ups@127.0.0.1"
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

`host` is the address used for the online (ping) check; `mac` is the NIC the
magic packet wakes. By default the packet is broadcast to `255.255.255.255`.

Set the optional per-client `wol_broadcast` when the WOL-capable NIC lives on a
different subnet than the address you ping (for example a dual-homed NAS whose
10G interface answers pings but does not support WOL, while its 2.5G interface
does). Point `host` at the pingable address, `mac` at the WOL-capable NIC, and
`wol_broadcast` at that NIC's subnet-directed broadcast:

```yaml
clients:
  - name: "nas"
    host: 192.168.1.7          # pingable (10G NIC, no WOL)
    mac: "aa:bb:cc:dd:ee:00"   # WOL-capable NIC (2.5G)
    wol_broadcast: 10.0.0.255  # directed broadcast for that NIC's subnet
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
