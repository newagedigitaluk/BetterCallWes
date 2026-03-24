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
top_match = re.search(r'(<body>\s*<!-- Top Bar -->.*?</header>)', index_html, re.DOTALL)
footer_match = re.search(r'(<!-- CTA Section -->.*?</html>)', index_html, re.DOTALL)

base_head = head_match.group(1)
base_top = top_match.group(1).replace('href="services/', 'href="services/').replace('href="about.html"', 'href="about.html"').replace('href="pricing.html"', 'href="pricing.html"').replace('href="reviews.html"', 'href="reviews.html"').replace('href="contact.html"', 'href="contact.html"').replace('href="services.html"', 'href="services.html"')
base_footer = footer_match.group(1).replace('href="services/', 'href="services/')

pages = {}

# 1. About Page
about_content = """
    <section class="hero" style="background: var(--color-primary); padding-top: 150px; padding-bottom: 80px;">
        <div class="container text-center">
            <h1 style="color: white; margin-bottom: 1.5rem; font-size: 3rem;">About Better Call Wes</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; max-width: 800px; margin: 0 auto;">Local, honest, and reliable plumbing & heating services from a true Southampton independent.</p>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center;">
                <div>
                    <img src="assets/images/wes-profile.png" alt="Wes - Your local Southampton plumber" style="border-radius: var(--radius-lg); box-shadow: var(--shadow-lg);">
                </div>
                <div>
                    <div class="section-label" style="justify-content: flex-start;">MY STORY</div>
                    <h2 style="margin-bottom: 1.5rem;">Hi, I'm Wes</h2>
                    <p style="color: var(--text-body); font-size: 1.1rem; line-height: 1.8; margin-bottom: 1.5rem;">I started <strong>Better Call Wes</strong> because I saw a need in Southampton for a truly honest, transparent plumbing service. After spending over a decade in the trade, I got tired of seeing homeowners hit with hidden fees, unexplained charges, and engineers who didn't show up on time.</p>
                    <p style="color: var(--text-body); font-size: 1.1rem; line-height: 1.8; margin-bottom: 1.5rem;">As a sole trader and fully certified Gas Safe engineer (#558654), I handle every single job myself. From the first WhatsApp message to the final tighten of a valve, you deal directly with me. No call centers, no salesmen, just professional, straightforward plumbing.</p>
                    
                    <div style="background: var(--bg-color); padding: 1.5rem; border-radius: var(--radius-md); border-left: 4px solid var(--color-accent); margin-top: 2rem;">
                        <h4 style="margin-bottom: 0.5rem;"><i data-lucide="check-circle" style="color: var(--color-accent); width: 18px; display: inline-block; vertical-align: bottom;"></i> My Personal Promise</h4>
                        <p style="color: var(--text-body); margin: 0;">I will never recommend a repair you don't need, I will always charge exactly what is on my Master Price Guide, and I will always leave your home as clean as I found it.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="section section-gray">
        <div class="container text-center">
            <h2 style="margin-bottom: 3rem;">My Core Qualifications</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem;">
                <div style="background: white; padding: 2rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
                    <i data-lucide="flame" style="width: 48px; height: 48px; color: var(--color-primary); margin-bottom: 1rem;"></i>
                    <h3>Gas Safe Registered</h3>
                    <p style="color: var(--text-body);">Register Number: 558654. Fully qualified to work safely and legally on gas appliances.</p>
                </div>
                <div style="background: white; padding: 2rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
                    <i data-lucide="shield-check" style="width: 48px; height: 48px; color: var(--color-primary); margin-bottom: 1rem;"></i>
                    <h3>Fully Insured</h3>
                    <p style="color: var(--text-body);">Comprehensive public liability insurance to protect your property while I work.</p>
                </div>
                <div style="background: white; padding: 2rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
                    <i data-lucide="award" style="width: 48px; height: 48px; color: var(--color-primary); margin-bottom: 1rem;"></i>
                    <h3>10+ Years Experience</h3>
                    <p style="color: var(--text-body);">Over a decade of hands-on fault finding, installations, and complex plumbing repairs.</p>
                </div>
            </div>
        </div>
    </section>
"""
pages['about.html'] = {
    'title': 'About Better Call Wes | Your Local Southampton Plumber',
    'desc': 'Learn more about Wes, an independent, Gas Safe registered plumber serving Southampton with transparent pricing and honest advice.',
    'content': about_content
}

