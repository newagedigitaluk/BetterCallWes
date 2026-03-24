import os
import re

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

index_html = read_file('/home/antigravity/Projects/Better Call Wes/Website/index.html')

# Extract header and footer
head_match = re.search(r'(<!DOCTYPE html>.*?</head>)', index_html, re.DOTALL)
top_match = re.search(r'(<body>\s*<!-- Top Bar -->.*?</header>)', index_html, re.DOTALL)
footer_match = re.search(r'(<!-- Footer -->.*?</html>)', index_html, re.DOTALL)

base_head = head_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/')
base_top = top_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/').replace('href="services/', 'href="/services/').replace('href="about.html"', 'href="../about.html"').replace('href="pricing.html"', 'href="../pricing.html"').replace('href="reviews.html"', 'href="../reviews.html"').replace('href="contact.html"', 'href="../contact.html"').replace('href="services.html"', 'href="../services.html"').replace('href="/"', 'href="../"')
base_footer = footer_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/').replace('href="services/', 'href="/services/').replace('href="about.html"', 'href="../about.html"').replace('href="pricing.html"', 'href="../pricing.html"').replace('href="reviews.html"', 'href="../reviews.html"').replace('href="contact.html"', 'href="../contact.html"').replace('href="services.html"', 'href="../services.html"').replace('href="/"', 'href="../"')

