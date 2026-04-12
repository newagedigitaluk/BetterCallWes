"""
update_location_pages.py

Rewrites the unique content sections of each location page so that every
page has genuinely distinct text, meta data, and FAQs.  This resolves the
"Discovered – currently not indexed" issue in Google Search Console caused
by near-identical templated content across all location pages.

Sections updated per page:
  - <title>
  - <meta name="description">
  - Hero <h1>
  - Hero sub-paragraph
  - Local-expertise h3 + 3 paragraphs
  - FAQ section (inserted before CTA) + FAQ JSON-LD schema
"""

import re
from pathlib import Path

WEBSITE_DIR = Path(__file__).parent.parent.parent / "Website"

# ---------------------------------------------------------------------------
# Unique content per area
# ---------------------------------------------------------------------------
LOCATION_DATA = {
    "bassett": {
        "name": "Bassett",
        "title": "Plumber & Heating Engineer in Bassett, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Bassett, Southampton. Boiler repairs, servicing and central heating for Bassett's family homes — same-day response available. Call Wes: 07700 155 655.",
        "h1": "Plumber & Heating Engineer Serving Bassett",
        "hero_p": "Bassett is home to some of Southampton's best-kept family properties, and keeping the heating and plumbing in good order is part of that. Wes covers all of Bassett with no call-out fee during normal hours and same-day availability for urgent jobs.",
        "h3": "Experienced With Bassett's Family Homes",
        "p1": "Bassett is one of Southampton's more established northern suburbs, with a mix of 1930s and post-war detached and semi-detached homes. Many properties along Bassett Avenue, Brownhill Road and the Bassett Green area still have original copper pipework and older conventional heating systems — the kind of work I deal with every week.",
        "p2": "If your boiler hasn't been serviced in a few years, or you're getting cold spots on radiators, there's a good chance the system needs attention. Older Bassett properties often have gravity-fed systems and open-vented boilers that require an engineer who understands them, rather than someone used only to modern combis.",
        "p3": "I cover the whole Bassett area and can usually attend the same day for urgent callouts. Gas Safe registered (reg. 558654), with transparent pricing and no surprise invoices — you'll know the cost before I start.",
        "faqs": [
            {
                "q": "Do you cover Bassett Green and the Brownhill Road area?",
                "a": "Yes — I cover the whole of Bassett including Bassett Green, Bassett Avenue, Brownhill Road and all surrounding streets in the north Southampton SO16 postcode area. I'm usually able to attend within a day for non-emergency work, and the same day for urgent heating or plumbing issues."
            },
            {
                "q": "My Bassett home has a gravity-fed heating system — can you work on it?",
                "a": "Absolutely. Gravity-fed and open-vented systems are common in older Bassett properties and I'm very familiar with them. Whether you need a repair, a system flush, or advice on upgrading to a modern combi, I can assess and advise without pushing you toward unnecessary work."
            },
            {
                "q": "How much does a boiler service cost in Bassett?",
                "a": "A standard annual boiler service is £85 including a full safety check and efficiency assessment. If your boiler is due a service, it's the single best thing you can do to extend its life and keep it running safely through winter. I carry out services across Bassett throughout the week."
            },
        ],
    },
    "bitterne": {
        "name": "Bitterne",
        "title": "Plumber & Heating Engineer in Bitterne, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Bitterne, Southampton SO18. Boiler repairs, central heating and plumbing for Bitterne homes — same-day response for urgent callouts. 07700 155 655.",
        "h1": "Your Local Plumber & Gas Engineer in Bitterne",
        "hero_p": "Bitterne is one of the most active areas I cover — a busy residential community on the eastern side of Southampton with a real mix of housing types and ages. If you've got a boiler problem or a plumbing issue, I can usually be with you the same day.",
        "h3": "Experienced With Bitterne's Mix of Housing",
        "p1": "Bitterne has a varied mix of housing — from 1930s and 1950s semi-detached properties to more modern developments off Mousehole Lane and along the Itchen waterfront. Many of the older homes have had several boiler changes over the decades, and I'm familiar with the common issues that come with ageing pipework and corroded system components.",
        "p2": "I carry out a lot of work in and around the Bitterne Precinct area and the residential streets running down toward the River Itchen. Sludge build-up in older systems is one of the most common things I find — a power flush usually makes a significant difference to heating efficiency and often cures cold radiators that have been a problem for years.",
        "p3": "Based in Southampton, I can reach most of Bitterne quickly for urgent callouts. Gas Safe registered (reg. 558654), no call-out fee during normal hours, and a clear upfront quote before any work begins.",
        "faqs": [
            {
                "q": "Do you cover the SO18 postcode area?",
                "a": "Yes — Bitterne and the surrounding SO18 postcode is one of my most regular areas. I cover all streets in and around Bitterne including Mousehole Lane, West End Road, and the residential areas close to the River Itchen."
            },
            {
                "q": "My radiators are cold at the top but warm at the bottom — what does that mean?",
                "a": "Cold at the top and warm at the bottom usually means trapped air in the system — the radiators need bleeding. If bleeding doesn't fix it, or it keeps happening, there may be a larger issue with the system pressure or a faulty pump. I can diagnose and resolve this in a single visit in most cases."
            },
            {
                "q": "Can you fix a boiler that keeps losing pressure in Bitterne?",
                "a": "Yes — this is one of the most common jobs I attend across Bitterne and east Southampton. A boiler that repeatedly loses pressure usually has a small leak somewhere in the system, often at a radiator valve or a concealed joint. I'll find it, fix it, and re-pressurise the system in one visit."
            },
        ],
    },
    "bitterne-manor": {
        "name": "Bitterne Manor",
        "title": "Plumber & Heating Engineer in Bitterne Manor | Better Call Wes",
        "meta": "Gas Safe plumber in Bitterne Manor, Southampton. Specialist in older properties — boiler repairs, heating and pipework for Victorian and Edwardian homes. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Bitterne Manor",
        "hero_p": "Bitterne Manor is one of Southampton's older residential areas, with a mix of Victorian, Edwardian and inter-war properties close to the River Itchen. Older homes need an engineer who understands older systems — that's exactly the kind of work I do every week.",
        "h3": "Older Homes, Older Plumbing — I Know What to Look For",
        "p1": "Bitterne Manor sits close to the eastern bank of the Itchen and contains some of the area's oldest housing stock. Victorian and Edwardian properties here often have original cast iron pipework, lead sections, or gravity-fed heating systems that require specific knowledge to work on safely and effectively.",
        "p2": "I regularly attend properties near Bitterne Manor Road and Manor Farm Road. Lead pipe replacement is something I carry out fairly often in this area — if your property was built before the 1970s, it's worth getting the pipework checked, particularly the section from the street into the house.",
        "p3": "Gas Safe registered (reg. 558654), covering Bitterne Manor as part of my core east Southampton area. No call-out fee during normal hours, honest advice about what your system actually needs, and a clear quote before I start.",
        "faqs": [
            {
                "q": "My property in Bitterne Manor was built before 1950 — what plumbing issues should I be aware of?",
                "a": "Pre-1950 properties in Bitterne Manor often have lead pipework on the water supply side, cast iron waste pipes, and gravity-fed hot water systems. Lead pipes are the most important to address — I can inspect and replace these, and advise on the most cost-effective approach for your property."
            },
            {
                "q": "Do you carry out boiler replacements in Bitterne Manor?",
                "a": "Yes — including fitting a new combi boiler to replace an older conventional system or back boiler. Many Bitterne Manor properties are good candidates for upgrading to a modern combi, which removes the need for a hot water tank and usually improves efficiency significantly."
            },
            {
                "q": "How quickly can you attend an emergency in Bitterne Manor?",
                "a": "For genuine emergencies such as a gas leak or burst pipe, I aim to attend as quickly as possible. For urgent heating failures — no heating or hot water — I can usually attend the same day. Bitterne Manor is well within my regular coverage area."
            },
        ],
    },
    "bitterne-park": {
        "name": "Bitterne Park",
        "title": "Plumber & Heating Engineer in Bitterne Park | Better Call Wes",
        "meta": "Gas Safe plumber serving Bitterne Park, Southampton. Boiler repairs, servicing and central heating for Bitterne Park's family homes and period properties. 07700 155 655.",
        "h1": "Plumber & Heating Engineer in Bitterne Park",
        "hero_p": "Bitterne Park is one of Southampton's most sought-after residential neighbourhoods — a mix of large Edwardian and 1930s homes on leafy streets near Cobden Bridge. Whether it's a boiler breakdown or a plumbing issue that's been getting worse, I cover the whole area and can usually respond the same day.",
        "h3": "Trusted By Bitterne Park Homeowners",
        "p1": "Bitterne Park has a distinctive mix of larger Edwardian and 1930s semi-detached homes, particularly around the tree-lined streets near Cobden Bridge and along Cobden Avenue. These properties often have older heating systems that have been modified over the years — which can create complications when something goes wrong.",
        "p2": "One of the most common jobs I get called for in Bitterne Park is a boiler that's losing pressure or a system with cold radiators at the top — often a sign of air locks or sludge build-up that's been developing for years. In most cases, bleeding the radiators and a system flush resolves it without a major repair bill.",
        "p3": "Gas Safe registered (reg. 558654), with no call-out charge during normal hours. I always explain what I've found before doing any work, so you're never committed to a repair you weren't expecting. Serving Bitterne Park and all surrounding SO18 postcodes.",
        "faqs": [
            {
                "q": "Do you work on Edwardian and 1930s properties in Bitterne Park?",
                "a": "Yes — period properties make up a large proportion of the homes I work on in Bitterne Park. I'm experienced with gravity-fed systems, older copper pipework, and the kind of modified heating layouts common in homes of this era."
            },
            {
                "q": "Can you carry out a power flush on a Bitterne Park property?",
                "a": "Yes. Power flushing is one of the most effective ways to restore heating efficiency in older systems. If you have radiators that are cooler than they should be or a heating system that takes a long time to warm up, a power flush often makes a significant improvement."
            },
            {
                "q": "What's included in your boiler service?",
                "a": "An annual boiler service includes a full safety inspection, cleaning of internal components, a flue integrity check, a gas pressure and flow rate test, and a report on the boiler's condition. The service costs £85 and I carry it out across Bitterne Park throughout the year."
            },
        ],
    },
    "bitterne-village": {
        "name": "Bitterne Village",
        "title": "Plumber & Heating Engineer in Bitterne Village | Better Call Wes",
        "meta": "Gas Safe plumber in Bitterne Village, Southampton. Boiler repairs, heating and plumbing for homes across Bitterne Village — same-day response available. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Bitterne Village",
        "hero_p": "Bitterne Village is at the heart of the broader Bitterne community — a mix of housing types in a convenient location for much of east Southampton. If you've got a plumbing or heating issue, I'm never far away.",
        "h3": "A Local Engineer Who Knows the Area",
        "p1": "The Bitterne Village area includes a wide range of property types — from older terraces near the High Street to more modern detached homes further from the centre. With that range of housing comes a real variety of plumbing and heating setups, and I'm experienced with all of them.",
        "p2": "Boiler breakdowns, dripping taps, leaking pipes, cold radiators — these are all jobs I cover on a daily basis across east Southampton. One thing I see regularly in Bitterne Village is boilers that are well overdue a service. An annual service not only keeps the boiler running safely but usually catches small issues before they become expensive ones.",
        "p3": "I cover Bitterne Village as part of my regular Southampton patch. Gas Safe registered (reg. 558654), no call-out fee during standard hours, and a clear upfront cost before any work starts.",
        "faqs": [
            {
                "q": "Do you cover the streets around Bitterne High Street?",
                "a": "Yes — I cover all of Bitterne Village including the streets around the High Street and the surrounding residential areas. Response times are usually same-day for urgent issues and next-day for routine work."
            },
            {
                "q": "My boiler keeps switching itself off — what could be causing this?",
                "a": "A boiler that cuts out repeatedly (known as 'short cycling' or 'lockout') can be caused by low pressure, a faulty thermostat, a dirty flame sensor, or an overheating issue. I can diagnose the fault in a single visit and in most cases fix it the same day, as I carry common spare parts in the van."
            },
            {
                "q": "Do you offer a guarantee on your work?",
                "a": "Yes — all labour is guaranteed. For parts fitted, manufacturer warranties apply. If a repair I've carried out develops the same fault within a reasonable period, I'll return to investigate without an additional call-out charge."
            },
        ],
    },
    "chandlers-ford": {
        "name": "Chandler's Ford",
        "title": "Plumber & Heating Engineer in Chandler's Ford | Better Call Wes",
        "meta": "Gas Safe plumber serving Chandler's Ford, Eastleigh. Boiler repairs, central heating and plumbing for Chandler's Ford homes. Same-day response available. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Chandler's Ford",
        "hero_p": "Chandler's Ford sits just north of Southampton and has grown significantly over the past few decades into a busy, family-oriented community. It's a wide mix of housing — from post-war semis to modern estates — and Wes covers the whole area regularly.",
        "h3": "Covering Chandler's Ford's Diverse Housing Stock",
        "p1": "Chandler's Ford expanded rapidly from the 1960s onwards and now has a mix of housing types across Hiltingbury, Merdon Avenue, and the newer developments closer to the M3. Older properties often have original pipework and conventional boilers, while newer builds tend to come with combi systems that bring their own maintenance requirements.",
        "p2": "One of the most common callouts I get in Chandler's Ford is for boilers that lose pressure repeatedly. This usually points to a small leak somewhere in the system — often at a radiator valve or a concealed joint — and it's something I can diagnose and fix in a single visit in most cases.",
        "p3": "Although Chandler's Ford is technically in Eastleigh borough, it's well within my regular coverage area. Gas Safe registered (reg. 558654), covering all Chandler's Ford postcodes. No call-out fee during normal hours and a clear fixed quote before any work starts.",
        "faqs": [
            {
                "q": "Do you cover the Hiltingbury and Merdon Avenue areas of Chandler's Ford?",
                "a": "Yes — I cover the whole of Chandler's Ford including Hiltingbury, Merdon Avenue, Fryern Hill and all surrounding residential streets in the SO53 postcode. Chandler's Ford is one of my regular areas and I'm usually able to attend the same day for urgent jobs."
            },
            {
                "q": "My house in Chandler's Ford has underfloor heating — can you work on it?",
                "a": "Yes. I carry out underfloor heating work including fault diagnosis, thermostat replacement and manifold repairs. If you have a wet underfloor heating system that's not performing as it should, I can assess it and advise on the best course of action."
            },
            {
                "q": "How much does a new boiler installation cost in Chandler's Ford?",
                "a": "New boiler installations vary depending on the boiler model and what's involved in the installation. For a like-for-like combi replacement, you're typically looking at £1,800–£2,500 fully installed including parts and labour. I'll always provide a fixed quote before any work starts so there are no surprises."
            },
        ],
    },
    "eastleigh": {
        "name": "Eastleigh",
        "title": "Plumber & Heating Engineer in Eastleigh | Better Call Wes",
        "meta": "Gas Safe plumber serving Eastleigh, Hampshire SO50. Boiler repairs, heating and landlord gas safety certificates for Eastleigh homes. Same-day response. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Eastleigh",
        "hero_p": "Eastleigh is a busy market town just north of Southampton with a strong community of homeowners and landlords who need reliable, honest trades. I cover Eastleigh regularly and can usually attend the same day for urgent plumbing or heating issues.",
        "h3": "Eastleigh's Housing Needs an Engineer You Can Trust",
        "p1": "Eastleigh has a distinctive housing stock — Victorian terraces near the town centre built when the railway came through in the 1840s, inter-war semis on Bishopstoke Road and Cranbury Road, and newer estates on the town's fringes. Each era of housing brings its own plumbing characteristics and typical faults.",
        "p2": "I carry out a significant amount of landlord work in Eastleigh — annual gas safety certificates (CP12s), boiler servicing, and plumbing maintenance for rental properties across the town. If you're a landlord with a portfolio in the area, I can often schedule inspections back-to-back across multiple properties to keep costs and disruption down.",
        "p3": "Gas Safe registered (reg. 558654), covering all Eastleigh postcodes including SO50. Transparent pricing — no VAT, no hidden call-out charges during standard hours, and a clear cost before anything is started.",
        "faqs": [
            {
                "q": "Do you carry out landlord gas safety certificates in Eastleigh?",
                "a": "Yes — landlord gas safety inspections (CP12 certificates) are one of the most common jobs I carry out in Eastleigh. Certificates are issued on the day of inspection. If you have multiple rental properties in Eastleigh, I can carry out inspections back-to-back to minimise disruption."
            },
            {
                "q": "Can you service a boiler in Eastleigh the same week?",
                "a": "In most cases, yes. I carry out boiler services across Eastleigh throughout the week. An annual service is a legal requirement for rented properties and strongly recommended for owner-occupied homes — it's the most cost-effective way to prevent an unexpected breakdown."
            },
            {
                "q": "My Victorian terrace in Eastleigh has old cast iron pipes — should I be concerned?",
                "a": "Cast iron waste pipes are common in older Eastleigh terraces and they're generally still serviceable, but they can crack, corrode or block more readily than modern plastic pipework. If you're having recurring blockages or noticing damp near waste pipes, it's worth having them inspected."
            },
        ],
    },
    "freemantle": {
        "name": "Freemantle",
        "title": "Plumber & Heating Engineer in Freemantle, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber in Freemantle, Southampton. Specialist in Victorian terrace plumbing — boiler repairs, heating and pipework for older properties. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Freemantle",
        "hero_p": "Freemantle is a dense, characterful part of west Southampton — packed with Victorian terraces and a strong sense of community. These older properties are some of my favourite to work on, and I know the common issues they throw up inside out.",
        "h3": "Victorian Terraces Need a Specialist Eye",
        "p1": "Freemantle is dominated by late Victorian and Edwardian terraced housing built in the decades when Southampton was expanding rapidly toward the west. These properties are well built but their plumbing infrastructure is old — often original copper or iron pipework, gravity-fed tanks in the loft, and boilers that have been retrofitted into spaces not designed for them.",
        "p2": "Lead pipework is still present in some Freemantle properties, particularly on the supply side from the street boundary. I carry out lead pipe replacement regularly in this part of Southampton. It's not always an emergency, but it's worth knowing about if your home pre-dates the 1970s and the pipework hasn't been touched.",
        "p3": "I work across Freemantle and the wider west Southampton area regularly. Gas Safe registered (reg. 558654), no call-out fee during normal hours, and always an honest assessment of what your system actually needs — not what generates the biggest bill.",
        "faqs": [
            {
                "q": "Do you work on Victorian terraced houses in Freemantle?",
                "a": "Yes — Victorian terraces are some of the most common properties I work on across west Southampton. I'm very familiar with the plumbing and heating layouts typical of these homes, including gravity-fed systems, loft tanks, and the modifications that have been made to them over the decades."
            },
            {
                "q": "I think I have lead pipes in my Freemantle home — what should I do?",
                "a": "If your home was built before the 1970s and you haven't had the pipework checked, it's worth arranging an inspection. Lead pipes are most commonly found on the supply pipe from the street into the house. I can inspect and, where necessary, replace lead pipework with modern copper or plastic — advising on the most cost-effective approach for your specific property."
            },
            {
                "q": "Can you install a new boiler to replace a back boiler in Freemantle?",
                "a": "Yes — back boiler replacement is a job I carry out regularly in older west Southampton properties. Removing a back boiler and fitting a modern wall-mounted combi typically improves efficiency significantly and frees up space. I'll assess whether your existing pipework and radiators are suitable and give you a clear quote for the full installation."
            },
        ],
    },
    "harefield": {
        "name": "Harefield",
        "title": "Plumber & Heating Engineer in Harefield, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Harefield, Southampton. Boiler repairs, heating and plumbing for Harefield homes. Honest pricing, same-day response available. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Harefield",
        "hero_p": "Harefield is a residential area in east Southampton with a mix of post-war and more recent housing. I cover Harefield as part of my regular east Southampton patch — fast response, honest pricing, and no unnecessary work.",
        "h3": "Reliable Plumbing and Heating in Harefield",
        "p1": "Harefield sits in the eastern part of Southampton, close to Thornhill and the Hedge End boundary. The area has a mix of housing built from the 1950s onwards — many properties still have their original heating systems, which can be less efficient and more prone to breakdowns as they age beyond 15–20 years.",
        "p2": "Boiler breakdowns and inefficient heating systems are among the most common jobs I attend in this part of Southampton. If your boiler is over 10 years old and hasn't been serviced regularly, it's at significantly higher risk of breakdown — and an annual service is the most cost-effective way to keep it running reliably.",
        "p3": "I cover all of Harefield and the surrounding east Southampton area. Gas Safe registered (reg. 558654), no hidden fees, and a clear upfront quote before any work starts.",
        "faqs": [
            {
                "q": "Do you cover the Thornhill and Harefield area for emergency plumbing?",
                "a": "Yes — Harefield, Thornhill and the surrounding east Southampton area is within my regular coverage zone. For urgent heating or plumbing issues I aim to attend the same day wherever possible."
            },
            {
                "q": "My boiler is making a banging noise in Harefield — is that serious?",
                "a": "Banging or kettling noises from a boiler are usually caused by limescale build-up on the heat exchanger, which is common in areas with harder water. It's not an immediate emergency but it does reduce efficiency and can eventually cause the heat exchanger to fail. A chemical descale or system inhibitor treatment often resolves it."
            },
            {
                "q": "How long does a boiler repair usually take?",
                "a": "Most boiler repairs are completed within two to three hours, depending on what the fault is. I carry a wide range of common spare parts in the van, which means many repairs can be completed in a single visit without waiting for parts to arrive."
            },
        ],
    },
    "hedge-end": {
        "name": "Hedge End",
        "title": "Plumber & Heating Engineer in Hedge End | Better Call Wes",
        "meta": "Gas Safe plumber serving Hedge End, Hampshire SO30. Boiler repairs, heating and plumbing for Hedge End's growing residential estates. Same-day response. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Hedge End",
        "hero_p": "Hedge End has grown enormously in recent decades and is now one of the largest residential areas east of Southampton. New builds and established estates sit alongside each other here — and both bring their own plumbing and heating needs.",
        "h3": "New Builds and Established Homes — I Cover Both",
        "p1": "Hedge End has seen significant residential development since the 1980s, with large estates off Botley Road, Wildern Lane, and around the Hedge End retail park. These newer properties tend to come with combi boilers and modern plumbing — but that doesn't mean they're trouble-free. Manufacturer warranties expire, and components still wear out.",
        "p2": "One issue I see more often in newer Hedge End properties than in older ones is inadequate system flushing at the time of installation, leading to sludge build-up earlier than you'd expect. If your heating is inefficient or certain radiators are cooler than others, a power flush is often the solution — and it can make a dramatic difference.",
        "p3": "I cover Hedge End and all surrounding SO30 postcodes. Gas Safe registered (reg. 558654), clear fixed pricing, and no call-out fee during normal hours. Most urgent jobs can be attended the same day.",
        "faqs": [
            {
                "q": "Do you cover the Wildern and Hedge End retail park area?",
                "a": "Yes — I cover the whole of Hedge End including all residential streets around Botley Road, Wildern Lane, Bursledon Road and the surrounding SO30 postcode area. I'm usually available same-day for urgent heating or plumbing issues."
            },
            {
                "q": "My new build in Hedge End is only 5 years old — does it still need a boiler service?",
                "a": "Yes — annual boiler servicing is recommended regardless of the age of the boiler, and is usually a condition of the manufacturer's warranty. Servicing a relatively new boiler is quick and straightforward, and it keeps the warranty valid while checking that everything is running as efficiently as it should."
            },
            {
                "q": "Can you install a magnetic filter on my Hedge End boiler?",
                "a": "Yes — fitting a magnetic filter (such as an Adey MagnaClean or Fernox TF1) is something I recommend for most properties and carry out regularly. It captures iron oxide sludge before it circulates through the system, extending boiler life and improving efficiency. It takes around 30–45 minutes to fit and can be done alongside a service."
            },
        ],
    },
    "highfield": {
        "name": "Highfield",
        "title": "Plumber & Heating Engineer in Highfield, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Highfield, Southampton SO17. Boiler repairs, heating and landlord gas safety certificates for Highfield homes and HMOs. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Highfield",
        "hero_p": "Highfield is one of Southampton's most characterful residential areas — a mix of large Victorian houses, many converted to flats or HMOs, and owner-occupied family homes close to the university and the Common.",
        "h3": "Experience With Highfield's Varied Housing",
        "p1": "Highfield has a dense concentration of Victorian and Edwardian housing that has been through many changes over the decades. The proximity to the University of Southampton means a large proportion of properties are rented — many as student houses or professional HMOs. Landlord gas safety certificates (CP12s) are something I carry out frequently across this area.",
        "p2": "Older converted properties in Highfield often have complex, modified heating systems — tanks in the loft, shared pipework between flats, or boilers that have been relocated during conversion. These systems need someone who can read what's actually installed rather than assuming a standard layout.",
        "p3": "I cover Highfield and the surrounding SO17 area. Gas Safe registered (reg. 558654), landlord certificates issued on the day, and transparent pricing with no hidden costs.",
        "faqs": [
            {
                "q": "Do you carry out landlord gas safety certificates for HMOs in Highfield?",
                "a": "Yes — landlord gas safety inspections are one of my most common jobs in Highfield. I work with landlords who have single properties and those with larger portfolios. Certificates are issued on the day of inspection and I can often schedule multiple properties in the same road on the same visit."
            },
            {
                "q": "Can you work on a converted Victorian property in Highfield that's been split into flats?",
                "a": "Yes — converted Victorian properties are common in Highfield and I'm experienced with the modified plumbing and heating layouts they typically have. Whether you need work on a shared system or individual flat-by-flat boilers, I can assess the setup and advise on the best approach."
            },
            {
                "q": "My student house in Highfield needs a gas safety certificate before the new tenants move in — how quickly can you do it?",
                "a": "I can usually carry out a gas safety inspection within a few days — often sooner. I know how important turnaround is between tenancies and I'll accommodate urgent requests wherever possible. Call or WhatsApp to check my availability."
            },
        ],
    },
    "lordshill": {
        "name": "Lordshill",
        "title": "Plumber & Heating Engineer in Lordshill, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Lordshill, Southampton. Boiler repairs, heating and plumbing for Lordshill homes. Honest pricing, no call-out fee. Call Wes: 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Lordshill",
        "hero_p": "Lordshill is one of west Southampton's main residential areas — a large community of homes built mainly in the 1970s and 1980s. I cover Lordshill regularly and know the kind of systems these properties typically have.",
        "h3": "1970s and 1980s Homes — Common Issues I See Every Week",
        "p1": "Lordshill was largely developed as a planned residential area through the 1970s, with a mix of council-built and private housing across the estate. Many of the boilers in these properties are now at or past the point where replacement becomes more cost-effective than continued repair.",
        "p2": "The most common job I attend in Lordshill is a boiler that's started losing pressure or showing fault codes. These are often symptoms of a system that hasn't been regularly maintained — a service and flush can extend the life of the boiler considerably, or if it's genuinely beyond economic repair, I'll tell you that honestly rather than stringing out the repairs.",
        "p3": "I cover the whole Lordshill area. Gas Safe registered (reg. 558654), no call-out fee during normal hours, and a straightforward quote before any work starts.",
        "faqs": [
            {
                "q": "Do you cover the whole Lordshill estate?",
                "a": "Yes — I cover all of Lordshill including the surrounding streets in the SO16 postcode area. I'm regularly working across the area and can usually attend urgent heating or plumbing callouts the same day."
            },
            {
                "q": "My boiler in Lordshill is from the 1990s — is it worth repairing?",
                "a": "A boiler from the 1990s is now 25–35 years old, which is well beyond the expected lifespan of most boilers. If it's still functioning reliably and parts are available, a repair may make sense in the short term. But if it's repeatedly breaking down, a replacement will almost always be more cost-effective. I'll give you an honest assessment so you can make an informed decision."
            },
            {
                "q": "Can you bleed and balance my radiators in Lordshill?",
                "a": "Yes — radiator bleeding and system balancing is a straightforward job I carry out regularly across west Southampton. If some rooms in your home are warmer than others, balancing the system can make a real difference to comfort and heating efficiency."
            },
        ],
    },
    "lordswood": {
        "name": "Lordswood",
        "title": "Plumber & Heating Engineer in Lordswood, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Lordswood, Southampton. Boiler repairs, heating and plumbing for Lordswood homes. Same-day response available. Call Wes: 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Lordswood",
        "hero_p": "Lordswood is a west Southampton residential area close to Lordswood Leisure Centre and the open spaces at the edge of the city. I cover Lordswood as part of my regular west Southampton patch — straightforward pricing and honest advice on every job.",
        "h3": "Covering Lordswood's Post-War Housing",
        "p1": "Lordswood has a mix of post-war housing including both social and private homes built from the 1950s onwards. Many of the properties here have older heating systems that were installed decades ago and are now coming toward the end of their reliable working life. Regular servicing makes a real difference to how long a boiler lasts.",
        "p2": "I'm often called out to Lordswood properties for boiler pressure issues, leaking radiator valves, and systems that aren't heating evenly across the house. In many cases, a combination of a service and a system flush resolves the issue without needing a new boiler.",
        "p3": "Gas Safe registered (reg. 558654), covering Lordswood and all surrounding areas in west Southampton. No hidden charges, no call-out fee during standard hours, and a clear price before starting.",
        "faqs": [
            {
                "q": "Do you cover Lordswood and the surrounding area?",
                "a": "Yes — Lordswood and the surrounding west Southampton area is well within my regular coverage zone. I'm usually available same-day for urgent callouts and within a couple of days for routine work."
            },
            {
                "q": "My central heating doesn't heat the whole house evenly — what could be wrong?",
                "a": "Uneven heating across a house is usually caused by one of three things: radiators that need balancing, sludge build-up restricting flow in some radiators, or a pump that's not running at the right speed. I can diagnose the cause and fix it — often in a single visit."
            },
            {
                "q": "Do you carry out bathroom plumbing in Lordswood?",
                "a": "Yes — I carry out a full range of plumbing work including bathroom installations and repairs. Dripping taps, leaking showers, toilet cistern repairs, and replacing bath or shower taps are all jobs I handle regularly across west Southampton."
            },
        ],
    },
    "maybush": {
        "name": "Maybush",
        "title": "Plumber & Heating Engineer in Maybush, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Maybush, Southampton. Boiler repairs, heating and plumbing for Maybush homes. No call-out fee, same-day response. Call Wes: 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Maybush",
        "hero_p": "Maybush is a west Southampton area with a strong residential community. I cover Maybush as part of my core west Southampton patch, with fast response times and transparent pricing on every job.",
        "h3": "Reliable Plumbing and Heating in Maybush",
        "p1": "Maybush sits between Lordswood and Millbrook in west Southampton, with a mix of post-war and more recent housing. Older properties in the area sometimes still have original back boilers or older conventional systems that are increasingly difficult to get parts for — and where replacement makes more sense than repair.",
        "p2": "If you've got a back boiler or an older system boiler that's starting to cause trouble, it's worth getting an honest assessment of whether repair or replacement makes more financial sense. I won't push you toward an unnecessary replacement — but equally I'll tell you when a boiler has genuinely reached the end of its economic life.",
        "p3": "Gas Safe registered (reg. 558654), no call-out fee during normal hours. I cover the whole Maybush area and the surrounding west Southampton postcodes.",
        "faqs": [
            {
                "q": "Do you cover Millbrook Road East and the Maybush area?",
                "a": "Yes — Maybush and the surrounding streets including Millbrook Road East are well within my regular coverage area. For urgent plumbing or heating issues I aim to attend the same day."
            },
            {
                "q": "Can you replace a back boiler in a Maybush property?",
                "a": "Yes — back boiler replacement is a job I carry out in older west Southampton properties. Removing a back boiler and fitting a modern wall-mounted boiler is a significant upgrade, usually improving both efficiency and reliability. I'll carry out a survey first and give you a fixed quote for the complete installation."
            },
            {
                "q": "How long does it take to fit a new boiler?",
                "a": "A straightforward like-for-like combi replacement typically takes four to six hours — so it's usually completed in a single day. More complex installations involving new pipework routes or system changes may take longer. I'll give you a realistic time estimate as part of the quote."
            },
        ],
    },
    "millbrook": {
        "name": "Millbrook",
        "title": "Plumber & Heating Engineer in Millbrook, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Millbrook, Southampton. Boiler repairs, heating and plumbing for Millbrook homes. Transparent pricing, fast response. Call Wes: 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Millbrook",
        "hero_p": "Millbrook is in west Southampton, mixing residential streets with the industrial and commercial areas near the docks. The residential community here needs a reliable local plumber who's straightforward and doesn't overcomplicate things.",
        "h3": "West Southampton's Straightforward Heating Engineer",
        "p1": "Millbrook's residential streets include a mix of terraced housing and semi-detached properties, many built in the 1950s and 1960s. Properties of this age often have systems that have been modified over the years — resulting in a patchwork of copper, plastic, and occasionally older lead pipework.",
        "p2": "I carry out a lot of general plumbing repairs across Millbrook — leaking joints, dripping taps, blocked toilets, and boiler callouts. These are all jobs I can usually sort in a single visit. I carry common spare parts in the van to avoid wasted callouts where possible.",
        "p3": "Gas Safe registered (reg. 558654), covering Millbrook and all surrounding areas in west Southampton. No hidden fees, no call-out charge during normal hours, and a clear quote before work starts.",
        "faqs": [
            {
                "q": "Do you cover the residential streets in Millbrook near the Sports Centre?",
                "a": "Yes — I cover all of Millbrook's residential areas including streets around Southampton Sports Centre and along Millbrook Road. I'm regularly in this part of the city and can usually attend same-day for urgent issues."
            },
            {
                "q": "I have a dripping tap that's getting worse — can you fix it?",
                "a": "Yes — dripping taps are one of the most common small plumbing jobs I deal with. In most cases it's a washer or cartridge that needs replacing — a job that takes less than an hour. Left unfixed, a dripping tap wastes a surprising amount of water and can cause damage to the tap seat over time."
            },
            {
                "q": "Do you fix leaking pipes under floorboards?",
                "a": "Yes — concealed pipe leaks are something I deal with regularly. I'll locate the source of the leak, lift the minimum amount of flooring necessary to access and repair it, and advise on how to prevent recurrence. If you're not sure where the leak is coming from, a WhatsApp video of the symptoms is often helpful before I attend."
            },
        ],
    },
    "portswood": {
        "name": "Portswood",
        "title": "Plumber & Heating Engineer in Portswood, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber in Portswood, Southampton SO17. Boiler repairs, heating and landlord gas safety certificates for Portswood homes and HMOs. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Portswood",
        "hero_p": "Portswood is one of Southampton's most densely populated areas — a lively neighbourhood of Victorian terraces, student houses, and established family homes close to the university and the city centre.",
        "h3": "Portswood's High Rental Density — I Know the Area Well",
        "p1": "Portswood has a very high proportion of rented properties, including a large number of HMOs and student houses. Landlord gas safety inspections are one of the most common jobs I carry out in this area — they're a legal requirement for all rented properties with gas appliances, and I can certificate multiple properties in the same road on the same day.",
        "p2": "The Victorian terraces that dominate Portswood have been through many plumbing and heating updates over the decades. Shared walls, old cast iron waste pipes, and heating systems that have had numerous modifications make these properties more complex than they appear from the outside.",
        "p3": "I cover Portswood and the surrounding SO17 area. Gas Safe registered (reg. 558654), landlord CP12 certificates issued on the same day, and transparent pricing — no hidden charges, no call-out fee during standard hours.",
        "faqs": [
            {
                "q": "Do you carry out landlord gas safety certificates in Portswood?",
                "a": "Yes — Portswood is one of the areas I carry out the most landlord gas safety inspections. If you have a rental property or multiple properties in the area, I can carry out inspections and issue certificates on the day. I'm also happy to do annual boiler services at the same time to keep everything in order."
            },
            {
                "q": "Can you work on a Victorian terrace that's been converted to flats in Portswood?",
                "a": "Yes — converted Victorian terraces are common in Portswood and I deal with them regularly. These properties often have modified or shared plumbing and heating systems, and I'm experienced at assessing what's there and carrying out work safely and effectively."
            },
            {
                "q": "My tenant in Portswood has reported a gas smell — what should I do?",
                "a": "If there's a suspected gas leak, the tenant should turn off the gas at the meter, open windows, leave the property, and call the National Gas Emergency Service on 0800 111 999. Once it's been made safe, contact me and I'll carry out a gas tightness test and trace any fault before the supply is turned back on."
            },
        ],
    },
    "shirley": {
        "name": "Shirley",
        "title": "Plumber & Heating Engineer in Shirley, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Shirley, Southampton SO15. Boiler repairs, central heating and plumbing for Shirley homes. Same-day response available. Call Wes: 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Shirley",
        "hero_p": "Shirley is one of west Southampton's most established residential areas — a mix of inter-war semis, Victorian terraces, and modern infill development along and around Shirley High Street. I cover all of Shirley as part of my regular patch.",
        "h3": "Shirley's Mix of Housing — From Pre-War to Modern",
        "p1": "Shirley has one of the most varied housing stocks in Southampton — large 1930s semis along Bellemoor Road and Winchester Road, Victorian terraces closer to the high street, and more recent development on former commercial land. Each type brings different plumbing characteristics, and I'm experienced across all of them.",
        "p2": "One of the most common jobs I get called to in Shirley is a central heating system that hasn't been flushed in years. In older properties with steel radiators and copper pipework, corrosion builds up over time and ends up restricting flow through the system. A power flush usually transforms heating efficiency and can cure cold or slow-to-warm radiators that have been a problem for years.",
        "p3": "Gas Safe registered (reg. 558654), covering all of Shirley and surrounding SO15/SO16 postcodes. No call-out fee during normal hours, and a clear, honest quote before any work starts.",
        "faqs": [
            {
                "q": "Do you cover the Shirley High Street and Bellemoor Road area?",
                "a": "Yes — I cover the whole of Shirley including Bellemoor Road, Winchester Road, Shirley High Street and all surrounding streets across the SO15 postcode. Shirley is one of my regular areas and I'm usually able to attend the same day for urgent issues."
            },
            {
                "q": "What is a power flush and does my Shirley home need one?",
                "a": "A power flush is a deep clean of your central heating system using a high-flow pump and specialist chemicals to remove iron oxide sludge and debris. If your radiators are slow to heat up, have cold patches, or your system is noisy, a power flush is often the answer. It typically takes three to five hours depending on system size and the level of contamination."
            },
            {
                "q": "Can you replace a radiator in my Shirley home?",
                "a": "Yes — radiator replacement is a straightforward job I carry out regularly across Shirley and west Southampton. Whether you want a like-for-like replacement or an upgrade to a larger or different style of radiator, I can advise on sizing, fit the new radiator, and balance the system afterwards."
            },
        ],
    },
    "southampton": {
        "name": "Southampton",
        "title": "Plumber & Heating Engineer in Southampton | Better Call Wes",
        "meta": "Gas Safe plumber based in Southampton. Boiler repairs, central heating, gas safety and plumbing across Southampton SO14–SO18. Same-day response. 07700 155 655.",
        "h1": "Southampton's Local Plumber & Gas Engineer",
        "hero_p": "Better Call Wes is a Southampton-based plumbing and heating business serving the whole city and surrounding areas. Gas Safe registered, transparent pricing, and genuinely local — Wes lives and works in Southampton.",
        "h3": "Southampton's Housing — From Docks to Suburbs",
        "p1": "Southampton has one of the most varied housing stocks of any city its size — Victorian terraces in Freemantle and Portswood, large Edwardian semis in Bitterne Park and Bassett, post-war estates in Lordshill and Millbrook, and modern apartment blocks in the city centre. I work across all of it, every week.",
        "p2": "Being based in Southampton means I genuinely know the city. I know which postcodes have harder water, which areas have older copper pipework, and which housing types are most likely to have particular system configurations. That local knowledge means faster diagnosis and fewer wasted trips.",
        "p3": "Gas Safe registered (reg. 558654), covering all Southampton postcodes SO14 through SO18 and beyond. No call-out fee during normal hours, honest advice, and a clear fixed quote before any work begins.",
        "faqs": [
            {
                "q": "Which areas of Southampton do you cover?",
                "a": "I cover the whole of Southampton city and surrounding areas including Bitterne, Shirley, Portswood, Highfield, Freemantle, Lordshill, Millbrook, Bassett, Swaythling, and extending out to Eastleigh, Chandler's Ford, and Hedge End. If you're in the SO postcode area, get in touch and I'll confirm coverage."
            },
            {
                "q": "Do you work on both residential and rental properties in Southampton?",
                "a": "Yes — I work for homeowners, landlords, and managing agents across Southampton. For landlords, I carry out annual gas safety certificates, boiler services, and general plumbing maintenance. I can often certificate multiple properties in the same area on the same day to keep costs down."
            },
            {
                "q": "What makes Better Call Wes different from other plumbers in Southampton?",
                "a": "Transparent, upfront pricing — no VAT, no hidden charges, no call-out fee during normal hours. I'll tell you the cost before I start, not after. I'm also genuinely local, Gas Safe registered (reg. 558654), and have over 110 five-star reviews from Southampton customers."
            },
        ],
    },
    "st-denys": {
        "name": "St Denys",
        "title": "Plumber & Heating Engineer in St Denys, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving St Denys, Southampton SO17. Specialist in Victorian railway terraces — boiler repairs, heating and pipework for older properties. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving St Denys",
        "hero_p": "St Denys is a compact, characterful neighbourhood built largely to house railway workers in the Victorian era. These terraces are well-built and much-loved, but their plumbing and heating setups often reflect more than a century of modifications.",
        "h3": "Victorian Railway Terraces — Their Quirks and Common Issues",
        "p1": "St Denys sits close to the train station and the River Itchen, and its housing stock reflects its railway heritage — tight Victorian terraces built in the 1870s–1900s with small footprints and plumbing that has been adapted many times over the decades. I've worked on plenty of these properties and know what to expect.",
        "p2": "Common issues in St Denys properties include original pipework that has been patched rather than properly replaced, gravity-fed hot water systems in the loft that are inefficient by modern standards, and rear extensions with plumbing that doesn't quite meet current standards. All things I can assess and advise on honestly.",
        "p3": "Gas Safe registered (reg. 558654), covering St Denys and the surrounding SO17/SO18 areas. No call-out fee during normal hours, and a clear cost before any work starts.",
        "faqs": [
            {
                "q": "Do you work on Victorian railway terraces in St Denys?",
                "a": "Yes — the Victorian terraces in St Denys are some of my most interesting properties to work on. I'm very familiar with the plumbing layouts typical of these homes and can assess and repair older systems that other engineers might struggle with."
            },
            {
                "q": "My St Denys terrace has a hot water tank in the loft — should I replace it with a combi?",
                "a": "It depends on your hot water usage and the size of your property. For a smaller terrace with one bathroom and moderate hot water demand, a combi is often a great upgrade — removing the tank, improving efficiency, and freeing up space. For larger households, a system boiler with a cylinder may still make more sense. I'll assess your situation and give you an honest recommendation."
            },
            {
                "q": "Can you carry out a gas safety check in St Denys quickly?",
                "a": "Yes — gas safety checks (including landlord CP12 certificates) can usually be arranged within a few days, often sooner. St Denys is well within my regular coverage area and I'm frequently working in the SO17 postcode."
            },
        ],
    },
    "swaythling": {
        "name": "Swaythling",
        "title": "Plumber & Heating Engineer in Swaythling, Southampton | Better Call Wes",
        "meta": "Gas Safe plumber serving Swaythling, Southampton SO16/SO17. Boiler repairs, heating and plumbing for Swaythling homes. Same-day response available. 07700 155 655.",
        "h1": "Plumber & Gas Engineer Serving Swaythling",
        "hero_p": "Swaythling is a northern Southampton suburb close to Southampton Airport and the university's main campus. A mix of 1930s semis, post-war housing, and properties with student tenants makes it one of the more varied areas I cover.",
        "h3": "Serving Swaythling's Mix of Owner-Occupied and Rented Homes",
        "p1": "Swaythling has a notable mix of housing — established 1930s and 1950s semis in the residential streets around Swaythling High Street, student accommodation near the university, and some more recent development closer to the airport and motorway links. The proximity to the university means there's also a significant population of landlords who need annual gas safety certificates.",
        "p2": "I carry out a lot of boiler servicing and gas safety work in this area — both for owner-occupiers and landlords. If you own a rental property in Swaythling, I can carry out the annual CP12 certificate and boiler service in one visit, which is what the law requires for rented properties and is the most efficient way to handle it.",
        "p3": "Gas Safe registered (reg. 558654), covering all of Swaythling and surrounding SO16/SO17 postcodes. No call-out fee during normal hours and clear upfront pricing on every job.",
        "faqs": [
            {
                "q": "Do you cover the Swaythling High Street and university area?",
                "a": "Yes — I cover all of Swaythling including the residential streets around Swaythling High Street and the areas adjacent to the University of Southampton campus. I'm regularly working in this part of the city."
            },
            {
                "q": "Can you carry out a boiler service and gas safety certificate at the same time in Swaythling?",
                "a": "Yes — combining an annual boiler service with the landlord gas safety inspection is the most efficient approach and is something I recommend. Both can be carried out in a single visit, and I'll issue the CP12 certificate on the same day."
            },
            {
                "q": "My 1930s semi in Swaythling has original radiators — should I replace them?",
                "a": "Original cast iron radiators from the 1930s can still work well if the system is maintained properly. They hold more water and heat more slowly than modern steel radiators, but they also retain heat longer. If they're not leaking and are heating correctly, there's no urgent need to replace them. If efficiency is a concern, I can advise on options."
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# HTML generation helpers
# ---------------------------------------------------------------------------

def build_faq_section(data):
    """Build the FAQ HTML section to inject before the CTA."""
    name = data["name"]
    faqs = data["faqs"]
    items = ""
    for faq in faqs:
        items += f"""            <div style="border-bottom: 1px solid var(--color-border, #e5e7eb); padding-bottom: 1.5rem;">
                <h3 style="color: var(--color-primary); margin-bottom: 0.75rem; font-size: 1.1rem;">{faq["q"]}</h3>
                <p style="color: var(--text-body); line-height: 1.6; margin: 0;">{faq["a"]}</p>
            </div>\n"""

    return f"""
    <section class="section section-gray">
        <div class="container">
            <div class="section-header">
                <div class="section-label">FAQS</div>
                <h2>Common Questions from {name} Residents</h2>
            </div>
            <div style="max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem;">
{items}            </div>
        </div>
    </section>
    """


def build_faq_schema(data):
    """Build the FAQ JSON-LD schema block."""
    faqs = data["faqs"]
    entities = []
    for faq in faqs:
        q = faq["q"].replace('"', '\\"')
        a = faq["a"].replace('"', '\\"')
        entities.append(
            f'    {{"@type": "Question", "name": "{q}", "acceptedAnswer": {{"@type": "Answer", "text": "{a}"}}}}'
        )
    entities_str = ",\n".join(entities)
    return f"""    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
{entities_str}
      ]
    }}
    </script>"""


# ---------------------------------------------------------------------------
# Replacement functions
# ---------------------------------------------------------------------------

def replace_title(content, data):
    return re.sub(
        r"<title>.*?</title>",
        f"<title>{data['title']}</title>",
        content,
        flags=re.DOTALL,
    )


def replace_meta_description(content, data):
    return re.sub(
        r'<meta name="description"\s*\n?\s*content="[^"]*">',
        f'<meta name="description"\n        content="{data["meta"]}">',
        content,
    )


def replace_h1(content, data):
    return re.sub(
        r'(<h1 style="color: white; margin-bottom: 1\.5rem; font-size: 3rem;">).*?(</h1>)',
        rf'\g<1>{data["h1"]}\2',
        content,
        flags=re.DOTALL,
    )


def replace_hero_paragraph(content, data):
    return re.sub(
        r'(<p style="color: rgba\(255,255,255,0\.8\); font-size: 1\.25rem; max-width: 800px; margin: 0 auto 2rem;">).*?(</p>)',
        rf'\g<1>{data["hero_p"]}\2',
        content,
        flags=re.DOTALL,
    )


def replace_local_expertise(content, data):
    """Replace the h3 + 3 paragraphs in the local expertise section."""
    new_block = (
        f'<h3 style="margin-bottom: 1rem; color: var(--color-primary);">{data["h3"]}</h3>\n'
        f'                    <p style="margin-bottom: 1rem; color: var(--text-body); font-size: 1.1rem; line-height: 1.6;">\n'
        f'                        {data["p1"]}\n'
        f'                    </p>\n'
        f'                    <p style="margin-bottom: 1rem; color: var(--text-body); font-size: 1.1rem; line-height: 1.6;">\n'
        f'                        {data["p2"]}\n'
        f'                    </p>\n'
        f'                    <p style="color: var(--text-body); font-size: 1.1rem; line-height: 1.6;">\n'
        f'                        {data["p3"]}\n'
        f'                    </p>'
    )
    return re.sub(
        r'<h3 style="margin-bottom: 1rem; color: var\(--color-primary\);">.*?</h3>'
        r'.*?'
        r'(<p style="color: var\(--text-body\); font-size: 1\.1rem; line-height: 1\.6;">.*?</p>)',
        new_block,
        content,
        flags=re.DOTALL,
        count=1,
    )


def inject_faq_section(content, data):
    """Insert FAQ section before the CTA section if not already present."""
    if "FAQPage" in content:
        return content  # already has FAQ, skip

    faq_html = build_faq_section(data)
    faq_schema = build_faq_schema(data)

    # Insert FAQ section before the CTA (navy background section)
    content = re.sub(
        r'(\s*<section class="section" style="background: var\(--color-primary\); color: white; text-align: center;">)',
        faq_html + r"\1",
        content,
        count=1,
    )

    # Insert FAQ schema before </head>
    content = re.sub(
        r"(</head>)",
        faq_schema + "\n\\1",
        content,
        count=1,
    )

    return content


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_file(html_path, data):
    content = html_path.read_text(encoding="utf-8")
    original = content

    content = replace_title(content, data)
    content = replace_meta_description(content, data)
    content = replace_h1(content, data)
    content = replace_hero_paragraph(content, data)
    content = replace_local_expertise(content, data)
    content = inject_faq_section(content, data)

    if content == original:
        return "unchanged"

    html_path.write_text(content, encoding="utf-8")
    return "updated"


def main():
    location_dir = WEBSITE_DIR / "locations"
    if not location_dir.exists():
        print(f"ERROR: {location_dir} not found")
        return

    updated = skipped = errors = unchanged = 0

    for slug, data in LOCATION_DATA.items():
        # Handle both slug variants (chandler-s-ford + chandlers-ford)
        candidates = [
            location_dir / f"{slug}.html",
            location_dir / f"{slug.replace('-s-', 's-')}.html",  # chandler-s-ford -> chandlers-ford handled separately
        ]

        # Special case: also apply chandlers-ford content to chandler-s-ford.html if it exists
        if slug == "chandlers-ford":
            candidates.append(location_dir / "chandler-s-ford.html")

        processed_any = False
        for path in candidates:
            if not path.exists():
                continue
            try:
                result = process_file(path, data)
                processed_any = True
                if result == "updated":
                    updated += 1
                    print(f"  ✅ Updated: {path.name}")
                else:
                    unchanged += 1
                    print(f"  ⚠️  Unchanged (patterns not matched): {path.name}")
            except Exception as e:
                errors += 1
                print(f"  ❌ Error on {path.name}: {e}")

        if not processed_any:
            skipped += 1
            print(f"  ⏭  Skipped: {slug}.html (file not found)")

    print(f"\nDone — Updated: {updated}  Unchanged: {unchanged}  Skipped: {skipped}  Errors: {errors}")


if __name__ == "__main__":
    main()
