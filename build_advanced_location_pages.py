import os
import re
import json
import random
import urllib.parse

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

index_html = read_file('/home/antigravity/Projects/Better Call Wes/Website/index.html')

head_match = re.search(r'(<!DOCTYPE html>.*?</head>)', index_html, re.DOTALL)
top_match = re.search(r'(<body>\s*<!-- Top Bar -->.*?</header>)', index_html, re.DOTALL)
footer_match = re.search(r'(<!-- Footer -->.*?</html>)', index_html, re.DOTALL)

base_head = head_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/')
base_top = top_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/').replace('href="services/', 'href="../services/').replace('href="about.html"', 'href="../about.html"').replace('href="pricing.html"', 'href="../pricing.html"').replace('href="reviews.html"', 'href="../reviews.html"').replace('href="contact.html"', 'href="../contact.html"').replace('href="services.html"', 'href="../services.html"').replace('href="/"', 'href="../"')
base_footer = footer_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/').replace('href="services/', 'href="../services/').replace('href="about.html"', 'href="../about.html"').replace('href="pricing.html"', 'href="../pricing.html"').replace('href="reviews.html"', 'href="../reviews.html"').replace('href="contact.html"', 'href="../contact.html"').replace('href="services.html"', 'href="../services.html"').replace('href="/"', 'href="../"')

locations = json.loads(read_file('/home/antigravity/Projects/Better Call Wes/SEO Site Design/location_data.json'))

# Content Variations (No VAT mentioned)
headlines = [
    "Your Local Plumber in {display}",
    "Expert Plumbing & Heating Engineer in {display}",
    "Gas Safe Registered Plumber for {display}",
    "Reliable Heating Solutions in {display}"
]

subtitles = [
    "From emergency boiler repairs to dripping taps, Better Call Wes provides rapidly responding, transparent services for {display} residents.",
    "Looking for a reliable plumbing professional in {full}? I offer guaranteed workmanship, upfront pricing, and rapid response times.",
    "Serving the {display} community with top-rated boiler installations, servicing, and emergency plumbing repairs. Book online today.",
    "Don't let plumbing problems ruin your week in {display}. As a highly-rated Gas Safe engineer, I'm thoroughly equipped to fix any issue."
]

