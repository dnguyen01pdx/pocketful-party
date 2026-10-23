#!/usr/bin/env python3
"""Turn a printable spec (printables/<slug>.json) into print-ready HTML.

Then tools/render.js turns the HTML into static/printables/<slug>.pdf plus one
PNG per page in printables/_png/<slug>/ (used inside pin designs).

Spec fields: slug, title, subtitle, theme (see THEMES), type, and per type:
  trivia: questions [{q, a}], key_title
  cards:  cards [str], card_label, per_page (6 or 8)
  bingo:  words [str] (24+), count, free_label, caller (bool)
  list:   sections [{h, items [str]}], checkbox (bool), note
  story:  paragraphs [str], how_to (str)
Usage: python3 tools/printables.py printables/<slug>.json
"""
import html, json, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Two "riso inks" per theme + a font pair. Each season gets its own look.
THEMES = {
    "thanksgiving": dict(a="#B5452A", b="#F2A93B", paper="#FBF4E6", disp="Bricolage Grotesque", dispw=800, body="Literata", tag="Thanksgiving"),
    "friendsgiving": dict(a="#2E4F8F", b="#FF7A3D", paper="#FBF4E6", disp="Bricolage Grotesque", dispw=800, body="Archivo", tag="Friendsgiving"),
    "christmas": dict(a="#0F7A4F", b="#E8443A", paper="#FBF6EC", disp="Big Shoulders Display", dispw=900, body="Archivo", tag="Christmas"),
    "christmas-cozy": dict(a="#7A1F2B", b="#2F6B4F", paper="#F7F0E3", disp="Fraunces", dispw=800, body="Literata", tag="Christmas"),
    "newyear": dict(a="#1B1F3B", b="#D4A537", paper="#F7F4EE", disp="Big Shoulders Display", dispw=900, body="DM Sans", tag="New Year's Eve"),
    "valentines": dict(a="#C2185B", b="#FF8FB1", paper="#FFF6F4", disp="Fraunces", dispw=800, body="DM Sans", tag="Valentine's"),
    "shower": dict(a="#4A6C5B", b="#E7A99B", paper="#FBF7F1", disp="Fraunces", dispw=700, body="DM Sans", tag="Shower"),
    "party": dict(a="#3E5C86", b="#D9452F", paper="#F5ECDC", disp="Big Shoulders Display", dispw=900, body="Archivo", tag="Party"),
}


def fonts(t):
    fams = {t["disp"], t["body"], "DM Mono"}
    q = "&".join("family=" + f.replace(" ", "+") + ":wght@400;500;700;800;900" if f not in ("DM Mono",) else "family=DM+Mono:wght@400;500" for f in sorted(fams))
    q = q.replace("Fraunces:wght@400;500;700;800;900", "Fraunces:opsz,wght@9..144,400;9..144,700;9..144,800;9..144,900")
    q = q.replace("Literata:wght@400;500;700;800;900", "Literata:opsz,wght@7..72,400;7..72,500;7..72,700")
    q = q.replace("Bricolage+Grotesque:wght@400;500;700;800;900", "Bricolage+Grotesque:opsz,wght@12..96,400;12..96,700;12..96,800")
    return f'<link href="https://fonts.googleapis.com/css2?{q}&display=block" rel="stylesheet">'


