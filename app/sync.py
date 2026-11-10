#!/usr/bin/env python3
"""
Home Calendar Sync Script
=========================
Fetches remote .ics calendar feeds and saves them locally so the
calendar display HTML can read them without CORS issues.

Run manually:         python3 sync.py
Run on a schedule:    add to crontab (see README.md)

Config file:  calendars.json  (in the same directory as this script)
Output:       ics/  directory (created automatically)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import ssl
import shutil
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "calendars.json"
ICS_DIR = SCRIPT_DIR / "ics"
LOG_FILE = SCRIPT_DIR / "sync.log"

# Timeout per request in seconds
REQUEST_TIMEOUT = 15

# User-agent to avoid being blocked by some calendar providers
USER_AGENT = "Mozilla/5.0 (compatible; HomeCalendarSync/1.0)"


def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        log(f"Config file not found: {CONFIG_FILE}", "ERROR")
        log("Run setup.py first, or create calendars.json manually.", "ERROR")
        sys.exit(1)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def fetch_ics(url: str) -> str:
    """Fetch an ICS URL, return the raw text content."""
    # Convert webcal:// to https://
    url = url.replace("webcal://", "https://", 1).replace("webcal:", "https:", 1)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    # Create SSL context that doesn't fail on minor cert issues
    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            charset = "utf-8"
            content_type = resp.headers.get("Content-Type", "")
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].strip().split(";")[0].strip()
            raw = resp.read()
            return raw.decode(charset, errors="replace")
    except ssl.SSLError:
        # Retry without cert verification as last resort
        ctx_no_verify = ssl.create_default_context()
        ctx_no_verify.check_hostname = False
        ctx_no_verify.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx_no_verify) as resp:
            raw = resp.read()
            return raw.decode("utf-8", errors="replace")


def validate_ics(content: str) -> bool:
    return "BEGIN:VCALENDAR" in content or "BEGIN:VEVENT" in content


def sync_source(source: dict) -> dict:
    """Sync a single calendar source. Returns updated source dict."""
    name = source.get("name", "Unnamed")
    url = source.get("url", "")
    filename = source.get("filename", "")

    if not url:
        log(f"  Skipping '{name}': no URL configured", "WARN")
        source["lastStatus"] = "error"
        source["lastError"] = "No URL"
        return source

    if not filename:
        # Auto-generate filename from source ID
        filename = f"cal_{source.get('id', int(time.time()))}.ics"
        source["filename"] = filename

    output_path = ICS_DIR / filename

    log(f"  Syncing '{name}' from {url[:60]}{'...' if len(url) > 60 else ''}")

    try:
        content = fetch_ics(url)

        if not validate_ics(content):
            raise ValueError("Response does not appear to be a valid ICS file")

        # Count events for logging
        event_count = content.count("BEGIN:VEVENT")

        # Write atomically via temp file
        tmp_path = output_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        shutil.move(str(tmp_path), str(output_path))

        source["lastStatus"] = "ok"
        source["lastSync"] = datetime.now().isoformat()
        source["lastError"] = None
        source["eventCount"] = event_count
        log(f"    OK — {event_count} events saved to {filename}")

    except urllib.error.HTTPError as e:
        source["lastStatus"] = "error"
        source["lastError"] = f"HTTP {e.code}: {e.reason}"
        log(f"    FAILED: HTTP {e.code} {e.reason}", "ERROR")

    except urllib.error.URLError as e:
        source["lastStatus"] = "error"
        source["lastError"] = str(e.reason)
        log(f"    FAILED: {e.reason}", "ERROR")

    except Exception as e:
        source["lastStatus"] = "error"
        source["lastError"] = str(e)
        log(f"    FAILED: {e}", "ERROR")

    return source


def main() -> None:
    log("=" * 50)
    log("Home Calendar Sync starting")

    config = load_config()
    sources = config.get("sources", [])

    if not sources:
        log("No calendar sources configured in calendars.json", "WARN")
        log("Open the calendar in your browser, go to Settings → Calendar sources, add sources, then re-run sync.py")
        return

    # Ensure output directory exists
    ICS_DIR.mkdir(exist_ok=True)

    ok_count = 0
    err_count = 0

    for i, source in enumerate(sources):
        sources[i] = sync_source(source)
        if sources[i].get("lastStatus") == "ok":
            ok_count += 1
        else:
            err_count += 1

    config["sources"] = sources
    config["lastSync"] = datetime.now().isoformat()
    save_config(config)

    log(f"Sync complete: {ok_count} succeeded, {err_count} failed")
    log("=" * 50)


if __name__ == "__main__":
    main()