pages_data = [
    {
        "filename": "boiler-repair.html",
        "title": "Boiler Repair in Southampton | Fast & Reliable | Better Call Wes",
        "desc": "Emergency gas boiler repairs in Southampton. I fix all makes and models. Fast diagnostics and affordable fixes with upfront pricing. Call Wes today.",
        "schema_name": "Boiler Repair Service",
        "h1": "Expert Boiler Repairs in Southampton",
        "subtitle": "No Heating? No Hot Water? I carry the parts to fix most faults in a single visit.",
        "price": "£100",
        "image": "boiler-repair.png",
        "signs": [
            ("No Heating or Hot Water", "The most obvious sign of a total boiler breakdown or diverter valve failure."),
            ("Strange Noises", "Banging, kettling, or whistling sounds indicate scale build-up or pump failure."),
            ("Low Pressure", "If your boiler keeps losing pressure, there is likely a leak in the system or a faulty expansion vessel."),
            ("Pilot Light Goes Out", "A common issue caused by a broken thermocouple or draught.")
        ],
        "services": [
            ("Diverter Valve Replacement", "/booking.html"),
            ("Expansion Vessel Recharge", "/booking.html"),
            ("Pump & Fan Replacement", "/booking.html"),
            ("PCB Diagnostics & Fitting", "/booking.html")
        ],
        "process": "1. Send a WhatsApp Video. 2. I diagnose or quote. 3. Fast, clean repair. 4. 12-month guarantee.",
        "faq": [
            ("How much does a boiler repair cost?", "I charge a flat flat £100 diagnostic fee for the first hour, which covers most minor repairs. If parts are needed, I quote upfront before proceeding. No hidden fees."),
            ("Do you carry spare parts?", "Yes, I stock common parts for major brands like Worcester Bosch, Vaillant, Baxi, and Ideal to ensure I can fix most issues on the first visit.")
        ]
    },
    {
        "filename": "boiler-servicing.html",
        "title": "Boiler Servicing Southampton | Gas Safe | Better Call Wes",
        "desc": "Keep your boiler efficient and safe with our comprehensive boiler servicing. Serving Southampton. Gas Safe registered. Book your annual service today.",
        "schema_name": "Boiler Servicing",
        "h1": "Complete Boiler Servicing & Maintenance",
        "subtitle": "Prevent breakdowns, validate your warranty, and keep your home safe with our comprehensive annual boiler service.",
        "price": "£100",
        "image": "gas-safety.png",
        "signs": [
            ("It's Been Over a Year", "Manufacturers require an annual service to keep warranties valid."),
            ("Yellow Flame", "If the flame is yellow instead of crisp blue, your boiler may be producing carbon monoxide."),
            ("Higher Energy Bills", "An inefficient boiler uses more gas, driving up your monthly heating costs."),
            ("Takes Long to Heat", "If radiators take ages to warm up, the boiler needs a tune-up or system needs flushing.")
        ],
        "services": [
            ("Standard Annual Service", "/booking.html"),
            ("Full Strip-Down Service", "/booking.html"),
            ("Landlord Gas Safety (CP12)", "/services/landlord-gas-safety-certificates.html"),
            ("System Health Check", "/booking.html")
        ],
        "process": "1. Book your slot online. 2. Gas Safe inspection. 3. Flue & emissions test. 4. Digital service record provided.",
        "faq": [
            ("What is included in a boiler service?", "I inspect the main components, perform a flue gas analysis, check for gas leaks, clean the condensate trap, and ensure the boiler is burning gas safely and efficiently."),
            ("How long does a service take?", "A standard service takes around 45 minutes to an hour. A full strip-down service takes longer.")
        ]
    },
    {
        "filename": "plumbing-repairs.html",
        "title": "Local Plumbing Repairs in Southampton | Better Call Wes",
        "desc": "Trusted local plumber in Southampton for all general plumbing repairs. Leaking taps, blocked toilets, and burst pipes fixed fast.",
        "schema_name": "Plumbing Service",
        "h1": "Reliable Plumbing Repairs in Southampton",
        "subtitle": "From dripping taps to blocked toilets, get professional, mess-free plumbing solutions at honest prices.",
        "price": "£60",
        "image": "plumbing-repairs.png",
        "signs": [
            ("Dripping Taps", "A constant drip wastes water and drives you crazy. Usually a quick washer or cartridge fix."),
            ("Toilet Won't Stop Running", "A faulty fill valve wastes hundreds of litres of water a day."),
            ("Slow Draining Sinks", "Blockages in the trap or pipework need clearing before they cause a flood."),
            ("Water Patches on Ceiling", "Hidden leaks require immediate attention before structural damage occurs.")
        ],
        "services": [
            ("Toilet Repair", "/services/toilet-repair.html"),
            ("Tap Replacement", "/services/tap-repair.html"),
            ("Shower Repair", "/services/shower-repair.html"),
            ("Leak Detection", "/services/pipe-leak-repair.html")
        ],
        "process": "1. WhatsApp me a photo. 2. Get an instant quote. 3. I fix it right the first time. 4. Left clean and tidy.",
        "faq": [
            ("What is your minimum call-out charge?", "My minimum labour charge is £100, which covers the first hour of work for diagnostics or small repairs."),
            ("Do you supply the parts?", "Yes, I can supply high-quality replacement parts, taps, and valves, or I can fit parts you have already purchased.")
        ]
    },
    {
        "filename": "boiler-installation.html",
        "title": "New Boiler Installation Southampton | Combi Swaps | Better Call Wes",
        "desc": "Get a reliable, energy-efficient new boiler installed by a Gas Safe engineer in Southampton. Free quotes and 12-month workmanship guarantee.",
        "schema_name": "Boiler Installation",
        "h1": "Professional Boiler Installation & Replacement",
        "subtitle": "Upgrade to an A-rated, energy-efficient boiler. Expert fitting, premium brands, and completely transparent quoting.",
        "price": "£2100",
        "image": "boiler-repair.png",
        "signs": [
            ("Boiler is 10+ Years Old", "Older boilers lose efficiency rapidly and parts become impossible to find."),
            ("Frequent Breakdowns", "If you are constantly paying for repairs, a replacement is more cost-effective."),
            ("Radiators Aren't Hot", "A failing pump or scaled-up heat exchanger means your boiler can't cope."),
            ("Gurgling Noises", "A sign of deep system issues that sometimes require a complete boiler and system replacement.")
        ],
        "services": [
            ("Combi Boiler Swaps", "/services/combi-boiler-installations.html"),
            ("System Upgrades", "/services/boiler-systems.html"),
            ("Smart Thermostat Setup", "/services/heating-controls.html"),
            ("Complete New Heating", "/services/central-heating.html")
        ],
        "process": "1. Free home survey or WhatsApp quote. 2. Transparent fixed-price estimate. 3. Safe installation and system flush. 4. Handover and warranty registration.",
        "faq": [
            ("How much does a new boiler cost?", "A standard combi-to-combi swap starts around £2,100 including materials, but prices vary based on the specific boiler model, flue requirements, and pipework alterations needed."),
            ("How long does installation take?", "A straightforward combi boiler replacement usually takes one full day.")
        ]
    },
    {
        "filename": "central-heating.html",
        "title": "Central Heating Services Southampton | Power Flushing | Better Call Wes",
        "desc": "Keep your home warm with expert central heating services. Power flushing, radiator installations, and smart controls in Southampton.",
        "schema_name": "Central Heating Service",
        "h1": "Complete Central Heating Services",
        "subtitle": "Maximize your home's warmth and efficiency with professional power flushing, radiator upgrades, and smart controls.",
        "price": "£180",
        "image": "heating-radiator.png",
        "signs": [
            ("Cold Spots on Radiators", "Usually means sludge build-up (requires power flushing) or trapped air."),
            ("Noisy Pipes", "Banging pipes (water hammer) or gurgling radiators need professional attention."),
            ("High Energy Bills", "An inefficient system with old radiators or sludge wastes heat and money."),
            ("Thermostat Not Working", "If your boiler runs constantly or won't turn on, the controls may need replacing.")
        ],
        "services": [
            ("Power Flushing", "/services/power-flushing.html"),
            ("Radiator Installs", "/services/radiators.html"),
            ("Smart Controls", "/services/smart-controls.html"),
            ("Unvented Cylinders", "/booking.html")
        ],
        "process": "1. Assess your heating needs. 2. Recommend efficiency upgrades. 3. Professional installation. 4. Comprehensive system testing.",
        "faq": [
            ("What is power flushing?", "Power flushing is a deep cleaning process that pumps chemicals through your heating system to remove sludge, rust, and debris, restoring efficiency and heat output."),
            ("Can you install smart thermostats?", "Yes, I regularly install Hive, Nest, and other smart heating controls from £120-£160 (labour only).")
        ]
    },
    {
        "filename": "gas-services.html",
        "title": "Gas Engineer Southampton | CP12 & Certificates | Better Call Wes",
        "desc": "Fully qualified Gas Safe engineer in Southampton. Landlord certificates (CP12), gas leak detection, and appliance installations.",
        "schema_name": "Gas Safe Engineer Support",
        "h1": "Certified Gas Engineering & Safety Checks",
        "subtitle": "Gas Safe registered (#558654) for complete peace of mind. Landlord certificates, gas leak repairs, and appliance installations.",
        "price": "£90",
        "image": "gas-safety.png",
        "signs": [
            ("Smell of Gas", "If you smell gas, turn off the supply at the meter immediately, open windows, and call the National Gas Emergency Service. Then call me for repair."),
            ("Tenancy Changing", "Landlords are legally required to have an annual Gas Safety Certificate (CP12) for all gas appliances."),
            ("Floppy Yellow Flame", "Gas appliances should burn with a crisp blue flame. Yellow means dangerous incomplete combustion."),
            ("New Appliance Upgrades", "Installing a new gas hob or oven requires a certified Gas Safe engineer.")
        ],
        "services": [
            ("Landlord Certificates (CP12)", "/services/landlord-gas-safety-certificates.html"),
            ("Gas Leak Detection", "/services/gas-leak-detection.html"),
            ("Gas Pipe Installation", "/services/gas-pipe-installation.html"),
            ("Hob/Oven Installation", "/services/gas-appliance-servicing.html")
        ],
        "process": "1. Verify credentials (Gas Safe #558654). 2. Rigorous tightness testing. 3. Safe installation or repair. 4. Official certification issued.",
        "faq": [
            ("How much is a Landlord Gas Safety Certificate?", "I charge £90 for a CP12 certificate which covers up to 2 appliances (e.g., boiler and gas hob)."),
            ("Can I install a gas cooker myself?", "Legally, no. All gas appliance installations must be carried out by a competent, registered Gas Safe engineer.")
        ]
    }
]

