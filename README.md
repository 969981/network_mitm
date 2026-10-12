# network_mitm

> [!CAUTION]
> **HOS 23.0.1 / Atmosphère 1.12.0 — RC1 boot hang reported.**
> Installing `v0.2.11-hos23.0.1-rc1` may prevent boot past the Nintendo Switch logo.
> [Issue #2](https://github.com/969981/network_mitm/issues/2) tracks the blocker.
> Do not install the RC1 binary. To recover, power off and move
> `sd:/atmosphere/contents/4200000000000666/` to your PC, then reboot.
> Fresh builds are for diagnostics only until runtime verification.


Nintendo Switch Network MITM sysmodule.

network_mitm allows you to:
- Dump traffic from SSL of the running game (NEX,...) in PCAP files.
- Mitm ssl to replace `NintendoClass2CAG3` CA with a user provided one (useful for NPLN traffic capture).

More features might appears depending of the needs.

## Configuration
The following configuration should be added to `/atmosphere/config/system_settings.ini`:

```ini
; network_mitm config
[network_mitm]
; Enable SSL: This should be set to 1 for certificate swapping, and also for PCAP capturing.
enable_ssl = u8!0x1
; Uncomment this line to enable mitm of everything (including system titles).
; should_mitm_all = u8!0x1
; Uncomment this line to disable SSL verifications (DANGEROUS)
; should_disable_ssl_verification = u8!0x1
; Root CA filename: this should be present in the root of the SD (sd:/rootCA.pem for the below example)
custom_ca_public_cert = str!rootCA.pem
; By default, the sysmodule will dump decrypted network traffic user-link PCAPs to the SD card only for the main application.
; Uncomment this line to disable.
; should_dump_ssl_traffic = u8!0x0
; Possible values "ethernet", "ip" or "user"
; pcap_link_type = str!user
```

## Building

Make sure that the submodules are initialized and up to date.

```bash
git submodule update --init --recursive
```

### With Docker

1. Install `Docker` and `docker compose` (or `docker-compose`).

2. Run `docker compose up --build` (or `docker-compose up --build`). It runs `make` in the container.

### Without Docker

1. Install [`devkitPro`](https://devkitpro.org/wiki/Getting_Started) and the following dependencies:
    - `switch-dev`
    - `switch-mbedtls`
    - `switch-libjpeg-turbo`
    - `libnx` (Currently requires master branch)

2. Run `make` command.

## Licensing

This software is licensed under the terms of the GPLv2.

You can find a copy of the license in the [LICENSE file](LICENSE).
