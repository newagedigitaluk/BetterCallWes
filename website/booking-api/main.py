"""Better Call Wes booking API.

A thin layer between the website's booking form and ServiceM8's REST API.

Endpoints (all under /api):
    GET  /api/healthcheck            — basic liveness + SM8 auth check
    GET  /api/services               — services.json, prices populated live
    GET  /api/materials?items=A,B,C  — live prices for the listed item_numbers
    GET  /api/availability?service=X&days=14 — free slots for the next N days
    POST /api/book                   — create the booking (job + materials + activity)

Deployment: Dockerised. Coolify runs it behind nginx, ideally proxied
at api.bettercallwes.co.uk. Set SERVICEM8_API_KEY in the Coolify env.
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from availability import (
    TimeBlock,
    WorkingHours,
    free_slots,
    parse_busy_blocks,
    whole_day_slots,
)
from cache import TTLCache
from confirmation import (
    ConfirmationContext,
    normalise_uk_mobile,
    parse_name,
    render_email,
    render_sms,
)
from signing import (
    BookingToken,
    TokenExpired,
    TokenInvalid,
    email_hash,
    make_token,
    verify_token,
)
from sm8 import ServiceM8Client, ServiceM8Error

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("booking-api")

# ─────────── Config / globals ───────────

SM8_API_KEY = os.environ.get("SERVICEM8_API_KEY", "")
SERVICES_JSON_PATH = Path(
    os.environ.get(
        "SERVICES_JSON",
        str(Path(__file__).parent.parent / "site" / "data" / "services.json"),
    )
)
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://bettercallwes.co.uk,https://www.bettercallwes.co.uk,http://localhost:8000",
).split(",")
DEFAULT_DAYS_AHEAD = int(os.environ.get("DEFAULT_DAYS_AHEAD", "14"))
MATERIALS_CACHE_TTL = float(os.environ.get("MATERIALS_CACHE_TTL", "300"))  # 5 min
ACTIVITY_CACHE_TTL = float(os.environ.get("ACTIVITY_CACHE_TTL", "60"))  # 60 s

# Magic-link tokens for self-serve booking management. Empty disables
# the feature gracefully — confirmation emails revert to "call/text me"
# wording, and the manage-booking endpoints return 503.
MAGIC_LINK_SECRET = os.environ.get("MAGIC_LINK_SECRET", "")
PUBLIC_SITE_BASE = os.environ.get(
    "PUBLIC_SITE_BASE", "https://bettercallwes.co.uk"
).rstrip("/")
RESCHEDULE_LEAD_HOURS = int(os.environ.get("RESCHEDULE_LEAD_HOURS", "12"))
RESCHEDULE_MAX_PER_BOOKING = int(os.environ.get("RESCHEDULE_MAX_PER_BOOKING", "2"))
# Wes's contact for internal alerts when a customer reschedules/cancels
WES_ALERT_EMAIL = os.environ.get("WES_ALERT_EMAIL", "wes@bettercallwes.co.uk")
WES_ALERT_PHONE = os.environ.get("WES_ALERT_PHONE", "+447700155655")

sm8: ServiceM8Client | None = None  # initialised in lifespan

# Caches
materials_cache: TTLCache[list[dict]] | None = None
activity_cache: TTLCache[list[dict]] | None = None

# Wes's staff UUID — used for the optional <platform-user-signature/> tag
DEFAULT_STAFF_UUID = "5673d021-27b2-4356-a14b-1760cabfcd3b"


# ─────────── Pydantic models ───────────


class BookingRequest(BaseModel):
    service: str = Field(..., description="Service slug, e.g. 'boiler-service'")
    answers: dict[str, Any] = Field(default_factory=dict)
    slot_start: datetime = Field(..., description="Local time, ISO 8601 (no TZ)")
    slot_end: datetime
    customer_name: str = Field(..., min_length=2, max_length=200)
    customer_phone: str = Field(..., min_length=7, max_length=30)
    customer_email: EmailStr
    customer_address: str = Field(..., min_length=10, max_length=500)
    customer_postcode: str = Field(..., min_length=5, max_length=10)
    hear_about: str | None = None
    # Optional UTM tracking params — captured from the URL by the
    # booking form and passed through so we can attribute the lead
    # in SM8's marketing custom fields.
    utm_source: str = Field(default="", max_length=80)
    utm_medium: str = Field(default="", max_length=80)
    utm_campaign: str = Field(default="", max_length=120)
    utm_content: str = Field(default="", max_length=120)
    utm_term: str = Field(default="", max_length=120)


class BookingResponse(BaseModel):
    success: bool
    job_uuid: str
    job_number: str | None = None
    estimated_total: float
    slot_start: datetime
    slot_end: datetime
    message: str


class SlotResponse(BaseModel):
    start: datetime
    end: datetime
    duration_min: int


# ─────────── Helpers ───────────


def load_services_config() -> dict[str, Any]:
    """Re-read services.json on every call. File is small; this lets edits
    take effect without restarting the API container."""
    if not SERVICES_JSON_PATH.exists():
        raise RuntimeError(f"services.json not found at {SERVICES_JSON_PATH}")
    with SERVICES_JSON_PATH.open() as f:
        return json.load(f)


def map_utm_to_marketing_source(
    *,
    utm_source: str,
    utm_medium: str,
) -> str:
    """Translate UTM params into one of Wes's existing
    customfield_marketing_source values, so SM8 reporting stays clean.

    Allowed values (from sampling 200 recent jobs):
      Checkatrade, Google Organic, Referred, PPC, Google My Business,
      Other, Existing, Facebook, Google Local Services,
      Gas Safe Register, Google Local Ads, Bark
    """
    src = (utm_source or "").strip().lower()
    med = (utm_medium or "").strip().lower()

    # Medium-led overrides — these define the channel regardless of source
    if med in {"local_services", "lsa"}:
        return "Google Local Services"
    if med in {"cpc", "ppc", "paid", "paidsearch", "paid_search"}:
        # Treat Google paid search differently from Local Ads
        if src in {"google", "google_ads", "googleads"}:
            return "PPC"
        if src in {"facebook", "fb", "meta", "instagram", "ig"}:
            return "Facebook"
        return "PPC"
    if med in {"display", "remarketing"}:
        return "PPC"

    # Source-led
    if src in {"google", "google_organic", "google-search"}:
        return "Google Organic"
    if src in {"google_business", "gmb", "google_my_business", "googlemybusiness"}:
        return "Google My Business"
    if src in {"google_local_ads", "google_local"}:
        return "Google Local Ads"
    if src in {"facebook", "fb", "meta", "instagram", "ig"}:
        return "Facebook"
    if src == "checkatrade":
        return "Checkatrade"
    if src == "bark":
        return "Bark"
    if src in {"referral", "referred", "word_of_mouth", "wom"}:
        return "Referred"
    if src in {"gas_safe", "gassafe", "gas_safe_register"}:
        return "Gas Safe Register"
    if src in {"existing", "existing_customer", "repeat"}:
        return "Existing"
    return ""  # caller falls back to default if empty


def material_index(materials: list[dict]) -> dict[str, dict]:
    """Index materials by item_number for O(1) lookup. Active only."""
    out: dict[str, dict] = {}
    for m in materials:
        if m.get("active") not in ("1", 1, True):
            continue
        item = m.get("item_number") or ""
        if item and item not in out:
            out[item] = {
                "uuid": m["uuid"],
                "name": m.get("name", ""),
                "price": float(m.get("price", 0) or 0),
                "item_number": item,
            }
    return out


def enrich_services_with_prices(
    config: dict[str, Any], mat_index: dict[str, dict]
) -> dict[str, Any]:
    """Walk the services config and inject live prices next to each
    material reference so the form can render without a second fetch."""
    enriched = json.loads(json.dumps(config))  # deep copy

    def attach_price(item_number: str | None) -> dict | None:
        if not item_number:
            return None
        return mat_index.get(item_number)

    for slug, svc in enriched.get("services", {}).items():
        svc["base_material"] = attach_price(svc.get("base_material_item"))
        for q in svc.get("questions", []):
            # Material on the question itself (e.g. tick-box add-on)
            if "material_add" in q:
                q["material"] = attach_price(q["material_add"])
            # Materials inside options (e.g. radio swap, or option-specific add)
            for opt in q.get("options", []) or []:
                if "material_swap" in opt and opt["material_swap"]:
                    opt["material"] = attach_price(opt["material_swap"])
                if "material_add" in opt and opt["material_add"]:
                    opt["material"] = attach_price(opt["material_add"])
                # Plumbing job-type options each have a category_uuid embedded
                # — keep as-is, no enrichment needed
            # Materials in "material_add_when_over" (Power Flush per-radiator)
            if "material_add_when_over" in q and q["material_add_when_over"]:
                mat = q["material_add_when_over"].get("material")
                q["material_add_when_over"]["material_info"] = attach_price(mat)
        # always-add materials (e.g. Power Flush chemicals)
        if svc.get("always_add_materials"):
            svc["always_add_material_info"] = [
                attach_price(item) for item in svc["always_add_materials"]
            ]
    return enriched


# ─────────── Lifespan / startup ───────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sm8, materials_cache, activity_cache
    if not SM8_API_KEY:
        raise RuntimeError("SERVICEM8_API_KEY env var is required")
    sm8 = ServiceM8Client(api_key=SM8_API_KEY)
    materials_cache = TTLCache(MATERIALS_CACHE_TTL, sm8.list_materials)

    # Activity cache is keyed by start_date (today), so it self-rotates daily
    config = load_services_config()
    staff_uuid = config["config"]["staff_uuid"]

    async def fetch_activity() -> list[dict]:
        today_str = date.today().strftime("%Y-%m-%d")
        return await sm8.list_activity(staff_uuid=staff_uuid, start_date=today_str)

    activity_cache = TTLCache(ACTIVITY_CACHE_TTL, fetch_activity)

    log.info("booking-api ready (services.json=%s)", SERVICES_JSON_PATH)
    try:
        yield
    finally:
        if sm8:
            await sm8.close()


app = FastAPI(title="Better Call Wes booking API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ─────────── Endpoints ───────────


@app.get("/api/healthcheck")
async def healthcheck() -> dict[str, Any]:
    assert sm8 is not None
    try:
        info = await sm8.check_auth()
        return {
            "status": "ok",
            "servicem8": "ok",
            "active_staff": info.get("active_staff"),
        }
    except Exception as e:  # noqa: BLE001
        log.exception("healthcheck failed")
        return {"status": "degraded", "servicem8": f"error: {e}"}


@app.get("/api/services")
async def get_services() -> dict[str, Any]:
    """Returns services.json with material prices populated from live SM8 data."""
    assert materials_cache is not None
    config = load_services_config()
    materials = await materials_cache.get()
    return enrich_services_with_prices(config, material_index(materials))


@app.get("/api/materials")
async def get_materials(items: str = Query(..., description="Comma-separated item_numbers")) -> dict[str, dict]:
    """Live prices for the requested item_numbers. Used if the form
    wants targeted lookups (most use the enriched /api/services instead)."""
    assert materials_cache is not None
    requested = [s.strip() for s in items.split(",") if s.strip()]
    if not requested:
        raise HTTPException(400, "items parameter required")
    materials = await materials_cache.get()
    idx = material_index(materials)
    return {item: idx[item] for item in requested if item in idx}


@app.get("/api/availability")
async def get_availability(
    service: str = Query(..., description="Service slug"),
    days: int = Query(DEFAULT_DAYS_AHEAD, ge=1, le=60),
    duration_min: int | None = Query(None, description="Override slot duration"),
) -> list[SlotResponse]:
    """Free slots for the next `days` working days."""
    assert activity_cache is not None
    config = load_services_config()
    svc = config["services"].get(service)
    if not svc:
        raise HTTPException(404, f"Unknown service: {service}")

    hours_cfg = config["config"]["working_hours"]
    hours = WorkingHours(
        days=tuple(hours_cfg["days"]),
        morning_start=datetime.strptime(hours_cfg["morning_start"], "%H:%M").time(),
        morning_end=datetime.strptime(hours_cfg["morning_end"], "%H:%M").time(),
        afternoon_start=datetime.strptime(hours_cfg["afternoon_start"], "%H:%M").time(),
        afternoon_end=datetime.strptime(hours_cfg["afternoon_end"], "%H:%M").time(),
    )

    activity = await activity_cache.get()
    busy = parse_busy_blocks(activity)

    # Note: SM8 is the single source of truth for the diary. If Wes
    # wants a personal day blocked, he adds it as a manual jobactivity
    # in SM8 (which then shows up in Outlook via his SM8→Outlook
    # calendar subscription). No external feed merge needed.

    requested = duration_min or svc.get("base_duration_min", 60)

    # Booking rules (lead-time buffer + same-day cutoff + latest start time).
    # Tunable from services.json so Wes can adjust without a redeploy of
    # this service.
    rules = config["config"].get("booking_rules", {})
    min_lead_hours = float(rules.get("min_lead_time_hours", 0))
    same_day_cutoff = rules.get("same_day_cutoff_hour")
    whole_day_lead_days = int(rules.get("whole_day_min_lead_days", 1))
    latest_start_raw = rules.get("latest_start_time")
    latest_start = (
        datetime.strptime(latest_start_raw, "%H:%M").time()
        if latest_start_raw else None
    )

    # Power Flush + similar full-day services
    if requested >= 360:  # 6+ hours = block the whole day
        slots = list(
            whole_day_slots(
                days_ahead=days,
                busy=busy,
                hours=hours,
                whole_day_min_lead_days=whole_day_lead_days,
            )
        )
    else:
        slots = list(
            free_slots(
                duration_min=requested,
                days_ahead=days,
                busy=busy,
                hours=hours,
                min_lead_time_hours=min_lead_hours,
                same_day_cutoff_hour=same_day_cutoff,
                latest_start_time=latest_start,
            )
        )

    return [
        SlotResponse(start=s.start, end=s.end, duration_min=s.duration_min)
        for s in slots[:200]
    ]


@app.post("/api/book", response_model=BookingResponse)
async def book(req: BookingRequest) -> BookingResponse:
    """Create the booking end-to-end.

    Flow:
      1. Validate service + postcode + slot
      2. Resolve materials based on answers
      3. POST /jobtemplate/{uuid}/job.json → creates job, applies template
         badges (confirmation + reminder), clones base material
      4. POST /jobmaterial.json for each add-on
      5. POST /jobactivity.json to lock the slot on Wes's diary
      6. If category_uuid differs from template default, POST /job/{uuid}.json
    """
    assert sm8 is not None
    assert materials_cache is not None
    assert activity_cache is not None

    config = load_services_config()
    svc = config["services"].get(req.service)
    if not svc:
        raise HTTPException(404, f"Unknown service: {req.service}")

    # ─ Postcode gate ─
    allowed = config["config"]["service_area"]["postcodes"]
    postcode_clean = req.customer_postcode.upper().replace(" ", "")
    in_area = any(postcode_clean.startswith(p) for p in allowed)
    if not in_area:
        raise HTTPException(
            400, config["config"]["service_area"]["rejection_message"]
        )

    # ─ Resolve materials from answers ─
    materials = await materials_cache.get()
    mat_idx = material_index(materials)

    materials_to_add: list[tuple[str, float]] = []  # list of (item_number, quantity)
    category_uuid = svc.get("category_uuid")

    for q in svc.get("questions", []):
        qid = q["id"]
        answer = req.answers.get(qid)
        if answer is None or answer is False or answer == "":
            continue

        # Tick-box add-on
        if q.get("type") == "checkbox" and q.get("material_add") and answer:
            materials_to_add.append((q["material_add"], 1.0))
            if q.get("category_swap_when_checked"):
                category_uuid = q["category_swap_when_checked"]

        # Numeric add-on (e.g. gas-fire count)
        elif q.get("type") == "number" and q.get("material_add"):
            try:
                qty = float(answer)
                if qty > 0:
                    materials_to_add.append((q["material_add"], qty))
            except (TypeError, ValueError):
                pass

        # Numeric with threshold (Power Flush per-radiator above 8)
        elif q.get("type") == "number" and q.get("material_add_when_over"):
            cfg = q["material_add_when_over"]
            try:
                value = float(answer)
                threshold = float(cfg.get("threshold", 0))
                if value > threshold:
                    materials_to_add.append((cfg["material"], value - threshold))
            except (TypeError, ValueError):
                pass

        # Radio with material_swap (Boiler Service: Standard vs Full Stripdown)
        elif q.get("type") == "radio" and q.get("options"):
            picked = next(
                (o for o in q["options"] if o.get("value") == answer), None
            )
            if picked:
                if picked.get("material_swap"):
                    # Spawn from this material instead of the template default
                    # — record on the side and apply after spawn (swap line)
                    svc_base_override = picked["material_swap"]
                    svc["_runtime_base_override"] = svc_base_override
                if picked.get("material_add"):
                    materials_to_add.append((picked["material_add"], 1.0))
                if picked.get("category_uuid"):
                    category_uuid = picked["category_uuid"]

        # Plumbing job-type select sets category + duration
        elif q.get("type") == "select" and q.get("options"):
            picked = next(
                (o for o in q["options"] if o.get("value") == answer), None
            )
            if picked and picked.get("category_uuid"):
                category_uuid = picked["category_uuid"]

    # always-add materials (e.g. Power Flush chemicals)
    for item in svc.get("always_add_materials") or []:
        materials_to_add.append((item, 1.0))

    # ─ Build a job description summarising the answers ─
    description_lines = [f"BOOKED ONLINE: {svc['name']}"]
    description_lines.append(f"Customer: {req.customer_name}")
    description_lines.append(f"Phone: {req.customer_phone}")
    description_lines.append(f"Email: {req.customer_email}")
    description_lines.append(f"Slot: {req.slot_start.isoformat()} to {req.slot_end.isoformat()}")
    description_lines.append("")
    description_lines.append("ANSWERS:")
    for q in svc.get("questions", []):
        ans = req.answers.get(q["id"])
        if ans is None or ans == "" or ans is False:
            continue
        description_lines.append(f"- {q.get('label', q['id'])}: {ans}")
    if req.hear_about:
        description_lines.append(f"How heard: {req.hear_about}")
    description = "\n".join(description_lines)

    # ─ 1) Create job from template ─
    template_uuid = svc["template_uuid"]
    if template_uuid.startswith("TBC-"):
        raise HTTPException(
            501,
            f"Service '{req.service}' has no SM8 template configured yet. "
            "Create the template in ServiceM8 and update services.json.",
        )

    # Construct a UK-style address string + remember the structured
    # components so we can explicitly set them on the job after creation.
    # SM8 auto-extracts geo_city/geo_postcode/geo_country from job_address
    # but only if the address is well-formed; we want the structured
    # fields populated reliably regardless of how the customer typed
    # the address.
    address_text = req.customer_address.strip()
    address_lower = address_text.lower()
    pc_clean = req.customer_postcode.upper().strip()
    # Strip any trailing commas to avoid double-comma noise
    if address_text.endswith(","):
        address_text = address_text[:-1].rstrip()
    parts = [address_text]
    if "southampton" not in address_lower and "hampshire" not in address_lower:
        # Postcode is verified to be SO14-SO53, so the city is always Southampton
        parts.append("Southampton")
    if pc_clean.replace(" ", "") not in address_lower.replace(" ", "").upper():
        parts.append(pc_clean)
    # Country is set on the job record via geo_country (UK-only business — no
    # need to clutter the displayed address with it).
    full_address = ", ".join(parts)

    # Parse customer name into first/last for the SM8 contact record.
    first_name_create, last_name_create = parse_name(req.customer_name)

    try:
        created = await sm8.create_job_from_template(
            template_uuid=template_uuid,
            company_name=req.customer_name,
            job_address=full_address,
            job_description=description,
        )
    except (httpx.HTTPStatusError, ServiceM8Error) as e:
        log.exception("create_job failed")
        raise HTTPException(502, f"ServiceM8 job creation failed: {e}") from e
    except Exception as e:  # noqa: BLE001
        log.exception("create_job failed")
        raise HTTPException(502, f"ServiceM8 job creation failed: {e}") from e

    job_uuid = created.uuid

    # ─ 2) Attach the customer as a JOB contact (NOT a company contact). ─
    # The /jobtemplate/{uuid}/job.json endpoint accepts only company +
    # address + description (verified — passing customer fields returns
    # 400 "Body does not match schema"). To populate the job's "Job
    # Contact" field, POST to /jobcontact.json with the job_uuid.
    # Note: /companycontact.json (which the earlier code tried, commit
    # 087cf79) attaches to the company but NOT the job — that's why the
    # job UI showed no contact for those bookings.
    try:
        await sm8.add_job_contact(
            job_uuid=job_uuid,
            first=first_name_create,
            last=last_name_create,
            mobile=req.customer_phone,
            phone=req.customer_phone,
            email=req.customer_email,
            type_="JOB",
        )
    except Exception:  # noqa: BLE001
        log.exception("add_job_contact failed (booking proceeds without job contact)")

    # ─ 3) Append each add-on material ─
    estimated_total = 0.0
    base_mat = mat_idx.get(svc.get("base_material_item", ""))
    if base_mat:
        estimated_total += base_mat["price"]

    for idx, (item_number, qty) in enumerate(materials_to_add):
        mat = mat_idx.get(item_number)
        if not mat:
            log.warning("material %s not found in catalogue; skipping", item_number)
            continue
        try:
            await sm8.add_job_material(
                job_uuid=job_uuid,
                material_uuid=mat["uuid"],
                quantity=qty,
                price=mat["price"],
                name=mat["name"],
                sort_order=300 + idx,
            )
            estimated_total += mat["price"] * qty
        except Exception:  # noqa: BLE001
            log.exception("add_job_material failed for %s", item_number)
            # Continue on partial failure — better a job with some lines than rolled-back

    # ─ Lock the slot on Wes's diary ─
    staff_uuid = config["config"]["staff_uuid"]
    try:
        await sm8.create_activity(
            job_uuid=job_uuid,
            staff_uuid=staff_uuid,
            start_iso=req.slot_start.strftime("%Y-%m-%d %H:%M:%S"),
            end_iso=req.slot_end.strftime("%Y-%m-%d %H:%M:%S"),
        )
    except Exception:  # noqa: BLE001
        log.exception("create_activity failed (job created but diary not locked)")
        # Don't fail the booking — Wes will see the job and can schedule manually

    # ─ 5) Patch the job with explicit address + category + marketing fields ─
    # Belt-and-braces: even if SM8's geocoder didn't parse the address
    # string correctly, setting geo_postcode / geo_city / geo_country
    # directly guarantees the structured fields exist on the record.
    patch_fields: dict[str, Any] = {
        "geo_postcode": pc_clean,
        "geo_city": "Southampton",
        "geo_country": "United Kingdom",
        # Marketing attribution — every online booking gets these flags.
        # Values picked to match Wes's existing taxonomy in SM8 reporting.
        "customfield_contact_method": "Website",
        "customfield_lead_quality": "Good",
    }
    # Marketing source — derived from UTM params if available.
    mkt_source = map_utm_to_marketing_source(
        utm_source=req.utm_source, utm_medium=req.utm_medium,
    )
    if mkt_source:
        patch_fields["customfield_marketing_source"] = mkt_source
    else:
        # No UTM params present — likely a direct visit or someone who
        # already knew the URL. Tag as "Other" so reporting still works.
        patch_fields["customfield_marketing_source"] = "Other"
    # Campaign reference (e.g. utm_campaign=spring_boiler_service) helps
    # tie a specific ad/post back to its bookings.
    campaign_bits = [
        b for b in (req.utm_campaign, req.utm_content, req.utm_term) if b
    ]
    if campaign_bits:
        patch_fields["customfield_campaign_ref"] = " / ".join(campaign_bits)

    if category_uuid and category_uuid != svc.get("category_uuid"):
        patch_fields["category_uuid"] = category_uuid
    try:
        await sm8.update_job(job_uuid, patch_fields)
    except Exception:  # noqa: BLE001
        log.exception("update_job (geo + category + marketing) failed")

    # ─ 6) Send confirmation email + SMS to the customer ─
    # SM8's auto-confirmation flow only fires for bookings via SM8's
    # own widget. API-created jobs need us to send manually via the
    # Messaging API endpoints (X-Api-Key auth, despite the public docs
    # claiming OAuth — verified working).
    manage_url = ""
    if MAGIC_LINK_SECRET:
        try:
            tok = make_token(
                secret=MAGIC_LINK_SECRET,
                job_uuid=job_uuid,
                slot_start=req.slot_start,
                customer_email=req.customer_email,
            )
            manage_url = f"{PUBLIC_SITE_BASE}/manage-booking.html?t={tok}"
        except Exception:  # noqa: BLE001
            log.exception("magic-link token generation failed (booking still succeeds)")

    confirmation_ctx = ConfirmationContext(
        customer_first=first_name_create,
        customer_last=last_name_create,
        customer_email=req.customer_email,
        customer_phone=req.customer_phone,
        service_name=svc.get("name", req.service),
        slot_start=req.slot_start,
        slot_end=req.slot_end,
        job_address=full_address,
        estimated_total=estimated_total,
        job_uuid=job_uuid,
        manage_url=manage_url,
    )
    try:
        subject, text_body, html_body = render_email(confirmation_ctx)
        await sm8.send_email(
            to=req.customer_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            reply_to="wes@bettercallwes.co.uk",
            regarding_job_uuid=job_uuid,
        )
    except Exception:  # noqa: BLE001
        log.exception("send confirmation email failed (booking still succeeded)")

    try:
        sms_message = render_sms(confirmation_ctx)
        sms_to = normalise_uk_mobile(req.customer_phone)
        await sm8.send_sms(
            to=sms_to,
            message=sms_message,
            regarding_job_uuid=job_uuid,
        )
    except Exception:  # noqa: BLE001
        log.exception("send confirmation SMS failed (booking still succeeded)")

    # Invalidate availability cache so the next /api/availability reflects the new slot
    activity_cache.invalidate()

    return BookingResponse(
        success=True,
        job_uuid=job_uuid,
        job_number=None,
        estimated_total=round(estimated_total, 2),
        slot_start=req.slot_start,
        slot_end=req.slot_end,
        message="Booking confirmed. Wes will be in touch shortly to confirm details.",
    )


# ─────────── Manage-booking (magic-link) endpoints ───────────


class RescheduleRequest(BaseModel):
    slot_start: datetime
    slot_end: datetime


class CancelRequest(BaseModel):
    # Pre-set category the customer picked (radio button on the page).
    # Optional — empty string if they didn't pick one.
    reason_category: str = Field(default="", max_length=80)
    # Free-text "anything else?" note. Optional, capped to keep SM8 happy.
    reason_text: str = Field(default="", max_length=500)


class ManageBookingState(BaseModel):
    """What the manage-booking page renders. Designed not to leak
    sensitive customer info beyond what the email/SMS already revealed."""
    job_uuid: str
    service: str
    service_name: str
    slot_start: datetime
    slot_end: datetime
    job_address: str
    customer_first: str
    reschedules_used: int
    reschedules_max: int
    can_modify: bool          # false if within lead-time window
    lead_hours: int
    active: bool              # false = already cancelled


def _resolve_token_or_503(token: str) -> BookingToken:
    """Verify the magic-link token. Raises HTTPException on any problem."""
    if not MAGIC_LINK_SECRET:
        raise HTTPException(503, "Self-serve booking management isn't configured")
    try:
        return verify_token(token, secret=MAGIC_LINK_SECRET)
    except TokenExpired:
        raise HTTPException(
            410,
            "This link has expired — your appointment time has already passed. "
            "Please contact Wes directly if you need help.",
        ) from None
    except TokenInvalid as e:
        raise HTTPException(
            400, f"Invalid management link: {e}. Please use the link from your confirmation email/SMS."
        ) from None


def _job_from_token(job_record: dict, tok: BookingToken) -> None:
    """Sanity-check that the token + job match. Raises 404/410 if not."""
    if not job_record:
        raise HTTPException(404, "Booking not found")
    # Hard-deleted (active=0)? Refuse.
    if str(job_record.get("active", "1")) not in ("1", "True", "true"):
        raise HTTPException(410, "This booking has already been cancelled")
    # Marked Unsuccessful via the cancel flow? Refuse modifications.
    status = str(job_record.get("status", "")).strip().lower()
    if status == "unsuccessful":
        raise HTTPException(410, "This booking has already been cancelled")


def _count_reschedules(activities: list[dict]) -> int:
    """How many times the customer has rescheduled this booking.

    We soft-delete (active=0) the prior jobactivity on each reschedule
    rather than physically removing it, so inactive scheduled records
    are the audit trail.
    """
    inactive_scheduled = [
        a for a in activities
        if str(a.get("active", "1")) in ("0", "False", "false")
        and str(a.get("activity_was_scheduled", "1")) in ("1", "True", "true")
    ]
    return len(inactive_scheduled)


def _slot_lead_ok(slot_start: datetime, *, now: datetime | None = None) -> bool:
    """True if slot_start is at least RESCHEDULE_LEAD_HOURS in the future."""
    n = now or datetime.now()
    return slot_start >= n + timedelta(hours=RESCHEDULE_LEAD_HOURS)


def _service_slug_from_template(template_uuid: str, config: dict) -> str | None:
    """Reverse-lookup the service slug from the SM8 template uuid."""
    for slug, svc in config.get("services", {}).items():
        if svc.get("template_uuid") == template_uuid:
            return slug
    return None


async def _gather_manage_state(tok: BookingToken) -> tuple[ManageBookingState, dict]:
    """Common path: fetch the job + activities, derive manage state.
    Returns (state, job_record) so callers can mutate the job afterwards."""
    assert sm8 is not None
    job = await sm8.get_job(tok.job_uuid)
    _job_from_token(job, tok)

    config = load_services_config()
    template_uuid = job.get("job_template_uuid", "") or job.get("template_uuid", "")
    slug = _service_slug_from_template(template_uuid, config) or ""
    svc = config["services"].get(slug, {})
    service_name = svc.get("name", "Booking")

    # Activities (active + inactive) for reschedule count
    activities = await sm8.list_activity_for_job(tok.job_uuid)
    used = _count_reschedules(activities)

    # The current active scheduled block — that's "the slot"
    active_scheduled = [
        a for a in activities
        if str(a.get("active", "1")) in ("1", "True", "true")
        and str(a.get("activity_was_scheduled", "1")) in ("1", "True", "true")
    ]
    active_scheduled.sort(key=lambda a: a.get("start_date", ""))
    if not active_scheduled:
        raise HTTPException(410, "This booking has no scheduled slot — please contact Wes")
    current = active_scheduled[-1]  # the most-recent one
    slot_start = datetime.strptime(current["start_date"], "%Y-%m-%d %H:%M:%S")
    slot_end = datetime.strptime(current["end_date"], "%Y-%m-%d %H:%M:%S")

    # Parse customer first name from job description (we wrote it in there)
    customer_first = "there"
    for line in (job.get("job_description") or "").splitlines():
        if line.lower().startswith("customer:"):
            full = line.split(":", 1)[1].strip()
            customer_first = full.split()[0] if full else "there"
            break

    state = ManageBookingState(
        job_uuid=tok.job_uuid,
        service=slug,
        service_name=service_name,
        slot_start=slot_start,
        slot_end=slot_end,
        job_address=job.get("job_address", ""),
        customer_first=customer_first,
        reschedules_used=used,
        reschedules_max=RESCHEDULE_MAX_PER_BOOKING,
        can_modify=_slot_lead_ok(slot_start),
        lead_hours=RESCHEDULE_LEAD_HOURS,
        active=True,
    )
    return state, job


@app.get("/api/booking/{token}", response_model=ManageBookingState)
async def get_booking(token: str) -> ManageBookingState:
    """Manage-page bootstrap: returns the current state for rendering."""
    tok = _resolve_token_or_503(token)
    state, _ = await _gather_manage_state(tok)
    return state


@app.get("/api/booking/{token}/availability", response_model=list[SlotResponse])
async def get_booking_availability(
    token: str,
    days: int = Query(DEFAULT_DAYS_AHEAD, ge=1, le=60),
) -> list[SlotResponse]:
    """Free slots for THIS booking's service — same logic as /api/availability
    but the service is locked to whatever the booking is for."""
    tok = _resolve_token_or_503(token)
    state, _ = await _gather_manage_state(tok)
    if not state.service:
        raise HTTPException(404, "Service for this booking could not be resolved")
    # Defer to the standard availability endpoint
    return await get_availability(service=state.service, days=days, duration_min=None)


@app.post("/api/booking/{token}/reschedule", response_model=ManageBookingState)
async def reschedule_booking(token: str, req: RescheduleRequest) -> ManageBookingState:
    """Move the booking to a new slot.

    Rules (server-enforced):
      - Customer must have ≥ RESCHEDULE_LEAD_HOURS notice from the CURRENT slot
      - Customer must have used < RESCHEDULE_MAX_PER_BOOKING reschedules
      - The NEW slot must also be ≥ RESCHEDULE_LEAD_HOURS in the future
    """
    assert sm8 is not None
    assert activity_cache is not None
    tok = _resolve_token_or_503(token)
    state, job = await _gather_manage_state(tok)
    config = load_services_config()
    staff_uuid = config["config"]["staff_uuid"]

    if not state.can_modify:
        raise HTTPException(
            409,
            f"This booking is within {state.lead_hours}h of starting — please contact Wes directly.",
        )
    if state.reschedules_used >= state.reschedules_max:
        raise HTTPException(
            409,
            f"You've used all {state.reschedules_max} self-serve reschedules on this booking. "
            "Please contact Wes for further changes.",
        )
    if not _slot_lead_ok(req.slot_start):
        raise HTTPException(
            400,
            f"The new slot must be at least {state.lead_hours}h from now.",
        )

    # ─ Deactivate the existing scheduled activity (audit trail) ─
    activities = await sm8.list_activity_for_job(tok.job_uuid)
    for a in activities:
        if str(a.get("active", "1")) in ("1", "True", "true") and \
           str(a.get("activity_was_scheduled", "1")) in ("1", "True", "true"):
            try:
                await sm8.deactivate_activity(a["uuid"])
            except Exception:  # noqa: BLE001
                log.exception("deactivate_activity failed for %s", a.get("uuid"))

    # ─ Create the new activity ─
    try:
        await sm8.create_activity(
            job_uuid=tok.job_uuid,
            staff_uuid=staff_uuid,
            start_iso=req.slot_start.strftime("%Y-%m-%d %H:%M:%S"),
            end_iso=req.slot_end.strftime("%Y-%m-%d %H:%M:%S"),
        )
    except Exception as e:  # noqa: BLE001
        log.exception("reschedule: create_activity failed")
        raise HTTPException(502, f"Could not save the new slot: {e}") from e

    # ─ Update job description with a small audit line ─
    try:
        existing_desc = job.get("job_description", "")
        old_slot = f"{state.slot_start.strftime('%Y-%m-%d %H:%M')}"
        new_slot = f"{req.slot_start.strftime('%Y-%m-%d %H:%M')}"
        audit = f"\n[Customer reschedule {datetime.now().strftime('%Y-%m-%d %H:%M')}] {old_slot} → {new_slot}"
        await sm8.update_job(tok.job_uuid, {"job_description": existing_desc + audit})
    except Exception:  # noqa: BLE001
        log.exception("reschedule: audit line update failed (non-fatal)")

    # ─ Notify Wes + customer ─
    await _notify_reschedule(state, req, job)

    # Invalidate availability cache so the freed/new slot reflects immediately
    activity_cache.invalidate()

    # Return refreshed state
    refreshed, _ = await _gather_manage_state(tok)
    return refreshed


def _format_cancel_reason(req: CancelRequest) -> str:
    """Build the string that goes into SM8's `unsuccessful_reason` field.

    Combines the radio-button category with any free-text note so Wes
    sees both the structured signal AND any nuance the customer added.
    Returns an empty string if neither was given.
    """
    cat = (req.reason_category or "").strip()
    note = (req.reason_text or "").strip()
    if cat and note:
        return f"{cat} — {note}"
    return cat or note


@app.post("/api/booking/{token}/cancel", response_model=dict)
async def cancel_booking(token: str, req: CancelRequest) -> dict[str, Any]:
    """Cancel a booking. Marks the SM8 job as Unsuccessful (keeps it
    visible in SM8's Unsuccessful list, doesn't hard-delete) and
    deactivates the scheduled activity to free the slot. Reason text
    lands in SM8's "Reason for cancellation" field."""
    assert sm8 is not None
    assert activity_cache is not None
    tok = _resolve_token_or_503(token)
    state, job = await _gather_manage_state(tok)

    if not state.can_modify:
        raise HTTPException(
            409,
            f"This booking is within {state.lead_hours}h of starting — please contact Wes directly.",
        )

    reason = _format_cancel_reason(req)
    # Prefix with a marker so Wes always knows this came from self-serve
    sm8_reason = (
        f"Customer cancelled via self-serve link. {reason}" if reason
        else "Customer cancelled via self-serve link (no reason given)."
    )

    # ─ Deactivate the scheduled activity (frees the diary slot) ─
    activities = await sm8.list_activity_for_job(tok.job_uuid)
    for a in activities:
        if str(a.get("active", "1")) in ("1", "True", "true"):
            try:
                await sm8.deactivate_activity(a["uuid"])
            except Exception:  # noqa: BLE001
                log.exception("cancel: deactivate_activity failed for %s", a.get("uuid"))

    # ─ Mark the job Unsuccessful with the reason ─
    try:
        await sm8.mark_job_unsuccessful(tok.job_uuid, reason=sm8_reason)
    except Exception as e:  # noqa: BLE001
        log.exception("cancel: mark_job_unsuccessful failed")
        raise HTTPException(502, f"Could not cancel the job: {e}") from e

    await _notify_cancel(state, job, reason=reason)
    activity_cache.invalidate()

    return {"success": True, "message": "Your booking has been cancelled."}