# 2. Contact Page
contact_content = """
    <section class="hero" style="background: var(--color-primary); padding-top: 150px; padding-bottom: 80px;">
        <div class="container text-center">
            <h1 style="color: white; margin-bottom: 1.5rem; font-size: 3rem;">Contact Me</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; max-width: 800px; margin: 0 auto;">Book online instantly, send a WhatsApp for a free quote, or give me a call.</p>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4rem;">
                <div>
                    <h2 style="margin-bottom: 1.5rem;">Get in Touch</h2>
                    <p style="color: var(--text-body); margin-bottom: 2rem;">I aim to respond to all inquiries within an hour during business hours. If it's an emergency, please call directly.</p>
                    
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <a href="https://wa.me/447700155655" style="display: flex; align-items: flex-start; gap: 1rem; text-decoration: none; color: inherit;">
                            <div style="background: #25D366; color: white; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <i data-lucide="video"></i>
                            </div>
                            <div>
                                <h4 style="margin-bottom: 0.25rem;">WhatsApp Video Quote (Fastest)</h4>
                                <p style="color: var(--text-body);">Send a video of the problem for an accurate, free quote.</p>
                            </div>
                        </a>
                        
                        <a href="tel:07700155655" style="display: flex; align-items: flex-start; gap: 1rem; text-decoration: none; color: inherit;">
                            <div style="background: var(--color-primary); color: white; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <i data-lucide="phone"></i>
                            </div>
                            <div>
                                <h4 style="margin-bottom: 0.25rem;">Call Me</h4>
                                <p style="color: var(--text-body);">07700 155 655 (Mon-Fri 8am - 6pm)</p>
                            </div>
                        </a>

                        <a href="mailto:wes@bettercallwes.co.uk" style="display: flex; align-items: flex-start; gap: 1rem; text-decoration: none; color: inherit;">
                            <div style="background: var(--bg-color); color: var(--color-primary); width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <i data-lucide="mail"></i>
                            </div>
                            <div>
                                <h4 style="margin-bottom: 0.25rem;">Email</h4>
                                <p style="color: var(--text-body);">wes@bettercallwes.co.uk</p>
                            </div>
                        </a>
                    </div>
                </div>

                <div style="background: white; padding: 3rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-lg);">
                    <h3 style="margin-bottom: 1.5rem;">Or Book Directly in My Diary</h3>
                    <p style="color: var(--text-body); margin-bottom: 2rem;">Skip the back-and-forth and secure your appointment slot instantly online.</p>
                    <a href="booking.html" class="btn btn-primary" style="width: 100%; text-align: center; display: block; padding: 18px;"><i data-lucide="calendar"></i> Open Booking System</a>
                </div>
            </div>
        </div>
    </section>

    <section class="section section-gray">
        <div class="container text-center">
            <h2 style="margin-bottom: 2rem;">Service Area</h2>
            <p style="max-width: 600px; margin: 0 auto 2rem; color: var(--text-body);">I provide fully mobile plumbing and heating services across Southampton and all surrounding SO postcodes.</p>
            <iframe width="100%" height="450" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.com/maps?q=Southampton,+UK&t=&z=11&ie=UTF8&iwloc=&output=embed" style="border-radius: var(--radius-lg); box-shadow: var(--shadow-md); max-width: 1000px; margin: 0 auto;"></iframe>
        </div>
    </section>
"""
pages['contact.html'] = {
    'title': 'Contact Better Call Wes | Plumber in Southampton',
    'desc': 'Contact Better Call Wes for plumbing and heating in Southampton. Call 07700 155 655 or send a WhatsApp video for a fast, free quote.',
    'content': contact_content,
    'schema': """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "LocalBusiness",
      "name": "Better Call Wes",
      "image": "https://bettercallwes.co.uk/assets/logo.jpg",
      "@id": "https://bettercallwes.co.uk/",
      "url": "https://bettercallwes.co.uk/",
      "telephone": "07700155655",
      "address": {
        "@type": "PostalAddress",
        "addressLocality": "Southampton",
        "addressRegion": "Hampshire",
        "addressCountry": "UK"
      },
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": 50.9097,
        "longitude": -1.4044
      },
      "openingHoursSpecification": {
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": [
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday"
        ],
        "opens": "08:00",
        "closes": "18:00"
      },
      "sameAs": [
        "https://www.facebook.com/bettercallwes",
        "https://www.instagram.com/bettercallwes"
      ]
    }
    </script>
    """
}

