import os
import re

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

index_html = read_file('/home/antigravity/Projects/Better Call Wes/Website/index.html')

head_match = re.search(r'(<!DOCTYPE html>.*?</head>)', index_html, re.DOTALL)
top_match = re.search(r'(<body>\s*<!-- Header -->.*?</header>)', index_html, re.DOTALL)
footer_match = re.search(r'(<!-- Footer -->.*?</html>)', index_html, re.DOTALL)

base_head = head_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/')
base_top = top_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/').replace('href="services/', 'href="/services/').replace('href="about.html"', 'href="../about.html"').replace('href="pricing.html"', 'href="../pricing.html"').replace('href="reviews.html"', 'href="../reviews.html"').replace('href="contact.html"', 'href="../contact.html"').replace('href="services.html"', 'href="../services.html"').replace('href="/"', 'href="../"')
base_footer = footer_match.group(1).replace('href="css/', 'href="../css/').replace('src="assets/', 'src="../assets/').replace('href="services/', 'href="/services/').replace('href="about.html"', 'href="../about.html"').replace('href="pricing.html"', 'href="../pricing.html"').replace('href="reviews.html"', 'href="../reviews.html"').replace('href="contact.html"', 'href="../contact.html"').replace('href="services.html"', 'href="../services.html"').replace('href="/"', 'href="../"')

