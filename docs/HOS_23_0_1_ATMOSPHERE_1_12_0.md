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

## HOS 23.x capture scope (safe default)

`ssl:s` is now registered only when `should_mitm_all = u8!0x1`, because the service's own `ShouldMitm` was already returning false for every client otherwise. This avoids setting up an unused system-service MITM port and worker threads on modern firmware. Default Pokémon HOME application `ssl` interception is unchanged. **Do not enable system-wide MITM during first-boot testing.**

### Report status

The first code changes address identified abort paths in diagnostic log and PCAP I/O, and prevent same-second filename collisions. They do **not** establish the root cause of the user-reported boot crash without a fatal report and hardware reproduction. HOS 23.0.1 runtime behaviour still requires validation.

## Automated build and experimental pre-release

The maintenance branch GitHub Actions workflow at
`https://github.com/969981/network_mitm/actions/workflows/build.yml`
can be started using **Run workflow**, with branch
`fix/hos-23.0.1-atmosphere-1.12`. If workflows are not available, the
repository owner must enable GitHub Actions in the repository Settings.

The workflow:
1. Builds pinned libnx and the pinned Atmosphere-libs network_mitm module.
2. Checks `exefs.nsp`, `boot2.flag`, and `mitm.lst`; validates the ZIP contents.
3. Uploads build logs, raw executable files and SD installer artifacts.
4. **Only if manually dispatched on this exact branch and the build passes,**
   publishes prerelease `v0.2.11-hos23.0.1-rc1`, including installer ZIP and
   SHA256SUMS.txt. Push/PR checks do not publish.

This pre-release is explicitly **experimental** pending HOS 23.0.1
hardware validation. No release should be described as tested merely because
a compiler returned success.

## Build #2 failure: packaging stage (2026-10-12)

The Actions run [38273618083](https://github.com/969981/network_mitm/actions/runs/38273618083) compiled `network_mitm.elf`, `network_mitm.nso`, and `network_mitm.nsp` successfully. The next step failed at `ls out/*.zip` because no ZIP existed under `out/`. The legacy `Makefile` used a silent `zip` invocation followed by `cd` in one shell recipe, which could mask the packaging failure with a successful final exit code. The precise suppressed ZIP failure message was not captured.

The new packager `.github/scripts/package.py` uses only the Python standard library, generates a slash-free revision-tagged ZIP from `out/sd/`, verifies required files/CRC/installer contents, and writes SHA-256 checksums. Make now fails on missing ZIP instead of reporting success. CI verifies the generated archive again before uploading or publishing any release.

## Boot-blocker — RC1 (2026-10-12)

The successful build [38277044749](https://github.com/969981/network_mitm/actions/runs/38277044749) produced [v0.2.11-hos23.0.1-rc1](https://github.com/969981/network_mitm/releases/tag/v0.2.11-hos23.0.1-rc1), but a HOS 23.0.1 / Atmosphère 1.12.0 console subsequently **hung at the Nintendo Switch logo** after installation. A successful CI build only validates packaging and linking; it does not validate early boot/runtime SSL compatibility. Track: [Issue #2](https://github.com/969981/network_mitm/issues/2).

### First isolate before editing the SSL IPC implementation

1. Cold-power-off and remove only `atmosphere/contents/4200000000000666/`; verify the console boots.
2. Back up `system_settings.ini`, then, with the module still present, change `enable_ssl = u8!0x0` and reboot. No PCAP capture will occur in this mode. If this boots, the hang is likely after enabling SSL interception; if not, it is earlier in module initialization, resource use, or conflict with another module.
3. Collect `atmosphere/logs/network_mitm_observer.log`, `atmosphere/fatal_errors/` when present, and a list of enabled sysmodules. Logs may contain secrets; sanitize before sharing.
4. Do not enable `should_mitm_all` or `should_disable_ssl_verification` during isolation.

### Release safety gate

Workflow now builds automatically but **does not publish** unless manually dispatched with `publish_preview: true`. RC1 is a known boot-blocking candidate; planned RC2 must stay a pre-release, unpromoted pending hardware testing. The previous document's automatic-publish instruction is superseded by this gate.
