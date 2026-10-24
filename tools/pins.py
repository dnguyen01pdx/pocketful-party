#!/usr/bin/env python3
"""Pin designs (1000x1500). Five layouts so the account never looks like one template.

Each pin spec (inside printables/<slug>.json -> "pins") has:
  template: stack | split | list | fan | hook
  headline, kicker (optional), sub (optional), items (list, for 'list'), quote (for 'hook')
  title, description: the Pinterest pin title/description (checked by tools/check.py)
Images used: the printable's page PNGs from printables/_png/<slug>/pN.png.
"""
import html, os

from brand import SITE, logo
from printables import THEMES, fonts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BRAND = logo(46) + html.escape(SITE["name"])


def e(s):
    return html.escape(s or "")


def base_css(t):
    return f"""
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--a:{t['a']};--b:{t['b']};--paper:{t['paper']}}}
body{{width:1000px;height:1500px;overflow:hidden;background:var(--paper);color:var(--a);font-family:'{t['body']}',sans-serif;position:relative}}
.disp{{font-family:'{t['disp']}',sans-serif;font-weight:{t['dispw']};line-height:.9;letter-spacing:-.015em}}
.mono{{font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:.1em}}
.ov{{mix-blend-mode:multiply}}
.grain{{position:absolute;inset:0;pointer-events:none;mix-blend-mode:multiply;opacity:.55;z-index:60;
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .3  0 0 0 0 .28  0 0 0 0 .25  0 0 0 .3 0'/></filter><rect width='400' height='400' filter='url(%23n)'/></svg>")}}
.brand{{position:absolute;display:flex;align-items:center;gap:14px;font:500 22px 'DM Mono',monospace;letter-spacing:.1em;text-transform:uppercase;z-index:20}}
.pk{{width:36px;height:31px;background:#3E5C86;clip-path:polygon(0 0,100% 0,100% 62%,50% 100%,0 62%);position:relative}}
.pk:after{{content:'';position:absolute;inset:5px 5px 7px;border:2px dashed #F2C66B;clip-path:polygon(0 0,100% 0,100% 62%,50% 100%,0 62%)}}
.free{{display:inline-block;background:var(--b);color:var(--a);padding:10px 18px 8px;font:500 24px 'DM Mono',monospace;letter-spacing:.1em;text-transform:uppercase}}
.sheet{{position:absolute;background:#fff;box-shadow:14px 14px 0 var(--a);border:3px solid var(--a)}}
.sheet img{{display:block;width:100%;height:100%;object-fit:cover;object-position:top}}
"""


# Shrink any [data-fit=maxHeightPx] text until it fits; render.js waits for __fitDone.
FIT = """<script>window.__fitDone=false;document.fonts.ready.then(()=>{document.querySelectorAll('[data-fit]').forEach(el=>{
const max=+el.dataset.fit;let fs=parseFloat(getComputedStyle(el).fontSize);
while(el.scrollHeight>max&&fs>28){fs-=3;el.style.fontSize=fs+'px'}});window.__fitDone=true})</script>"""


def doc(t, css, body):
    return (f'<!doctype html><html><head><meta charset="utf-8">{fonts(t)}<style>{base_css(t)}{css}</style></head>'
            f'<body>{body}<div class="grain"></div>{FIT}</body></html>')


def img(slug, n):
    return "file://" + os.path.join(ROOT, "printables", "_png", slug, f"p{n}.png")


def stack(t, slug, p):
    css = ".hl{position:absolute;left:60px;top:150px;width:880px;font-size:126px}"
    body = (f'<div class="ov" style="position:absolute;left:0;top:0;width:1000px;height:640px;background:var(--b)"></div>'
            f'<div class="brand" style="left:60px;top:60px">{BRAND}</div>'
            f'<div class="disp hl" data-fit="460">{e(p["headline"])}</div>'
            f'<div class="sheet" style="left:150px;top:{p.get("sheet_top", 700)}px;width:700px;height:906px;transform:rotate(-2.5deg)"><img src="{img(slug, p.get("page", 1))}"></div>'
            f'<div style="position:absolute;right:60px;bottom:70px;z-index:30" class="free">{e(p.get("kicker", "Free printable"))}</div>')
    return doc(t, css, body)


