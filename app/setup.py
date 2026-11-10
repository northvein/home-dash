#!/usr/bin/env python3
"""
Home Calendar Setup
===================
Run this once to create the initial configuration and folder structure.
Then edit calendars.json to add your calendar URLs.
"""

import json
import os
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "calendars.json"
ICS_DIR = SCRIPT_DIR / "ics"

EXAMPLE_CONFIG = {
    "sources": [
        {
            "id": 1,
            "name": "Example — replace with your calendar",
            "url": "https://calendar.google.com/calendar/ical/YOUR_CALENDAR_ID/basic.ics",
            "filename": "cal_1.ics",
            "memberId": None,
            "lastStatus": None,
            "lastSync": None,
            "lastError": None
        }
    ],
    "lastSync": None
}


def main():
    print()
    print("=" * 52)
    print("  Home Calendar — Setup")
    print("=" * 52)
    print()

    # Create ics/ directory
    ICS_DIR.mkdir(exist_ok=True)
    print(f"✓  Created ics/ directory at {ICS_DIR}")

    # Create calendars.json if it doesn't exist
    if CONFIG_FILE.exists():
        print(f"✓  calendars.json already exists — not overwriting")
    else:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(EXAMPLE_CONFIG, f, indent=2)
        print(f"✓  Created calendars.json at {CONFIG_FILE}")

    print()
    print("Next steps:")
    print()
    print("  1. Edit calendars.json and replace the example URL with")
    print("     your real .ics calendar URLs.")
    print()
    print("     Google Calendar URL:  Calendar Settings → Integrate →")
    print("                           'Secret address in iCal format'")
    print("     iCloud Calendar URL:  Right-click a calendar → Share →")
    print("                           'Public Calendar' → copy the URL")
    print("     Nextcloud:            Calendar → ... → Copy private link")
    print()
    print("  2. Run the sync:       python3 sync.py")
    print()
    print("  3. Start the server:   python3 serve.py")
    print()
    print("  4. On your tablet, open:")
    print("     http://<this-machine-ip>:8080/home-calendar.html")
    print()
    print("     Find your IP address with:  hostname -I")
    print()
    print("  5. (Optional) Schedule automatic syncing — see README.md")
    print()
    print("=" * 52)
    print()


if __name__ == "__main__":
    main()