# 15 Child pages derived from core hubs
child_pages = [
    # Boiler Replacements (Child of Boiler Installation)
    {
        "filename": "combi-boiler-installations.html",
        "parent": ("Boiler Installation", "/services/boiler-installation.html"),
        "title": "Combi Boiler Installations Southampton | Better Call Wes",
        "desc": "Upgrade to a high-efficiency combi boiler. Expert installation in Southampton by a Gas Safe engineer. Free quotes and 12-month guarantee.",
        "h1": "Combi Boiler Installations",
        "schema": "Boiler Installation",
        "price": "£2100",
        "content_p": "Combination (combi) boilers are the most popular heating system in the UK for a reason. They provide heating and hot water on demand without the need for bulky storage cylinders in the loft or airing cupboard. As a Gas Safe registered engineer, I specialise in seamless combi-to-combi swaps and system upgrades across Southampton, installing reliable brands like Worcester Bosch and Vaillant."
    },
    {
        "filename": "boiler-systems.html",
        "parent": ("Boiler Installation", "/services/boiler-installation.html"),
        "title": "System & Regular Boiler Installation Southampton | Better Call Wes",
        "desc": "Expert installation of system and regular boilers in Southampton. Ideal for larger homes with high hot water demand. Gas Safe registered.",
        "h1": "System & Regular Boilers",
        "schema": "Boiler Installation",
        "price": "£2500",
        "content_p": "While combi boilers are great for smaller properties, larger homes with multiple bathrooms often require a System or Regular (Conventional) boiler to meet high hot water demands. I can upgrade your existing traditional setup to a modern, highly efficient equivalent, perfectly balanced to keep up with your family's needs."
    },
    # Central Heating (Child of Central Heating Hub)
    {
        "filename": "power-flushing.html",
        "parent": ("Central Heating", "/services/central-heating.html"),
        "title": "Power Flushing Services Southampton | Better Call Wes",
        "desc": "Restore your central heating efficiency with professional power flushing in Southampton. Removes sludge and cold spots from radiators.",
        "h1": "Professional Power Flushing",
        "schema": "Heating System Cleaning",
        "price": "£440",
        "content_p": "If your radiators have cold spots at the bottom, your boiler is noisy, or your heating bills are climbing, your system is likely choked with black magnetite sludge. A professional power flush forces cleansing chemicals through your pipework at high velocity, stripping away the build-up. This restores heat output, quiets the boiler, and significantly extends the life of your heating system."
    },
    {
        "filename": "radiators.html",
        "parent": ("Central Heating", "/services/central-heating.html"),
        "title": "Radiator Installation & Replacement Southampton | Better Call Wes",
        "desc": "Upgrade your home's heating with new, efficient radiators. Professional sizing, fitting, and TRV installation in Southampton.",
        "h1": "Radiator Installation & Upgrades",
        "schema": "Radiator Installation",
        "price": "£180",
        "content_p": "Old, rusting, or undersized radiators struggle to heat rooms effectively and can drag down the efficiency of a modern boiler. I offer complete radiator replacement services, from standard white panels to modern designer columns and heated towel rails. I also install Thermostatic Radiator Valves (TRVs) to give you room-by-room temperature control."
    },
    {
        "filename": "heating-controls.html",
        "parent": ("Central Heating", "/services/central-heating.html"),
        "title": "Smart Heating Controls & Thermostats Southampton",
        "desc": "Take control of your heating bills with smart thermostat installations. Nest, Hive, and Tado setups by a registered Southampton engineer.",
        "h1": "Smart Heating Controls Installation",
        "schema": "Thermostat Installation",
        "price": "£120",
        "content_p": "Upgrading to a smart thermostat like Hive or Nest is one of the easiest ways to reduce your gas bills. By allowing you to control your heating from your phone and learning your schedule, smart controls ensure you never heat an empty house. I provide professional, hardwired installation integrated perfectly with your existing boiler."
    },
    # Plumbing Repairs (Child of Plumbing Repairs Hub)
    {
        "filename": "toilet-repair.html",
        "parent": ("Plumbing Repairs", "/services/plumbing-repairs.html"),
        "title": "Toilet Repair & Replacement Southampton | Better Call Wes",
        "desc": "Fast, reliable toilet repairs in Southampton. Running toilets, broken flushes, leaks, and blockages sorted quickly with no hidden fees.",
        "h1": "Toilet Repair Services",
        "schema": "Plumbing Repair",
        "price": "£100",
        "content_p": "A constantly running toilet can waste hundreds of litres of water a day, while a broken flush is a major inconvenience. Whether you have a traditional close-coupled toilet, a concealed cistern, or a modern push-button system, we carry the parts to fix faulty fill valves, broken siphons, and stubborn leaks quickly and cleanly."
    },
    {
        "filename": "tap-repair.html",
        "parent": ("Plumbing Repairs", "/services/plumbing-repairs.html"),
        "title": "Tap Repair & Replacement Southampton | Kitchen & Bathroom",
        "desc": "Stop the drip! Professional tap repair and replacement for kitchens and bathrooms in Southampton. Fast response, fair prices.",
        "h1": "Tap Repair & Replacement",
        "schema": "Plumbing Repair",
        "price": "£100",
        "content_p": "Dripping taps are annoying, wasteful, and can eventually stain your sinks or baths. Most dripping taps simply need a new ceramic cartridge or washer. If your taps are severely calcified or you just want an aesthetic upgrade, I also offer complete tap replacements, fitting high-quality mixer, pillar, or boiling water taps."
    },
    {
        "filename": "shower-repair.html",
        "parent": ("Plumbing Repairs", "/services/plumbing-repairs.html"),
        "title": "Shower Repair & Installation Southampton | Better Call Wes",
        "desc": "Electric and mixer shower repairs, replacements, and installations in Southampton. Fix fluctuating temperatures and low pressure.",
        "h1": "Shower Repair & Installation",
        "schema": "Plumbing Repair",
        "price": "£100",
        "content_p": "A cold or weak shower is a terrible way to start the day. If your thermostatic mixer shower is fluctuating wildly in temperature, or your electric shower has lost power, I can diagnose the fault. I replace faulty thermostatic cartridges, fix leaking shower valves, and can install brand new electric or thermostatic shower units."
    },
    {
        "filename": "outdoor-taps.html",
        "parent": ("Plumbing Repairs", "/services/plumbing-repairs.html"),
        "title": "Outdoor Tap Installation Southampton | Better Call Wes",
        "desc": "Professional outside garden tap installation in Southampton. Properly insulated and compliant with water regulations.",
        "h1": "Outdoor Garden Taps",
        "schema": "Plumbing Installation",
        "price": "£100",
        "content_p": "Make gardening and car washing infinitely easier with a professionally installed outdoor tap. I ensure all outside taps are fitted with the legally required double check valves to prevent contaminated water flowing back into your drinking supply. I also provide internal isolation valves so you can safely turn the tap off during freezing winter months."
    },
    {
        "filename": "pipe-leak-repair.html",
        "parent": ("Plumbing Repairs", "/services/plumbing-repairs.html"),
        "title": "Pipe Leak Detection & Repair Southampton | Emergency Plumber",
        "desc": "Rapid response for burst pipes, leaking joints, and water damage in Southampton. Find and fix leaks before they destroy your home.",
        "h1": "Pipe Leak Repair",
        "schema": "Plumbing Emergency Repair",
        "price": "£100",
        "content_p": "A leaking pipe, whether it's a slow drip from a compression joint under the sink or a burst pipe in the ceiling, requires immediate attention to prevent thousands of pounds in structural water damage. I trace leaks to their source, isolate the water supply, and perform permanent, robust repairs on copper, plastic, and lead pipework."
    },
    # Gas Engineering (Child of Gas Services Hub)
    {
        "filename": "landlord-gas-safety-certificates.html",
        "parent": ("Gas Engineering", "/services/gas-services.html"),
        "title": "Landlord Gas Safety Certificates (CP12) Southampton",
        "desc": "Legally required annual CP12 Gas Safety checks for landlords in Southampton. £90 for up to two appliances. Gas Safe registered.",
        "h1": "Landlord Gas Safety Certificates (CP12)",
        "schema": "Gas Safety Inspection",
        "price": "£90",
        "content_p": "If you rent out a property, it is your legal duty under the Gas Safety (Installation and Use) Regulations to ensure all gas appliances, pipework, and flues are maintained in a safe condition. I provide comprehensive annual inspections, conduct tightness tests, verify flue flow, and issue official CP12 digital certificates directly to you and your tenants."
    },
    {
        "filename": "gas-leak-detection.html",
        "parent": ("Gas Engineering", "/services/gas-services.html"),
        "title": "Gas Leak Detection & Repair Southampton | Better Call Wes",
        "desc": "If you smell gas, turn off the meter and call Wes. Professional Gas Safe leak detection and pipework repair in Southampton.",
        "h1": "Gas Leak Detection & Repair",
        "schema": "Gas Emergency Repair",
        "price": "£100",
        "content_p": "Gas leaks are a serious absolute emergency. If your smart meter detects a pressure drop or you smell gas, the National Grid will turn off your supply, but you need a private Gas Safe engineer to find it and fix it. We use advanced sniffing equipment and rigorous tightness testing drops to trace the leak, repair the pipework, and safely reinstate your gas supply."
    },
    {
        "filename": "gas-pipe-installation.html",
        "parent": ("Gas Engineering", "/services/gas-services.html"),
        "title": "Gas Pipe Installation & Rerouting Southampton",
        "desc": "Safe, compliant gas pipework installation and rerouting for home renovations, new kitchens, and boiler moves in Southampton.",
        "h1": "Gas Pipe Installation & Rerouting",
        "schema": "Gas Installation",
        "price": "£100",
        "content_p": "Whether you are moving your boiler to the loft, redesigning your kitchen for a new gas hob, or capping off old redundant fireplace feeds, gas pipework alterations must be strictly compliant with safety sizes and routing regulations. I size gas runs to ensure adequate pressure reaches your appliances and secure the pipework safely."
    },
    {
        "filename": "gas-appliance-servicing.html",
        "parent": ("Gas Engineering", "/services/gas-services.html"),
        "title": "Gas Cooker & Hob Installation Southampton | Better Call Wes",
        "desc": "Professional, certified installation of gas hobs, cookers, and ovens in Southampton. Gas Safe registered engineer.",
        "h1": "Gas Cooker & Hob Installation",
        "schema": "Gas Appliance Installation",
        "price": "£100",
        "content_p": "Purchased a new gas range cooker or built-in hob? It is illegal and highly dangerous to attempt a DIY installation. I will safely disconnect your old appliance, securely connect the new one using approved bayonet fittings or rigid pipework depending on the appliance type, and commission it thoroughly to ensure perfect, safe combustion."
    }
]

