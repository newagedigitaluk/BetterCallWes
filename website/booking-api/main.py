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

    # ─ 2) Append each add-on material ─
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

    # ─ 3) Attach customer contact to the company so SM8 has someone to
    #    send the badge-driven confirmation email/SMS to. The auto-
    #    created company from create_job_from_template has no contact
    #    records by default — only the company name + address — so
    #    SM8's automation has no email/phone to fire against.
    name_parts = req.customer_name.strip().split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    try:
        job_record = await sm8.get_job(job_uuid)
        company_uuid = job_record.get("company_uuid", "")
        if company_uuid:
            await sm8.add_company_contact(
                company_uuid=company_uuid,
                first=first_name,
                last=last_name,
                mobile=req.customer_phone,
                phone=req.customer_phone,
                email=req.customer_email,
                type_="JOB",
            )
        else:
            log.warning("job %s has no company_uuid; skipping contact creation", job_uuid)
    except Exception:  # noqa: BLE001
        log.exception("add_company_contact failed (job exists but no contact attached)")

    # ─ 4) Lock the slot on Wes's diary ─
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

    # ─ 5) Patch the job with explicit address + category fields ─
    # Belt-and-braces: even if SM8's geocoder didn't parse the address
    # string correctly, setting geo_postcode / geo_city / geo_country
    # directly guarantees the structured fields exist on the record.
    patch_fields: dict[str, Any] = {
        "geo_postcode": pc_clean,
        "geo_city": "Southampton",
        "geo_country": "United Kingdom",
    }
    if category_uuid and category_uuid != svc.get("category_uuid"):
        patch_fields["category_uuid"] = category_uuid
    try:
        await sm8.update_job(job_uuid, patch_fields)
    except Exception:  # noqa: BLE001
        log.exception("update_job (geo + category) failed")

    # ─ 6) Send confirmation email + SMS to the customer ─
    # SM8's auto-confirmation flow only fires for bookings via SM8's
    # own widget. API-created jobs need us to send manually via the
    # Messaging API endpoints (X-Api-Key auth, despite the public docs
    # claiming OAuth — verified working).
    first_name, last_name = parse_name(req.customer_name)
    confirmation_ctx = ConfirmationContext(
        customer_first=first_name,
        customer_last=last_name,
        customer_email=req.customer_email,
        customer_phone=req.customer_phone,
        service_name=svc.get("name", req.service),
        slot_start=req.slot_start,
        slot_end=req.slot_end,
        job_address=full_address,
        estimated_total=estimated_total,
        job_uuid=job_uuid,
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


if __name__ == "__main__":  # local dev: python main.py
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("DEV", "0") == "1",
    )