# 3. Pricing Page
pricing_content = """
    <section class="hero" style="background: var(--color-primary); padding-top: 150px; padding-bottom: 80px;">
        <div class="container text-center">
            <h1 style="color: white; margin-bottom: 1.5rem; font-size: 3rem;">Master Price Guide</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; max-width: 800px; margin: 0 auto;">Honest, transparent, upfront pricing. What you see is what you pay. No hidden fees.</p>
        </div>
    </section>

    <section class="section">
        <div class="container" style="max-width: 900px;">
            <div style="background: var(--color-accent); color: white; padding: 1.5rem; border-radius: var(--radius-md); margin-bottom: 3rem; display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check-circle"></i> Transparent Upfront Pricing</div>
                <div style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check-circle"></i> £100 Minimum Labour (1hr)</div>
                <div style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check-circle"></i> Free Boiler Install Quotes</div>
            </div>

            <h2 style="margin-bottom: 1.5rem;">1. Boiler Servicing & Compliance</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 3rem; background: white; box-shadow: var(--shadow-sm); border-radius: var(--radius-md); overflow: hidden;">
                <tr style="background: var(--bg-color); border-bottom: 2px solid #ddd; text-align: left;">
                    <th style="padding: 1rem;">Service Type</th>
                    <th style="padding: 1rem; width: 200px;">Price</th>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Standard Boiler Service</td>
                    <td style="padding: 1rem; font-weight: 600;">£100.00</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Full Strip-down Service (Deep diagnostic/clean)</td>
                    <td style="padding: 1rem; font-weight: 600;">£160.00</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Back Boiler Service</td>
                    <td style="padding: 1rem; font-weight: 600;">£120.00</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Gas Safety Certificate (LLGS / CP12)</td>
                    <td style="padding: 1rem; font-weight: 600;">£90.00 (up to 2 appliances)</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Additional Gas Appliance (Hob/Fire)</td>
                    <td style="padding: 1rem; font-weight: 600;">£20.00 - £50.00 per item</td>
                </tr>
                <tr>
                    <td style="padding: 1rem;">System Health Check (Inc. Water Test)</td>
                    <td style="padding: 1rem; font-weight: 600;">£130.00</td>
                </tr>
            </table>

            <h2 style="margin-bottom: 1.5rem;">2. Common Boiler Repairs (Labour + Parts Guide)</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 3rem; background: white; box-shadow: var(--shadow-sm); border-radius: var(--radius-md); overflow: hidden;">
                <tr style="background: var(--bg-color); border-bottom: 2px solid #ddd; text-align: left;">
                    <th style="padding: 1rem;">Task Description</th>
                    <th style="padding: 1rem; width: 250px;">Typical Total Bill</th>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Boiler Diagnostic Fee (First Hour Only)</td>
                    <td style="padding: 1rem; font-weight: 600;">£100.00</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Diverter Valve / 3-Port Valve Replacement</td>
                    <td style="padding: 1rem; font-weight: 600;">£180.00 - £250.00</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Expansion Vessel Recharge / Core replacement</td>
                    <td style="padding: 1rem; font-weight: 600;">£100.00 - £160.00</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Faulty Fan / Pump / Auto-Air Vent Replacement</td>
                    <td style="padding: 1rem; font-weight: 600;">£120.00 - £280.00</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">PCB Replacement (Diagnostics + Part)</td>
                    <td style="padding: 1rem; font-weight: 600;">£250.00 - £350.00</td>
                </tr>
            </table>

            <h2 style="margin-bottom: 1.5rem;">3. General Plumbing Repairs</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 3rem; background: white; box-shadow: var(--shadow-sm); border-radius: var(--radius-md); overflow: hidden;">
                <tr style="background: var(--bg-color); border-bottom: 2px solid #ddd; text-align: left;">
                    <th style="padding: 1rem;">Task Description</th>
                    <th style="padding: 1rem; width: 200px;">Typical Labour Only</th>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Tap Repair / Replacement (Standard Mixer)</td>
                    <td style="padding: 1rem; font-weight: 600;">£100.00 + Parts</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Toilet Flush/Fill Valve Service</td>
                    <td style="padding: 1rem; font-weight: 600;">£100.00 + Parts</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 1rem;">Toilet Blockage Removal (Standard Internal)</td>
                    <td style="padding: 1rem; font-weight: 600;">£100.00</td>
                </tr>
                <tr>
                    <td style="padding: 1rem;">Washing Machine / Dishwasher Installation</td>
                    <td style="padding: 1rem; font-weight: 600;">£100.00</td>
                </tr>
            </table>

            <div style="text-align: center; margin-top: 4rem;">
                <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">Don't see your repair listed? Send me a WhatsApp video for a rapid exact quote.</p>
                <a href="https://wa.me/447700155655" class="btn" style="background: #25D366; color: white;"><i data-lucide="video"></i> Get a Free Video Quote</a>
            </div>
        </div>
    </section>
"""
pages['pricing.html'] = {
    'title': 'Plumbing & Boiler Repair Prices | Better Call Wes',
    'desc': 'Transparent, upfront plumbing and heating prices in Southampton. Master Price Guide for boiler repairs, servicing, and plumbing fixes.',
    'content': pricing_content
}

