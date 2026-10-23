#!/usr/bin/env python3
"""Operator commands for the daily run.

  python3 tools/pipeline.py assets <slug>   printable PDF + page PNGs + pin images + cover, adds pins to the queue
  python3 tools/pipeline.py check  [slug]   checks before anything is queued (exit 1 on any problem)
  python3 tools/pipeline.py schedule        give every unscheduled pin a publish time within the daily limits
  python3 tools/pipeline.py reschedule      re-plan all unreleased pins (after changing pins_start)
  python3 tools/pipeline.py status          queue runway, last post, next pins
"""
import datetime as dt, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image

import pins as pinlib
from build import ROOT, SITE, load_posts, parse_post, utc

NODE_PATH = os.environ.get("NODE_PATH", "/opt/node22/lib/node_modules")
PINS = os.path.join(ROOT, "data", "pins.json")
BANNED = re.compile(r"\b(guarantee[ds]?|best ever|#1|miracle|click here|100% free money)\b", re.I)


def load_pins():
    return json.load(open(PINS)) if os.path.exists(PINS) else []


def save_pins(p):
    json.dump(p, open(PINS, "w"), indent=1)
    open(PINS, "a").write("\n")


def spec_for(slug):
    return json.load(open(os.path.join(ROOT, "printables", slug + ".json")))


def node(*args):
    env = dict(os.environ, NODE_PATH=NODE_PATH)
    subprocess.run(["node", os.path.join(ROOT, "tools", "render.js"), *args], check=True, env=env)


def assets(slug):
    spec = spec_for(slug)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "printables.py"), os.path.join(ROOT, "printables", slug + ".json")], check=True)
    pngdir = os.path.join(ROOT, "printables", "_png", slug)
    node("pdf", os.path.join(ROOT, "printables", "_html", slug + ".html"), os.path.join(ROOT, "static", "printables", slug + ".pdf"), pngdir)
    queue = load_pins()
    existing = {p["id"] for p in queue}
    tmp = os.path.join(ROOT, "printables", "_html", "pins")
    os.makedirs(tmp, exist_ok=True)
    for i, p in enumerate(spec["pins"], 1):
        hp = os.path.join(tmp, f"{slug}-{i}.html")
        open(hp, "w").write(pinlib.pin_html(spec["theme"], slug, p))
        png = os.path.join(tmp, f"{slug}-{i}.png")
        node("shot", hp, png, "1000", "1500")
        jpg = os.path.join(ROOT, "static", "pins", f"{slug}-{i}.jpg")
        Image.open(png).convert("RGB").save(jpg, quality=88, optimize=True, progressive=True)
        os.remove(png)
        pid = f"{slug}-{i}"
        if pid not in existing:
            queue.append(dict(id=pid, post=slug, board=spec["board"], image=f"pins/{slug}-{i}.jpg",
                              title=p["title"], description=p["description"], template=p["template"],
                              expires=spec.get("expires"), status="queued"))
    save_pins(queue)
    print(f"assets ok: {slug} ({len(spec['pins'])} pins)")


def check(slug=None):
    problems = []
    now = dt.datetime.now(dt.timezone.utc)
    posts = {p["slug"]: p for p in load_posts(now, include_future=True)}
    queue = load_pins()
    titles = {}
    for p in queue:
        if slug and p["post"] != slug:
            continue
        pid = p["id"]
        if p["post"] not in posts:
            problems.append(f"{pid}: post '{p['post']}' does not exist")
        if p["board"] not in SITE["boards"]:
            problems.append(f"{pid}: unknown board {p['board']}")
        fp = os.path.join(ROOT, "static", p["image"])
        if not os.path.exists(fp):
            problems.append(f"{pid}: image missing {p['image']}")
        else:
            im = Image.open(fp)
            if im.size != (1000, 1500):
                problems.append(f"{pid}: image is {im.size}, want 1000x1500")
            if os.path.getsize(fp) > 3_000_000:
                problems.append(f"{pid}: image over 3 MB")
            # blank-render guard: a failed render is nearly one flat color
            ext = im.convert("L").resize((50, 75)).getextrema()
            if ext[1] - ext[0] < 40:
                problems.append(f"{pid}: image looks blank")
        if not (10 <= len(p["title"]) <= 100):
            problems.append(f"{pid}: title length {len(p['title'])} (10-100)")
        if not (50 <= len(p["description"]) <= 500):
            problems.append(f"{pid}: description length {len(p['description'])} (50-500)")
        if p["description"].count("#") > 3:
            problems.append(f"{pid}: more than 3 hashtags")
        for field in ("title", "description"):
            if BANNED.search(p[field]):
                problems.append(f"{pid}: spammy wording in {field}: {BANNED.search(p[field]).group(0)}")
        if p["title"].lower() in titles:
            problems.append(f"{pid}: duplicate title with {titles[p['title'].lower()]}")
        titles[p["title"].lower()] = pid
    for s, post in posts.items():
        if slug and s != slug:
            continue
        for k in ("title", "date", "description", "cover", "printable", "season_label"):
            if not post.get(k):
                problems.append(f"post {s}: missing {k}")
        if post.get("printable") and not os.path.exists(os.path.join(ROOT, "static", post["printable"])):
            problems.append(f"post {s}: printable PDF missing")
        if post.get("cover") and not os.path.exists(os.path.join(ROOT, "static", post["cover"])):
            problems.append(f"post {s}: cover image missing")
        words = len(re.findall(r"\w+", post["body_md"]))
        if words < 600:
            problems.append(f"post {s}: only {words} words (want 600+ of real instructions)")
        if "[[printable]]" not in post["body_md"]:
            problems.append(f"post {s}: no [[printable]] download box")
        if len(post.get("description", "")) > 160:
            problems.append(f"post {s}: meta description over 160 chars")
    for x in problems:
        print("PROBLEM", x)
    print(f"check: {len(problems)} problem(s)")
    return not problems


