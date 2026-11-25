"""GitHub CLI requests with bounded retries for temporary failures."""

import json
import re
import subprocess
import sys
import time


def temporary_error(error):
    return bool(re.search(r"HTTP (?:429|5[0-9]{2})|timed? out|TLS handshake|connection reset|"
                          r"unexpected EOF|network is unreachable|temporary failure|"
                          r"connection refused|no such host|stream error",
                          error.stderr or "", re.IGNORECASE))


def gh(*args, retry=True):
    attempts = 5 if retry else 1
    for attempt in range(attempts):
        try:
            result = subprocess.run(["gh", *args], check=True, capture_output=True, encoding="utf-8")
            return result.stdout
        except subprocess.CalledProcessError as error:
            if attempt + 1 == attempts or not temporary_error(error):
                print(error.stderr or str(error), file=sys.stderr, flush=True)
                raise
            print(f"GitHub request failed temporarily; retrying ({attempt + 1}/{attempts - 1})", flush=True)
            time.sleep(2 ** attempt)


def api(*args, retry=True):
    return json.loads(gh("api", *args, retry=retry))


def optional_api(path):
    try:
        return api(path)
    except subprocess.CalledProcessError as error:
        if "HTTP 404" in (error.stderr or ""):
            return None
        raise