def split(t, slug, p):
    body = (f'<div style="position:absolute;left:0;top:0;width:1000px;height:820px;overflow:hidden;border-bottom:6px solid var(--a)">'
            f'<img src="{img(slug, p.get("page", 1))}" style="width:1300px;margin:-60px 0 0 -150px;transform:rotate(-4deg)"></div>'
            f'<div class="ov" style="position:absolute;left:0;top:820px;width:1000px;height:680px;background:var(--a)"></div>'
            f'<div style="position:absolute;left:70px;top:880px;width:860px;color:var(--paper)">'
            f'<div class="mono" style="font-size:24px;color:var(--b);margin-bottom:22px">{e(p.get("kicker", "Free printable"))}</div>'
            f'<div class="disp" style="font-size:112px" data-fit="300">{e(p["headline"])}</div>'
            f'<div style="font-size:32px;margin-top:26px;line-height:1.3;opacity:.92">{e(p.get("sub", ""))}</div></div>'
            f'<div class="brand" style="left:70px;bottom:50px;color:var(--paper)">{BRAND}</div>')
    return doc(t, "", body)


def listing(t, slug, p):
    items = "".join(f'<div style="display:flex;gap:26px;align-items:baseline;padding:32px 0;border-bottom:3px solid var(--a)">'
                    f'<div class="disp" style="font-size:78px;min-width:80px;color:var(--b);filter:brightness(.82)">{i + 1}</div>'
                    f'<div style="font-size:42px;line-height:1.2;font-weight:600">{e(x)}</div></div>' for i, x in enumerate(p["items"]))
    body = (f'<div class="ov" style="position:absolute;right:-180px;top:-160px;width:620px;height:620px;border-radius:50%;background:var(--b)"></div>'
            f'<div class="brand" style="left:70px;top:70px">{BRAND}</div>'
            f'<div style="position:absolute;left:70px;top:170px;width:860px">'
            f'<div class="disp" style="font-size:108px" data-fit="250">{e(p["headline"])}</div>'
            f'<div style="margin-top:30px;border-top:6px solid var(--a)">{items}</div></div>'
            f'<div style="position:absolute;left:70px;bottom:70px" class="free">{e(p.get("kicker", "Free printable inside"))}</div>')
    return doc(t, "", body)


def fan(t, slug, p):
    pages = p.get("pages", [1, 2, 3])
    sheets = ""
    for i, n in enumerate(pages[:3]):
        rot = [-9, 0, 8][i]
        left = [70, 230, 390][i]
        top = [190, 150, 210][i]
        sheets += f'<div class="sheet" style="left:{left}px;top:{top}px;width:540px;height:699px;transform:rotate({rot}deg);z-index:{i + 1}"><img src="{img(slug, n)}"></div>'
    body = (f'<div class="ov" style="position:absolute;left:-100px;top:80px;width:1200px;height:880px;background:var(--b);transform:rotate(-4deg)"></div>'
            f'<div class="brand" style="left:60px;top:50px">{BRAND}</div>{sheets}'
            f'<div style="position:absolute;left:60px;top:1010px;width:880px">'
            f'<div class="mono" style="font-size:24px;margin-bottom:18px">{e(p.get("kicker", "Free printable"))}</div>'
            f'<div class="disp" style="font-size:118px" data-fit="270">{e(p["headline"])}</div>'
            f'<div style="font-size:30px;margin-top:20px">{e(p.get("sub", ""))}</div></div>')
    return doc(t, "", body)


def hook(t, slug, p):
    body = (f'<div class="ov" style="position:absolute;right:-160px;bottom:120px;width:640px;height:640px;border-radius:50%;background:var(--b);opacity:.9"></div>'
            f'<div class="brand" style="left:70px;top:70px">{BRAND}</div>'
            f'<div class="mono" style="position:absolute;left:70px;top:250px;font-size:26px">{e(p.get("kicker", ""))}</div>'
            f'<div style="position:absolute;left:70px;top:320px;width:860px;border:5px solid var(--a);padding:60px 56px;background:var(--paper);box-shadow:20px 20px 0 var(--b)">'
            f'<div class="disp" style="font-size:96px;line-height:.98" data-fit="560">{e(p["quote"])}</div></div>'
            f'<div style="position:absolute;left:70px;bottom:170px;width:860px;z-index:5">'
            f'<div class="disp" style="font-size:84px" data-fit="180">{e(p["headline"])}</div>'
            f'<div style="font-size:30px;margin-top:16px">{e(p.get("sub", ""))}</div></div>'
            f'<div class="ov" style="position:absolute;left:0;bottom:0;width:1000px;height:70px;background:var(--b)"></div>')
    return doc(t, "", body)


TEMPLATES = dict(stack=stack, split=split, list=listing, fan=fan, hook=hook)


def pin_html(theme, slug, p):
    return TEMPLATES[p["template"]](THEMES[theme], slug, p)
