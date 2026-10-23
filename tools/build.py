#!/usr/bin/env python3
"""Build the static site into _site/.

Posts: content/posts/*.md with a front-matter block (key: value lines between ---).
Pins: data/pins.json. Only pins whose publish_at <= now are written to the
per-board RSS feeds (feeds/<board>.xml), which Pinterest auto-publishes from.
That is what makes posting gradual: the hourly build releases pins as their
time arrives, and nothing needs to be committed to release them.

Usage: python3 tools/build.py [--now 2026-11-01T12:00:00Z] [--out _site]
"""
import argparse, datetime as dt, html, json, os, re, shutil, sys
from email.utils import format_datetime
from xml.sax.saxutils import escape

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = json.load(open(os.path.join(ROOT, "site.json")))


def utc(s):
    if isinstance(s, dt.datetime):
        return s
    s = s.strip().replace("Z", "+00:00")
    d = dt.datetime.fromisoformat(s if "T" in s else s + "T12:00:00+00:00")
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def parse_post(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if line.strip() and ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["body_md"] = m.group(2)
    meta.setdefault("slug", os.path.splitext(os.path.basename(path))[0])
    meta["date_dt"] = utc(meta["date"])
    return meta


def load_posts(now, include_future=False):
    d = os.path.join(ROOT, "content", "posts")
    posts = [parse_post(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".md")]
    posts = [p for p in posts if p.get("draft", "false") != "true" and (include_future or p["date_dt"] <= now)]
    return sorted(posts, key=lambda p: p["date_dt"], reverse=True)


def url(path=""):
    return SITE["base_url"].rstrip("/") + "/" + path.lstrip("/")


def rel(path=""):
    """Root-relative link that works under a GitHub Pages project path."""
    base = re.sub(r"^https?://[^/]+", "", SITE["base_url"].rstrip("/"))
    return base + "/" + path.lstrip("/")


MD = markdown.Markdown(extensions=["tables", "attr_list", "md_in_html", "toc"])


def render_md(src):
    MD.reset()
    # shortcodes: [[printable]] -> download box, [[etsy:key]] -> shop card
    out = MD.convert(src)
    return out


def shortcodes(body, post):
    def printable(_):
        pdf = post.get("printable", "")
        if not pdf:
            return ""
        pages = post.get("printable_pages", "")
        return (f'<aside class="dl"><div class="dl-k">Free printable</div>'
                f'<div class="dl-t">{html.escape(post.get("printable_title", post["title"]))}</div>'
                f'<div class="dl-m">PDF · US Letter{(" · " + pages + " pages") if pages else ""} · print at home</div>'
                f'<a class="btn" href="{rel(pdf)}" download>Download the PDF</a></aside>')

    def etsy(m):
        p = SITE["etsy_products"].get(m.group(1))
        if not p:
            return ""
        return (f'<aside class="shop"><div class="dl-k">Want more games?</div>'
                f'<div class="dl-t">{html.escape(p["title"])}</div>'
                f'<div class="dl-m">From our own Etsy shop, Pocketful Studio · {p["price"]}</div>'
                f'<a class="btn alt" href="{p["url"]}" rel="noopener">See it on Etsy</a></aside>')

    body = re.sub(r"(?:<p>\s*)?\[\[printable\]\](?:\s*</p>)?", printable, body)
    body = re.sub(r"(?:<p>\s*)?\[\[etsy:([\w-]+)\]\](?:\s*</p>)?", etsy, body)
    return body


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800;900&family=Archivo:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">')


def layout(title, body, desc="", canonical="", image="", kind="website", extra_head=""):
    t = html.escape(title)
    d = html.escape(desc or SITE["tagline"])
    og_img = f'<meta property="og:image" content="{image}">' if image else ""
    verify = (f'<meta name="p:domain_verify" content="{SITE["pinterest_verify"]}">' if SITE.get("pinterest_verify") else "")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title><meta name="description" content="{d}">
<link rel="canonical" href="{canonical or url()}">
<meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:type" content="{kind}">
<meta property="og:site_name" content="{SITE['name']}">{og_img}{verify}
<link rel="alternate" type="application/rss+xml" title="{SITE['name']}" href="{rel('feed.xml')}">
<link rel="icon" href="{rel('img/favicon.png')}">
{FONTS}<link rel="stylesheet" href="{rel('css/site.css')}">{extra_head}
</head><body>
<header class="top"><a class="brand" href="{rel()}"><span class="pk"></span>Pocketful <b>Party</b></a>
<nav><a href="{rel()}#games">Games</a><a href="{rel('about/')}">About</a><a href="{SITE['etsy_shop']}" rel="noopener">Shop</a></nav></header>
<main>{body}</main>
<footer class="foot"><div><span class="pk"></span> {SITE['name']} · free printable party games</div>
<div><a href="{rel('about/')}">About</a> · <a href="{rel('disclosure/')}">Disclosure</a> · <a href="{rel('privacy/')}">Privacy</a> · <a href="{rel('feed.xml')}">RSS</a></div></footer>
</body></html>"""


def card(p):
    img = p.get("cover", "")
    return (f'<a class="card" href="{rel(p["slug"] + "/")}">'
            f'<div class="card-img" style="background-image:url({rel(img)})"></div>'
            f'<div class="card-k">{html.escape(p.get("season_label", ""))}</div>'
            f'<div class="card-t">{html.escape(p["title"])}</div></a>')


def write(out, path, content):
    full = os.path.join(out, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)


def build_pin_feeds(out, now, posts_by_slug):
    pins_path = os.path.join(ROOT, "data", "pins.json")
    pins = json.load(open(pins_path)) if os.path.exists(pins_path) else []
    # Nothing is released until Pinterest is connected (site.json pins_start), so the
    # feeds can't dump a backlog on the first fetch.
    start = utc(SITE["pins_start"]) if SITE.get("pins_start") else None
    released = [p for p in pins if start and p.get("publish_at") and p.get("status", "queued") not in ("hold", "expired")
                and start <= utc(p["publish_at"]) <= now
                and p["post"] in posts_by_slug]
    feeds = {}
    for p in released:
        feeds.setdefault(p["board"], []).append(p)
    for board in SITE["boards"]:
        items = sorted(feeds.get(board, []), key=lambda p: p["publish_at"], reverse=True)[:50]
        xml = [f'<?xml version="1.0" encoding="UTF-8"?>',
               '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
               f'<title>{escape(SITE["name"])}: {escape(SITE["boards"][board])}</title>',
               f'<link>{url()}</link><description>{escape(SITE["boards"][board])} pins</description>',
               f'<atom:link href="{url("feeds/" + board + ".xml")}" rel="self" type="application/rss+xml"/>',
               f'<lastBuildDate>{format_datetime(now)}</lastBuildDate>']
        for p in items:
            img = url(p["image"])
            link = url(p["post"] + "/") + f"?utm_source=pinterest&utm_medium=pin&utm_content={p['id']}"
            size = 0
            fp = os.path.join(ROOT, "static", p["image"])
            if os.path.exists(fp):
                size = os.path.getsize(fp)
            xml += ["<item>", f"<title>{escape(p['title'])}</title>", f"<link>{escape(link)}</link>",
                    f"<guid isPermaLink=\"false\">{p['id']}</guid>",
                    f"<pubDate>{format_datetime(utc(p['publish_at']))}</pubDate>",
                    f"<description>{escape(p['description'])}</description>",
                    f'<enclosure url="{img}" type="image/png" length="{size}"/>',
                    f'<media:content url="{img}" medium="image" type="image/png"/>', "</item>"]
        xml.append("</channel></rss>")
        write(out, f"feeds/{board}.xml", "\n".join(xml))
    return len(released), len(pins)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--now")
    ap.add_argument("--out", default=os.path.join(ROOT, "_site"))
    a = ap.parse_args()
    now = utc(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    out = a.out
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(os.path.join(ROOT, "static"), out)

    posts = load_posts(now)
    by_slug = {p["slug"]: p for p in posts}

    for p in posts:
        body = shortcodes(render_md(p["body_md"]), p)
        hero = (f'<header class="post-h"><div class="kicker">{html.escape(p.get("season_label", ""))}</div>'
                f'<h1>{html.escape(p["title"])}</h1>'
                f'<div class="meta">By {SITE["author"]} · {p["date_dt"]:%B %-d, %Y}</div></header>')
        cover = (f'<img class="cover" src="{rel(p["cover"])}" alt="{html.escape(p.get("cover_alt", p["title"]))}" width="1000" height="1500">'
                 if p.get("cover") else "")
        disclose = ('<p class="disc">Heads up: links to Pocketful Studio go to our own Etsy shop. '
                    'We make a little if you buy, and the free printable here stays free either way.</p>')
        ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": p["title"],
                         "datePublished": p["date_dt"].isoformat(), "author": {"@type": "Person", "name": SITE["author"]},
                         "image": url(p.get("cover", "")), "description": p.get("description", "")})
        more = [q for q in posts if q["slug"] != p["slug"]][:3]
        related = ('<section class="more"><h2>More games</h2><div class="grid">' + "".join(card(q) for q in more) + "</div></section>") if more else ""
        page = f'<article class="post">{hero}<div class="post-grid"><div class="post-body">{disclose}{body}</div><div class="post-side">{cover}</div></div></article>{related}'
        write(out, f"{p['slug']}/index.html",
              layout(p["title"] + " | " + SITE["name"], page, p.get("description", ""), url(p["slug"] + "/"),
                     url(p.get("cover", "")), "article", f'<script type="application/ld+json">{ld}</script>'))

    # pages
    pdir = os.path.join(ROOT, "content", "pages")
    for f in sorted(os.listdir(pdir)):
        if f.endswith(".md"):
            pg = parse_post(os.path.join(pdir, f))
            write(out, f"{pg['slug']}/index.html",
                  layout(pg["title"] + " | " + SITE["name"],
                         f'<article class="post page"><header class="post-h"><h1>{html.escape(pg["title"])}</h1></header><div class="post-body">{render_md(pg["body_md"])}</div></article>',
                         pg.get("description", ""), url(pg["slug"] + "/")))

    # home
    home = (f'<section class="hero"><div class="hero-k">Free printables · no email required</div>'
            f'<h1>Party games that actually get people playing.</h1>'
            f'<p>Print-at-home games for holidays, showers, birthdays and game nights. Each one has clear rules, '
            f'tips for different group sizes, and a PDF you can download right from the page.</p></section>'
            f'<section id="games"><div class="grid">' + "".join(card(p) for p in posts) + "</div></section>")
    write(out, "index.html", layout(SITE["name"] + ": " + SITE["tagline"], home, SITE["tagline"], url()))

    # 404, robots, sitemap, blog feed
    write(out, "404.html", layout("Not found | " + SITE["name"], f'<section class="hero"><h1>That page wandered off.</h1><p><a href="{rel()}">Back to the games</a></p></section>'))
    write(out, "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {url('sitemap.xml')}\n")
    sm = ['<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f"<url><loc>{url()}</loc></url>"]
    sm += [f"<url><loc>{url(p['slug'] + '/')}</loc><lastmod>{p['date_dt']:%Y-%m-%d}</lastmod></url>" for p in posts]
    sm.append("</urlset>")
    write(out, "sitemap.xml", "\n".join(sm))
    rss = ['<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>',
           f"<title>{escape(SITE['name'])}</title><link>{url()}</link><description>{escape(SITE['tagline'])}</description>"]
    for p in posts[:30]:
        rss.append(f"<item><title>{escape(p['title'])}</title><link>{url(p['slug'] + '/')}</link><guid>{url(p['slug'] + '/')}</guid>"
                   f"<pubDate>{format_datetime(p['date_dt'])}</pubDate><description>{escape(p.get('description', ''))}</description></item>")
    rss.append("</channel></rss>")
    write(out, "feed.xml", "\n".join(rss))
    open(os.path.join(out, ".nojekyll"), "w").close()

    released, total = build_pin_feeds(out, now, by_slug)
    print(f"built {len(posts)} posts, released {released}/{total} pins into feeds, now={now:%Y-%m-%dT%H:%MZ}")


if __name__ == "__main__":
    main()
