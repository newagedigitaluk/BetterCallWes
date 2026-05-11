# Better Call Wes

Sole-trader plumbing and heating business — Southampton, Hampshire (SO14–SO51).
Gas Safe registered. Phone 07700 155 655. Email hello@bettercallwes.co.uk.

The live site is a static HTML/CSS build served by Nginx in Docker, deployed to
a self-hosted Ubuntu VPS via Coolify on every push to `main`.

## Where things live

```
.
├── CLAUDE.md          ← Project instructions Claude reads at session start
├── Dockerfile         ← Build config (COPY website/site → nginx)
├── nginx.conf         ← Web-server config (try_files / clean URLs)
├── README.md          ← This file
│
├── docs/              ← All documentation
│   ├── DEPLOY.md, DESIGN.md, SITE.md, PRODUCT.md, MASTER_PRICE_GUIDE_UK.md
│   ├── meta/          ← Meta ads docs (CTWA, token rotation, V3 build/state)
│   ├── seo-site-design/  ← Original SEO design brief
│   ├── website-brief/    ← PDF briefs from initial site design
│   └── screenshots/   ← Archived reference screenshots (gitignored)
│
├── website/           ← Everything website + marketing
│   ├── site/          ← THE DEPLOYABLE static site (Dockerfile copies this)
│   ├── scripts/       ← Python build/SEO scripts
│   │   └── seo/       ← DataForSEO + VebAPI automation pipeline
│   ├── social/        ← Content bank + posting automation
│   │   └── ads/       ← Generated ad creatives (images gitignored)
│   ├── ServiceM8/     ← Invoice templates + n8n workflows
│   ├── marketingskills/  ← Marketing content library
│   └── Brand Images/  ← Large raw originals (gitignored)
│
├── workspace/         ← Business ops (Obsidian, session scripts, outputs)
├── reels/             ← Video-reel project (Remotion)
└── Financial Docs/    ← Cashflow, exports (kept local, off git)
```

## Common tasks

| Task | How |
|---|---|
| Edit a service page | `website/site/services/<name>.html` |
| Edit a location page | `website/site/locations/<slug>.html` |
| Run the SEO dashboard | `python3 website/scripts/seo/seo_dashboard.py` |
| Post the next social entry | `python3 website/social/post_daily.py` |
| Trigger a deploy | `git push origin main` (Coolify rebuilds automatically) |

## Documentation entry points

- **For deployment**: `docs/DEPLOY.md`
- **For design system**: `docs/DESIGN.md`
- **For site structure**: `docs/SITE.md`
- **For Wes's brand & writing voice**: `docs/PRODUCT.md`
- **For pricing the work**: `docs/MASTER_PRICE_GUIDE_UK.md`
- **For Meta ads work**: `docs/meta/`
- **For SEO automation**: `website/scripts/seo/README.md`

## Working sessions

Claude Code reads `CLAUDE.md` automatically at session start.
The Obsidian vault at `~/obsidian-vault/Better-Call-Wes/` carries the
progress log, decisions log, architecture notes, and SEO reports.

Start a session: `workspace/scripts/start-session.sh`
End a session: `workspace/scripts/end-session.sh`
