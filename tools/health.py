#!/usr/bin/env python3
"""Daily health report (markdown on stdout). Exit 1 if anything needs attention.

Checks the live site, every pin feed and the images in it, the pin queue runway,
how long since the last post, and whether the daily writer has logged a run.
"""
import datetime as dt, json, os, sys, urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import ROOT, SITE, load_posts, url, utc

now = dt.datetime.now(dt.timezone.utc)
bad, ok = [], []


def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "pocketful-health/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read()


def check(name, fn):
    try:
        msg = fn()
        ok.append(f"{name}: {msg}")
    except Exception as e:  # report every failure, keep going
        bad.append(f"{name}: {e}")


def home():
    s, b = get(url())
    assert s == 200 and b"Pocketful" in b, f"status {s}"
    return "up"


check("Homepage", home)

images = set()
for board in SITE["boards"]:
    def feed(board=board):
        s, b = get(url(f"feeds/{board}.xml"))
        root = ET.fromstring(b)
        items = root.findall("./channel/item")
        for it in items[:10]:
            enc = it.find("enclosure")
            if enc is not None:
                images.add(enc.get("url"))
        return f"{len(items)} pins in feed"
    check(f"Feed {board}", feed)


def imgs():
    for u in sorted(images):
        s, b = get(u)
        assert s == 200 and len(b) > 20000, f"broken image {u}"
    return f"{len(images)} recent pin images load"


check("Pin images", imgs)

queue = json.load(open(os.path.join(ROOT, "data", "pins.json")))
future = sorted(utc(p["publish_at"]) for p in queue if p.get("publish_at") and utc(p["publish_at"]) > now)
waiting = [p for p in queue if not p.get("publish_at") and p.get("status", "queued") == "queued"]
runway = (future[-1] - now).days if future else 0
(ok if runway >= 3 else bad).append(f"Pin queue: {len(future)} scheduled, runway {runway} day(s), {len(waiting)} unscheduled")

posts = load_posts(now)
if posts:
    age = (now - posts[0]["date_dt"]).days
    (ok if age <= 4 else bad).append(f"Last post: {posts[0]['slug']} ({age} day(s) ago), {len(posts)} live")
else:
    bad.append("Last post: no posts live")

runs = os.path.join(ROOT, "data", "runs")
logs = sorted(f for f in os.listdir(runs) if f.endswith(".md")) if os.path.isdir(runs) else []
if logs:
    last = dt.date.fromisoformat(logs[-1][:10])
    gap = (now.date() - last).days
    (ok if gap <= 2 else bad).append(f"Daily writer: last run log {logs[-1]} ({gap} day(s) ago)")
else:
    bad.append("Daily writer: no run logs yet")

print(f"## Pocketful Party health · {now:%Y-%m-%d %H:%M} UTC\n")
print("**Needs attention**\n" + "\n".join(f"- {x}" for x in bad) + "\n" if bad else "**All green.**\n")
print("**OK**\n" + "\n".join(f"- {x}" for x in ok))
sys.exit(1 if bad else 0)
