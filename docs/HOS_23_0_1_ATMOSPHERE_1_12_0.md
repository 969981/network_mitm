# network_mitm — HOS 23.0.1 / Atmosphère 1.12.0 维护记录

> **Status: experimental.** Compilation does not guarantee that the SSL interfaces of HOS 23.0.1 are binary-compatible. Device testing is required.

## Base
- Branch: `fix/hos-23.0.1-atmosphere-1.12`, based on upstream `23_support` (fecf95eb).
- Atmosphère-libs pin: `aae2da0155a490abd3bfd17a70ccd16bb73c916a` (2026-09-27, Atmosphère 1.12.0 timeframe).
- libnx pin: `feebd026ca0f5dcc2119f46ad8e0d16ad3dd4973` (2026-10-01).
- Build: `.github/workflows/build.yml` in GitHub Actions devkitPro environment.

## Root cause of broken upstream 23_support CI
The previous gitlink referenced Atmosphere-libs `d3083af` (2026-06, HOS 22.5.0). GitHub Actions built the newer libnx and failed with missing `pglEventObserverGetProcessEvent`, `pglGetHostContentMetaInfo`, etc. The Atmosphere-libs API must be pinned consistently with libnx.

## Runtime crash investigation
The screenshot shows Program ID `4200000000000666`, `std::abort()`. The subsequent failure to save an Atmosphère crash report to SD (`00000202`) is **not evidence by itself** that SD failure caused the original abort. Verify the observer log and/or fatal report before claiming root cause.

Previous code had unconditional aborts on logging initialization and PCAP read/write/flush operations. The updated implementation should degrade gracefully when file I/O fails, while leaving forward SSL operations intact.

## Installation / rollback
1. Back up the whole `sd:/atmosphere/contents/4200000000000666/` directory.
2. Make a full backup of `sd:/atmosphere/config/system_settings.ini`.
3. Only install the output of a **successful** CI run after reviewing the build log. Copy the inner `atmosphere/` directory to SD root.
4. Minimal configuration:
   ```ini
   [network_mitm]
   enable_ssl = u8!0x1
   should_dump_ssl_traffic = u8!0x1
   pcap_link_type = str!user
   ```
5. Do not set `should_mitm_all` or `should_disable_ssl_verification` for initial testing. These broaden interception and risk.
6. Start with a single harmless network action, verify logs and PCAP output, then test Pokémon HOME.
7. On boot crash, power off and **remove only** `sd:/atmosphere/contents/4200000000000666/`. Do not wipe the whole contents directory.

Logs: `sd:/atmosphere/logs/network_mitm_observer.log`.
PCAP: `sd:/atmosphere/pcap/<16-digit-program-id>/*.pcap`.

## Validation gates
- [ ] GitHub Actions compilation complete; NSP and installer generated
- [ ] HOS 23.0.1 boots with module enabled; no Atmosphère fatal screen
- [ ] SSL traffic forwarding works; unrelated titles are unaffected
- [ ] Several connections opened in one second create unique filenames
- [ ] SD nearly full/unavailable disables capture, not SSL transport
- [ ] Reboot / unload rollback safe; verify HOME traffic collection

**Do not share PCAPs without removing tokens, personal data, and certificates.**
