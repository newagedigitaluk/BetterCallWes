# CLAUDE.md — Better Call Wes

## Venture Overview

Better Call Wes is a sole-trader plumbing and heating business based in Southampton, Hampshire. Wes holds Gas Safe registration #558654. The business serves SO14–SO51 postcodes. The site is a static HTML/CSS build served via Nginx in Docker, deployed through Coolify on a self-hosted Ubuntu VPS.

Key contact details: phone 07700 155 655, email hello@bettercallwes.co.uk.

---

## Repository Structure

This repository contains both the website and the business workspace:

```
Better Call Wes/
├── CLAUDE.md                  ← You are here
├── Dockerfile                 ← Docker build config (copies website/site → nginx)
├── nginx.conf                 ← Web server config
├── website/                   ← Single umbrella for everything website-related
│   ├── site/                  ← THE DEPLOYABLE static site (HTML/CSS/JS/images)
│   ├── scripts/               ← Python build scripts + scripts/seo/ pipeline
│   ├── docs/                  ← DESIGN.md, SITE.md, deployment docs
│   ├── social/                ← Social media content bank + posting automation
│   ├── ServiceM8/             ← Job management forms + n8n workflows
│   ├── marketingskills/       ← Marketing content library
│   ├── Brand Images/          ← Brand + work photos for ads/social
│   └── SEO Site Design/       ← Original SEO design brief
└── workspace/                 ← Business operations and session management
    ├── obsidian/              ← Quotes, customers, suppliers, templates
    ├── scripts/               ← start-session.sh, end-session.sh
    └── outputs/               ← Generated documents
```

---

## Session Start — Read These Files First

At the start of every session, read the following files in order:

1. `~/obsidian-vault/_claude/Master-Context.md` — global context about Wes and all ventures
2. `~/obsidian-vault/Better-Call-Wes/Architecture.md` — current tech stack and site structure
3. `~/obsidian-vault/Better-Call-Wes/Progress-Log.md` — what has been done and what is in progress (read the top 3–5 entries)
4. `~/obsidian-vault/Better-Call-Wes/Decisions.md` — significant past decisions and their reasoning

After reading, summarise what you understand about the current state of the project, then ask what Wes wants to work on today before starting any work.

---

## Standing Conventions

- **Language**: British English throughout — "colour" not "color", "optimise" not "optimize", "plumber" not "plumber" (obvs), etc.
- **Code style**: Keep Python scripts simple and self-contained. No unnecessary abstractions or dependencies.
- **HTML/CSS**: Semantic HTML5, mobile-first CSS. Match the established design system (Navy `#0A2540`, Orange `#FF6B00`).
- **SEO**: Every page must have a unique `<title>`, `<meta description>`, canonical URL, and JSON-LD schema where appropriate.
- **Links**: Always validate internal links after any structural changes (`website/scripts/validate_links.py`).
- **No frameworks**: Do not introduce JS frameworks (React, Vue, etc.) unless explicitly asked. The site is intentionally plain HTML/CSS.
- **Deployment**: Docker + Coolify. Do not commit secrets. Environment variables go in Coolify, not in code.

---

## Session Management Rules

- **Always run `workspace/scripts/start-session.sh` at the beginning of each new session** to get context from recent sessions and open tasks
- **Always run `workspace/scripts/end-session.sh` before ending a session** to log what was done and commit to git
- **Never end a session without saving a summary** — session continuity depends on accurate logs
- **Keep session logs concise** — bullet points preferred over long paragraphs
- **Tag any unresolved items as TODO** in session summaries so they're picked up next time

---

## Knowledge Base Rules

- **Save all generated quotes** to `workspace/obsidian/quotes/` as `YYYY-MM-DD-customer-name.md`
- **Save all customer records** to `workspace/obsidian/customers/` as `customer-name.md` and update after every job
- **Save supplier research** to `workspace/obsidian/suppliers/`
- **Use templates** from `workspace/obsidian/templates/` for all customer-facing documents (quotes, emails, job summaries)
- **Never commit sensitive payment information** — no card numbers, bank account details (except business account for quotes), or personal financial data

---

## Git Sync Rules

- **Commit and push to GitHub at the end of every session** (the `end-session.sh` script handles this)
- **Use clear commit messages** describing what was done (e.g., "Session summary 2026-03-22 Better Call Wes")
- **Never commit sensitive customer payment information** — add sensitive patterns to `.gitignore` if needed

---

## Communication Rules

- **Always use templates as a starting point** for emails (from `workspace/obsidian/templates/customer-email-template.md`)
- **Never send any email or external message without Wes's explicit approval**
- **Always show the draft first and wait for confirmation** before sending anything customer-facing
- **Keep all customer communication professional and friendly** — match the tone in the templates
- **British English** in all customer communications

---

## Session End — Update These Files

At the end of every session (or when asked to wrap up), update the following files:

### Progress-Log: `~/obsidian-vault/Better-Call-Wes/Progress-Log.md`

Add a new entry at the **top** of the file (below the header, above previous entries) in this format:

```markdown
## YYYY-MM-DD — [brief title of session]

- [bullet: what was completed]
- [bullet: what was completed]

**In progress:**
- [anything left unfinished]

**Blockers:**
- [any blockers discovered, or "None"]
```

### Decisions: `~/obsidian-vault/Better-Call-Wes/Decisions.md`

If any significant decisions were made during the session, add an entry at the **top** of the decisions list in this format:

```markdown
## YYYY-MM-DD — [decision title]

**Decision**: [what was decided]

**Reasoning**: [why this was chosen]

**Alternatives considered**:
- [alternative] — rejected: [reason]
```

Only add a decision entry if an architectural, tooling, or strategy decision was made. Skip if the session was purely implementation of a previously agreed approach.


---

## Environment & File Access

This project lives on the VPS at `/home/wes/Coding/Projects/<this project>/` on local **ext4** disk (migrated 2026-04-25 from a fuse.rclone gdrive mount). The Mac browses these files via **SSHFS at `~/VPS/Projects/<this project>/`** (FUSE-T, auto-mounted on login by `com.wes.vps-sshfs.plist`).

**Do not run `npm install`, builds, test runners, `pip install`, or other heavy tooling through the Mac SSHFS mount** — every file access goes over the network and will be slow. Run all dev work on the VPS directly (SSH or VS Code Remote-SSH). The SSHFS mount is for browsing, opening files in Mac apps, and quick edits only.

Nightly archival to `gdrive:Coding-Backup/latest/` runs at 03:30 UTC. Logs: `~/.local/share/rclone/archival.log`.
