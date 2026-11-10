#!/usr/bin/env python3
"""
Home Calendar Local Server
==========================
Serves the calendar HTML and synced ICS files over your local network.
Open this on your home server / Raspberry Pi, then browse to it on the tablet.

Usage:
    python3 serve.py              # serves on port 8080
    python3 serve.py 9000         # serves on a custom port

Then open http://<your-server-ip>:8080 on the tablet.
Find your server IP with: hostname -I
"""

import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime


SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_PORT = 8080

# How often to auto-sync calendars while the server is running (minutes)
AUTO_SYNC_INTERVAL_MINUTES = 15


class CalendarHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves files with permissive CORS headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

    def end_headers(self):
        # Allow the page to fetch local ICS files (same-origin, but be explicit)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt, *args):
        # Suppress routine access logs to keep terminal clean
        # Only log errors (4xx, 5xx)
        if args and len(args) >= 2:
            code = str(args[1])
            if code.startswith(("4", "5")):
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] {fmt % args}")


def run_sync():
    """Run sync.py as a subprocess."""
    sync_script = SCRIPT_DIR / "sync.py"
    if not sync_script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(sync_script)],
            cwd=str(SCRIPT_DIR),
            timeout=120,
        )
    except Exception as e:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Auto-sync failed: {e}")


def auto_sync_loop(interval_minutes: int):
    """Background thread: sync calendars periodically."""
    while True:
        time.sleep(interval_minutes * 60)
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Auto-syncing calendars...")
        run_sync()
        print(f"[{ts}] Auto-sync complete.")


def get_local_ip() -> str:
    """Best-effort local IP detection."""
    import socket
    try:
        # Connect to an external address to find which interface we'd use
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

    # Initial sync before starting server
    print("Running initial calendar sync...")
    run_sync()

    # Start background auto-sync thread
    sync_thread = threading.Thread(
        target=auto_sync_loop,
        args=(AUTO_SYNC_INTERVAL_MINUTES,),
        daemon=True,
    )
    sync_thread.start()

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", port), CalendarHandler)
    local_ip = get_local_ip()

    print()
    print("=" * 52)
    print("  Home Calendar Server running")
    print("=" * 52)
    print(f"  Local:    http://localhost:{port}")
    print(f"  Network:  http://{local_ip}:{port}")
    print(f"  Calendar: http://{local_ip}:{port}/home-calendar.html")
    print()
    print(f"  Calendars auto-sync every {AUTO_SYNC_INTERVAL_MINUTES} minutes.")
    print("  Press Ctrl+C to stop.")
    print("=" * 52)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
