# Topical map: bettercallwes.co.uk, November 2026

**Method:** FrameworkSEO.com lessons on topical maps for service businesses, keyword cannibalization and publishing order. Site structure from filesystem. Search volumes are estimates based on GSC impression data, UK national volumes, and Southampton population scaling (0.38% of UK). DataForSEO pull via `keyword_volumes.py` should be run to validate estimates before execution.

**Site foundation:**
Source context: BCW earns money by getting booked for boiler repair, boiler service, gas safety checks and plumbing jobs by homeowners and landlords in Southampton. Central entity: Gas Safe plumber and heating engineer. Central search intent: find a trusted local tradesperson and book.

---

## First 10 pages to write or fix, and why

### 1. Fix the homepage title (phase 1 / existing page)

**What:** Rewrite the homepage title from "Boiler Repair and Servicing Southampton: Same-Visit Fix" to something like "Plumber Southampton | Gas Safe Heating and Plumbing".

**Why:** The homepage and boiler-repair.html are both competing for "boiler repair Southampton". GSC already shows Google testing services.html, emergency-boiler-repair.html and boiler-repair.html for the same query alongside the homepage, pulling all four to low positions. The homepage should own "plumber Southampton" (400/mo, now ranking 2-5). Once it steps off boiler repair, that signal consolidates into boiler-repair.html.

**Gate:** This unblocks every other boiler repair ranking. Do it first.

---

### 2. Fix services.html to be a pure navigation page (phase 1 / existing page)

**What:** Remove "boiler repair" from the services.html title and meta description. The page should not target any transactional query. Its job is to pass link equity to individual service pages.

**Why:** GSC shows services.html now appears at position 36-50 for boiler repair queries, diluting boiler-repair.html. As a nav hub it should have zero competition with its children.

---

### 3. Add boiler-losing-pressure.html and boiler-no-hot-water.html to the sitemap (phase 2 / existing pages)

**What:** These two blog posts exist on disk but are absent from sitemap.xml and the blog index page. Add both entries to sitemap.xml and add cards to blog/index.html.

**Why:** boiler-losing-pressure.html targets "why does my boiler keep losing pressure" (national volume 8,100/mo, KD ~50). That is the highest-volume query on the whole site with a live page already written. It is invisible to crawlers. boiler-no-hot-water.html targets a 3,600/mo query in the same boat.

---

### 4. Merge bitterne-park.html, bitterne-manor.html and bitterne-village.html into bitterne.html (phase 4 / existing pages)

**What:** Create one strong Bitterne location page with sections for the neighbourhoods. 301-redirect the three sub-area URLs.

**Why:** "Plumber Bitterne" gets ~60/mo. "Plumber Bitterne Park" gets ~15/mo. The three sub-area pages each have minimal volume and split link equity. A single Bitterne page with sections for each neighbourhood is more useful, easier to give local facts to, and will rank better for all Bitterne variants.

---

### 5. Write: boiler making noise (new blog post)

**Target search:** "boiler making noise" / "kettling boiler" (national volume ~2,900/mo, KD ~48).

**Why first:** Top question from people who have a boiler problem but are not yet sure it needs repair. Feeds boiler-repair.html and power-flushing.html (sludge-caused kettling often leads to a power flush). Distinct from the pressure and hot water posts already live. Write structured around the noise type: banging, whistling, kettling, gurgling.

**Links to:** /services/boiler-repair.html, /services/power-flushing.html, /blog/how-much-does-a-boiler-repair-cost.html

---

### 6. Write: radiators not heating up (new blog post)

**Target search:** "radiators not heating up" / "radiator cold at bottom" (national volume ~3,500/mo, KD ~45).

**Why second:** Covers three distinct causes (sludge, air lock, pump fault) that lead to three different services: power flush, bleeding (DIY but confirms the fault), radiator repair. High information gain because most pages lump all radiator faults together. Feeds power-flushing.html, radiators.html and central-heating.html.

**Links to:** /services/power-flushing.html, /services/radiators.html, /services/central-heating.html

---

### 7. Write: how often should you service your boiler (new blog post)

**Target search:** "how often should you service your boiler" (national volume ~2,000/mo, KD ~42).

**Why third:** Directly feeds boiler-servicing.html, the second-highest revenue service on the site. Most answers online are generic. A Gas Safe engineer giving the honest answer with reasons (once a year, here is what gets missed on a cheap service, here is why it matters for warranty) scores well on E-E-A-T. Clear informational-to-transactional funnel.

**Links to:** /services/boiler-servicing.html, /services/landlord-gas-safety-certificates.html, /blog/how-much-does-a-boiler-service-cost.html

---

### 8. Write: signs your boiler needs replacing (new blog post)

**Target search:** "signs your boiler needs replacing" (national volume ~1,000/mo, KD ~40).

**Why fourth:** Distinct intent from is-it-worth-replacing-your-boiler.html (which answers the question after the reader has already decided to investigate). This one is earlier in the funnel: the reader has noticed symptoms and wants confirmation. The two posts form a natural cluster with cross-links. Feeds boiler-installation.html and boiler-repair.html.

**Links to:** /services/boiler-installation.html, /services/boiler-repair.html, /blog/is-it-worth-replacing-your-boiler.html, /blog/how-much-does-a-boiler-repair-cost.html

---

### 9. Create: boiler repair Eastleigh (new service-location page)

**Target search:** "boiler repair Eastleigh" (local volume ~80/mo, KD ~18).

**Why:** Eastleigh is a separate town (not a Southampton suburb), passes the dual warrant test: real search volume AND the page can include genuine local facts (jobs completed in Eastleigh, town centre buildings, Eastleigh housing stock, travel time from Wes's base). Currently the Eastleigh location page covers general plumbing; this targets the highest-value service in the area. Create only after phases 1-2 fixes are done and boiler-repair.html is consolidating signals.

**Gate:** boiler-repair.html must be the settled winner for boiler repair Southampton before spinning off sub-pages.

---

### 10. Fix gas-appliance-servicing.html title and slug mismatch (phase 2 / existing page)

**What:** The file is named `gas-appliance-servicing.html` but the title and H1 say "Gas Cooker and Hob Installation". Decide one intent and make the page consistent. The installation angle is recommended (servicing angle overlaps with boiler-servicing.html and gas-safety-check.html; installation is distinct).

**Why tenth:** Low volume (~25/mo) but a quick fix that removes a confusing signal. Also fix the double-word title on water-tank-services.html ("Water Tank Services Services").

---

## Cannibalization summary

| Pages competing | Query | Action |
|---|---|---|
| Homepage + boiler-repair.html + services.html + emergency-boiler-repair.html | boiler repair Southampton | Homepage fixes title; services.html removes transactional copy; boiler-repair.html is owner |
| Homepage + plumbing-repairs.html | plumber Southampton | Homepage keeps it; retarget plumbing-repairs.html to plumbing repairs Southampton |
| bitterne.html + bitterne-park.html + bitterne-manor.html + bitterne-village.html | plumber Bitterne | Merge sub-areas into bitterne.html with 301 redirects |
| locations/southampton.html + homepage | plumber in Southampton | Either add genuine local facts to southampton.html or redirect to homepage |

---

## Volume notes

All monthly volumes are estimates. Local volumes (Southampton queries) are scaled from GSC impression data and UK national benchmarks. National volumes (blog post targets) come from public UK keyword data. Run `website/scripts/seo/keyword_volumes.py` with the queries from this map to get live DataForSEO figures before writing any new page.
