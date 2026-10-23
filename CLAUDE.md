# Pocketful Party: operator runbook

Free printable party games blog that gets its traffic from Pinterest. Owner: Dylan (non-engineer, <5 hrs/week, wants it hands-off).
Site: static, built by `tools/build.py`, hosted on GitHub Pages, deployed by `.github/workflows/deploy.yml` on every push and every hour.

## How the pieces fit

| Piece | Where |
|---|---|
| Posts | `content/posts/<slug>.md` (front matter + markdown; `[[printable]]` and `[[etsy:key]]` shortcodes) |
| Printable specs (game content + pin texts) | `printables/<slug>.json`, rendered by `tools/printables.py` + `tools/render.js` |
| Pin queue | `data/pins.json`. A pin goes live when the hourly build puts it into `feeds/<board>.xml`; Pinterest auto-publishes from those RSS feeds |
| Content plan | `data/calendar.json` (from Pinterest Trends research in `data/pinterest_trends_*.json`) |
| Pin design weights | `data/designs.json` (monthly analytics update these) |
| Run logs | `data/runs/YYYY-MM-DD.md` (one per daily run; the health check reads them) |
| Analytics | `data/analytics/YYYY-MM.json` |

Commands (cloud box needs `NODE_PATH=/opt/node22/lib/node_modules`):

```
python3 tools/pipeline.py assets <slug>   # PDF, page PNGs, pin JPGs, queue entries
python3 tools/pipeline.py check [slug]    # pre-queue checks; must print 0 problems
python3 tools/pipeline.py schedule        # assign publish times within limits
python3 tools/pipeline.py status
python3 tools/build.py                    # local build into _site/
```

## The daily run (scheduled task, every morning)

1. **Read before touching anything.** `git pull`, then `python3 tools/pipeline.py status`, the latest `data/runs/` log, open GitHub issues labeled `health`, and the last Actions runs (`gh run list -L 10` if available). Fix anything broken first; that is today's work.
2. **Pick the day's work.**
   - Mon / Wed / Fri: write the next post from `data/calendar.json` (earliest `publish_by` with empty status). Seasonal posts whose `publish_by` is already past the season peak get skipped (status `skipped`).
   - Tue / Thu: add 2 fresh pin designs to an older post that still has search demand (evergreen first, then in-season), using the weighted templates.
   - Sat / Sun: maintenance only (retries, link checks, queue top-up). Sunday also: check that the queue has 7+ days of runway.
3. **Write a post** (when it's a post day):
   - Write `printables/<slug>.json` first (the game itself), then `content/posts/<slug>.md` (700-1200 words: what's in it, how to play, variations for kids/adults/big groups, prizes, tips). Use the existing posts as the bar for quality and tone.
   - 4-5 pins per post, at least 4 different templates, each with its own title and description that matches what the post really contains.
   - `python3 tools/pipeline.py assets <slug>`, then look at every pin and at least the first printable page (Read the images). Re-render anything with clipped text, overlap or unreadable contrast.
   - `python3 tools/pipeline.py check <slug>` must report 0 problems. Then `python3 tools/pipeline.py schedule`.
   - Set the calendar entry's status to `published`.
4. **Commit and push to main** (message: what was added/fixed). The deploy workflow builds and releases due pins.
5. **Verify the deploy**: wait for the Actions run (GitHub MCP `actions_list`), then fetch the new post URL and one feed with WebFetch (the cloud box's curl can't reach github.io). If it failed, read the log, fix, push again (up to 3 attempts; then log it as a blocker).
6. **Log** to `data/runs/YYYY-MM-DD.md`: what was done, checks, anything failed or skipped, queue runway. Commit it.
7. End with a 3-5 line summary (it is pushed to Dylan's phone): what went live, queue runway, anything that needs him.

## Content rules (non-negotiable)

- Every post must be genuinely useful: a real, complete, playable printable plus clear instructions. No thin listicles, no keyword stuffing, no copied content, no song lyrics or copyrighted characters' artwork.
- Trivia answers must be verified. If you can't verify a fact with confidence, drop the question.
- Never invent reviews, testimonials, sales numbers, "readers love this" claims or fake urgency.
- Pins: no misleading text (the pin must show what the post delivers), no more than 3 hashtags (prefer 0), no repeated identical pins. Respect `site.json` limits (8 pins/day, same post at most every 48 hours). Pinterest spam rules: no mass-repinning, no clickbait, no link-only pins.
- Designs are made by code, not generative AI imagery. If generative AI imagery is ever used, label it per Pinterest's AI rules.
- FTC: posts that link to our Etsy shop say so (the build adds the line automatically). Any affiliate link must be disclosed near the top of the post and on /disclosure/.
- Keep each season's look distinct (themes in `tools/printables.py`); don't drift into one generic template.

## Monthly analytics (1st of the month)

Pinterest analytics: read the business account's analytics (Chrome, logged in as Dylan) for the last 30 days: impressions, saves, outbound clicks per pin. Map pins by the `utm_content=<pin id>` on each link. Save `data/analytics/YYYY-MM.json`, update `data/designs.json` weights (outbound clicks per 1k impressions by template; floor 0.5, cap 3), list the top 5 posts and the content gaps (searches in the trends file with no post), and add the gaps to `data/calendar.json`. Refresh Pinterest Trends data for the next 3 months of seasons.

## Pinterest connection (one-time, needs Dylan's yes)

Pins stay unreleased while `site.json` has `"pins_start": null`. Once the blog's Pinterest business account exists: claim the site (put the code in `site.json` `pinterest_verify`), add one RSS feed per board that has pins (`<base_url>/feeds/<board>.xml` -> matching board), set `pins_start` to the current UTC time, run `python3 tools/pipeline.py reschedule`, commit and push.

## Never without Dylan's explicit OK

Spending money, creating accounts, accepting new terms, applying to ad networks or affiliate programs, changing the domain/DNS, or deleting published posts.
