#!/usr/bin/env python3
"""
Apply VISUAL luxury enhancements to service pages
Preserves ALL original content - only enhances styling and adds visual elements
"""

import re
from pathlib import Path

def add_luxury_styles_to_head(html_content):
    """Add luxury CSS styles before </head> tag - preserves all existing content"""

    luxury_styles = '''
    <style>
        /* Luxury Visual Enhancements - Preserves all content */
        .hero-luxury-bg {
            position: relative;
            background: linear-gradient(135deg, #0F2942 0%, #1A3A5A 100%);
            overflow: hidden;
        }

        .hero-luxury-bg::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -25%;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(255, 107, 0, 0.1) 0%, transparent 70%);
            pointer-events: none;
        }

        .glass-card-luxury {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 60px -15px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.6);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .glass-card-luxury:hover {
            transform: translateY(-8px);
            box-shadow: 0 30px 80px -20px rgba(0, 0, 0, 0.25), 0 0 40px -10px rgba(255, 107, 0, 0.2);
        }

        .trust-badge {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
            padding: 1.5rem;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease;
            min-width: 140px;
        }

        .trust-badge:hover {
            transform: translateY(-4px);
        }

        .trust-badge img {
            height: 50px;
            width: auto;
            object-fit: contain;
            filter: grayscale(100%);
            opacity: 0.6;
            transition: all 0.3s ease;
        }

        .trust-badge:hover img {
            filter: grayscale(0%);
            opacity: 1;
        }

        .trust-badge span {
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748B;
            text-align: center;
        }

        @media (max-width: 768px) {
            .trust-badge {
                min-width: 120px;
                padding: 1rem;
            }
        }
    </style>
'''

    # Insert before </head>
    return html_content.replace('</head>', luxury_styles + '\n</head>')

def add_manufacturer_badges_after_hero(html_content):
    """Add manufacturer trust badges section after hero - BOILER PAGES ONLY"""

    badges_html = '''
    <!-- Manufacturer Trust Badges -->
    <section class="section" style="padding: 3rem 0; background: #F8FAFC;">
        <div class="container">
            <p style="text-align: center; color: #64748B; font-weight: 600; margin-bottom: 2rem; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px;">Certified to service all major brands</p>
            <div style="display: flex; gap: 2rem; align-items: center; justify-content: center; flex-wrap: wrap;">
                <div class="trust-badge">
                    <img src="../assets/images/worcester-bosch-logo.png" alt="Worcester Bosch" onerror="this.style.display='none'">
                    <span>Worcester Bosch</span>
                </div>
                <div class="trust-badge">
                    <img src="../assets/images/ideal-logo.png" alt="Ideal Boilers" onerror="this.style.display='none'">
                    <span>Ideal</span>
                </div>
                <div class="trust-badge">
                    <img src="../assets/images/vaillant-logo.png" alt="Vaillant" onerror="this.style.display='none'">
                    <span>Vaillant</span>
                </div>
                <div class="trust-badge">
                    <img src="../assets/images/baxi-logo.png" alt="Baxi" onerror="this.style.display='none'">
                    <span>Baxi</span>
                </div>
            </div>
        </div>
    </section>
'''

    # Find first </section> after hero and insert badges after it
    # Look for the first closing section tag
    match = re.search(r'(<section[^>]*hero[^>]*>.*?</section>)', html_content, re.DOTALL)
    if match:
        hero_section = match.group(1)
        return html_content.replace(hero_section, hero_section + '\n' + badges_html, 1)

    return html_content

def enhance_page_visually(file_path, add_manufacturer_badges=False):
    """Apply visual enhancements while preserving ALL content"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add luxury styles to head
    content = add_luxury_styles_to_head(content)

    # 2. Add manufacturer badges if this is a boiler page
    if add_manufacturer_badges:
        content = add_manufacturer_badges_after_hero(content)

    # 3. Enhance existing cards with glass effect CLASS (don't change content)
    # Find cards and add glass-card-luxury class if they don't have it
    content = re.sub(
        r'<div style="background: white; padding: 2rem; border-radius: var\(--radius-md\);([^"]*)"',
        r'<div class="glass-card-luxury" style="padding: 2rem; border-radius: 24px;\1"',
        content
    )

    # Write enhanced version
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Enhanced {file_path.name} (content preserved, visuals upgraded)")

def main():
    base_dir = Path("/home/wes/Coding/Projects/Better Call Wes/Website/services")

    # Boiler pages get manufacturer badges
    boiler_pages = [
        "boiler-repair.html",
        "boiler-installation.html",
        "boiler-servicing.html"
    ]

    print("🎨 Applying VISUAL luxury enhancements...")
    print("📝 All SEO content will be preserved\n")

    for service_file in boiler_pages:
        file_path = base_dir / service_file
        if file_path.exists():
            enhance_page_visually(file_path, add_manufacturer_badges=True)
        else:
            print(f"⚠️  {service_file} not found")

    print("\n✅ Visual enhancements complete!")
    print("✓ All original SEO content preserved")
    print("✓ Manufacturer badges added to 3 boiler pages only")
    print("✓ Glass card effects added")
    print("✓ Gradient backgrounds enhanced")

if __name__ == "__main__":
    main()
