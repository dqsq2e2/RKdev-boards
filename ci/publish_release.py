#!/usr/bin/env python3
"""Publish verified firmware and retain one release per board and storage profile."""

import hashlib
from datetime import date
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from github import api, gh, optional_api, temporary_error

VERSION = r"[A-Za-z0-9._-]{1,64}"


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


def release_order(tag, board, profile):
    match = re.fullmatch(rf"{re.escape(board)}-{profile}-([0-9]{{4}})-v([0-9]+)\.([0-9]+)-r([1-9][0-9]*)", tag)
    return tuple(map(int, match.groups())) if match else (0, 0, 0, 0)


def release_assets(release):
    return {asset["name"]: (asset["size"], asset.get("digest")) for asset in release["assets"]
            if asset["state"] == "uploaded"}


def list_releases(repo_path):
    pages = api("--paginate", "--slurp", f"{repo_path}/releases?per_page=100")
    return [release for page in pages for release in page]


def ensure_release(repo, commit, tag, title, files, expected):
    repo_path = f"repos/{repo}"
    for attempt in range(5):
        try:
            current = next((release for release in list_releases(repo_path) if release["tag_name"] == tag), None)
            ref = optional_api(f"{repo_path}/git/ref/tags/{tag}")
            if ref and (ref["object"]["type"] != "commit" or ref["object"]["sha"] != commit):
                raise ValueError(f"version tag {tag} belongs to another commit")
            if current is None:
                current = api("--method", "POST", f"{repo_path}/releases",
                              "-f", f"tag_name={tag}", "-f", f"target_commitish={commit}",
                              "-f", f"name={title}", "-f", "body=完整启动镜像，包含主线 U-Boot 和 RKdev 恢复系统。",
                              "-F", "draft=true", "-f", "make_latest=false", retry=False)
            if current["prerelease"]:
                raise ValueError(f"release {tag} is marked as a prerelease")
            if current["draft"]:
                assets = release_assets(current)
                pending = [name for name in files if assets.get(name) != expected[name]]
                if pending:
                    gh("release", "upload", tag, "--repo", repo, "--clobber", *pending)
                current = api(f"{repo_path}/releases/{current['id']}")
                if release_assets(current) != expected:
                    raise ValueError(f"draft {tag} does not match the verified build")
                gh("release", "edit", tag, "--repo", repo, "--draft=false", "--latest=false")
                current = api(f"{repo_path}/releases/{current['id']}")
            ref = api(f"{repo_path}/git/ref/tags/{tag}")["object"]
            if (ref["type"] != "commit" or ref["sha"] != commit or current["draft"]
                    or not current["published_at"] or release_assets(current) != expected):
                raise ValueError(f"release {tag} does not match the verified build")
            return current
        except subprocess.CalledProcessError as error:
            if attempt == 4 or not temporary_error(error):
                raise
            print(f"Resuming release {tag} after a temporary GitHub failure", flush=True)
            time.sleep(2 ** attempt)


def delete_resource(path):
    try:
        gh("api", "--method", "DELETE", path)
    except subprocess.CalledProcessError as error:
        if "HTTP 404" not in (error.stderr or ""):
            raise


def cleanup(repo_path, current, board, board_id, profile):
    names = set((board, board_id))
    patterns = [re.compile(rf"{re.escape(name)}-{profile}-(?:[0-9]{{4}}-)?v{VERSION}") for name in names]
    order = release_order(current["tag_name"], board, profile)

    def superseded(tag):
        return (tag != current["tag_name"] and any(pattern.fullmatch(tag) for pattern in patterns)
                and max(release_order(tag, name, profile) for name in names) < order)

    for release in list_releases(repo_path):
        if superseded(release["tag_name"]):
            delete_resource(f"{repo_path}/releases/{release['id']}")
            print(f"Removed superseded release {release['tag_name']}")
    for name in sorted(names):
        for ref in api(f"{repo_path}/git/matching-refs/tags/{name}-{profile}-"):
            tag = ref["ref"].removeprefix("refs/tags/")
            if superseded(tag):
                delete_resource(f"{repo_path}/git/refs/tags/{tag}")
                print(f"Removed superseded tag {tag}")


def publish(repo, commit, board, board_id, profile, version, build_date):
    if (any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) for name in (board, board_id))
            or profile not in ("spi", "emmc")
            or not re.fullmatch(VERSION, version)):
        raise ValueError("invalid board, storage profile, or version")
    day = date.fromisoformat(build_date)
    if not re.fullmatch(rf"{day.month}\.{day.day}-r[1-9][0-9]*", version):
        raise ValueError("version does not match the build date")
    tag = f"{board}-{profile}-{day.year}-v{version}"
    image = f"{board_id}-v1-{profile}-{version}"
    loader = "u-boot-rockchip-spi.bin" if profile == "spi" else "u-boot-rockchip.bin"
    files = [f"{image}.img", f"{image}.json", loader, "SHA256SUMS"]
    expected = verify_files(files)

    repo_path = f"repos/{repo}"
    releases = list_releases(repo_path)
    order = release_order(tag, board, profile)
    if any(not release["draft"] and release_order(release["tag_name"], board, profile) > order
           for release in releases):
        print(f"Skipped superseded build {tag}")
        return
    current = ensure_release(repo, commit, tag, f"{board} · {profile} · {version}", files, expected)
    cleanup(repo_path, current, board, board_id, profile)
    print(f"Published board release: {current['html_url']}")


if __name__ == "__main__":
    try:
        publish(os.environ["GH_REPO"], os.environ["GITHUB_SHA"], os.environ["RKDEV_BOARD"],
                os.environ["RKDEV_BOARD_ID"], os.environ["RKDEV_PROFILE"],
                os.environ["RKDEV_VERSION"], os.environ["RKDEV_BUILD_DATE"])
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"publish: {error}")
