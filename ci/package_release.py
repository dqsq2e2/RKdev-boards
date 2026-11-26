#!/usr/bin/env python3
"""Archive the verified RKdev image and its upgrade manifest for publication."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo


def release_files(board, profile, version):
    archive = f"{board}-v1-{profile}-{version}.zip"
    loader = "u-boot-rockchip-spi.bin" if profile == "spi" else "u-boot-rockchip.bin"
    return [archive, loader, "SHA256SUMS"]


def package(out, board, board_id, profile, version):
    image = f"{board_id}-v1-{profile}-{version}.img"
    manifest = Path(image).with_suffix(".json").name
    metadata = (out / manifest).read_bytes()
    declared = json.loads(metadata)["image"]
    if declared["name"] != image or declared["bytes"] != (out / image).stat().st_size:
        raise ValueError("manifest does not describe the built image")

    archive, loader, sums = release_files(board, profile, version)
    temporary = out / f"{archive}.tmp"
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as bundle:
            entry = ZipInfo(image)
            entry.compress_type = ZIP_DEFLATED
            entry.file_size = declared["bytes"]
            with (out / image).open("rb") as source, bundle.open(entry, "w") as target:
                shutil.copyfileobj(source, target, length=1 << 20)
            bundle.writestr(ZipInfo(manifest), metadata, compress_type=ZIP_DEFLATED)
        with ZipFile(temporary) as bundle, bundle.open(image) as contents:
            if (hashlib.file_digest(contents, "sha256").hexdigest() != declared["sha256"]
                    or bundle.read(manifest) != metadata):
                raise ValueError("archive does not match its image manifest")
        temporary.replace(out / archive)
    finally:
        temporary.unlink(missing_ok=True)

    lines = []
    for name in (archive, loader):
        with (out / name).open("rb") as stream:
            lines.append(f"{hashlib.file_digest(stream, 'sha256').hexdigest()}  {name}\n")
    temporary_sums = out / f"{sums}.tmp"
    temporary_sums.write_text("".join(lines), encoding="ascii", newline="\n")
    temporary_sums.replace(out / sums)
    print(f"Packaged {out / archive}")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--board", required=True)
    cli.add_argument("--board-id", required=True)
    cli.add_argument("--profile", choices=("emmc", "spi"), required=True)
    cli.add_argument("--version", required=True)
    args = cli.parse_args()
    try:
        package(args.out, args.board, args.board_id, args.profile, args.version)
    except (BadZipFile, KeyError, OSError, ValueError) as error:
        cli.exit(1, f"package: {error}\n")