# ─────────── Internal helpers: notify Wes + the customer ───────────


def _fmt_slot(dt_start: datetime, dt_end: datetime) -> str:
    return f"{dt_start.strftime('%a %d %b, %H:%M')}–{dt_end.strftime('%H:%M')}"


async def _notify_reschedule(
    state: ManageBookingState,
    req: RescheduleRequest,
    job: dict,
) -> None:
    """Email + SMS Wes about the reschedule, and send the customer a new
    confirmation."""
    assert sm8 is not None
    old = _fmt_slot(state.slot_start, state.slot_end)
    new = _fmt_slot(req.slot_start, req.slot_end)

    # ─ Wes: email ─
    try:
        await sm8.send_email(
            to=WES_ALERT_EMAIL,
            subject=f"BCW — booking rescheduled by customer ({state.customer_first})",
            text_body=(
                f"A customer has rescheduled their booking via the self-serve link.\n\n"
                f"  Service:   {state.service_name}\n"
                f"  Customer:  {state.customer_first}\n"
                f"  Address:   {state.job_address}\n"
                f"  Old slot:  {old}\n"
                f"  New slot:  {new}\n"
                f"  Job UUID:  {state.job_uuid}\n"
                f"  Reschedules used: {state.reschedules_used + 1} / {state.reschedules_max}\n"
            ),
            regarding_job_uuid=state.job_uuid,
        )
    except Exception:  # noqa: BLE001
        log.exception("Wes-alert email (reschedule) failed")

    # ─ Wes: SMS ─
    try:
        await sm8.send_sms(
            to=WES_ALERT_PHONE,
            message=(
                f"BCW: {state.customer_first} rescheduled their {state.service_name}. "
                f"{old} → {new}."
            ),
            regarding_job_uuid=state.job_uuid,
        )
    except Exception:  # noqa: BLE001
        log.exception("Wes-alert SMS (reschedule) failed")

    # ─ Customer: re-send the confirmation email/SMS with the new slot ─
    # Reuse the original ConfirmationContext shape; the existing template
    # works fine for a "your booking has been updated" mail.
    cust_email = ""
    cust_phone = ""
    # Pull from job_description (we wrote them in there at booking time)
    for line in (job.get("job_description") or "").splitlines():
        low = line.lower()
        if low.startswith("phone:"):
            cust_phone = line.split(":", 1)[1].strip()
        elif low.startswith("email:"):
            cust_email = line.split(":", 1)[1].strip()
    if cust_email:
        manage_url = ""
        if MAGIC_LINK_SECRET:
            try:
                tok = make_token(
                    secret=MAGIC_LINK_SECRET,
                    job_uuid=state.job_uuid,
                    slot_start=req.slot_start,
                    customer_email=cust_email,
                )
                manage_url = f"{PUBLIC_SITE_BASE}/manage-booking.html?t={tok}"
            except Exception:  # noqa: BLE001
                pass
        ctx = ConfirmationContext(
            customer_first=state.customer_first,
            customer_last="",
            customer_email=cust_email,
            customer_phone=cust_phone,
            service_name=state.service_name,
            slot_start=req.slot_start,
            slot_end=req.slot_end,
            job_address=state.job_address,
            estimated_total=None,
            job_uuid=state.job_uuid,
            manage_url=manage_url,
        )
        try:
            subject, text_body, html_body = render_email(ctx)
            # Tweak subject so it reads as an update rather than first confirmation
            subject = "Your Better Call Wes booking has been rescheduled — " + req.slot_start.strftime('%-d %B at %H:%M')
            await sm8.send_email(
                to=cust_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                reply_to="wes@bettercallwes.co.uk",
                regarding_job_uuid=state.job_uuid,
            )
        except Exception:  # noqa: BLE001
            log.exception("customer reschedule confirmation email failed")
        if cust_phone:
            try:
                sms_body = render_sms(ctx)
                # Prepend a small "updated" marker
                sms_body = "Updated: " + sms_body
                await sm8.send_sms(
                    to=normalise_uk_mobile(cust_phone),
                    message=sms_body,
                    regarding_job_uuid=state.job_uuid,
                )
            except Exception:  # noqa: BLE001
                log.exception("customer reschedule confirmation SMS failed")


