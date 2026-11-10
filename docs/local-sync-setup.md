# Home Calendar — Local Sync Setup

This folder contains three scripts that work together to give the calendar reliable access to remote `.ics` feeds without any browser CORS issues.

## How it works

```
[Google / iCloud / Nextcloud]
         │  HTTPS
         ▼
      sync.py          ← runs on your home server / Pi
         │  saves .ics files locally
         ▼
      ics/cal_1.ics
      ics/cal_2.ics
         │  HTTP (same-origin, no CORS)
         ▼
      serve.py         ← local web server
         │
         ▼
   home-calendar.html  ← displays on your tablet
```

`sync.py` fetches remote calendars (no CORS because it's Python, not a browser).  
`serve.py` serves everything over your local network so the tablet can read it.  
The HTML reads `/ics/cal_1.ics` from the same server — same origin, no CORS problem.

---

## First-time setup

```bash
# 1. Run setup to create the ics/ folder and example config
python3 setup.py

# 2. Edit calendars.json — add your real calendar URLs
nano calendars.json       # or use any text editor

# 3. Test the sync
python3 sync.py

# 4. Start the server
python3 serve.py

# 5. On your tablet, navigate to:
#    http://<server-ip>:8080/home-calendar.html
#    Find your IP:  hostname -I
```

---

## calendars.json format

```json
{
  "sources": [
    {
      "id": 1,
      "name": "Family",
      "url": "https://calendar.google.com/calendar/ical/abc123/basic.ics",
      "filename": "cal_1.ics",
      "memberId": 1,
      "lastStatus": null,
      "lastSync": null,
      "lastError": null
    },
    {
      "id": 2,
      "name": "Work",
      "url": "webcal://p62-caldav.icloud.com/published/2/xyz...",
      "filename": "cal_2.ics",
      "memberId": 2,
      "lastStatus": null,
      "lastSync": null,
      "lastError": null
    }
  ]
}
```

**`memberId`** links a calendar to a family member defined in the HTML settings panel (for colour coding). Match the `id` values from your members list in the app. Set to `null` to use the default palette colour.

**`webcal://` URLs** are automatically converted to `https://` by sync.py.

---

## Getting your calendar URL

### Google Calendar
1. Open Google Calendar → Settings (gear icon) → Settings
2. Click the calendar name in the left panel
3. Scroll to **Integrate calendar**
4. Copy the **Secret address in iCal format** (not the public one)

### Apple iCloud
1. Open Calendar on Mac or iCloud.com
2. Right-click a calendar → **Share Calendar**
3. Enable **Public Calendar**
4. Copy the link — it will start with `webcal://`

### Nextcloud / Baikal / Radicale
1. Open Nextcloud Calendar → click the `⋯` next to a calendar
2. Choose **Copy private link**
3. The URL ends in `/dav/...` — use this directly

---

## Scheduling automatic syncs (crontab)

To sync every 15 minutes automatically:

```bash
crontab -e
```

Add this line (adjust the path to where you put these files):

```
*/15 * * * * /usr/bin/python3 /home/pi/home-calendar/sync.py >> /home/pi/home-calendar/sync.log 2>&1
```

For hourly sync (plenty for a home calendar):

```
0 * * * * /usr/bin/python3 /home/pi/home-calendar/sync.py >> /home/pi/home-calendar/sync.log 2>&1
```

Find your Python path with: `which python3`

---

## Running the server on boot (systemd)

Create `/etc/systemd/system/home-calendar.service`:

```ini
[Unit]
Description=Home Calendar Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/home-calendar
ExecStart=/usr/bin/python3 /home/pi/home-calendar/serve.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable home-calendar
sudo systemctl start home-calendar

# Check it's running:
sudo systemctl status home-calendar
```

`serve.py` will also auto-sync calendars every 15 minutes while it's running, so the crontab is optional if you use systemd.

---

## File structure

```
home-calendar/
├── home-calendar.html   ← the calendar display
├── sync.py              ← fetches remote .ics files
├── serve.py             ← local HTTP server
├── setup.py             ← first-time setup
├── calendars.json       ← your calendar sources config
├── sync.log             ← sync output log
└── ics/
    ├── cal_1.ics        ← synced calendar files
    └── cal_2.ics
```

---

## Troubleshooting

**Sync fails with SSL error**  
Some self-hosted servers use self-signed certificates. `sync.py` will retry without SSL verification as a fallback.

**Sync fails with HTTP 403 / 401**  
The calendar URL may require authentication. Google Calendar "Secret" iCal links include a token in the URL — make sure you're using the secret link, not the public one.

**Events not showing after sync**  
1. Check `sync.log` to confirm the sync succeeded
2. Open the calendar in browser, press the sync button (↺) in the nav bar
3. Open browser DevTools → Console to look for errors

**Calendar shows old events after updating the ICS**  
The HTML caches events in `localStorage`. After a successful sync, press the ↺ button in the nav bar to reload from the local files.

**Can't reach the server from the tablet**  
- Make sure both devices are on the same Wi-Fi network
- Check the server IP with `hostname -I`
- Check the firewall: `sudo ufw allow 8080`
