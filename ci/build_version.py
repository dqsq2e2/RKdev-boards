#!/usr/bin/env python3
"""Resolve a date-based version from the workflow's daily run sequence."""

from datetime import datetime, time, timedelta, timezone
import os
from pathlib import Path
import subprocess
import sys

from github import api


BUILD_TIMEZONE = timezone(timedelta(hours=8))


def version_for_run(run, daily_runs):
    day = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")).astimezone(BUILD_TIMEZONE).date()
    numbers = [entry["run_number"] for entry in daily_runs
               if entry["workflow_id"] == run["workflow_id"] and entry["run_number"] <= run["run_number"]
               and datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
               .astimezone(BUILD_TIMEZONE).date() == day]
    first = min([run["run_number"], *numbers])
    return f"{day.month}.{day.day}-r{run['run_number'] - first + 1}", day.isoformat()


def resolve(repo, run_id):
    run = api(f"repos/{repo}/actions/runs/{run_id}")
    timestamp = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")).astimezone(BUILD_TIMEZONE)
    start = datetime.combine(timestamp.date(), time(), BUILD_TIMEZONE)
    end = start + timedelta(days=1, seconds=-1)
    interval = "..".join(value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") for value in (start, end))
    pages = api("--paginate", "--slurp", f"repos/{repo}/actions/workflows/{run['workflow_id']}/runs"
                f"?created={interval}&per_page=100")
    return version_for_run(run, [entry for page in pages for entry in page["workflow_runs"]])


if __name__ == "__main__":
    try:
        version, day = resolve(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_RUN_ID"])
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
            stream.write(f"version={version}\nbuild_date={day}\n")
        print(f"RKdev {version} ({day})")
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"version: {error}")
