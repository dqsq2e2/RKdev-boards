#!/usr/bin/env python3
"""Make the selected board's verified local firmware inputs available to RKdev."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

MAX_FILE = 64 * 1024 * 1024


def unpack(bundle, board_id, files, out):
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        for filename, checksum in files.items():
            board_entry = f"{board_id}/{filename}"
            entry = board_entry if board_entry in names else filename
            if names.count(entry) != 1:
                raise ValueError(f"firmware bundle needs exactly one entry for {board_entry}")
            member = archive.getinfo(entry)
            if not 0 < member.file_size <= MAX_FILE:
                raise ValueError(f"invalid firmware size: {filename}")
            data = archive.read(member)
            if hashlib.sha256(data).hexdigest() != checksum:
                raise ValueError(f"firmware SHA-256 mismatch: {filename}")
            (out / filename).write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rkdev", type=Path, required=True)
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--profile", choices=["default", "spi", "emmc"], default="default")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, help="optional local ZIP instead of RKDEV_FIRMWARE_BUNDLE_URL")
    args = parser.parse_args()
    sys.path.insert(0, str(args.rkdev.resolve() / "tools"))
    from contract import Invalid, load_board

    try:
        _, board, profile, cfg = load_board(args.board, None if args.profile == "default" else args.profile)
        files = {}
        for entry in (*board["firmware"].values(), *cfg.get("firmware", {}).values()):
            if "file" in entry:
                name, checksum = entry["file"], entry["sha256"]
                if files.setdefault(name, checksum) != checksum:
                    raise ValueError(f"conflicting firmware requirements for {name}")
        args.out.mkdir(parents=True, exist_ok=True)
        if files:
            url = os.environ.get("RKDEV_FIRMWARE_BUNDLE_URL", "")
            if args.bundle:
                unpack(args.bundle, board["board_id"], files, args.out)
            elif url.startswith("https://"):
                with tempfile.TemporaryDirectory(prefix="rkdev-firmware-") as work:
                    bundle = Path(work) / "assets.zip"
                    result = subprocess.run(
                        ["curl", "--fail", "--silent", "--show-error", "--location", "--globoff",
                         "--proto", "=https", "--proto-redir", "=https", "--retry", "3", "--max-time", "120",
                         "--max-filesize", str(2 * MAX_FILE), "--output", bundle, "--", url],
                        check=False,
                    )
                    if result.returncode:
                        raise ValueError("firmware bundle download failed")
                    unpack(bundle, board["board_id"], files, args.out)
            else:
                raise ValueError("set an HTTPS RKDEV_FIRMWARE_BUNDLE_URL for: " + ", ".join(sorted(files)))
        print(profile)
    except (Invalid, OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"firmware: {error}\n")


if __name__ == "__main__":
    main()