def slots_for_day(day, n):
    # US daytime spread (UTC): 13:00 .. 03:00 next day
    start = dt.datetime.combine(day, dt.time(13, 0), dt.timezone.utc)
    step = 14 * 60 // max(n, 1)
    return [start + dt.timedelta(minutes=step * i + 7) for i in range(n)]


def schedule():
    lim = SITE["limits"]
    queue = load_pins()
    now = dt.datetime.now(dt.timezone.utc)
    taken = [utc(p["publish_at"]) for p in queue if p.get("publish_at")]
    last_by_post = {}
    for p in queue:
        if p.get("publish_at"):
            t = utc(p["publish_at"])
            last_by_post[p["post"]] = max(last_by_post.get(p["post"], t), t)
    todo = [p for p in queue if not p.get("publish_at") and p.get("status", "queued") == "queued"]
    # seasonal pins with the soonest expiry go first, then evergreen in queue order
    todo.sort(key=lambda p: (p.get("expires") or "9999-12-31"))
    if SITE.get("pins_start"):
        now = max(now, utc(SITE["pins_start"]))
    day = (now + dt.timedelta(hours=1)).date()
    gap = dt.timedelta(hours=lim["min_hours_between_same_post"])
    placed = 0
    for _ in range(120):
        if not todo:
            break
        used = sum(1 for t in taken if t.date() == day)
        for slot in slots_for_day(day, lim["pins_per_day"])[used:]:
            if slot <= now:
                continue
            for p in list(todo):
                last = last_by_post.get(p["post"])
                if last and abs(slot - last) < gap:
                    continue
                if p.get("expires") and slot.date() > dt.date.fromisoformat(p["expires"]):
                    p["status"] = "expired"
                    todo.remove(p)
                    continue
                p["publish_at"] = slot.strftime("%Y-%m-%dT%H:%M:%SZ")
                taken.append(slot)
                last_by_post[p["post"]] = slot
                todo.remove(p)
                placed += 1
                break
        day += dt.timedelta(days=1)
    save_pins(queue)
    print(f"scheduled {placed} pin(s); {len(todo)} still waiting")


def status():
    now = dt.datetime.now(dt.timezone.utc)
    queue = load_pins()
    future = sorted(utc(p["publish_at"]) for p in queue if p.get("publish_at") and utc(p["publish_at"]) > now)
    released = [p for p in queue if p.get("publish_at") and utc(p["publish_at"]) <= now]
    posts = load_posts(now)
    print(f"posts live: {len(posts)}; last post: {posts[0]['date_dt']:%Y-%m-%d}" if posts else "posts live: 0")
    print(f"pins released: {len(released)}; queued for later: {len(future)}")
    print(f"queue runway until: {future[-1]:%Y-%m-%d}" if future else "queue runway: EMPTY")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "assets":
        assets(sys.argv[2])
    elif cmd == "check":
        sys.exit(0 if check(sys.argv[2] if len(sys.argv) > 2 else None) else 1)
    elif cmd == "schedule":
        schedule()
    elif cmd == "reschedule":
        # clear every not-yet-released time (e.g. after setting pins_start) and plan again
        now = dt.datetime.now(dt.timezone.utc)
        start = utc(SITE["pins_start"]) if SITE.get("pins_start") else None
        q = load_pins()
        for p in q:
            if p.get("publish_at") and (not start or utc(p["publish_at"]) > now or utc(p["publish_at"]) < start):
                p.pop("publish_at")
                if p.get("status") == "expired":
                    p["status"] = "queued"
        save_pins(q)
        schedule()
    else:
        status()
