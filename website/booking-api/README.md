# booking-api

FastAPI service that powers the website booking form for Better Call Wes. Talks to ServiceM8 on the backend, exposes a small JSON API to the browser.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/healthcheck` | Liveness + SM8 auth probe |
| `GET` | `/api/services` | Returns services.json with live prices injected |
| `GET` | `/api/materials?items=A,B,C` | Targeted live price lookup by item_number |
| `GET` | `/api/availability?service=X&days=14` | Free slots from Wes's diary |
| `POST` | `/api/book` | Creates the job, materials, and diary activity |

## Local development

```sh
cd website/booking-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in SERVICEM8_API_KEY
DEV=1 python main.py
# Listening on http://127.0.0.1:8000
```

Quick smoke tests:

```sh
curl http://127.0.0.1:8000/api/healthcheck | jq
curl 'http://127.0.0.1:8000/api/services' | jq '.services | keys'
curl 'http://127.0.0.1:8000/api/availability?service=boiler-service&days=7' | jq
```

## Deployment via Coolify

Set up a new "Application" pointing at the same GitHub repo as the website.

**Build settings:**
- Build Pack: Dockerfile
- Base Directory: `website/`
- Dockerfile Path: `booking-api/Dockerfile`
- Port: `8000`

**Domains:**
- `api.bettercallwes.co.uk` (recommended — keeps API + website on the same TLD without path collisions)

**Environment variables:**
- `SERVICEM8_API_KEY` — required, paste from your existing `.env`
- `ALLOWED_ORIGINS` — `https://bettercallwes.co.uk,https://www.bettercallwes.co.uk`
- Everything else defaults sensibly.

**Health check:** Coolify can use `GET /api/healthcheck`. The Dockerfile has a built-in HEALTHCHECK that returns non-zero if SM8 auth fails.

**Logs:** structured Python logging at INFO. Bump to `LOG_LEVEL=DEBUG` if you need to see request bodies.

## How the booking flow works

When `POST /api/book` is called:

1. **Validate** — service exists in services.json, postcode is in SO14-SO53 service area.
2. **Resolve materials** — walk the customer's answers and gather every material item_number that should be added (tick-boxes, radio swaps, numeric quantity add-ons, always-add materials like Power Flush chemicals).
3. **Create job** — `POST /jobtemplate/{template_uuid}/job.json` to ServiceM8. The template's badges (confirmation + reminder) auto-apply, the base material is cloned in.
4. **Append materials** — `POST /jobmaterial.json` for each add-on.
5. **Lock the slot** — `POST /jobactivity.json` writes the chosen time onto Wes's diary so no one else can book the same window.
6. **Set category** — if the answers swapped the category (e.g. tick-box added Gas Safety = combined category), `POST /job/{uuid}.json` updates it.
7. **Invalidate availability cache** so the next `/api/availability` call reflects the new booking.

Partial failures: if `add_job_material` or `create_activity` fails for one line, the booking still succeeds — the job exists, Wes will see it on his dispatch board and can finish the booking by hand. Hard failure on `create_job` returns a 502 to the browser.

## Caching

| Cache | TTL | Why |
|---|---|---|
| `material.json` (~93k records) | 5 min | Wes updates prices rarely; SM8 rate limit is 180/min |
| `jobactivity.json` | 60 s | Diary changes more often; balance freshness vs request rate |

Both caches invalidate on successful `POST /api/book` so the next page-load reflects reality.

## Source of truth

- **Prices**: ServiceM8 `material.json` (live, fetched via API). Don't hardcode in code.
- **Templates / categories / staff_uuid**: ServiceM8 (UUIDs in services.json reference them).
- **Booking form structure / question wiring**: `website/site/data/services.json` (read by both the website and this API).
- **Booking form HTML**: `website/site/booking.html` (next session).

## Known limits

- `jobtemplate` is read-only via API key (POST returns 403). New templates must be created in the SM8 web UI.
- "Variable - use questions to calculate price" services in SM8 (the Service Pricing config) are NOT used by this API — we route through the simpler job-template endpoint and append materials manually based on the form answers. Wes's variable-pricing Service configs remain useful as a backup booking path if anyone hits SM8's own widget URL directly.
- Single-instance only. If you scale to multiple replicas, the in-memory caches drift between them. Move to Redis at that point.