def generate_page(data):
    # JSON-LD Schema
    schema = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org/",
      "@type": "Service",
      "name": "{data['schema_name']}",
      "provider": {{
        "@type": "LocalBusiness",
        "name": "Better Call Wes",
        "telephone": "07700 155 655",
        "address": {{
          "@type": "PostalAddress",
          "addressLocality": "Southampton",
          "addressRegion": "Hampshire",
          "addressCountry": "UK"
        }}
      }},
      "areaServed": ["Southampton", "Eastleigh", "Shirley", "Bitterne", "Hedge End", "Chandler's Ford", "Romsey"],
      "hasOfferCatalog": {{
        "@type": "OfferCatalog",
        "name": "Plumbing and Heating Services",
        "itemListElement": [
          {{
            "@type": "Offer",
            "itemOffered": {{
              "@type": "Service",
              "name": "{data['schema_name']}"
            }},
            "priceCurrency": "GBP",
            "price": "{data['price'].replace('£','')}"
          }}
        ]
      }}
    }}
    </script>
    """

    # Head Replacement (Add schema and title/desc)
    custom_head = base_head.replace('<title>Better Call Wes - Your Local Southampton Plumber | Gas Safe Registered</title>', f'<title>{data["title"]}</title>')
    custom_head = re.sub(r'<meta name="description".*?>', f'<meta name="description" content="{data["desc"]}">', custom_head)
    custom_head = custom_head.replace('</head>', f'{schema}\n</head>')

    hero_section = f"""
    <section class="hero" style="background: var(--color-primary); min-height: 40vh; padding-top: 150px; padding-bottom: 80px;">
        <div class="container">
            <div class="hero-content" style="max-width: 800px; margin: 0 auto; text-align: center;">
                <h1 style="color: white; margin-bottom: 1.5rem;">{data['h1']}</h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; margin-bottom: 2rem;">{data['subtitle']}</p>
                <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                    <a href="../booking.html" class="btn btn-primary"><i data-lucide="calendar"></i> Book Online</a>
                    <a href="https://wa.me/447700155655" class="btn btn-outline" style="background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.3); color: white;"><i data-lucide="video"></i> WhatsApp Quote</a>
                </div>
            </div>
        </div>
    </section>
    """

    signs_html = "".join([f"""
    <div style="background: white; padding: 2rem; border-radius: var(--radius-md); box-shadow: var(--shadow-sm); border-top: 4px solid var(--color-accent);">
        <h3 style="margin-bottom: 1rem; color: var(--color-primary);">{sign[0]}</h3>
        <p style="color: var(--text-body);">{sign[1]}</p>
    </div>
    """ for sign in data["signs"]])

    signs_section = f"""
    <section class="section section-gray">
        <div class="container">
            <div class="section-header">
                <div class="section-label">WARNING SIGNS</div>
                <h2>When to Call a Professional</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem;">
                {signs_html}
            </div>
        </div>
    </section>
    """

    services_html = "".join([f"""
    <div class="service-card">
        <div class="service-icon"><i data-lucide="check-circle"></i></div>
        <h3>{srv[0]}</h3>
        <a href="..{srv[1]}" class="learn-more">{'Book Now' if 'booking.html' in srv[1] else 'Learn More'} <i data-lucide="arrow-right" size="16"></i></a>
    </div>
    """ for srv in data["services"]])

    specific_services_section = f"""
    <section class="section">
        <div class="container">
            <div class="section-header">
                <div class="section-label">WHAT I DO</div>
                <h2>Specific Service Options</h2>
            </div>
            <div class="service-grid" style="grid-template-columns: repeat(2, 1fr);">
                {services_html}
            </div>
        </div>
    </section>
    """

    image_break = f"""
    <section style="position: relative; height: 280px; overflow: hidden;">
        <img src="../assets/images/{data['image']}" alt="{data['schema_name']}" style="width: 100%; height: 100%; object-fit: cover;">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(90deg, rgba(15,41,66,0.85) 0%, rgba(15,41,66,0.4) 60%, rgba(15,41,66,0.1) 100%); display: flex; align-items: center;">
            <div class="container">
                <h2 style="color: white; margin-bottom: 0.75rem; font-size: 2rem;">Professional Workmanship Guaranteed</h2>
                <p style="color: rgba(255,255,255,0.8); font-size: 1.15rem; max-width: 500px;">Every job comes with a 12-month workmanship guarantee and is backed by my Gas Safe registration (#558654).</p>
            </div>
        </div>
    </section>
    """

    process_section = f"""
    <section class="section" style="background: var(--color-primary); color: white;">
        <div class="container">
            <div class="section-header">
                <div class="section-label" style="color: var(--color-accent);">HOW IT WORKS</div>
                <h2 style="color: white;">My Simple Process</h2>
                <p style="color: rgba(255,255,255,0.8); max-width: 600px; margin: 1rem auto; font-size: 1.2rem;">{data['process']}</p>
            </div>
            <div style="text-align: center;">
                <p style="margin-bottom: 2rem; color: rgba(255,255,255,0.9);">I know dealing with plumbing issues is stressful. My goal is to make it as frictionless as possible. From transparent quoting to professional execution.</p>
                <a href="../booking.html" class="btn btn-primary">Book Your Appointment</a>
            </div>
        </div>
    </section>
    """

    faq_html = "".join([f"""
    <div style="background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);">
        <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; color: var(--color-primary);">{faq[0]}</h3>
        <p style="color: var(--text-body); margin: 0; padding-top: 0.5rem;">{faq[1]}</p>
    </div>
    """ for faq in data["faq"]])

    faq_section = f"""
    <section class="section section-gray">
        <div class="container" style="max-width: 800px;">
            <div class="section-header">
                <div class="section-label">FAQS</div>
                <h2>Service Questions Answered</h2>
            </div>
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                {faq_html}
            </div>
        </div>
    </section>
    """
    
    local_section = f"""
    <section class="section">
        <div class="container">
            <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 3rem; align-items: center;">
                <div style="text-align: center;">
                    <h2>Serving Southampton & Beyond</h2>
                    <p style="max-width: 700px; margin: 1rem auto; font-size: 1.1rem; color: var(--text-body);">
                        As a fully mobile Gas Safe registered plumber, I cover the entire Southampton area, including SO14 to SO51 postcodes. Whether you need {data['h1'].lower()} in Bitterne, Shirley, Eastleigh, or Chandler's Ford, I'm your trusted local professional.
                    </p>
                </div>
                <div>
                    <img src="../assets/images/plumber-tools.png" alt="Professional plumbing tools" style="width: 100%; border-radius: var(--radius-lg); box-shadow: var(--shadow-md);">
                </div>
            </div>
        </div>
    </section>
    """

    final_html = (
        custom_head + "\n<body>\n" +
        base_top + "\n" +
        hero_section + "\n" +
        signs_section + "\n" +
        specific_services_section + "\n" +
        image_break + "\n" +
        process_section + "\n" +
        faq_section + "\n" +
        local_section + "\n" +
        base_footer
    )

    write_file(f'/home/antigravity/Projects/Better Call Wes/Website/services/{data["filename"]}', final_html)


for page in pages_data:
    generate_page(page)

print("Service Hub Pages generated successfully.")
