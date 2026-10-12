# HOS 23.0.1 — Boot probe P0 (experimental, **not** a fix)

Branch: `diag/hos-23.0.1-boot-probe`, derived from the failing RC1 maintenance branch.

## A/B basis
- The real console **hangs at the Nintendo logo** with RC1 installed.
- Completely removing `sd:/atmosphere/contents/4200000000000666/` restores normal boot.
- The older observer log reached `Accepting requests.`, proving the SSL MITM server was registered on at least one attempt, not proving the server threads/forwarding worked.
- A user's `enable_ssl = 0` test still hung, but whether this had Atmosphère's required `u8!0x0` type or updated log is **not established**.

## What this probe changes
- Build-time `NETWORK_MITM_BOOT_PROBE=1`: the `Main()` path **does not register any ssl/ssl:s MITM services**, does not start IPC worker threads, and does not start PCAP capture.
- `InitializeSystemModule()` still sets up heap, SM, FS, SD card wait/mount, and observer log.
- Early `setsysInitialize()` / `timeInitialize()` are skipped, so this tests early boot without those two clients.
- Writes to a separate `sd:/atmosphere/logs/network_mitm_boot_probe.log` file. Delete old copy before test to prevent confusion.
- The generated ZIP filename includes `BOOT-PROBE-P0-NO-SSL` so it cannot be mistaken for a working MITM capture release.
- **No GitHub Release** is created from this branch; get the installer from a manually dispatched Actions run artifact.

## Safe test protocol
1. First verify normal boot **with the RC1 folder removed** (already confirmed).
2. Back up SD card and old logs. Only on a test setup, obtain the `BOOT-PROBE-P0-NO-SSL` ZIP from Actions. It still includes a `boot2.flag` for early boot; this remains risky and may hang, so keep SD recovery access.
3. Extract it to the SD root. **Do not** install the old RC1 files over it or mix `exefs.nsp` versions.
4. Attempt one cold boot. If successful, look for `BOOT_PROBE P0` marker lines in the new log; if stuck, shut down, remove only this title ID folder and verify boot recovery.
5. Report the two outcomes: boots/no boots, and whether the `BOOT_PROBE P0: Main reached` line is present.

## Interpretation
- **Boot works and Main marker present:** early SM/SD mount/logger stage is viable; next probe should reintroduce `setsys` and `time` one at a time before enabling SSL.
- **Boot still hangs:** investigate boot2 process startup, memory resource and SD/logger SM dependencies; not ssl session forwarding because none was registered.
- **Boot works but no marker:** check actual ZIP installed, log file creation and whether this sysmodule was launched.

This is a diagnostic-only build and intentionally provides **zero** HTTPS capture functionality.
