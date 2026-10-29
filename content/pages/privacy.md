---
title: Privacy
date: 2026-10-23
description: What Med Mapped collects (very little).
---
Med Mapped doesn't ask for your name or email, and you don't need an account to download anything.

The site is hosted on GitHub Pages, which keeps standard server logs (like IP addresses) for security. Links from Pinterest carry a tag in the web address so I can see which pin a visit came from; that tag doesn't identify you.

## Visit counts

I count page views so I know which guides are actually helping people. When a page loads, it sends one small note to my database (hosted by Supabase) with:

- which page you opened, like /cost-of-applying-to-med-school/
- the website that linked you here, by domain only (like pinterest.com), not the full address
- any tracking tags on the link (the utm_ ones), which is how I tell which pin you came from
- whether the screen is phone, tablet or desktop sized
- the time

That's it! No cookies, no IP address, no browser fingerprint, and nothing that could tell me who you are or connect one visit to another. Nobody can read the individual entries through the website; I only look at totals. Blocking JavaScript or using a content blocker stops the count entirely, and the site works exactly the same.

If I ever add ads or an email list, this page will be updated first and will explain what's collected and how to opt out.
