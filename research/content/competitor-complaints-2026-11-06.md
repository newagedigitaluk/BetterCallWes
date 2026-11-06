# Competitor complaints analysis -- Southampton plumbing and heating
# 2026-11-06

**Status**: Script ready, waiting for DataForSEO pull (see NEEDS-HQ note). Angles below
are based on established UK trades complaint patterns; running the script will confirm
weighting and add verbatim review quotes.

The script at `website/scripts/competitor_reviews.py` will:
- Search "plumber Southampton", "heating engineer Southampton" etc. via
  `/v3/business_data/google/search/live`
- Pull 1-3 star reviews for the top 10 results via
  `/v3/business_data/google/reviews/live`
- Write JSON to `SEO-Data/competitor-reviews/YYYY-MM-DD/`
- Write a report (with verbatim quotes) to `SEO-Reports/competitor-reviews-YYYY-MM-DD.md`
- Estimated cost: under $0.10

---

## Complaint themes (well-established UK trades patterns)

These five appear consistently in trades review research and in the Sabri Suby content
Wes referenced. The script will confirm which are most common for Southampton specifically.

| Theme | What customers say |
|---|---|
| No-show | Booked, took time off work, nobody arrived. No call. |
| Poor communication | Cannot reach them. No update on when they are coming. Radio silence mid-job. |
| Surprise pricing | Quoted X, invoiced Y. "Extra parts", "took longer", no warning. |
| Mess | Left plasterboard dust, old fittings, muddy footprints. |
| Quality / rework | Same fault back within days. Bodge repair. Called a second firm to fix the first. |

Lateness and rudeness appear less frequently but reinforce the same trust deficit.

---

## Content angles for BCW reels and ads

Rules: never name or imply a named competitor (ASA comparative advertising rules).
Focus on what Wes does, not what others fail at.

---

### Angle 1 -- Show up. Every time.

**Pain addressed**: Customer books a plumber, clears their diary, and nobody comes.

**Reel hook** (spoken to camera or on-screen text):
> "I know what it feels like to wait in all day for a tradesperson who never shows.
> That is why I confirm the morning of every job, every time."

**Ad headline**: Booked. Confirmed. Here on time.

**Caption angle**:
Getting stood up by a tradesperson is one of the most frustrating things. I confirm
the morning of every job and I show up. If something changes, I call you first.
WhatsApp me to book a slot.

**Visual idea**: Wes checking his calendar on his phone in the van, then pulling up
outside a house at the agreed time.

---

### Angle 2 -- You will always know what is happening.

**Pain addressed**: The plumber goes quiet. No ETA, no update on the fault, no reply.

**Reel hook**:
> "Still waiting to hear back from your plumber? I reply to every message, same day.
> Here is what a job looks like when communication is not an afterthought."

**Ad headline**: Message me on WhatsApp. I actually reply.

**Caption angle**:
I keep you updated at every step: on my way, what I found, what it costs, when
it is done. You should never have to wonder what is happening in your own home.

**Visual idea**: Split screen -- WhatsApp conversation with fast replies vs. blank
chat. Or: Wes typing a voice note in the van before leaving a job.

---

### Angle 3 -- No surprises on the invoice.

**Pain addressed**: Quoted one price, invoiced far more with no prior warning.

**Reel hook**:
> "Before I pick up a single tool, we agree a price. If the job changes, I stop
> and tell you. You decide. I never add costs without asking first."

**Ad headline**: Price agreed before I start. No extras added after.

**Caption angle**:
I give you a fixed price before the work starts. If something unexpected comes
up mid-job I pause, explain what I found, and get your go-ahead before carrying
on. No nasty surprises when the invoice lands.

**Visual idea**: Wes on the phone or WhatsApp with a customer going through a quote,
then cutting to the finished job with a matching invoice on screen.

---

### Angle 4 -- I leave your home exactly as I found it.

**Pain addressed**: Customer has to clean up after the tradesperson leaves.

**Reel hook**:
> "End of every job: dust sheets up, tools packed, waste bagged. Watch."
> (Time-lapse of Wes packing up and leaving a spotless kitchen.)

**Ad headline**: Job done. Home clean. That is the standard.

**Caption angle**:
Overshoes on when I arrive. Dust sheets down. Waste bagged before I go.
Your home should look better after I visit, not worse.

**Visual idea**: POV shot laying dust sheet, then reveal of clean floor after job.
Strong before/after potential for a reel.

---

### Angle 5 -- Fixed properly, first time.

**Pain addressed**: The same fault comes back within a week. Customer has to call
a second engineer to undo a botched repair.

**Reel hook**:
> "If your boiler is making the same noise two days after a repair, the fault was
> not fixed -- the symptom was. Here is what a proper diagnosis looks like."

**Ad headline**: Gas Safe. Done right. No call-backs.

**Caption angle**:
Gas Safe registered, fully insured. I diagnose the root cause, not just the
symptom. If a fault comes back within 30 days I return at no charge.

**Visual idea**: Wes using a flue gas analyser or pressure gauge -- shows competence,
not just a spanner. Good trust signal for anyone who has been let down before.

---

### Angle 6 -- One person. You know exactly who is coming.

**Pain addressed**: Large companies send anyone. The person who quoted is not the
person who shows up. No accountability.

**Reel hook**:
> "When you book me, you get me. Not a subcontractor you have never met.
> Same number, same face, same accountability."

**Ad headline**: Gas Safe registered. Fully insured. 5-star rated in Southampton.

**Caption angle**:
I am Wes. I work alone, so you always know who is coming through your door.
No call-centres, no subcontractors, no surprises. Just a Gas Safe registered
engineer who answers his own WhatsApp.

**Visual idea**: Wes opening the van door and walking to a front door -- real,
not stock. Reinforces the "you know who you are getting" message.

---

## Notes for the reel pipeline

- Angles 1, 3 and 4 are the most visual and suit a 30-60 second reel.
- Angles 2 and 6 suit a talking-head or caption-only format (WhatsApp screenshots
  are strong social proof if Wes has permission to use them).
- Angle 5 needs trade-physics QA before filming: show real diagnostic tools,
  not generic "plumber with spanner" shots.
- None of these name or imply a specific competitor. The pain is universal;
  BCW is the solution.
- Once the DataForSEO data is pulled, the two or three highest-count themes should
  become priority reels for the next batch.
