#!/usr/bin/env python3
"""Publish verified firmware and retain one published release per board."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


VERSION = r"[A-Za-z0-9._-]{1,64}"


def gh(*args, capture=False):
    return subprocess.run(["gh", *args], check=True, stdout=subprocess.PIPE if capture else None,
                          encoding="utf-8").stdout


def api(*args):
    return json.loads(gh("api", *args, capture=True))


def verify_files(files):
    expected = {}
    for name in files:
        path = Path(name)
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        expected[name] = (path.stat().st_size, f"sha256:{digest}")
    checksums = Path("SHA256SUMS").read_text(encoding="ascii").splitlines()
    entries = {name: f"sha256:{digest}" for digest, name in (line.split("  ", 1) for line in checksums)}
    if len(checksums) != len(files) - 1 or entries != {name: expected[name][1] for name in files[:-1]}:
        raise ValueError("SHA256SUMS does not match the firmware files")
    return expected


def publish(repo, commit, board, profile, version):
    if (not re.fullmatch(r"[a-z0-9][a-z0-9-]*", board) or profile not in ("spi", "emmc")
            or not re.fullmatch(VERSION, version)):
        raise ValueError("invalid board, storage profile, or version")
    tag = f"{board}-{profile}-v{version}"
    image = f"{board}-v1-{profile}-{version}"
    loader = "u-boot-rockchip-spi.bin" if profile == "spi" else "u-boot-rockchip.bin"
    files = [f"{image}.img", f"{image}.json", loader, "SHA256SUMS"]
    expected = verify_files(files)

    repo_path = f"repos/{repo}"
    pages = api("--paginate", "--slurp", f"{repo_path}/releases?per_page=100")
    releases = [release for page in pages for release in page]
    current = next((release for release in releases if release["tag_name"] == tag), None)
    if current is None:
        refs = api(f"{repo_path}/git/matching-refs/tags/{tag}")
        if any(ref["ref"] == f"refs/tags/{tag}" for ref in refs):
            raise ValueError(f"version tag {tag} already exists; choose a new version")
        gh("release", "create", tag, "--repo", repo, "--target", commit, "--latest=false",
           "--title", f"{board} · {profile} · {version}",
           "--notes", "完整启动镜像，包含主线 U-Boot 和 RKdev 恢复系统。", *files)
        current = api(f"{repo_path}/releases/tags/{tag}")

    ref = api(f"{repo_path}/git/ref/tags/{tag}")["object"]
    assets = {asset["name"]: (asset["size"], asset.get("digest")) for asset in current["assets"]
              if asset["state"] == "uploaded"}
    if (ref["type"] != "commit" or ref["sha"] != commit or current["draft"] or current["prerelease"]
            or not current["published_at"] or assets != expected):
        raise ValueError(f"release {tag} does not match the verified build")

    managed_tag = re.compile(rf"{re.escape(board)}-(?:spi|emmc)-v{VERSION}")
    old = [release for release in releases if release["id"] != current["id"] and not release["draft"]
           and managed_tag.fullmatch(release["tag_name"])]
    if any(release["published_at"] > current["published_at"] for release in old):
        raise ValueError(f"a newer release already exists for {board}")
    for release in old:
        gh("api", "--method", "DELETE", f"{repo_path}/releases/{release['id']}")
        print(f"Removed superseded release {release['tag_name']}")
    print(f"Published board release: {current['html_url']}")


if __name__ == "__main__":
    try:
        publish(os.environ["GH_REPO"], os.environ["GITHUB_SHA"], os.environ["RKDEV_BOARD"],
                os.environ["RKDEV_PROFILE"], os.environ["RKDEV_VERSION"])
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"publish: {error}")
