#!/usr/bin/env python3
"""Resolve a date-based version for one board and storage profile."""

from datetime import datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from github import api


BUILD_TIMEZONE = timezone(timedelta(hours=8))
RUN_NAME_PREFIX = "RKdev 构建 "
RUN_NAME = re.compile(rf"^{re.escape(RUN_NAME_PREFIX)}(?P<board>[a-z0-9][a-z0-9-]*) · "
                      r"(?P<profile>default|spi|emmc)$")


def _run_key(run, default_profiles):
    match = RUN_NAME.fullmatch(run.get("display_title", ""))
    if not match:
        return None
    board = match["board"]
    profile = match["profile"]
    if profile == "default":
        profile = default_profiles.get(board)
    return (board, profile) if profile in ("spi", "emmc") else None


def _day(run):
    return datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) \
        .astimezone(BUILD_TIMEZONE).date()


def version_for_run(run, daily_runs, board, profile, default_profiles):
    day = _day(run)
    key = (board, profile)
    numbers = {entry["run_number"] for entry in daily_runs
               if entry["workflow_id"] == run["workflow_id"]
               and entry["run_number"] <= run["run_number"]
               and _day(entry) == day
               and _run_key(entry, default_profiles) == key}
    numbers.add(run["run_number"])
    return f"{day.month}.{day.day}-r{len(numbers)}", day.isoformat()


def default_profile(board):
    board_file = Path(__file__).resolve().parents[1] / "boards" / board / "v1" / "board.json"
    with board_file.open(encoding="utf-8") as stream:
        profile = json.load(stream)["default_profile"]
    if profile not in ("spi", "emmc"):
        raise ValueError(f"invalid default profile for {board}: {profile}")
    return profile


def resolve(repo, run_id, board, profile):
    run = api(f"repos/{repo}/actions/runs/{run_id}")
    timestamp = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) \
        .astimezone(BUILD_TIMEZONE)
    start = datetime.combine(timestamp.date(), time(), BUILD_TIMEZONE)
    end = start + timedelta(days=1, seconds=-1)
    interval = "..".join(value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") for value in (start, end))
    pages = api("--paginate", "--slurp", f"repos/{repo}/actions/workflows/{run['workflow_id']}/runs"
                f"?created={interval}&per_page=100")
    return version_for_run(run, [entry for page in pages for entry in page["workflow_runs"]],
                           board, profile, {board: default_profile(board)})


if __name__ == "__main__":
    try:
        board = os.environ["RKDEV_BOARD"]
        profile = os.environ["RKDEV_PROFILE"]
        version, day = resolve(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_RUN_ID"],
                               board, profile)
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
            stream.write(f"version={version}\nbuild_date={day}\n")
        print(f"RKdev {version} ({day})")
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"version: {error}")