# 4. Reviews Page
reviews_content = """
    <section class="hero" style="background: var(--color-primary); padding-top: 150px; padding-bottom: 80px;">
        <div class="container text-center">
            <h1 style="color: white; margin-bottom: 1.5rem; font-size: 3rem;">Customer Reviews</h1>
            <div class="rating-badge mx-auto" style="border-color: rgba(255,255,255,0.2); justify-content: center; display: inline-flex; margin-bottom: 1.5rem;">
                <span class="stars">★★★★★</span>
                <span style="color: white;">4.9 Average Rating from 200+ Reviews</span>
            </div>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; max-width: 800px; margin: 0 auto;">See why homeowners across Southampton trust Better Call Wes for their plumbing and heating needs.</p>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 2rem;">
                <!-- Review 1 -->
                <div class="service-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="display: flex; gap: 0.25rem; color: #FFB800;">★★★★★</div>
                        <span style="font-size: 0.85rem; color: var(--text-light);">2 weeks ago</span>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Boiler Repair</h4>
                    <p style="font-style: italic; margin-bottom: 1.5rem; color: var(--text-body);">"Wes came out the same day our boiler broke down. He diagnosed the problem quickly and had it fixed within the hour. Really reasonable price too. Would definitely recommend!"</p>
                    <div style="font-weight: 600; color: var(--text-dark);">Sarah M.</div>
                    <div style="font-size: 0.9rem; color: var(--text-light);">Shirley, Southampton</div>
                </div>

                <!-- Review 2 -->
                <div class="service-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="display: flex; gap: 0.25rem; color: #FFB800;">★★★★★</div>
                        <span style="font-size: 0.85rem; color: var(--text-light);">1 month ago</span>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Tap and Toilet Repairs</h4>
                    <p style="font-style: italic; margin-bottom: 1.5rem; color: var(--text-body);">"Needed a few small plumbing jobs done that other plumbers wouldn't touch. Wes was happy to help and did a brilliant job. Really tidy worker and explained everything clearly."</p>
                    <div style="font-weight: 600; color: var(--text-dark);">James T.</div>
                    <div style="font-size: 0.9rem; color: var(--text-light);">Bitterne, Southampton</div>
                </div>

                <!-- Review 3 -->
                <div class="service-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="display: flex; gap: 0.25rem; color: #FFB800;">★★★★★</div>
                        <span style="font-size: 0.85rem; color: var(--text-light);">2 months ago</span>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Annual Boiler Service</h4>
                    <p style="font-style: italic; margin-bottom: 1.5rem; color: var(--text-body);">"Had Wes service our boiler – very thorough, on time, and upfront pricing saved us money. Already booked him for next year. Highly recommend for anyone in Southampton."</p>
                    <div style="font-weight: 600; color: var(--text-dark);">Helen W.</div>
                    <div style="font-size: 0.9rem; color: var(--text-light);">Woolston, Southampton</div>
                </div>
                
                <!-- Review 4 -->
                <div class="service-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="display: flex; gap: 0.25rem; color: #FFB800;">★★★★★</div>
                        <span style="font-size: 0.85rem; color: var(--text-light);">3 months ago</span>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Smart Thermostat Fitting</h4>
                    <p style="font-style: italic; margin-bottom: 1.5rem; color: var(--text-body);">"Great service installing my new Hive thermostat. Wes walked me through how to use the app before leaving. Very professional setup."</p>
                    <div style="font-weight: 600; color: var(--text-dark);">David R.</div>
                    <div style="font-size: 0.9rem; color: var(--text-light);">Eastleigh</div>
                </div>

                <!-- Review 5 -->
                <div class="service-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="display: flex; gap: 0.25rem; color: #FFB800;">★★★★★</div>
                        <span style="font-size: 0.85rem; color: var(--text-light);">3 months ago</span>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Leak Repair</h4>
                    <p style="font-style: italic; margin-bottom: 1.5rem; color: var(--text-body);">"Found a leak under my kitchen sink on a Friday evening. Wes came round first thing Saturday and sorted it with a new trap. Real lifesaver."</p>
                    <div style="font-weight: 600; color: var(--text-dark);">Emma P.</div>
                    <div style="font-size: 0.9rem; color: var(--text-light);">Chandler's Ford</div>
                </div>
                
                <!-- Review 6 -->
                <div class="service-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="display: flex; gap: 0.25rem; color: #FFB800;">★★★★★</div>
                        <span style="font-size: 0.85rem; color: var(--text-light);">4 months ago</span>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Landlord Certificate</h4>
                    <p style="font-style: italic; margin-bottom: 1.5rem; color: var(--text-body);">"I use Wes for all my rental properties now. He liaises directly with the tenants, sorts the CP12s on time, and invoices clearly. Zero hassle."</p>
                    <div style="font-weight: 600; color: var(--text-dark);">Tom K.</div>
                    <div style="font-size: 0.9rem; color: var(--text-light);">Southampton</div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 4rem;">
                <h3 style="margin-bottom: 1rem;">Experience the Service for Yourself</h3>
                <a href="booking.html" class="btn btn-primary">Book an Appointment</a>
            </div>
        </div>
    </section>
"""
pages['reviews.html'] = {
    'title': 'Customer Reviews | Better Call Wes Southampton',
    'desc': 'Read 5-star reviews from Southampton homeowners who trust Better Call Wes for transparent, reliable plumbing and heating services.',
    'content': reviews_content
}

for filename, data in pages.items():
    title = data['title']
    desc = data['desc']
    schema = data.get('schema', '')
    content = data['content']
    
    custom_head = base_head.replace('<title>Better Call Wes - Your Local Southampton Plumber | Gas Safe Registered</title>', f'<title>{title}</title>')
    custom_head = re.sub(r'<meta name="description".*?>', f'<meta name="description" content="{desc}">', custom_head)
    if schema:
        custom_head = custom_head.replace('</head>', f'{schema}\n</head>')
        
    final_html = (
        custom_head + "\n<body>\n" +
        base_top + "\n" +
        content + "\n" +
        base_footer
    )
    
    write_file(f'/home/antigravity/Projects/Better Call Wes/Website/{filename}', final_html)

print("Trust pages (About, Contact, Pricing, Reviews) generated successfully.")
