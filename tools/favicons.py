"""Render the brand logo into the favicon set search engines and phones look for.

    python3 tools/favicons.py   # writes static/favicon.ico, static/apple-touch-icon.png, static/img/favicon-*.png

Google shows a site's favicon in results only if it is square and a multiple of 48px,
so the PNGs are 48/96/192 and the .ico carries 16/32/48. Run it again if the logo
in tools/brand.py changes, and commit the output (the deploy doesn't render images).
"""
import os
import subprocess
import tempfile

from PIL import Image

from brand import logo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "static")


def shot(size, pad, out):
    # white tile behind the map so the icon reads on Google's light and dark result pages
    svg = logo(size - 2 * pad)
    page = (f'<!doctype html><html><body style="margin:0;background:#fff;width:{size}px;height:{size}px;'
            f'display:flex;align-items:center;justify-content:center">{svg}</body></html>')
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(page)
    subprocess.run(["node", os.path.join(ROOT, "tools", "render.js"), "shot", f.name, out, str(size), str(size)], check=True)
    os.unlink(f.name)


def main():
    img = os.path.join(STATIC, "img")
    for size in (48, 96, 192, 512):
        shot(size, round(size * 0.04), os.path.join(img, f"favicon-{size}.png"))
    shot(180, 18, os.path.join(STATIC, "apple-touch-icon.png"))
    Image.open(os.path.join(img, "favicon-192.png")).save(os.path.join(STATIC, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    old = os.path.join(img, "favicon.png")
    if os.path.exists(old):
        os.remove(old)
    print("favicons written to static/")


if __name__ == "__main__":
    main()
