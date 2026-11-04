"""Build the pre-Field-Services pieces on the BCW HighLevel sub-account.

Dry run by default: prints what exists and what it would create. Pass --apply
to create the missing pieces. Idempotent: anything with the same name is left
alone, so it is safe to re-run after Wes widens the token's scopes.

    with-secret .env -- python3 website/scripts/ghl/bcw_ghl_setup.py           # dry run
    with-secret .env -- python3 website/scripts/ghl/bcw_ghl_setup.py --apply   # build

Nothing here messages a contact, buys a number, turns on AI, connects payments
or touches ServiceM8. Calendars are created switched off (isActive false).
Details and the UI-only steps are in docs/GHL-SETUP.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ghl_api import call  # noqa: E402

APPLY = "--apply" in sys.argv
PIPELINE_NAME = "Jobs (SM8 mirror)"

# Mirrors the SM8 job flow: enquiry -> quote -> work order -> completed -> invoice.
# "Parts on order" stands in for the SM8 queue of the same name.
# "Unsuccessful" in SM8 is the opportunity's Lost status here, not a stage.
PIPELINE_STAGES = [
    "Enquiry",
    "Visit booked",
    "Quote sent",
    "Quote accepted",
    "Parts on order",
    "Work booked",
    "Completed",
    "Invoiced",
    "Paid",
    "Review requested",
]

CONTACT_FIELDS = [
    {"name": "Appliance Make", "dataType": "TEXT", "placeholder": "e.g. Worcester Bosch"},
    {"name": "Appliance Model", "dataType": "TEXT", "placeholder": "e.g. Greenstar 30i"},
    {"name": "Appliance GC Number", "dataType": "TEXT", "placeholder": "e.g. 47-406-05"},
    {"name": "Appliance Type", "dataType": "SINGLE_OPTIONS",
     "options": ["Combi", "System", "Regular (heat only)", "Back boiler", "Gas fire", "Other"]},
    {"name": "Appliance Location", "dataType": "TEXT", "placeholder": "e.g. kitchen cupboard"},
    {"name": "Last Service Date", "dataType": "DATE"},
    {"name": "Next Service Due", "dataType": "DATE"},
    {"name": "Gas Safety Record Expiry", "dataType": "DATE"},
]

OPPORTUNITY_FIELDS = [
    {"name": "SM8 Job UUID", "dataType": "TEXT"},
    {"name": "SM8 Job Number", "dataType": "TEXT"},
]

# One "event" calendar per bookable service, from website/site/data/services.json.
# Hours match the booking API: Mon-Fri, 09:00-12:00 and 13:00-17:00.
HOURS = [{"daysOfTheWeek": [d], "hours": [
    {"openHour": 9, "openMinute": 0, "closeHour": 12, "closeMinute": 0},
    {"openHour": 13, "openMinute": 0, "closeHour": 17, "closeMinute": 0},
]} for d in (1, 2, 3, 4, 5)]

CALENDARS = [
    ("Boiler Service", 60, "Annual boiler service. Standard or full stripdown."),
    ("Gas Safety Check (CP12)", 60, "Landlord or homeowner gas safety check. 1 boiler + 1 hob."),
    ("Boiler Repair / Diagnostic", 60, "£100 first-hour diagnostic. Repairs quoted separately."),
    ("General Plumbing", 60, "Hourly call-out. From £100 first hour, parts quoted on the day."),
    ("Power Flush", 480, "Whole-day power flush, up to 8 radiators."),
]


def report(label, status, detail=""):
    print(f"  [{status}] {label} {detail}".rstrip())


def ensure_fields(model, wanted):
    st, js = call("GET", "/locations/{LOC}/customFields?model=" + model)
    if st != 200:
        report(f"{model} custom fields", f"HTTP {st}", js.get("message", ""))
        return
    have = {f["name"].strip().lower() for f in js.get("customFields", []) if f.get("model") == model}
    for f in wanted:
        if f["name"].lower() in have:
            report(f["name"], "exists")
            continue
        if not APPLY:
            report(f["name"], "would create", f["dataType"])
            continue
        st, out = call("POST", "/locations/{LOC}/customFields", dict(f, model=model))
        report(f["name"], "created" if st in (200, 201) else f"HTTP {st}", "" if st in (200, 201) else str(out)[:160])


def ensure_pipeline():
    st, js = call("GET", "/opportunities/pipelines?locationId={LOC}")
    if st != 200:
        report("pipelines", f"HTTP {st}")
        return
    if any(p["name"] == PIPELINE_NAME for p in js.get("pipelines", [])):
        report(PIPELINE_NAME, "exists")
        return
    if not APPLY:
        report(PIPELINE_NAME, "would create", " > ".join(PIPELINE_STAGES))
        return
    body = {"locationId": os.environ["GHL_LOCATION_ID"], "name": PIPELINE_NAME,
            "stages": [{"name": s, "position": i} for i, s in enumerate(PIPELINE_STAGES)],
            "showInFunnel": True, "showInPieChart": True}
    st, out = call("POST", "/opportunities/pipelines", body)
    if st in (200, 201):
        report(PIPELINE_NAME, "created")
    else:
        report(PIPELINE_NAME, f"HTTP {st}", "build in the UI, see docs/GHL-SETUP.md. " + str(out)[:120])


def ensure_calendars():
    st, js = call("GET", "/calendars/?locationId={LOC}")
    if st != 200:
        report("calendars", f"HTTP {st}", "token lacks calendars scope, see docs/GHL-SETUP.md")
        return
    have = {c["name"] for c in js.get("calendars", [])}
    for name, mins, desc in CALENDARS:
        if name in have:
            report(name, "exists")
            continue
        if not APPLY:
            report(name, "would create", f"{mins} min, switched off")
            continue
        body = {
            "locationId": os.environ["GHL_LOCATION_ID"],
            "name": name,
            "description": desc,
            "calendarType": "event",
            "slotDuration": mins, "slotDurationUnit": "mins",
            "slotInterval": 30 if mins <= 60 else 60, "slotIntervalUnit": "mins",
            "appoinmentPerSlot": 1,
            "openHours": HOURS if mins <= 60 else [dict(h, hours=[{"openHour": 9, "openMinute": 0, "closeHour": 17, "closeMinute": 0}]) for h in HOURS],
            "allowBookingAfter": 2, "allowBookingAfterUnit": "hours",
            "allowReschedule": True, "allowCancellation": True,
            "autoConfirm": False,
            "isActive": False,
        }
        st, out = call("POST", "/calendars/", body)
        report(name, "created (off)" if st in (200, 201) else f"HTTP {st}", "" if st in (200, 201) else str(out)[:160])


def main():
    print("Mode:", "APPLY" if APPLY else "dry run (pass --apply to build)")
    print("Pipeline"); ensure_pipeline()
    print("Contact fields"); ensure_fields("contact", CONTACT_FIELDS)
    print("Opportunity fields"); ensure_fields("opportunity", OPPORTUNITY_FIELDS)
    print("Calendars"); ensure_calendars()


if __name__ == "__main__":
    main()
