import re

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

index_html = read_file('/home/antigravity/Projects/Better Call Wes/Website/index.html')

# Extract sections
head_match = re.search(r'(<!DOCTYPE html>.*?</header>)', index_html, re.DOTALL)
head_content = head_match.group(1)

hero_match = re.search(r'(<!-- Hero Section -->.*?</section>)', index_html, re.DOTALL)
hero_content = hero_match.group(1)

why_match = re.search(r'(<!-- Why Southampton Trusts Wes -->.*?</section>)', index_html, re.DOTALL)
why_content = why_match.group(1)

services_match = re.search(r'(<!-- Main Services -->.*?</section>)', index_html, re.DOTALL)
services_content = "" # We will rewrite this

about_match = re.search(r'(<!-- Meet Wes -->.*?</section>)', index_html, re.DOTALL)
about_content = about_match.group(1)

reviews_match = re.search(r'(<!-- Customer Testimonials -->.*?</section>)', index_html, re.DOTALL)
reviews_content = reviews_match.group(1)

service_areas_match = re.search(r'(<!-- Service Areas -->.*?</section>)', index_html, re.DOTALL)
service_areas_content = service_areas_match.group(1)

cta_match = re.search(r'(<!-- CTA Section -->.*?</section>)', index_html, re.DOTALL)
cta_content = cta_match.group(1)

footer_match = re.search(r'(<!-- Footer -->.*?</html>)', index_html, re.DOTALL)
footer_content = footer_match.group(1)

# --- Transformations ---

# 1. Update Hero CTAs
hero_content = hero_content.replace(
    '<a href="booking.html" class="btn btn-primary">',
    '<a href="booking.html" class="btn btn-primary">'
)
hero_content = hero_content.replace(
    '<a href="https://wa.me/447700155655" class="btn btn-dark" target="_blank">',
    '<a href="tel:07700155655" class="btn btn-outline" style="background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.3); color: white;">'
)
hero_content = hero_content.replace('WhatsApp Me', 'Call Now')

# 2. Rewrite Why Choose Us with 5 new differentiators
new_why_content = """
    <!-- Why Southampton Trusts Wes -->
    <section class="section">
        <div class="container">
            <div class="section-header">
                <div class="section-label">WHY CHOOSE WES</div>
                <h2>The Southampton Plumbing Difference</h2>
            </div>
            
            <div class="service-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
                <div class="service-card text-center">
                    <div class="service-icon mx-auto"><i data-lucide="video"></i></div>
                    <h3>WhatsApp Video Quoting</h3>
                    <p>Send us a video/photo on WhatsApp for a fast, free quote before we even arrive. Save time and avoid unnecessary callouts.</p>
                </div>
                <div class="service-card text-center">
                    <div class="service-icon mx-auto"><i data-lucide="calendar-check"></i></div>
                    <h3>Online Booking System</h3>
                    <p>Book directly into our diary online at a time that suits you. The most frictionless way to secure your appointment.</p>
                </div>
                <div class="service-card text-center">
                    <div class="service-icon mx-auto"><i data-lucide="tag"></i></div>
                    <h3>Transparent Pricing</h3>
                    <p>Fair, upfront pricing based on our Master Price Guide. What we quote is what you pay—no hidden fees.</p>
                </div>
                <div class="service-card text-center">
                    <div class="service-icon mx-auto"><i data-lucide="shield-check"></i></div>
                    <h3>12-Month Guarantee</h3>
                    <p>Standard 12-Month Workmanship Guarantee on all jobs. Gas Safe registered (#558654) for complete peace of mind.</p>
                </div>
                <div class="service-card text-center" style="grid-column: 1 / -1; max-width: 400px; margin: 0 auto;">
                    <div class="service-icon mx-auto"><i data-lucide="clock"></i></div>
                    <h3>Honest Availability</h3>
                    <p>Appointments booked based on daily availability. No false emergency promises, just reliable, honest service when we can get to you.</p>
                </div>
            </div>
        </div>
    </section>
"""

