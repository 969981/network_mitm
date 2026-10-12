#!/usr/bin/env python3
"""Build and verify a Switch SD-card installer with a deterministic filename.

Uses only the Python standard library; any packaging error stops the Make target.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SD_ROOT = ROOT / "out" / "sd"
OUTPUT = ROOT / "out"
TITLE_ROOT = "atmosphere/contents/4200000000000666"
REQUIRED = {
    f"{TITLE_ROOT}/exefs.nsp",
    f"{TITLE_ROOT}/mitm.lst",
    f"{TITLE_ROOT}/flags/boot2.flag",
}


def archive_path() -> Path:
    header = (ROOT / "network_mitm/include/networkmitm_version.h").read_text()
    numbers = []
    for field in ("MAJOR", "MINOR", "MICRO"):
        match = re.search(
            rf"^#define\s+NETWORK_MITM_VERSION_{field}\s+(\d+)\s*$",
            header,
            re.MULTILINE,
        )
        if not match:
            raise RuntimeError(f"Missing NETWORK_MITM_VERSION_{field}")
        numbers.append(match.group(1))
    revision = os.environ.get("GITHUB_SHA")
    if not revision:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    if not re.fullmatch(r"[0-9a-fA-F]{8,64}", revision):
        raise RuntimeError("Unrecognized git revision")
    suffix = "-BOOT-PROBE-P0-NO-SSL" if os.environ.get("NETWORK_MITM_BOOT_PROBE") == "1" else ""
    name = f"network_mitm-{'.'.join(numbers)}-hos23.0.1-{revision[:8]}{suffix}.zip"
    return OUTPUT / name


def source_files() -> dict[str, Path]:
    files = {
        file.relative_to(SD_ROOT).as_posix(): file
        for file in SD_ROOT.rglob("*")
        if file.is_file()
    }
    missing = REQUIRED - files.keys()
    if missing:
        raise RuntimeError(f"Missing installer files: {sorted(missing)}")
    if files[f"{TITLE_ROOT}/exefs.nsp"].stat().st_size == 0:
        raise RuntimeError("Compiled exefs.nsp is empty")
    mitm_list = files[f"{TITLE_ROOT}/mitm.lst"].read_text().splitlines()
    if "ssl" not in mitm_list or "ssl:s" not in mitm_list:
        raise RuntimeError("mitm.lst does not include ssl and ssl:s")
    return files


def verify(archive_name: Path, files: dict[str, Path]) -> str:
    if not archive_name.is_file():
        raise RuntimeError(f"Installer ZIP was not generated: {archive_name}")
    with zipfile.ZipFile(archive_name, "r") as archive:
        names = set(archive.namelist())
        if names != files.keys():
            raise RuntimeError(
                f"Archive entries differ from SD contents: missing={files.keys() - names}; "
                f"extra={names - files.keys()}"
            )
        corrupted = archive.testzip()
        if corrupted:
            raise RuntimeError(f"ZIP CRC error: {corrupted}")
        if archive.getinfo(f"{TITLE_ROOT}/exefs.nsp").file_size == 0:
            raise RuntimeError("ZIP includes an empty exefs.nsp")
    sha = hashlib.sha256()
    with archive_name.open("rb") as payload:
        for chunk in iter(lambda: payload.read(1024 * 1024), b""):
            sha.update(chunk)
    check_text = f"{sha.hexdigest()}  {archive_name.name}\n"
    manifest = OUTPUT / "SHA256SUMS.txt"
    if not manifest.is_file() or manifest.read_text() != check_text:
        raise RuntimeError("SHA256SUMS.txt missing or does not match ZIP")
    return check_text.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify", action="store_true", help="Validate existing archive and SHA256"
    )
    opts = parser.parse_args()
    files = source_files()
    target = archive_path()
    if not opts.verify:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            target, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name, filename in sorted(files.items()):
                archive.write(filename, arcname=name)
        sha = hashlib.sha256(target.read_bytes()).hexdigest()
        (OUTPUT / "SHA256SUMS.txt").write_text(f"{sha}  {target.name}\n")
    print(f"Verified installer: {target}")
    print(verify(target, files))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"Installer packaging FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