def css(t):
    return f"""
@page{{size:Letter;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--a:{t['a']};--b:{t['b']};--paper:{t['paper']}}}
body{{font-family:'{t['body']}',sans-serif;color:var(--a);background:#fff}}
.page{{width:8.5in;height:11in;position:relative;overflow:hidden;background:var(--paper);page-break-after:always;padding:.55in .6in .5in}}
.page:last-child{{page-break-after:auto}}
.grain{{position:absolute;inset:0;pointer-events:none;mix-blend-mode:multiply;opacity:.5;
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .3  0 0 0 0 .28  0 0 0 0 .25  0 0 0 .22 0'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>")}}
.ov{{mix-blend-mode:multiply}}
.disp{{font-family:'{t['disp']}',sans-serif;font-weight:{t['dispw']};line-height:.92;letter-spacing:-.01em}}
.mono{{font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:.09em}}
.head{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid var(--a);padding-bottom:10px;margin-bottom:18px;position:relative}}
.head h1{{font-size:44px;max-width:5.4in}}
.head .mono{{font-size:10px;text-align:right}}
.blob{{position:absolute;border-radius:50%;background:var(--b);opacity:.85}}
.foot{{position:absolute;left:.6in;right:.6in;bottom:.28in;display:flex;justify-content:space-between;font:400 8.5px 'DM Mono',monospace;letter-spacing:.08em;text-transform:uppercase;opacity:.8}}
.pk{{display:inline-block;width:13px;height:11px;background:#3E5C86;clip-path:polygon(0 0,100% 0,100% 62%,50% 100%,0 62%);vertical-align:-1px;margin-right:6px}}
/* trivia */
.qs{{columns:2;column-gap:.35in;font-size:13.4px;line-height:1.42}}
.q{{break-inside:avoid;margin-bottom:15px;display:flex;gap:8px}}
.q .n{{font:800 15px '{t['disp']}';min-width:22px;color:var(--b);mix-blend-mode:multiply;filter:brightness(.8)}}
.q .ln{{border-bottom:1.2px solid var(--a);height:22px;margin-top:3px;opacity:.6}}
.key{{columns:2;column-gap:.4in;font-size:12px;line-height:1.45}}
.key div{{break-inside:avoid;margin-bottom:5px}}
.key b{{color:var(--a)}}
.score{{display:flex;gap:14px;margin-top:6px;font-size:11px}}
.score span{{flex:1;border:1.5px solid var(--a);padding:6px 8px;height:44px}}
/* cards */
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:0;border:1.5px dashed var(--a);height:8.9in}}
.card{{border:1.5px dashed var(--a);margin:-.75px;padding:18px 20px;overflow:hidden;display:flex;flex-direction:column;justify-content:center;position:relative}}
.card .lbl{{position:absolute;top:12px;left:18px;font:500 8.5px 'DM Mono';letter-spacing:.1em;text-transform:uppercase}}
.card .t{{font-family:'{t['disp']}';font-weight:{t['dispw']};font-size:21px;line-height:1.08}}
.card .or{{font:500 10px 'DM Mono';letter-spacing:.1em;margin:7px 0;color:var(--b);filter:brightness(.85)}}
.card .corner{{position:absolute;right:-24px;bottom:-24px;width:70px;height:70px;border-radius:50%;background:var(--b);opacity:.55;mix-blend-mode:multiply}}
/* bingo */
.bingo{{border:3px solid var(--a);margin:0 auto;width:6.4in}}
.bingo .hdr{{display:grid;grid-template-columns:repeat(5,1fr);background:var(--a);color:var(--paper)}}
.bingo .hdr div{{text-align:center;font-size:42px;padding:6px 0 2px}}
.bingo .cells{{display:grid;grid-template-columns:repeat(5,1fr)}}
.bingo .cells div{{height:1.05in;border:1.5px solid var(--a);display:flex;align-items:center;justify-content:center;text-align:center;padding:6px;font-size:12px;line-height:1.2;font-weight:600}}
.bingo .cells .free{{background:var(--b);color:var(--paper);font:800 15px '{t['disp']}'}}
.cardno{{text-align:center;margin-top:8px;font-size:10px}}
.caller{{columns:3;font-size:12.5px;line-height:1.9}}
.caller div:before{{content:'';display:inline-block;width:11px;height:11px;border:1.5px solid var(--a);margin-right:8px;vertical-align:-1px}}
/* list */
.sec h2{{font-size:24px;margin:14px 0 6px;color:var(--a)}}
.sec ul{{list-style:none;columns:2;column-gap:.35in;font-size:13px;line-height:1.5}}
.sec li{{break-inside:avoid;margin-bottom:6px;display:flex;gap:9px}}
.sec li .bx{{min-width:13px;height:13px;border:1.6px solid var(--a);margin-top:3px}}
.note{{font-size:12px;margin-top:4px;opacity:.9}}
.story p{{font-size:14.5px;line-height:1.75;margin-bottom:11px}}
.story b{{color:var(--b);filter:brightness(.8);letter-spacing:.06em}}
.howto{{border:2px solid var(--a);padding:10px 14px;font-size:12px;margin-bottom:16px}}
"""


def page(t, spec, inner, n, total, blob=None):
    blob_html = ""
    if blob:
        x, y, s = blob
        blob_html = f'<div class="blob ov" style="left:{x};top:{y};width:{s};height:{s}"></div>'
    return (f'<section class="page">{blob_html}'
            f'<div class="head"><h1 class="disp">{html.escape(spec["title"])}</h1>'
            f'<div class="mono">{html.escape(spec.get("subtitle", ""))}<br>{THEMES[spec["theme"]]["tag"]} · page {n}/{total}</div></div>'
            f'{inner}<div class="foot"><span><span class="pk"></span>Pocketful Party · free for personal use</span>'
            f'<span>more free games: {html.escape(spec.get("site_label", "pocketful party"))}</span></div><div class="grain"></div></section>')


