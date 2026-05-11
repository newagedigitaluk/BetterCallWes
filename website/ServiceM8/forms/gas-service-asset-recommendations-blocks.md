# Recommendations Section — Word Template Content

Drop-in content for the **Engineer's Recommendations** section of the Gas
Service and Maintenance Record document template (form UUID
`38ee6e7d-a2b1-476d-a50a-e863be3b8316`, document template UUID
`2a5fbbf8-6d1e-4af3-8afb-1dfac48bff7b`).

The form field that drives this section is **`Recommendations`** — a
multi-answer multiple-choice with four options:

- New Boiler
- Powerflush
- Magnetic Filter
- Smart Thermostat

ServiceM8 delivers a multi-answer value as a single comma-separated
string (e.g. `"New Boiler, Powerflush"`). Word's native `IF` field can
match individual values with the `*` wildcard, so each block below tests
for its own option and renders only if ticked.

## How to insert the IF fields in Word

1. In Word, place the cursor where the conditional content should appear.
2. Press **Ctrl+F9** to insert a pair of field braces `{ }` (typing `{`
   directly does not work — it must be a Word field).
3. Type the IF expression inside the braces.
4. Inside the IF, press **Ctrl+F9** again to insert the inner MERGEFIELD
   reference for `form_recommendations`.
5. Press **F9** to update the field. Right-click → **Toggle Field Codes**
   to flip between code view and rendered view.

## Outer wrapper — section heading

Show the heading and intro line only when at least one recommendation is
ticked. Wrap the entire recommendations section (heading + all four
blocks) in this outer IF:

```
{ IF "{ MERGEFIELD form_recommendations }" <> "" "
=============================================
ENGINEER'S RECOMMENDATIONS
=============================================

Following today's service, I've noted the following recommendations to
keep your heating system running safely and efficiently. There's no
obligation — these are simply my professional notes for your reference.

[INSERT THE FOUR BLOCKS BELOW HERE]

If you'd like a no-obligation quote for any of the items above, just
reply to this email or call me on 07700 155 655.
" "" }
```

---

## Block 1 — New Boiler

```
{ IF "{ MERGEFIELD form_recommendations }" = "*New Boiler*" "

▸ Boiler Upgrade

Based on what I've found today, your current boiler is approaching the
end of its serviceable life and a replacement would be the most
cost-effective option going forward.

A modern A-rated boiler will:

  • Cut your gas usage — typically 20–30% saving versus an older,
    non-condensing model
  • Heat your home faster and hold temperature more reliably
  • Come with a 10-year manufacturer's warranty (parts and labour)
  • Pair with a smart thermostat for full app and voice control
  • Be installed in one day with minimal disruption

I work with Worcester Bosch, Vaillant, Ideal and Viessmann — all top-tier
British and European brands. I'm happy to put together a fixed-price
quote covering the boiler, fitting, system flush, magnetic filter and
warranty registration so you know exactly where you stand.
" "" }
```

---

## Block 2 — Powerflush

```
{ IF "{ MERGEFIELD form_recommendations }" = "*Powerflush*" "

▸ System Powerflush

Today's checks have flagged sludge and debris in your heating system.
Over time this magnetite build-up coats the inside of radiators and the
boiler's heat exchanger, making the system work harder and shortening
its life.

A professional powerflush will:

  • Restore even heat across every radiator (no more cold spots)
  • Reduce running costs by improving heat transfer
  • Protect the boiler from premature failure
  • Quiet down a noisy, kettling system
  • Extend the life of pumps, valves and the heat exchanger

The flush takes around half a day, includes a fresh dose of inhibitor,
and is best paired with a magnetic filter (see below) to keep the system
clean afterwards.
" "" }
```

---

## Block 3 — Magnetic Filter

```
{ IF "{ MERGEFIELD form_recommendations }" = "*Magnetic Filter*" "

▸ Magnetic System Filter

Your system would benefit from a magnetic filter fitted on the return
pipework to the boiler.

What it does:

  • Continuously captures iron-oxide sludge before it reaches the boiler
  • Protects the heat exchanger and pump from damage
  • Keeps the system running at peak efficiency between services
  • Is checked and cleaned at every annual service (no extra work for you)

A magnetic filter is a one-off fit, takes about an hour, and is one of
the single most effective things you can do to extend the life of a
modern condensing boiler. Many manufacturers now require one for the
warranty to remain valid.
" "" }
```

---

## Block 4 — Smart Thermostat

```
{ IF "{ MERGEFIELD form_recommendations }" = "*Smart Thermostat*" "

▸ Smart Thermostat Upgrade

Your existing controls are working but are due an upgrade. A modern
smart thermostat gives you proper control over your heating and pays for
itself in saved gas within a couple of seasons.

Benefits:

  • Schedule heating around your actual routine (not the clock on the wall)
  • Control from your phone — turn the heating off when you're out, on
    before you get home
  • Room-by-room control with optional smart radiator valves
  • Compatible with Alexa, Google Home and Apple HomeKit
  • Typical saving: £80–£150 a year on gas

I install Hive, Nest, Tado and Drayton Wiser — happy to advise on which
is the best fit for your home and broadband setup.
" "" }
```

---

## Notes for testing

- After inserting all five IF fields, generate a test document from a
  form response with **all four** boxes ticked → all four blocks should
  render. Then a response with **none** ticked → the whole
  recommendations section should disappear.
- The wildcard match `"*New Boiler*"` is case-sensitive in Word fields.
  If SM8 ever outputs values with different casing, change to
  `"*new boiler*"` and tick a box to confirm.
- If you ever rename a recommendation choice in the form (e.g.
  "Powerflush" → "Power Flush"), you must update the matching string in
  the IF field too — Word doesn't track that link.
- For the price guide reference points (boiler, powerflush, filter,
  smart thermostat costs) — `website/docs/MASTER_PRICE_GUIDE_UK.md` has
  the up-to-date BCW figures if you'd rather embed indicative pricing
  than keep these blocks pricing-free.
