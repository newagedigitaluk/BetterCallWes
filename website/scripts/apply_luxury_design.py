#!/usr/bin/env python3
"""
Apply luxury design template to all service pages
Reads boiler-repair.html as the template and adapts content for each service
"""

import os
import re
from pathlib import Path

# Service-specific content mapping
SERVICE_CONTENT = {
    "boiler-installation.html": {
        "title": "Professional Boiler Installation",
        "hero_text": "New Boiler Installation in Southampton",
        "subtitle": "Upgrading your boiler? I'll recommend the right system for your home and install it properly. Gas Safe registered, fully insured, with a 12-month workmanship guarantee.",
        "warning_section_title": "SIGNS YOU NEED A NEW BOILER",
        "canonical_url": "https://bettercallwes.co.uk/services/boiler-installation.html"
    },
    "boiler-servicing.html": {
        "title": "Annual Boiler Servicing",
        "hero_text": "Boiler Servicing in Southampton",
        "subtitle": "Keep your boiler running safely and efficiently with an annual service. I'll check all components, clean the system, and provide a full service report.",
        "warning_section_title": "WHY SERVICE YOUR BOILER",
        "canonical_url": "https://bettercallwes.co.uk/services/boiler-servicing.html"
    },
    "central-heating.html": {
        "title": "Central Heating Services",
        "hero_text": "Central Heating Experts in Southampton",
        "subtitle": "From radiator repairs to full system upgrades, I provide professional central heating services across Southampton and surrounding areas.",
        "warning_section_title": "HEATING PROBLEMS",
        "canonical_url": "https://bettercallwes.co.uk/services/central-heating.html"
    },
    "plumbing-repairs.html": {
        "title": "Plumbing Repairs",
        "hero_text": "Fast Plumbing Repairs in Southampton",
        "subtitle": "Leaking taps? Burst pipes? I offer fast, reliable plumbing repairs with transparent pricing and professional workmanship.",
        "warning_section_title": "COMMON PLUMBING ISSUES",
        "canonical_url": "https://bettercallwes.co.uk/services/plumbing-repairs.html"
    },
    "power-flushing.html": {
        "title": "Power Flushing Services",
        "hero_text": "Power Flushing in Southampton",
        "subtitle": "Is your heating system sluggish? Cold spots on radiators? A power flush removes sludge and debris, restoring full efficiency.",
        "warning_section_title": "SIGNS YOU NEED A POWER FLUSH",
        "canonical_url": "https://bettercallwes.co.uk/services/power-flushing.html"
    },
    "toilet-repairs.html": {
        "title": "Toilet Repairs",
        "hero_text": "Toilet Repairs in Southampton",
        "subtitle": "Running toilet? Won't flush properly? I fix all toilet issues quickly and professionally, with parts in stock for same-day repairs.",
        "warning_section_title": "COMMON TOILET PROBLEMS",
        "canonical_url": "https://bettercallwes.co.uk/services/toilet-repairs.html"
    },
    "gas-safety-check.html": {
        "title": "Gas Safety Certificates",
        "hero_text": "Gas Safety Checks in Southampton",
        "subtitle": "Landlord certificates, homeowner checks, and Gas Safe compliance. Fast turnaround with digital certificates provided on completion.",
        "warning_section_title": "WHY GET A GAS SAFETY CHECK",
        "canonical_url": "https://bettercallwes.co.uk/services/gas-safety-check.html"
    },
}

def apply_luxury_template(service_file, template_path, output_dir):
    """Apply luxury design from template to a service page"""

    # Read the template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    service_name = os.path.basename(service_file)

    # Get service-specific content or use defaults
    content = SERVICE_CONTENT.get(service_name, {
        "title": f"Service Page",
        "hero_text": "Professional Services in Southampton",
        "subtitle": "Quality workmanship, transparent pricing, Gas Safe registered.",
        "warning_section_title": "SERVICE INFORMATION",
        "canonical_url": f"https://bettercallwes.co.uk/services/{service_name}"
    })

    # Update title
    template = re.sub(
        r'<title>.*?</title>',
        f'<title>{content["title"]} | Better Call Wes</title>',
        template
    )

    # Update canonical URL
    template = re.sub(
        r'<link rel="canonical" href=".*?" />',
        f'<link rel="canonical" href="{content["canonical_url"]}" />',
        template
    )

    # Update hero heading
    template = re.sub(
        r'<h1 style="color: white.*?>.*?</h1>',
        f'<h1 style="color: white; margin-bottom: 1.5rem; line-height: 1.1;">{content["hero_text"]}</h1>',
        template,
        flags=re.DOTALL
    )

    # Update hero subtitle
    template = re.sub(
        r'<p style="color: rgba\(255,255,255,0\.9\); font-size: 1\.35rem.*?</p>',
        f'<p style="color: rgba(255,255,255,0.9); font-size: 1.35rem; margin-bottom: 2.5rem; line-height: 1.6;">{content["subtitle"]}</p>',
        template,
        count=1
    )

    # Write output
    output_path = os.path.join(output_dir, service_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"✅ Applied luxury design to {service_name}")

def main():
    # Paths
    base_dir = Path("/home/wes/Coding/Projects/Better Call Wes/website/site/services")
    template_file = base_dir / "boiler-repair.html"

    # Priority services to upgrade first
    priority_services = [
        "boiler-installation.html",
        "boiler-servicing.html",
        "central-heating.html",
        "plumbing-repairs.html",
        "power-flushing.html",
        "toilet-repairs.html",
        "gas-safety-check.html"
    ]

    print("🎨 Applying luxury design to service pages...\n")

    for service in priority_services:
        service_path = base_dir / service
        if service_path.exists():
            apply_luxury_template(service_path, template_file, base_dir)
        else:
            print(f"⚠️  {service} not found, skipping")

    print("\n✅ Luxury design applied to priority service pages!")
    print(f"📝 Updated {len(priority_services)} pages")

if __name__ == "__main__":
    main()
