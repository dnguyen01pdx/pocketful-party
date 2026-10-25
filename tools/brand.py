"""Brand bits shared by the site, printables and pins: name, logo mark."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = json.load(open(os.path.join(ROOT, "site.json")))


def logo(size=40, paper="#FFFFFF", ink="#0E3B46", fold="#3C9DC2", pin="#FF6F59"):
    """Folded map with a dotted route that ends at a map pin with a medical cross."""
    return (f'<svg class="logo" width="{size}" height="{size}" viewBox="0 0 40 40" aria-hidden="true">'
            f'<path d="M2 13L13 9L25 13L36 9V35L25 39L13 35L2 39Z" fill="{paper}" stroke="{ink}" stroke-width="2.4" stroke-linejoin="round"/>'
            f'<path d="M13 9V35M25 13V39" stroke="{fold}" stroke-width="1.6"/>'
            f'<path d="M6 33C10 31 9 25 14 25S19 28 23 24" fill="none" stroke="{fold}" stroke-width="1.8" stroke-dasharray="2.4 2" stroke-linecap="round"/>'
            f'<path d="M29 25C24 19 22 16 22 12.5A7 7 0 0 1 36 12.5C36 16 34 19 29 25Z" fill="{pin}" stroke="{ink}" stroke-width="2.2" stroke-linejoin="round"/>'
            f'<path d="M29 8.6V16.4M25.1 12.5H32.9" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round"/></svg>')


def wordmark():
    """'Med Mapped' -> 'Med <b>Mapped</b>' (last word in the accent color)."""
    words = SITE["name"].split()
    return " ".join(words[:-1]) + f" <b>{words[-1]}</b>" if len(words) > 1 else f"<b>{SITE['name']}</b>"