# 3. New Lead Form / Booking CTA Section
new_booking_cta_content = """
    <!-- Lead Capture / Booking Integration -->
    <section class="section section-gray" id="book-online">
        <div class="container">
            <div style="background: var(--color-primary); color: white; border-radius: var(--radius-xl); padding: 4rem 2rem; display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center; box-shadow: var(--shadow-lg); overflow: hidden; position: relative;">
                <div style="position: absolute; right: -10%; top: -20%; opacity: 0.05; transform: scale(3);">
                    <i data-lucide="calendar"></i>
                </div>
                <div style="position: relative; z-index: 10;">
                    <div class="section-label" style="justify-content: flex-start; color: var(--color-accent); margin-bottom: 1rem;">BOOK IN SECONDS</div>
                    <h2 style="margin-bottom: 1.5rem; color: white;">Skip the Call. Book Online.</h2>
                    <p style="margin-bottom: 2rem; font-size: 1.15rem; color: rgba(255,255,255,0.8);">Our online booking system is the fastest, easiest way to secure your appointment. Choose a time that works perfectly for your schedule.</p>
                    <ul style="list-style: none; padding: 0; margin-bottom: 2.5rem; display: flex; flex-direction: column; gap: 1rem;">
                        <li style="display: flex; align-items: center; gap: 0.75rem;"><i data-lucide="check-circle" style="color: var(--color-accent);"></i> See real-time availability</li>
                        <li style="display: flex; align-items: center; gap: 0.75rem;"><i data-lucide="check-circle" style="color: var(--color-accent);"></i> Instant confirmation</li>
                        <li style="display: flex; align-items: center; gap: 0.75rem;"><i data-lucide="check-circle" style="color: var(--color-accent);"></i> No waiting on hold</li>
                    </ul>
                    <a href="booking.html" class="btn btn-primary" style="font-size: 1.1rem; padding: 18px 40px;">
                        <i data-lucide="calendar"></i> Open Booking Diary
                    </a>
                </div>
                <div style="background: white; border-radius: var(--radius-lg); padding: 3rem; text-align: center; position: relative; z-index: 10;">
                    <h3 style="color: var(--text-dark); margin-bottom: 1rem;">Need a Quote First?</h3>
                    <p style="color: var(--text-body); margin-bottom: 2rem;">Don't want to pay a call-out fee just for a quote? Send us a quick video showing the issue on WhatsApp.</p>
                    <a href="https://wa.me/447700155655" class="btn" style="background: #25D366; color: white; width: 100%;">
                        <i data-lucide="message-circle"></i> Send WhatsApp Video
                    </a>
                </div>
            </div>
        </div>
    </section>
"""

# 4. Rewrite Services Section (Core services first based on implementation plan)
new_services_content = """
    <!-- Core Services -->
    <section class="section">
        <div class="container">
            <div class="section-header">
                <div class="section-label">OUR EXPERTISE</div>
                <h2>Southampton's Plumbing & Heating Specialists</h2>
                <p style="margin-top: 1rem;">We've prioritized our most in-demand services for rapid response and reliable solutions.</p>
            </div>

            <div class="service-grid">
                <!-- Boiler Repair (Core) -->
                <div class="service-card">
                    <div class="service-icon"><i data-lucide="wrench"></i></div>
                    <h3>Boiler Repair & Breakdowns</h3>
                    <p>Fast diagnosis and repair for all makes and models. We carry common parts to fix most faults in a single visit.</p>
                    <div style="font-weight: 600; color: var(--color-accent); margin-bottom: 1rem;">Diagnostics from £100</div>
                    <a href="services/boiler-repair.html" class="learn-more">View Repair Options <i data-lucide="arrow-right" size="16"></i></a>
                </div>

                <!-- Boiler Servicing (Core) -->
                <div class="service-card">
                    <div class="service-icon"><i data-lucide="clipboard-check"></i></div>
                    <h3>Boiler Servicing & Maintenance</h3>
                    <p>Keep your heating efficient and safe. Includes full strip-down services and landlord Gas Safety Certificates (CP12).</p>
                    <div style="font-weight: 600; color: var(--color-accent); margin-bottom: 1rem;">Standard Service £100</div>
                    <a href="services/boiler-servicing.html" class="learn-more">View Maintenance Plans <i data-lucide="arrow-right" size="16"></i></a>
                </div>

                <!-- Plumbing Repairs (Core) -->
                <div class="service-card">
                    <div class="service-icon"><i data-lucide="droplets"></i></div>
                    <h3>Plumbing Repairs</h3>
                    <p>Leaking taps, blocked toilets, faulty valves, and broken showers. Reliable fixes for annoying everyday plumbing problems.</p>
                    <div style="font-weight: 600; color: var(--color-accent); margin-bottom: 1rem;">Labour from £100</div>
                    <a href="services/plumbing-repairs.html" class="learn-more">View Plumbing Services <i data-lucide="arrow-right" size="16"></i></a>
                </div>
            </div>
            
            <div style="margin-top: 4rem; text-align: center;">
                <p style="margin-bottom: 1rem;">Looking for Boiler Installations, Central Heating, or Gas Engineering?</p>
                <a href="services.html" class="btn btn-outline">Explore All Services</a>
            </div>
        </div>
    </section>
"""