async def _notify_cancel(
    state: ManageBookingState,
    job: dict,
    *,
    reason: str = "",
) -> None:
    """Notify Wes + customer that the booking has been cancelled."""
    assert sm8 is not None
    slot = _fmt_slot(state.slot_start, state.slot_end)
    reason_line = f"\n  Reason:    {reason}" if reason else ""
    reason_sms = f" Reason: {reason}." if reason else ""

    # ─ Wes ─
    try:
        await sm8.send_email(
            to=WES_ALERT_EMAIL,
            subject=f"BCW — booking CANCELLED by customer ({state.customer_first})",
            text_body=(
                f"A customer has cancelled their booking via the self-serve link.\n\n"
                f"  Service:   {state.service_name}\n"
                f"  Customer:  {state.customer_first}\n"
                f"  Address:   {state.job_address}\n"
                f"  Slot:      {slot}{reason_line}\n"
                f"  Job UUID:  {state.job_uuid}\n\n"
                "The job has been marked Unsuccessful in ServiceM8 and the slot is now free in your diary."
            ),
            regarding_job_uuid=state.job_uuid,
        )
    except Exception:  # noqa: BLE001
        log.exception("Wes-alert email (cancel) failed")

    try:
        await sm8.send_sms(
            to=WES_ALERT_PHONE,
            message=(
                f"BCW: {state.customer_first} CANCELLED their {state.service_name} "
                f"({slot}).{reason_sms} Slot now free."
            ),
            regarding_job_uuid=state.job_uuid,
        )
    except Exception:  # noqa: BLE001
        log.exception("Wes-alert SMS (cancel) failed")

    # ─ Customer ─
    cust_email = ""
    cust_phone = ""
    for line in (job.get("job_description") or "").splitlines():
        low = line.lower()
        if low.startswith("phone:"):
            cust_phone = line.split(":", 1)[1].strip()
        elif low.startswith("email:"):
            cust_email = line.split(":", 1)[1].strip()

    if cust_email:
        try:
            await sm8.send_email(
                to=cust_email,
                subject="Your Better Call Wes booking has been cancelled",
                text_body=(
                    f"Hi {state.customer_first},\n\n"
                    f"This confirms your {state.service_name} on {slot} has been cancelled.\n\n"
                    "If this wasn't you, or you'd like to rebook, just let me know:\n"
                    f"  Phone:    07700 155 655\n"
                    f"  WhatsApp: https://wa.me/447700155655\n"
                    f"  Online:   {PUBLIC_SITE_BASE}/booking.html\n\n"
                    "Warm regards,\nWes"
                ),
                reply_to="wes@bettercallwes.co.uk",
                regarding_job_uuid=state.job_uuid,
            )
        except Exception:  # noqa: BLE001
            log.exception("customer cancel email failed")
    if cust_phone:
        try:
            await sm8.send_sms(
                to=normalise_uk_mobile(cust_phone),
                message=(
                    f"Hi {state.customer_first}, your Better Call Wes booking ({slot}) "
                    "has been cancelled. Need to rebook? bettercallwes.co.uk/booking.html"
                ),
                regarding_job_uuid=state.job_uuid,
            )
        except Exception:  # noqa: BLE001
            log.exception("customer cancel SMS failed")


if __name__ == "__main__":  # local dev: python main.py
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("DEV", "0") == "1",
    )
