# Med Mapped: operator runbook

**Med Mapped** ("the road to med school, mapped out") is a blog written from the perspective of Dylan, a first-year med student (MD class of 2030). It gets free traffic from Pinterest and sends readers to his Etsy application trackers (med, residency, PA, dental, vet, grad; listing links in `site.json` `etsy_products`). Owner: Dylan (non-engineer, <5 hrs/week, wants it hands-off).
Renamed from "Pocketful Party" (party games) on 2026-10-24. The site lives at **https://medmapped.com** (bought 2026-10 at Porkbun, Dylan's account; DNS at Porkbun points to GitHub Pages, custom domain set in the repo's Pages settings). The repo keeps the old name; old github.io/pocketful-party links redirect to the domain. The old party posts have `category: extras`: their pages stay live for pins already out, but they're hidden from the site, sitemap and feeds, and their unreleased pins are on `hold`. Dylan wants holiday content to be its own separate thing, so don't write party posts here and don't release held pins.
The scheduled tasks that run this blog were created before the rename and their prompts still say "Pocketful Party blog (free printable party games)" and "verify every trivia fact". Those tasks can't be edited in place, so this file wins: it is the Med Mapped blog, every post follows the content rules below, and no party posts.
Site: static, built by `tools/build.py`, hosted on GitHub Pages, deployed by `.github/workflows/deploy.yml` on every push and every hour.

## How the pieces fit