# 5. Build FAQ Section
new_faq_content = """
    <!-- FAQ Section with Schema Hooks -->
    <section class="section section-gray">
        <div class="container" style="max-width: 800px;">
            <div class="section-header">
                <div class="section-label">COMMON QUESTIONS</div>
                <h2>Frequently Asked Questions</h2>
            </div>
            
            <div class="faq-accordion" style="display: flex; flex-direction: column; gap: 1rem;">
                <div style="background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);">
                    <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between;">Do you charge VAT? <i data-lucide="chevron-down"></i></h3>
                    <p style="color: var(--text-body); margin: 0; padding-top: 0.5rem;">No, we operate below the VAT threshold, which means the price we quote for labour is the final price. You do not pay an extra 20% VAT on top of our services.</p>
                </div>
                <div style="background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);">
                    <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between;">Do you offer free quotes? <i data-lucide="chevron-down"></i></h3>
                    <p style="color: var(--text-body); margin: 0; padding-top: 0.5rem;">For large jobs like boiler installations, yes. For repairs, we highly recommend our WhatsApp Video Quote service. Send us a video of the problem, and we'll give you a free, accurate estimate before ever stepping foot in your home.</p>
                </div>
                <div style="background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);">
                    <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between;">What areas do you cover? <i data-lucide="chevron-down"></i></h3>
                    <p style="color: var(--text-body); margin: 0; padding-top: 0.5rem;">We serve Southampton and the surrounding areas within the SO postcode region, including Eastleigh, Shirley, Bitterne, Hedge End, and Chandler's Ford.</p>
                </div>
                <div style="background: white; border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-sm);">
                    <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between;">Are you Gas Safe Registered? <i data-lucide="chevron-down"></i></h3>
                    <p style="color: var(--text-body); margin: 0; padding-top: 0.5rem;">Yes. Our Gas Safe Registration number is 558654. We are fully qualified to work on gas boilers, unvented cylinders, and central heating systems.</p>
                </div>
            </div>
        </div>
    </section>
"""

# Re-assemble Homepage in specified order:
# Hero -> Why Choose Us -> Reviews -> Book Online Form -> Services -> About -> Service Areas -> FAQ -> Final CTA -> Footer
final_html = (
    head_content + "\n" +
    hero_content + "\n" +
    new_why_content + "\n" +
    reviews_content + "\n" +
    new_booking_cta_content + "\n" +
    new_services_content + "\n" +
    about_content + "\n" +
    service_areas_content + "\n" +
    new_faq_content + "\n" +
    cta_content + "\n" +
    footer_content
)

write_file('/home/antigravity/Projects/Better Call Wes/Website/index.html', final_html)
print("index.html rewritten successfully.")