def generate_location_page(loc_data):
    display = loc_data['display']
    full_area = loc_data['full']
    url = loc_data['url']
    landmarks = loc_data['landmarks']
    geography = loc_data['geography']
    house_type = loc_data['house_type']
    
    random.seed(url)
    
    h1 = random.choice(headlines).format(display=display)
    subtitle = random.choice(subtitles).format(display=display, full=full_area)
    
    local_p = f"As a fully mobile plumbing service, I traverse all areas of {display}, {geography}. Whether you live near {landmarks} or further out in {full_area}, I know the local area inside and out. I understand the specific plumbing systems common to {display}'s properties, from {house_type}. I pride myself on offering a genuinely local service, meaning shorter wait times and a plumber who treats your neighborhood with genuine respect."

    map_query = urllib.parse.quote(f"{display}, Southampton, UK")
    map_embed = f'<iframe width="100%" height="400" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.com/maps?q={map_query}&t=&z=13&ie=UTF8&iwloc=&output=embed" style="border-radius: var(--radius-lg); box-shadow: var(--shadow-md);"></iframe>'

    schema = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "PlumbingService",
      "name": "Better Call Wes - {display}",
      "description": "{subtitle}",
      "url": "https://bettercallwes.co.uk/locations/{url}.html",
      "telephone": "07700 155 655",
      "address": {{
        "@type": "PostalAddress",
        "addressLocality": "Southampton",
        "addressRegion": "Hampshire"
      }},
      "areaServed": {{
        "@type": "Place",
        "name": "{display}"
      }}
    }}
    </script>
    """

    title = f"Plumber & Heating Engineer {display} | Better Call Wes"
    custom_head = base_head.replace('<title>Better Call Wes - Your Local Southampton Plumber | Gas Safe Registered</title>', f'<title>{title}</title>')
    custom_head = re.sub(r'<meta name="description".*?>', f'<meta name="description" content="{subtitle}">', custom_head)
    custom_head = custom_head.replace('</head>', f'{schema}\n</head>')

    layout_type = random.choice(["A", "B", "C"])

    hero_center = f"""
    <section class="hero" style="background: var(--color-primary); min-height: 40vh; padding-top: 150px; padding-bottom: 80px;">
        <div class="container text-center">
            <h1 style="color: white; margin-bottom: 1.5rem; font-size: 3rem;">{h1}</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; max-width: 800px; margin: 0 auto 2rem;">{subtitle}</p>
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <a href="../booking.html" class="btn btn-primary"><i data-lucide="calendar"></i> Book Online Now</a>
            </div>
        </div>
    </section>
    """

    hero_split = f"""
    <section class="hero" style="background: var(--color-primary); padding-top: 150px; padding-bottom: 80px;">
        <div class="container" style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 4rem; align-items: center;">
            <div>
                <h1 style="color: white; margin-bottom: 1.5rem; font-size: 2.8rem;">{h1}</h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 1.15rem; margin-bottom: 2rem;">{subtitle}</p>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <a href="../booking.html" class="btn btn-primary"><i data-lucide="calendar"></i> Check Availability</a>
                </div>
            </div>
            <div style="background: white; border-radius: var(--radius-lg); padding: 2rem; text-align: center; box-shadow: var(--shadow-lg);">
                <h3 style="color: var(--color-primary); margin-bottom: 1rem;">Send a Video Quote</h3>
                <p style="color: var(--text-body); margin-bottom: 1.5rem;">Skip the call-out fee. Send me a WhatsApp video of the problem in {display} for a fast free estimate.</p>
                <a href="https://wa.me/447700155655" class="btn" style="background: #25D366; color: white; width: 100%;"><i data-lucide="video"></i> WhatsApp Me</a>
            </div>
        </div>
    </section>
    """
    
    local_info_block = f"""
    <section class="section section-gray">
        <div class="container">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 4rem; align-items: center;">
                <div>
                    <div class="section-label" style="justify-content: flex-start;">COMMITTED TO {display.upper()}</div>
                    <h2 style="margin-bottom: 1.5rem;">Dedicated Local Service</h2>
                    <p style="color: var(--text-body); line-height: 1.8; font-size: 1.1rem; margin-bottom: 1.5rem;">{local_p}</p>
                    <ul style="list-style: none; padding: 0; display: flex; flex-direction: column; gap: 0.75rem;">
                        <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check-circle" style="color: var(--color-accent);"></i> Transparent Upfront Pricing</li>
                        <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check-circle" style="color: var(--color-accent);"></i> Fully Gas Safe Registered</li>
                        <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check-circle" style="color: var(--color-accent);"></i> 12-Month Workmanship Guarantee</li>
                    </ul>
                </div>
                <div>
                    {map_embed}
                </div>
            </div>
        </div>
    </section>
    """

    services_block = f"""
    <section class="section">
        <div class="container">
            <div class="section-header text-center mx-auto" style="max-width: 600px;">
                <h2 style="margin-bottom: 1rem;">Services in {display}</h2>
                <p>I provide a complete suite of plumbing and heating solutions. No hidden fees.</p>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; margin-top: 3rem;">
                <div>
                    <img src="../assets/images/bathroom-shower.png" alt="Modern bathroom installation in {display}" style="width: 100%; border-radius: var(--radius-lg); box-shadow: var(--shadow-md);">
                </div>
                <div class="service-grid" style="grid-template-columns: 1fr;">
                    <div class="service-card text-center" style="background: white;">
                        <div class="service-icon mx-auto"><i data-lucide="wrench"></i></div>
                        <h3>Boiler Repairs</h3>
                        <p>Expert diagnostics and repair in {display}.</p>
                    </div>
                    <div class="service-card text-center" style="background: white;">
                        <div class="service-icon mx-auto"><i data-lucide="droplets"></i></div>
                        <h3>Plumbing Fixes</h3>
                        <p>Leaking taps and blocked pipes sorted.</p>
                    </div>
                    <div class="service-card text-center" style="background: white;">
                        <div class="service-icon mx-auto"><i data-lucide="shield-check"></i></div>
                        <h3>Gas Safety</h3>
                        <p>Landlord certificates for {display} properties.</p>
                    </div>
                </div>
            </div>
            <div class="text-center" style="margin-top: 3rem;">
                <a href="../services.html" class="btn btn-outline">View All Services</a>
            </div>
        </div>
    </section>
    """
    
    trust_block = f"""
    <section class="section" style="background: var(--color-primary); color: white;">
        <div class="container text-center">
            <div class="rating-badge mx-auto mb-4" style="justify-content: center; display: inline-flex; border-color: rgba(255,255,255,0.2);">
                <span class="stars">★★★★★</span>
                <span style="color: white;">4.9 Average Rating</span>
            </div>
            <h2 style="margin-bottom: 2rem; color: white;">Why {display} Chooses Wes</h2>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem;">
                <div>
                    <i data-lucide="clock" style="width: 40px; height: 40px; color: var(--color-accent); margin-bottom: 1rem;"></i>
                    <h4 style="font-size: 1.1rem; color: white;">Arrives on Time</h4>
                </div>
                <div>
                    <i data-lucide="pound-sterling" style="width: 40px; height: 40px; color: var(--color-accent); margin-bottom: 1rem;"></i>
                    <h4 style="font-size: 1.1rem; color: white;">Upfront Quotes</h4>
                </div>
                <div>
                    <i data-lucide="shield" style="width: 40px; height: 40px; color: var(--color-accent); margin-bottom: 1rem;"></i>
                    <h4 style="font-size: 1.1rem; color: white;">12-Month Guarantee</h4>
                </div>
            </div>
        </div>
    </section>
    """

    cityscape_break = """
    <section style="position: relative; height: 250px; overflow: hidden;">
        <img src="../assets/images/southampton-cityscape.png" alt="Southampton waterfront" style="width: 100%; height: 100%; object-fit: cover;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(0deg, rgba(15,41,66,0.7) 0%, rgba(15,41,66,0.3) 100%); display: flex; align-items: center; justify-content: center;">
            <div class="container text-center">
                <h2 style="color: white; margin-bottom: 0.5rem;">Proudly Serving Southampton & Beyond</h2>
                <p style="color: rgba(255,255,255,0.85); font-size: 1.1rem;">Your trusted local plumber, covering all SO postcodes.</p>
            </div>
        </div>
    </section>
    """

    if layout_type == "A":
        page_content = hero_center + "\n" + services_block + "\n" + cityscape_break + "\n" + local_info_block + "\n" + trust_block
    elif layout_type == "B":
        page_content = hero_split + "\n" + local_info_block + "\n" + trust_block + "\n" + cityscape_break + "\n" + services_block
    else: # C
        page_content = hero_center + "\n" + trust_block + "\n" + cityscape_break + "\n" + local_info_block + "\n" + services_block

    final_html = (
        custom_head + "\n<body>\n" +
        base_top + "\n" +
        page_content + "\n" +
        base_footer
    )
    
    os.makedirs('/home/antigravity/Projects/Better Call Wes/Website/locations', exist_ok=True)
    write_file(f'/home/antigravity/Projects/Better Call Wes/Website/locations/{url}.html', final_html)

for loc in locations:
    generate_location_page(loc)

print("20 Highly Distinct Local Area Landing Pages generated successfully.")
