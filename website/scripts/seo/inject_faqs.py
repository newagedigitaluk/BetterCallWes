"""Inject FAQ blocks + FAQPage JSON-LD schema into service pages.

Content is authored once below, in Wes's voice (British English, plain, direct,
no marketing fluff), using real prices from MASTER_PRICE_GUIDE_UK.md. Each FAQ
question maps to a People Also Ask query captured in the SERP snapshots — see
content-gaps-2026-05-11.md.

Constraints (per memory):
- No "No VAT" anywhere.
- No Gas Safe registration number in copy.
- Don't imply Wes always answers the phone personally.
- £ amounts only.

Run as:
    python3 website/scripts/seo/inject_faqs.py
    python3 website/scripts/seo/inject_faqs.py --dry-run     # show planned changes only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SITE = Path("/home/wes/Coding/Projects/Better Call Wes/website/site")
SERVICES = SITE / "services"

FAQS: dict[str, list[tuple[str, str]]] = {
    "boiler-repair.html": [
        (
            "How much does a boiler repair usually cost?",
            "Most boiler repairs land between £100 and £280, including parts and labour. The £100 covers the first hour, which is the diagnostic — that's enough time to fix many faults outright. Bigger jobs like a PCB replacement run £250–£350.",
        ),
        (
            "Is it worth repairing a boiler?",
            "Usually yes if the boiler is under twelve years old and the repair cost is below a third of the price of a new one. Once you're past that, the maths starts favouring replacement, especially if the boiler has had multiple faults in a year.",
        ),
        (
            "What is the lifespan of a boiler?",
            "A modern combi boiler typically lasts twelve to fifteen years with annual servicing. Older system or back boilers can run longer, but parts get harder to find and efficiency drops off.",
        ),
        (
            "What is the most expensive part of a boiler to replace?",
            "The PCB — the control board — at £250–£350 fitted. Heat exchangers and gas valves are the next tier down, typically £200–£300.",
        ),
        (
            "What are the signs of a failing boiler?",
            "Banging or kettling noises, needing to re-pressurise more than once a month, a yellow rather than blue flame, error codes that keep coming back, or hot water that runs cold mid-shower. Any of those is worth a diagnostic before it gets worse.",
        ),
    ],
    "boiler-servicing.html": [
        (
            "How much should a full boiler service cost?",
            "A standard annual service is £100. A full strip-down service, where the burner and heat exchanger are cleaned properly, is £160. Both include a written report.",
        ),
        (
            "How frequently should a boiler be serviced?",
            "Once a year. Most manufacturers also require an annual service to keep the warranty valid — skipping a year usually voids the cover.",
        ),
        (
            "Is it worth replacing a 15 year old boiler?",
            "It's worth getting an honest assessment. A well-maintained fifteen-year-old boiler can still run safely, but efficiency is typically 70–80% versus 90%+ for a modern A-rated unit. The gas-bill saving often pays back a new boiler within seven to ten years.",
        ),
        (
            "What are signs that my boiler needs a service?",
            "Louder than usual, taking longer to heat up, higher gas bills, the flame burning yellow instead of blue, or any error code that clears itself. A service catches small faults before they become breakdown call-outs.",
        ),
        (
            "How long does a boiler service take?",
            "Around 45–60 minutes for a standard service, longer for a full strip-down. We arrive in a marked van and won't leave any mess behind.",
        ),
    ],
    "boiler-installation.html": [
        (
            "How much does a new boiler cost?",
            "A standard combi-to-combi swap starts at £2,100 including the boiler, parts, and a day's labour. System and regular boiler installs are quoted individually because the pipework and cylinder work varies.",
        ),
        (
            "How long does a boiler installation take?",
            "A straightforward combi swap is one full day. A boiler conversion (e.g. system to combi) is typically two days because the hot water cylinder and pipework need rearranging.",
        ),
        (
            "What is the best month to replace a boiler?",
            "Late summer or early autumn. Installers are less busy, lead times are shorter, and you're sorted before the first cold snap. Replacing in January when your old boiler has failed is usually the worst time — emergency installs cost more and choice is limited.",
        ),
        (
            "How much should it cost to have a new boiler fitted in 2026?",
            "Between £2,100 and £3,500 for most domestic installs, including a quality A-rated boiler, a magnetic filter, and a power flush if needed. The price varies with boiler brand, flue routing, and any system upgrades.",
        ),
        (
            "Can I get a government grant for a new boiler?",
            "The ECO4 scheme funds boiler replacements for some low-income households or those on means-tested benefits. Eligibility depends on the property's EPC rating and your circumstances. We can talk you through whether you're likely to qualify before you apply.",
        ),
    ],
    "new-boiler.html": [
        (
            "How much should it cost to have a new boiler fitted?",
            "Around £2,100 for a standard combi swap in Southampton, including the boiler, flue, fittings, and a day's labour. Larger systems or conversions cost more — we quote for free.",
        ),
        (
            "What size boiler do I need?",
            "For most three-bedroom homes a 24–30 kW combi is right. Larger houses with two bathrooms or high hot-water demand may need 35 kW or a system boiler with a cylinder. We'll size it properly during the quote, not just match the old unit.",
        ),
        (
            "What brands of combi boiler are most reliable?",
            "Worcester Bosch, Vaillant, and Ideal Logic+ all have strong track records and a Gas Safe install network. We'll recommend based on your home, budget, and warranty preferences rather than push a single brand.",
        ),
        (
            "How long does a new boiler last?",
            "Twelve to fifteen years if it's serviced annually. Skipping the service usually halves that and voids the warranty.",
        ),
        (
            "Do I need a power flush with a new boiler?",
            "Most manufacturers require the system to be cleaned before fitting a new boiler — otherwise the warranty doesn't apply. We include a chemical flush as standard; a full power flush is £440 if the system shows heavy sludge.",
        ),
    ],
    "gas-safety-check.html": [
        (
            "How much does a gas safety check cost in the UK?",
            "£90 for up to two appliances. Additional appliances are £20–£50 each. You receive the official certificate by email the same day.",
        ),
        (
            "Is it a legal requirement to have a gas safety check?",
            "Yes if you let out the property — landlords must arrange an annual check by a Gas Safe registered engineer. Owner-occupiers aren't legally required to, but an annual check is strongly recommended for safety and insurance.",
        ),
        (
            "Can I get a free gas safety check?",
            "Some energy suppliers (British Gas Priority Services, EDF, others) offer free checks for customers who are over 60, disabled, or on certain benefits. It's worth ringing your supplier first.",
        ),
        (
            "Can an electrician do a gas safety check?",
            "No. Anyone working on gas appliances must be Gas Safe registered. Electricians aren't qualified or insured for gas work, no matter how experienced they are with other trades.",
        ),
        (
            "What does a gas safety check involve?",
            "Each appliance is tested for tightness, gas pressure, ventilation, flue performance, and safe operation. We also check the gas pipework and meter. The whole thing usually takes 45–90 minutes for a standard home.",
        ),
    ],
    "landlord-gas-safety-certificates.html": [
        (
            "How much does a landlord gas safety certificate cost?",
            "£90 for up to two appliances, typically a boiler and a cooker. Each additional appliance is £20–£50. You get the CP12 certificate by email the same day.",
        ),
        (
            "How often do I need a landlord gas safety check?",
            "Every twelve months. The check must be done by a Gas Safe registered engineer, and you must give the tenant a copy of the certificate within 28 days of the check or before they move in.",
        ),
        (
            "What is a CP12 certificate?",
            "It's the landlord's gas safety record — the paperwork that proves every gas appliance in the property has been checked and is safe to use. CP12 is the historical name; the official term is Landlord Gas Safety Record.",
        ),
        (
            "What happens if I don't have a valid gas safety certificate?",
            "You're breaking the law. The Health and Safety Executive can fine you up to £6,000 per appliance, and you can't legally serve a Section 21 eviction notice. Your insurance is also likely to be void.",
        ),
        (
            "Do I need a gas safety check if my tenant has been there for years?",
            "Yes. It's an annual requirement regardless of how long the tenancy has run. We can usually book the check within a week — sooner if the previous certificate is about to expire.",
        ),
    ],
    "plumbing-repairs.html": [
        (
            "How much do UK plumbers charge per hour?",
            "Most Gas Safe plumbers in the south of England charge £80–£120 for the first hour. Our diagnostic fee is £100, which covers the first hour and often the full job for smaller repairs. After that it's £50 per 30 minutes.",
        ),
        (
            "What is the minimum charge for a plumber?",
            "£100, which covers up to an hour on site. That includes diagnosis, parts that are already on the van for common jobs, and most small fixes — a stuck tap, a running toilet, a slow drain.",
        ),
        (
            "What is a normal plumber call-out fee?",
            "£100 in Southampton for standard hours. We don't add a separate call-out fee on top — the £100 is the diagnostic and the first hour of work combined.",
        ),
        (
            "How to spot a dodgy plumber?",
            "Three checks. Ask for the Gas Safe ID card for any gas work and verify it on the Gas Safe register. Get the quote in writing before work starts, itemised for labour and parts. And look for reviews on the company name — not just stars, the wording of the reviews.",
        ),
        (
            "Do you give a guarantee on plumbing work?",
            "Yes — a 12-month workmanship guarantee on every job. Parts carry whatever the manufacturer warranty is, usually two years for most boiler components and longer for major parts.",
        ),
    ],
}

FAQ_SECTION_RE = re.compile(
    r'(<section[^>]*>\s*<div[^>]*>\s*<div class="section-header">\s*<div class="section-label">FAQS</div>.*?</section>)',
    re.DOTALL,
)
FAQ_SCHEMA_MARKER_BEGIN = "<!-- BEGIN FAQ JSON-LD -->"
FAQ_SCHEMA_MARKER_END = "<!-- END FAQ JSON-LD -->"
EXISTING_SCHEMA_RE = re.compile(
    rf"{re.escape(FAQ_SCHEMA_MARKER_BEGIN)}.*?{re.escape(FAQ_SCHEMA_MARKER_END)}",
    re.DOTALL,
)


def render_faq_html(faqs: list[tuple[str, str]]) -> str:
    items = []
    for q, a in faqs:
        items.append(
            "        <div style=\"background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);\">\n"
            f"          <h3 style=\"font-size: 1.15rem; margin-bottom: 0.5rem; color: var(--color-primary);\">{q}</h3>\n"
            f"          <p style=\"color: var(--text-body); margin: 0; padding-top: 0.5rem;\">{a}</p>\n"
            "        </div>"
        )
    inner = "\n".join(items)
    return (
        '<section class="section section-gray">\n'
        '  <div class="container" style="max-width: 800px;">\n'
        '    <div class="section-header">\n'
        '      <div class="section-label">FAQS</div>\n'
        '      <h2>Common questions, plain answers</h2>\n'
        '    </div>\n'
        '    <div style="display: flex; flex-direction: column; gap: 1rem;">\n'
        f"{inner}\n"
        "    </div>\n"
        "  </div>\n"
        "</section>"
    )


def render_faq_schema(faqs: list[tuple[str, str]]) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    return (
        f"{FAQ_SCHEMA_MARKER_BEGIN}\n"
        '<script type="application/ld+json">\n'
        f"{body}\n"
        "</script>\n"
        f"{FAQ_SCHEMA_MARKER_END}"
    )


def update_page(path: Path, faqs: list[tuple[str, str]], dry_run: bool) -> str:
    html = path.read_text(encoding="utf-8")
    actions: list[str] = []

    new_section = render_faq_html(faqs)
    if FAQ_SECTION_RE.search(html):
        html = FAQ_SECTION_RE.sub(new_section, html, count=1)
        actions.append("replaced FAQ section")
    else:
        anchor = html.find("<!-- Footer -->")
        if anchor < 0:
            anchor = html.find("<footer")
        if anchor < 0:
            return "no anchor for FAQ insert"
        html = html[:anchor] + new_section + "\n\n " + html[anchor:]
        actions.append("inserted FAQ section before footer")

    schema = render_faq_schema(faqs)
    if EXISTING_SCHEMA_RE.search(html):
        html = EXISTING_SCHEMA_RE.sub(schema, html, count=1)
        actions.append("replaced FAQ schema")
    else:
        head_close = html.find("</head>")
        if head_close < 0:
            return "no </head> for schema insert"
        html = html[:head_close] + schema + "\n " + html[head_close:]
        actions.append("inserted FAQ schema in <head>")

    if not dry_run:
        path.write_text(html, encoding="utf-8")
    return ", ".join(actions)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    missing: list[str] = []
    for fname in FAQS:
        if not (SERVICES / fname).exists():
            missing.append(fname)
    if missing:
        print(f"Missing service files: {missing}", file=sys.stderr)
        return 1

    for fname, faqs in FAQS.items():
        path = SERVICES / fname
        result = update_page(path, faqs, args.dry_run)
        prefix = "[dry-run] " if args.dry_run else "[updated] "
        print(f"{prefix}{fname}: {result} ({len(faqs)} Q&As)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