| Piece | Where |
|---|---|
| Posts | `content/posts/<slug>.md` (front matter + markdown; `[[printable]]` and `[[etsy:key]]` shortcodes; `category: applying` or `med-school`) |
| Brand (name, logo SVG) | `tools/brand.py` + `site.json` `name`/`tagline`/`author_bio`; the site, printables and pins all read it |
| MD Atlas (Dylan's app with a free version and a paid Pro tier, repo `dnguyen01pdx/Premed-Project`, Vercel) | `site.json` `atlas` (URL, blurb, tool cards). Linked in the nav, footer and a homepage block; `[[atlas:primary|secondaries|planner]]` drops a card into a post (use at most once, not next to the Etsy card). MD Atlas links back to the blog and shows its newest posts from `feed.xml`; both sites share the same colors and fonts |
| Facts about Dylan | `data/dylan_facts.md`: the only personal details posts may use |
| Printable specs (game content + pin texts) | `printables/<slug>.json`, rendered by `tools/printables.py` + `tools/render.js` |
| Pin queue | `data/pins.json`. A pin goes live when the hourly build puts it into `feeds/<board>.xml`; Pinterest auto-publishes from those RSS feeds. A pin spec may add `"link": "https://atlas.medmapped.com/..."` to send the pin to an MD Atlas page instead of its post (it still counts toward its post's 48h spacing) |
| Content plan | `data/calendar.json` (from Pinterest Trends research in `data/pinterest_trends_*.json`; the med plan is in `pinterest_trends_2026-10-med.json`) |
| Pin design weights | `data/designs.json` (monthly analytics update these) |
| Search | Google Search Console + Bing Webmaster Tools (Dylan's Google account) verify both sites with `google5101d02630a05884.html` (blog `static/`, MD Atlas `public/`): never delete it. Every push pings IndexNow (`indexnow` job in deploy.yml) |
| Traffic | Cookie-free page-view counter on every page (blog and MD Atlas) logging to Dylan's Supabase project: `site.json` `supabase` (URL + public publishable key; RLS makes it insert-only), schema/views/`traffic_summary()` in `tools/traffic.sql`, MD Atlas side in its `src/components/PageViews.tsx`. Privacy pages on both sites describe exactly what a row holds; change them first if the fields change |
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
   - Mon / Wed / Fri: write the next post from `data/calendar.json` (earliest `publish_by` with empty status). Keep the mix about half applying (converts to the trackers) and half med school life / study (most Pinterest demand). Seasonal posts whose `publish_by` is already past the season peak get skipped (status `skipped`).
   - Tue / Thu: add 2 fresh pin designs to an older post that still has search demand, using the weighted templates.
   - Sat / Sun: maintenance only (retries, link checks, queue top-up). Sunday also: check that the queue has 7+ days of runway.
3. **Write a post** (when it's a post day):
   - Write `printables/<slug>.json` first (the free checklist, worksheet or planner; types `list`, `fill`, `grid`, see `tools/printables.py`), then `content/posts/<slug>.md` (800-1300 words, first person as Dylan, specific, like advice to a friend; Dylan asked 2026-10-28 for a warm, friendly, encouraging tone with more exclamation points, roughly one every paragraph or two, never on every sentence; pin descriptions get the same warmth. Don't lean on "glad": Dylan said 2026-10-28 it was overused, so use it rarely and vary the warm phrasing). Use the 3 posts from 2026-10-24 as the bar for quality and tone.
   - **Research Reddit first** (Dylan, 2026-10-30): before writing, search Reddit (r/premed, r/medicalschool, r/MCAT, r/medicalschooladmissions, etc.) for threads on the topic. Lean on well-received threads (high upvotes, comments agreeing it helped) and skip controversial or downvoted ones. Use them for what applicants actually struggle with, the questions they ask and the tips that keep getting confirmed, then write it in your own words. Reddit is never the source for fees, dates or rules (those still come from the official source), never quote or copy a post, and never pass off a Redditor's story as Dylan's.
   - **Relatable, humble and personable** (Dylan, 2026-10-30): on top of warm, the posts should sound like a fellow student, not an expert lecturing. Admit what's hard or confusing, avoid bragging, and talk to the reader like a friend going through it too.
   - Link the matching tracker with `[[etsy:<key>]]` once, after the reader has gotten real value (not at the top), and link 1-2 related posts.
   - 4-5 pins per post, at least 4 different templates, each with its own title and description that matches what the post really contains.
   - `python3 tools/pipeline.py assets <slug>`, then look at every pin and at least the first printable page (Read the images). Re-render anything with clipped text, overlap or unreadable contrast.
   - `python3 tools/pipeline.py check <slug>` must report 0 problems. Then `python3 tools/pipeline.py schedule`.
   - Set the calendar entry's status to `published`.
4. **Commit and push to main** (message: what was added/fixed). The deploy workflow builds and releases due pins.
5. **Verify the deploy**: wait for the Actions run (GitHub MCP `actions_list`), then fetch the new post URL and one feed with WebFetch (the cloud box's curl can't reach the site). If it failed, read the log, fix, push again (up to 3 attempts; then log it as a blocker).
6. **Log** to `data/runs/YYYY-MM-DD.md`: what was done, checks, anything failed or skipped, queue runway. Commit it.
7. End with a 3-5 line summary (it is pushed to Dylan's phone): what went live, queue runway, anything that needs him.

## Content rules (non-negotiable)

- Every post must be genuinely useful: a real, complete printable plus clear, specific advice. No thin listicles, no keyword stuffing, no copied content.
- **Fees, dates, limits and rules must come from the official source** (AAMC/AMCAS, AACOMAS, CASPA, AADSAS, VMCAS, ERAS/NRMP, the test makers) and the post names the source and cycle year. Tell readers to confirm before paying. If you can't verify a number, leave it out.
- **Never invent Dylan's personal story.** First person is fine for opinions and advice ("here's how I'd do it"), but experiences, numbers, schools and anecdotes may only come from `data/dylan_facts.md`. Don't name his school until that file says it's OK.
- No medical advice, and nothing that claims to be official admissions advice or to speak for a school.
- MD Atlas has a paid Pro tier, so never call it "a free app" or "a free tool". Pitch it as "try the free version of MD Atlas" (Dylan, 2026-10-29). Saying a specific feature is in the free version is fine.
- Never invent reviews, testimonials, sales numbers, "readers love this" claims or fake urgency.
- Pins: no misleading text (the pin must show what the post delivers), no more than 3 hashtags (prefer 0), no repeated identical pins. Respect `site.json` limits (8 pins/day, same post at most every 48 hours). Pinterest spam rules: no mass-repinning, no clickbait, no link-only pins.
- Designs are made by code, not generative AI imagery. If generative AI imagery is ever used, label it per Pinterest's AI rules.
- FTC: posts that link to our Etsy shop say so (the build adds the line automatically). Any affiliate link must be disclosed near the top of the post and on /disclosure/.
- Keep each track's look distinct (themes `med`, `med-blue`, `study`, `residency`, `pa`, `dental`, `vet` in `tools/printables.py`, matching the inks on the Etsy tracker photos); don't drift into one generic template.

## Monthly analytics (1st of the month)

Pinterest analytics: read the business account's analytics (Chrome, logged in as Dylan) for the last 30 days: impressions, saves, outbound clicks per pin. Map pins by the `utm_content=<pin id>` on each link. Save `data/analytics/YYYY-MM.json`, update `data/designs.json` weights (outbound clicks per 1k impressions by template; floor 0.5, cap 3), list the top 5 posts and the content gaps (searches in the trends file with no post), and add the gaps to `data/calendar.json`. Refresh Pinterest Trends data for the next 3 months of seasons.

## Pinterest connection

Done 2026-10-23 on Dylan's account `dylannguyen01` (now a business account; it also holds his Etsy tracker boards). Site claimed; feeds connected are listed in `site.json` `connected_feeds`. The med feeds go to his existing tracker boards (Med School Applications, PA School Applications, etc.) plus "Med Student Life & Study Tips". **When a post uses a board that isn't connected yet**, in the same run: create the board on Pinterest if it doesn't exist (Chrome, own tab), add its feed at Settings > Bulk create Pins > Auto-publish > Add another, then add the board key to `connected_feeds`. Pinterest refuses a feed with no items, so connect it only after the board's first pin has been released and deployed (move that pin's `publish_at` earlier if needed). The health check flags any board with pins but no connected feed.

### Original setup steps (for reference)

Pins stay unreleased while `site.json` has `"pins_start": null`. Once the blog's Pinterest business account exists: claim the site (put the code in `site.json` `pinterest_verify`), add one RSS feed per board that has pins (`<base_url>/feeds/<board>.xml` -> matching board), set `pins_start` to the current UTC time, run `python3 tools/pipeline.py reschedule`, commit and push.

## Never without Dylan's explicit OK

Spending money, creating accounts, accepting new terms, applying to ad networks or affiliate programs, changing the domain/DNS, or deleting published posts.