def trivia(spec, t):
    qs = spec["questions"]
    per = spec.get("per_page", 20)
    chunks = [qs[i:i + per] for i in range(0, len(qs), per)]
    total = len(chunks) + 1
    pages = []
    num = 1
    for ci, ch in enumerate(chunks):
        items = ""
        for q in ch:
            items += f'<div class="q"><div class="n">{num}</div><div style="flex:1">{html.escape(q["q"])}<div class="ln"></div></div></div>'
            num += 1
        inner = (f'<div class="score mono"><span>Team / name</span><span style="flex:.45">Score</span></div>'
                 f'<div style="height:14px"></div><div class="qs">{items}</div>') if ci == 0 else f'<div class="qs">{items}</div>'
        pages.append(page(t, spec, inner, ci + 1, total, ("6.6in", "-0.9in", "2.4in") if ci == 0 else None))
    key = "".join(f'<div><b>{i + 1}.</b> {html.escape(q["a"])}</div>' for i, q in enumerate(qs))
    pages.append(page(t, dict(spec, title=spec.get("key_title", "Answer key")), f'<div class="key">{key}</div>', total, total))
    return pages


def cards(spec, t):
    per = spec.get("per_page", 8)
    cs = spec["cards"]
    chunks = [cs[i:i + per] for i in range(0, len(cs), per)]
    pages = []
    rows = per // 2
    for ci, ch in enumerate(chunks):
        cells = ""
        for c in ch:
            if " OR " in c:
                a, b = c.split(" OR ", 1)
                body = f'<div class="t">{html.escape(a)}</div><div class="or">— or —</div><div class="t">{html.escape(b)}</div>'
            else:
                body = f'<div class="t">{html.escape(c)}</div>'
            cells += f'<div class="card"><div class="lbl">{html.escape(spec.get("card_label", ""))}</div>{body}<div class="corner"></div></div>'
        cells += '<div class="card"></div>' * (per - len(ch))
        inner = f'<div class="cards" style="grid-template-rows:repeat({rows},1fr)">{cells}</div>'
        pages.append(page(t, spec, inner, ci + 1, len(chunks)))
    return pages


def bingo(spec, t):
    rnd = random.Random(spec["slug"])
    words = spec["words"]
    count = spec.get("count", 10)
    total = count + (1 if spec.get("caller", True) else 0)
    pages = []
    for i in range(count):
        pick = rnd.sample(words, 24)
        pick.insert(12, None)
        cells = "".join(
            f'<div class="free">{html.escape(spec.get("free_label", "FREE"))}</div>' if w is None else f"<div>{html.escape(w)}</div>"
            for w in pick)
        hdr = "".join(f'<div class="disp">{ch}</div>' for ch in spec.get("letters", "BINGO"))
        inner = (f'<div style="height:.25in"></div><div class="bingo"><div class="hdr">{hdr}</div><div class="cells">{cells}</div></div>'
                 f'<div class="cardno mono">card {i + 1} of {count}</div>')
        pages.append(page(t, spec, inner, i + 1, total, ("-1in", "8.6in", "2.6in")))
    if spec.get("caller", True):
        items = "".join(f"<div>{html.escape(w)}</div>" for w in sorted(words, key=str.lower))
        pages.append(page(t, dict(spec, title="Caller's checklist"),
                          f'<p class="note">Cut these out and draw from a bowl, or just tick them off as you call them.</p><div style="height:12px"></div><div class="caller">{items}</div>',
                          total, total))
    return pages


def listing(spec, t):
    secs = ""
    for s in spec["sections"]:
        lis = "".join(f'<li>{"<span class=bx></span>" if spec.get("checkbox", True) else ""}<span>{html.escape(i)}</span></li>' for i in s["items"])
        secs += f'<div class="sec"><h2 class="disp">{html.escape(s["h"])}</h2><ul>{lis}</ul></div>'
    note = f'<p class="note">{html.escape(spec["note"])}</p>' if spec.get("note") else ""
    return [page(t, spec, note + secs, 1, 1, ("6.8in", "-1in", "2.2in"))]


def story(spec, t):
    paras = "".join("<p>" + html.escape(p).replace("LEFT", "<b>LEFT</b>").replace("RIGHT", "<b>RIGHT</b>") + "</p>" for p in spec["paragraphs"])
    how = f'<div class="howto">{html.escape(spec["how_to"])}</div>' if spec.get("how_to") else ""
    return [page(t, spec, how + f'<div class="story">{paras}</div>', 1, 1)]


KINDS = dict(trivia=trivia, cards=cards, bingo=bingo, list=listing, story=story)


def main(path):
    spec = json.load(open(path))
    t = THEMES[spec["theme"]]
    pages = KINDS[spec["type"]](spec, t)
    out = os.path.join(ROOT, "printables", "_html", spec["slug"] + ".html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(f'<!doctype html><html><head><meta charset="utf-8">{fonts(t)}<style>{css(t)}</style></head><body>{"".join(pages)}</body></html>')
    print(out, len(pages), "pages")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