def generate_child_page(data):
    # JSON-LD Schema
    schema = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org/",
      "@type": "Service",
      "name": "{data['schema']}",
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
      "areaServed": ["Southampton", "Eastleigh", "Shirley", "Bitterne", "Hedge End"],
      "hasOfferCatalog": {{
        "@type": "OfferCatalog",
        "name": "{data['schema']}",
        "itemListElement": [
          {{
            "@type": "Offer",
            "itemOffered": {{
              "@type": "Service",
              "name": "{data['h1']}"
            }},
            "priceCurrency": "GBP",
            "price": "{data['price'].replace('£','')}"
          }}
        ]
      }}
    }}
    </script>
    """

    custom_head = base_head.replace('<title>Better Call Wes - Your Local Southampton Plumber | Gas Safe Registered</title>', f'<title>{data["title"]}</title>')
    custom_head = re.sub(r'<meta name="description".*?>', f'<meta name="description" content="{data["desc"]}">', custom_head)
    custom_head = custom_head.replace('</head>', f'{schema}\n</head>')

    hero_section = f"""
    <section class="hero" style="background: var(--color-primary); min-height: 40vh; padding-top: 150px; padding-bottom: 80px;">
        <div class="container">
            <div class="hero-content" style="max-width: 800px; margin: 0 auto; text-align: center;">
                <h1 style="color: white; margin-bottom: 1.5rem;">{data['h1']} in Southampton</h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; margin-bottom: 2rem;">{data['content_p']}</p>
                <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                    <a href="../booking.html" class="btn btn-primary"><i data-lucide="calendar"></i> Book Online</a>
                    <a href="https://wa.me/447700155655" class="btn btn-outline" style="background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.3); color: white;"><i data-lucide="video"></i> WhatsApp Quote</a>
                </div>
            </div>
        </div>
    </section>
    """

    warning_section = f"""
    <section class="section section-gray">
        <div class="container">
            <div class="section-header">
                <div class="section-label">WARNING SIGNS</div>
                <h2>When to Call a Professional for {data['h1']}</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem;">
                <div style="background: white; padding: 2rem; border-radius: var(--radius-md); box-shadow: var(--shadow-sm); border-top: 4px solid var(--color-accent);">
                    <h3 style="margin-bottom: 1rem; color: var(--color-primary);">Unexpected Noises or Leaks</h3>
                    <p style="color: var(--text-body);">If the system is making strange noises or you notice water pooling, it's time to get a professional assessment before it causes property damage.</p>
                </div>
                <div style="background: white; padding: 2rem; border-radius: var(--radius-md); box-shadow: var(--shadow-sm); border-top: 4px solid var(--color-accent);">
                    <h3 style="margin-bottom: 1rem; color: var(--color-primary);">Loss of Performance</h3>
                    <p style="color: var(--text-body);">A drop in pressure, cold spots, or a system that takes too long to respond usually indicates an underlying issue that needs expert attention.</p>
                </div>
            </div>
        </div>
    </section>
    """

    guarantee_section = f"""
    <section style="position: relative; height: 280px; overflow: hidden;">
        <img src="../assets/images/copper-pipework.webp" alt="{data['h1']}" style="width: 100%; height: 100%; object-fit: cover;" loading="lazy" decoding="async">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(90deg, rgba(15,41,66,0.85) 0%, rgba(15,41,66,0.4) 60%, rgba(15,41,66,0.1) 100%); display: flex; align-items: center;">
            <div class="container">
                <h2 style="color: white; margin-bottom: 0.75rem; font-size: 2rem;">Professional Workmanship Guaranteed</h2>
                <p style="color: rgba(255,255,255,0.8); font-size: 1.15rem; max-width: 500px;">Every {data['h1'].lower()} job comes with a 12-month workmanship guarantee and is backed by my Gas Safe registration (#558654).</p>
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
                <p style="color: rgba(255,255,255,0.8); max-width: 600px; margin: 1rem auto; font-size: 1.2rem;">1. Send a WhatsApp Video or Book Online. 2. I diagnose or quote. 3. Fast, clean execution. 4. 12-month guarantee.</p>
            </div>
            <div style="text-align: center;">
                <p style="margin-bottom: 2rem; color: rgba(255,255,255,0.9);">I know dealing with plumbing issues is stressful. My goal is to make it as frictionless as possible. From transparent quoting to professional execution.</p>
                <a href="../booking.html" class="btn btn-primary">Book Your Appointment</a>
            </div>
        </div>
    </section>
    """

    faq_section = f"""
    <section class="section section-gray">
        <div class="container" style="max-width: 800px;">
            <div class="section-header">
                <div class="section-label">FAQS</div>
                <h2>Questions about {data['h1']}</h2>
            </div>
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div style="background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);">
                    <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; color: var(--color-primary);">How much does it cost?</h3>
                    <p style="color: var(--text-body); margin: 0; padding-top: 0.5rem;">Pricing starts from {data['price']} depending on the complexity of the job. I always provide a clear, upfront quote before starting any work so there are no surprises.</p>
                </div>
                <div style="background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);">
                    <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; color: var(--color-primary);">Do you offer a guarantee?</h3>
                    <p style="color: var(--text-body); margin: 0; padding-top: 0.5rem;">Yes, all workmanship is backed by a 12-month guarantee. Any parts supplied also come with their standard manufacturer warranty.</p>
                </div>
            </div>
        </div>
    </section>
    """

    coverage_section = f"""
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
                    <img src="../assets/images/plumber-tools.webp" alt="Professional plumbing tools" style="width: 100%; border-radius: var(--radius-lg); box-shadow: var(--shadow-md);" loading="lazy" decoding="async">
                </div>
            </div>
        </div>
    </section>
    """

    final_html = (
        custom_head + "\n" +
        base_top + "\n" +
        hero_section + "\n" +
        warning_section + "\n" +
        guarantee_section + "\n" +
        process_section + "\n" +
        faq_section + "\n" +
        coverage_section + "\n" +
        base_footer
    )

    write_file(f'/home/antigravity/Projects/Better Call Wes/Website/services/{data["filename"]}', final_html)

for page in child_pages:
    generate_child_page(page)

print("Child Service Pages generated successfully.")
