# -*- coding: utf-8 -*-
"""Content for new_posts_batch_v4.json — posts 1-20.

Compact dicts; build_batch_v4.py expands them into the full post shape.
Array order IS posting order (cron: 08:07 / 13:07 / 18:07). Every index
≡ 1 (mod 3) — post_002, post_005, post_008 … — lands in the 13:07 slot and
must carry a strong personal post.
"""

POSTS_A = [

    # ---- 00 | 08:07 | local — mascot landmark -----------------------------
    {
        "pillar": "local",
        "topic": "Where's Wes today? — Southampton Common",
        "slug": "boiler-service",
        "link": "p211-wes-southampton-common",
        "itype": "asset",
        "ihint": "asset:logo_mascot",
        "caption": "Where's Wes today? 🌳",
        "scene": (
            "A bright late-summer photograph of Southampton Common — wide open parkland "
            "with mature oak and horse chestnut trees, a tarmac path curving through mown "
            "grass, dog walkers small in the distance, soft afternoon light"
        ),
        "fb": (
            "🌳 Where's Wes today?\n\n"
            "Cutting across the Common on the way to a service in Highfield. Best shortcut "
            "in the city and nobody will convince me otherwise.\n\n"
            "The Common is the bit of Southampton that tells you the season is turning "
            "before the calendar does. Conkers on the path. Dog walkers back in coats. "
            "Light going earlier every week.\n\n"
            "Which in my world means one thing — thousands of boilers are about to be "
            "asked to work hard for the first time in months, and a fair few of them "
            "aren't going to enjoy it.\n\n"
            "If yours has had six months off, get it looked at before everyone else "
            "remembers theirs exists.\n\n"
            "Where should the wrench turn up next? Drop a Southampton landmark in the "
            "comments and I'll try to get there.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "ig": (
            "Where's Wes today? 🌳\n\n"
            "Cutting across the Common on the way to a service in Highfield. Best shortcut "
            "in the city, no arguments.\n\n"
            "The Common tells you the season is turning before the calendar does. Conkers "
            "on the path. Coats back on. Light going earlier.\n\n"
            "Which means thousands of boilers round here are about to be asked to work "
            "hard for the first time in months — and a fair few won't enjoy it.\n\n"
            "Six months off? Worth a look before everyone else remembers theirs exists.\n\n"
            "Where should the wrench turn up next? Drop a landmark below.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "tw": (
            "Where's Wes today? 🌳\n\n"
            "Cutting across Southampton Common. Conkers on the path, coats back on — the "
            "season's turning.\n\n"
            "Which means a lot of boilers are about to work hard for the first time in "
            "months.\n\n{L}"
        ),
        "gb": (
            "Southampton Common is the spot that tells you the season is turning before "
            "the calendar does — conkers on the path, walkers back in coats, and the light "
            "going earlier every week. For a heating engineer that is the starting gun. "
            "Thousands of boilers across the city are about to be asked to work hard for "
            "the first time since spring, and the ones that have quietly developed a fault "
            "over the summer tend to announce it in the first cold week. That is also the "
            "week every engineer in Southampton is fully booked. An annual service now "
            "means the pressure, the seals, the flue readings and the heat exchanger all "
            "get checked while there is still room in the diary. Covering Southampton and "
            "the surrounding postcodes."
        ),
        "ig_tags": ["#SouthamptonCommon", "#LocalTrade", "#BoilerService"],
    },

    # ---- 01 | 13:07 | personal -------------------------------------------
    {
        "pillar": "personal",
        "topic": "The customer who tested my patience",
        "slug": "boiler-repair",
        "link": "p212-tested-my-patience",
        "itype": "brand",
        "ihint": "brand:wes_with_tools",
        "caption": "The customer who tested my patience 😅",
        "fb": (
            "😅 The customer who tested my patience.\n\n"
            "She rang six times before I'd even reached her road. Twice while I was "
            "driving. By the time I pulled up I'll be honest with you — I'd already made "
            "my mind up about her.\n\n"
            "Then I got inside.\n\n"
            "Nine days with no heating. Two young kids. Another firm had taken money off "
            "her and stopped answering the phone.\n\n"
            "She wasn't difficult. She was frightened, and not one person had explained "
            "anything to her.\n\n"
            "The fault took me forty minutes. The bit that actually mattered was the ten "
            "minutes after, sat at her kitchen table drawing the system out on the back of "
            "an envelope so she understood what had gone wrong and what it would cost.\n\n"
            "Most difficult customers aren't difficult. They've just been let down and "
            "left in the dark.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "The customer who tested my patience 😅\n\n"
            "Six calls before I'd even reached her road. I'd made my mind up about her "
            "before I got out of the van.\n\n"
            "Then I got inside. Nine days with no heating. Two young kids. Another firm "
            "had taken her money and stopped answering.\n\n"
            "She wasn't difficult. She was frightened, and nobody had explained anything.\n\n"
            "The fault took forty minutes. The ten minutes at the kitchen table afterwards "
            "mattered more.\n\n"
            "Most difficult customers have just been let down.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "tw": (
            "The customer who tested my patience 😅\n\n"
            "Six calls before I'd even reached her road. I'd made my mind up about her.\n\n"
            "Then I got inside. Nine days no heating. Another firm had ghosted her.\n\n"
            "Not difficult. Frightened.\n\n{L}"
        ),
        "gb": (
            "A customer once rang me six times before I had even reached her road, and I "
            "will admit I had formed an opinion before I got out of the van. Then I went "
            "inside. Nine days without heating, two young children in the house, and "
            "another company had taken a payment and stopped answering the phone. She was "
            "not being difficult. She was worried, and nobody had explained a single thing "
            "to her. The fault itself took about forty minutes to put right. The part that "
            "mattered was the ten minutes afterwards, sitting at the kitchen table sketching "
            "the system out so she understood what had failed and what it would cost. Clear "
            "explanations do more for people than speed ever will."
        ),
        "ig_tags": ["#TradeLife", "#SoleTrader", "#BoilerRepair", "#HonestTrade"],
    },

    # ---- 02 | 18:07 | tips — seasonal -------------------------------------
    {
        "pillar": "tips",
        "topic": "Five checks before the heating season starts",
        "slug": "boiler-service",
        "link": "p213-pre-winter-checks",
        "itype": "asset",
        "ihint": "asset:boiler",
        "caption": "Five checks before the cold arrives 🔧",
        "pos": "upper third",
        "fb": (
            "🔧 Five things worth checking now, before the heating goes on properly.\n\n"
            "1️⃣ Pressure. Cold system should sit around 1 to 1.5 bar. If it's dropped over "
            "the summer, something's letting go somewhere.\n\n"
            "2️⃣ Fire it up for twenty minutes. A fault that's been sat dormant since March "
            "will show itself now, not in the first frost.\n\n"
            "3️⃣ Walk round the rads. Cold at the top means air. Cold at the bottom means "
            "sludge — different problem, different fix.\n\n"
            "4️⃣ Check the condensate pipe outside. If it's exposed and unlagged, it will "
            "freeze and shut the boiler down.\n\n"
            "5️⃣ Test the thermostat and the timer. Batteries die quietly.\n\n"
            "Ten minutes of this in August saves a very cold, very expensive week later on.\n\n"
            "Save this for when you need it.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "ig": (
            "Five checks before the heating season starts 🔧\n\n"
            "1️⃣ Pressure — cold system should sit around 1 to 1.5 bar. Dropped over "
            "summer? Something's letting go.\n\n"
            "2️⃣ Run it for twenty minutes. Dormant faults show up now, not in the first "
            "frost.\n\n"
            "3️⃣ Walk the rads. Cold top = air. Cold bottom = sludge. Different problems.\n\n"
            "4️⃣ Look at the condensate pipe outside. Exposed and unlagged means it freezes.\n\n"
            "5️⃣ Test the thermostat and timer. Batteries die quietly.\n\n"
            "Ten minutes now saves a very cold week later.\n\n"
            "Save this for when you need it."
        ),
        "tw": (
            "Five checks before the heating season starts 🔧\n\n"
            "Pressure at 1-1.5 bar. Run it 20 mins. Walk the rads. Lag the condensate pipe. "
            "Test the thermostat.\n\n"
            "Ten minutes now saves a very cold week later.\n\n{L}"
        ),
        "gb": (
            "Before the heating goes on properly, five checks are worth ten minutes of your "
            "time. First, pressure: a cold system should sit at roughly 1 to 1.5 bar, and a "
            "drop over the summer points to a slow loss somewhere. Second, run the heating "
            "for twenty minutes — a fault that has been dormant since spring will show "
            "itself now rather than in the first frost. Third, walk round the radiators: "
            "cold at the top means trapped air, cold at the bottom means sludge, and those "
            "are two different problems. Fourth, look at the condensate pipe outside and lag "
            "it if it is exposed, because a frozen one shuts the boiler down. Fifth, test "
            "the thermostat and timer. Serving Southampton and surrounding areas."
        ),
        "ig_tags": ["#HeatingTips", "#BoilerService", "#HomeMaintenance", "#AutumnPrep"],
    },

    # ---- 03 | 08:07 | work ------------------------------------------------
    {
        "pillar": "work",
        "topic": "Real job — hot water fine, heating dead",
        "slug": "boiler-repair",
        "link": "p214-diverter-valve-job",
        "itype": "work",
        "ihint": "work:boiler_repair",
        "caption": "Hot water fine. Heating dead. 🔍",
        "fb": (
            "🔍 Real job: hot water perfect, radiators stone cold.\n\n"
            "That combination narrows things down fast. If the boiler will heat water on "
            "demand but won't send anything to the rads, the burner and the pump are "
            "usually fine — it's the bit that decides where the hot water goes.\n\n"
            "Diverter valve. It had stuck on the hot-water side and stayed there.\n\n"
            "Multimeter on the actuator confirmed it was getting the signal and doing "
            "nothing about it. Cartridge and actuator swapped, system rebalanced, every rad "
            "checked warm before I packed up.\n\n"
            "The reason I like this fault is that it's genuinely diagnosable. No guessing, "
            "no throwing parts at it and hoping. The symptom tells you where to look.\n\n"
            "Heating dead but hot water fine? That's the one.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "Hot water perfect. Radiators stone cold. 🔍\n\n"
            "That combination narrows it down fast. If the boiler heats water on demand but "
            "sends nothing to the rads, the burner and pump are usually fine — it's the bit "
            "that decides where the hot water goes.\n\n"
            "Diverter valve. Stuck on the hot-water side.\n\n"
            "Multimeter confirmed it was getting the signal and ignoring it. Cartridge and "
            "actuator swapped, system rebalanced, every rad checked warm before I left.\n\n"
            "No guessing. The symptom tells you where to look.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "tw": (
            "Real job: hot water perfect, rads stone cold 🔍\n\n"
            "That combination is a gift. Burner and pump fine — it's the valve deciding "
            "where the hot water goes.\n\n"
            "Diverter valve, stuck. Swapped and rebalanced.\n\n{L}"
        ),
        "gb": (
            "A recent Southampton job: plenty of hot water at the taps, but every radiator "
            "stone cold. That combination narrows the diagnosis down quickly. If a combi "
            "boiler will heat water on demand yet send nothing to the heating circuit, the "
            "burner and the pump are usually working — the problem is the component that "
            "decides where the hot water goes. In this case the diverter valve had stuck on "
            "the hot-water side. A multimeter on the actuator confirmed it was receiving the "
            "signal and not acting on it. The cartridge and actuator were replaced, the "
            "system rebalanced, and every radiator checked warm before I packed up. Faults "
            "like this are genuinely diagnosable, which means no parts fitted on a hunch."
        ),
        "ig_tags": ["#BoilerRepair", "#DiverterValve", "#RealJob", "#HeatingRepair"],
    },

    # ---- 04 | 13:07 | personal -------------------------------------------
    {
        "pillar": "personal",
        "topic": "The boiler I couldn't save",
        "slug": "new-boiler",
        "link": "p215-boiler-i-couldnt-save",
        "itype": "brand",
        "ihint": "brand:wes_with_tools",
        "caption": "The boiler I couldn't save 💭",
        "fb": (
            "💭 The boiler I couldn't save.\n\n"
            "Eighteen years old. Owned by a lady who'd lived in that house since the day it "
            "was built, and she loved that boiler the way people love an old car.\n\n"
            "Heat exchanger had gone. Parts obsolete. I rang three suppliers and a mate who "
            "hoards old stock, just in case.\n\n"
            "Nothing.\n\n"
            "I've had jobs where telling someone they need a new boiler is the easy bit. "
            "That wasn't one of them. She wasn't upset about the money. She was upset "
            "because her husband had chosen it.\n\n"
            "So I did the only thing that felt right. Took a photo of the old badge, printed "
            "it, and left it on the worktop next to the new paperwork.\n\n"
            "Some jobs aren't about the boiler at all.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "The boiler I couldn't save 💭\n\n"
            "Eighteen years old. Owned by a lady who'd lived in that house since it was "
            "built, and she loved that boiler like people love an old car.\n\n"
            "Heat exchanger gone. Parts obsolete. I rang three suppliers and a mate who "
            "hoards old stock. Nothing.\n\n"
            "She wasn't upset about the money. She was upset because her husband had chosen "
            "it.\n\n"
            "So I photographed the old badge, printed it, and left it on the worktop next to "
            "the new paperwork.\n\n"
            "Some jobs aren't about the boiler at all."
        ),
        "tw": (
            "The boiler I couldn't save 💭\n\n"
            "18 years old. Heat exchanger gone, parts obsolete. Rang three suppliers. "
            "Nothing.\n\n"
            "She wasn't upset about the money — her husband had chosen it.\n\n"
            "Some jobs aren't about the boiler.\n\n{L}"
        ),
        "gb": (
            "Not every boiler can be repaired, and the conversation that follows is rarely "
            "about money. A customer had an eighteen-year-old unit with a failed heat "
            "exchanger and no parts left in circulation anywhere I could find. I rang three "
            "suppliers and a contact who keeps old stock before accepting it was beyond "
            "saving. She had lived in the house since it was built and her late husband had "
            "chosen that boiler, which made the decision harder than any quote. When a "
            "replacement really is the only option I say so plainly, explain why, and give a "
            "written price before anything is ordered. When a repair is still sensible I say "
            "that too. Honest advice either way, across Southampton and the surrounding "
            "postcodes."
        ),
        "ig_tags": ["#NewBoiler", "#TradeLife", "#HonestAdvice", "#SoleTrader"],
    },

    # ---- 05 | 18:07 | emergency -------------------------------------------
    {
        "pillar": "emergency",
        "topic": "First cold snap and no heat — what to check",
        "slug": "boiler-repair",
        "link": "p216-first-cold-snap-no-heat",
        "itype": "brand",
        "ihint": "brand:wes_with_phone",
        "caption": "First cold snap, no heat? ❄️",
        "fb": (
            "❄️ First proper cold night of the year and the heating won't fire.\n\n"
            "It happens to hundreds of homes in Southampton the same week, every year. Here "
            "is what to check before you panic.\n\n"
            "🔎 Is there a fault code on the display? Photograph it.\n"
            "🔎 Pressure gauge — below 0.5 bar and the boiler will lock itself out.\n"
            "🔎 Thermostat batteries. Dead ones look exactly like a dead boiler.\n"
            "🔎 Has anything tripped in the consumer unit?\n"
            "🔎 Gas on? Check a hob ring lights.\n\n"
            "Still nothing — send me a WhatsApp video on 07700 155 655. Show me the display, "
            "the gauge and the pipework. I can usually tell you what's failed before I "
            "leave, which means I turn up with the right part rather than an empty guess.\n\n"
            "No heating in a cold house with kids or elderly relatives is a genuine "
            "emergency, and I treat it as one."
        ),
        "ig": (
            "First proper cold night and the heating won't fire ❄️\n\n"
            "It happens to hundreds of Southampton homes in the same week every year. Check "
            "these first:\n\n"
            "🔎 Fault code on the display — photograph it\n"
            "🔎 Pressure gauge — under 0.5 bar and it locks out\n"
            "🔎 Thermostat batteries — dead ones look like a dead boiler\n"
            "🔎 Anything tripped in the consumer unit\n"
            "🔎 Gas on? Check a hob ring lights\n\n"
            "Still nothing? Send me a WhatsApp video. Show me the display, the gauge, the "
            "pipework. I can usually name the fault before I set off — so I arrive with the "
            "right part.\n\n"
            "A cold house with kids or elderly relatives is a real emergency."
        ),
        "tw": (
            "First cold snap, no heat? ❄️\n\n"
            "Check: fault code, pressure (under 0.5 bar = lockout), thermostat batteries, "
            "tripped breaker, gas on.\n\n"
            "Still dead? WhatsApp me a video — 07700 155 655.\n\n{L}"
        ),
        "gb": (
            "The first genuinely cold night of the year is when Southampton discovers which "
            "boilers survived the summer. If yours will not fire, there are five things "
            "worth checking before you call anyone. Look for a fault code on the display and "
            "photograph it. Check the pressure gauge, because below roughly 0.5 bar most "
            "boilers lock themselves out. Replace the thermostat batteries, since a dead "
            "thermostat looks identical to a dead boiler. Check nothing has tripped in the "
            "consumer unit. Confirm the gas supply is on by lighting a hob ring. If it is "
            "still dead, send a short WhatsApp video showing the display, the gauge and the "
            "pipework — remote diagnosis means the right part comes with me rather than "
            "being ordered later."
        ),
        "ig_tags": ["#NoHeating", "#BoilerRepair", "#Emergency", "#ColdSnap"],
    },

    # ---- 06 | 08:07 | personal (asset) ------------------------------------
    {
        "pillar": "personal",
        "topic": "What I keep in my glovebox",
        "slug": "plumbing",
        "link": "p217-in-my-glovebox",
        "itype": "asset",
        "ihint": "asset:van",
        "caption": "What lives in my glovebox 🚐",
        "fb": (
            "🚐 What's actually in my glovebox. Not the van — the glovebox.\n\n"
            "🖊️ Two pens, because one always walks off\n"
            "📒 A paper notebook. Phones die, paper doesn't\n"
            "🔦 A pen torch that fits in a shirt pocket\n"
            "🧻 Blue roll, for wiping hands before I touch someone's door handle\n"
            "🍫 A cereal bar that's been there since roughly last winter\n"
            "🧦 A spare pair of socks. Ask anyone who's knelt in a puddle under a sink\n"
            "🚪 Overshoes, always, so nobody has to watch me walk over their carpet\n\n"
            "None of it is impressive. All of it exists because something went wrong once "
            "and I never wanted it to happen again.\n\n"
            "That's most of this trade, honestly. A long list of small lessons.\n\n"
            "What's the one thing in your car that's saved you? Go on."
        ),
        "ig": (
            "What's actually in my glovebox 🚐\n\n"
            "🖊️ Two pens — one always walks off\n"
            "📒 A paper notebook. Phones die, paper doesn't\n"
            "🔦 Pen torch that fits in a shirt pocket\n"
            "🧻 Blue roll, for hands before I touch a door handle\n"
            "🍫 A cereal bar of unknown age\n"
            "🧦 Spare socks. Ask anyone who's knelt in a puddle under a sink\n"
            "🚪 Overshoes, always\n\n"
            "None of it impressive. All of it there because something went wrong once and I "
            "didn't fancy a repeat.\n\n"
            "That's most of this trade — a long list of small lessons.\n\n"
            "What's the one thing in your car that's saved you?"
        ),
        "tw": (
            "What's in my glovebox 🚐\n\n"
            "Two pens. Paper notebook. Pen torch. Blue roll. A cereal bar of unknown age. "
            "Spare socks. Overshoes.\n\n"
            "None of it impressive. All of it there because something went wrong once.\n\n{L}"
        ),
        "gb": (
            "People ask what a plumber carries in the van. The more revealing answer is what "
            "is in the glovebox: two pens because one always disappears, a paper notebook "
            "because phones run out of battery, a pen torch, blue roll for wiping hands "
            "before touching a customer's door handle, spare socks for the days that involve "
            "kneeling in a puddle under a sink, and a pair of overshoes so nobody has to "
            "watch me walk across their carpet in work boots. None of it is impressive kit. "
            "Every item is there because something went wrong once and I did not want a "
            "repeat. Small habits are what make a job feel tidy from the customer's side. "
            "Covering Southampton and surrounding areas."
        ),
        "ig_tags": ["#VanLife", "#TradeLife", "#Plumbing", "#BehindTheScenes"],
    },

    # ---- 07 | 13:07 | personal -------------------------------------------
    {
        "pillar": "personal",
        "topic": "The job that taught me to check twice",
        "slug": "boiler-repair",
        "link": "p218-check-twice",
        "itype": "brand",
        "ihint": "brand:wes_with_tools",
        "caption": "The job that taught me: check twice ✋",
        "fb": (
            "✋ The job that taught me to check twice.\n\n"
            "Early on in my career. Customer said the boiler was losing pressure. I found a "
            "weeping valve, changed it, topped the system up, wrote it up as done and drove "
            "off feeling pretty good about myself.\n\n"
            "Four days later, same call. Same pressure drop.\n\n"
            "There was a second leak. Under the floor, in the far corner of the lounge, "
            "quietly soaking a joist while I was busy congratulating myself on the valve.\n\n"
            "The first fault I found wasn't wrong. It just wasn't the whole story — and I'd "
            "stopped looking the moment I found something that fitted.\n\n"
            "Now I don't close a job on the first thing I find. I check the system holds "
            "after the fix, not just that the fix looked right.\n\n"
            "Costs me twenty minutes. Has saved customers thousands.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "The job that taught me to check twice ✋\n\n"
            "Early days. Boiler losing pressure. I found a weeping valve, changed it, topped "
            "the system up, drove off pleased with myself.\n\n"
            "Four days later — same call, same pressure drop.\n\n"
            "Second leak. Under the floor in the corner of the lounge, quietly soaking a "
            "joist while I congratulated myself on the valve.\n\n"
            "The first fault wasn't wrong. It just wasn't the whole story, and I'd stopped "
            "looking the moment I found something that fitted.\n\n"
            "Now I check the system holds after the fix. Twenty minutes. Saved people "
            "thousands."
        ),
        "tw": (
            "The job that taught me to check twice ✋\n\n"
            "Found a weeping valve, fixed it, drove off happy. Four days later, same "
            "call.\n\n"
            "Second leak under the lounge floor.\n\n"
            "First fault found isn't always the whole story.\n\n{L}"
        ),
        "gb": (
            "Early in my career a customer's boiler was losing pressure. I found a weeping "
            "valve, replaced it, topped the system up and closed the job. Four days later "
            "the same call came in. There was a second leak under the lounge floor that had "
            "been quietly soaking a joist the whole time. The first fault I found was real — "
            "it simply was not the whole story, and I had stopped looking the moment I found "
            "something that fitted the symptom. Since then I do not sign off a pressure "
            "fault until the system has been left under watch and proven to hold. It adds "
            "twenty minutes to a visit and it has saved customers a great deal of money in "
            "hidden water damage."
        ),
        "ig_tags": ["#TradeLife", "#BoilerRepair", "#LessonsLearned", "#HonestTrade"],
    },

    # ---- 08 | 18:07 | local ------------------------------------------------
    {
        "pillar": "local",
        "topic": "Covering Bassett",
        "slug": "boiler-service",
        "link": "p219-bassett",
        "itype": "asset",
        "ihint": "asset:van_southampton",
        "caption": "Bassett — I know these houses 🏡",
        "fb": (
            "🏡 Bassett.\n\n"
            "Big gardens, mature trees, and a housing stock that runs from 1930s "
            "detacheds to modern infill — which means I never quite know what I'm walking "
            "into until the cupboard door opens.\n\n"
            "What I see a lot up there: system boilers with hot water cylinders, long pipe "
            "runs to the far end of the house, and radiators in the coldest room that never "
            "quite keep up. Nine times out of ten that's balancing rather than anything "
            "expensive.\n\n"
            "Bigger houses also mean the heating has more work to do. A system that limps "
            "through a mild autumn in a flat will make itself known in a four-bed with "
            "single-glazed bay windows.\n\n"
            "If yours hasn't been serviced this year, the diary is a lot friendlier now than "
            "it will be once the temperature drops.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "ig": (
            "Bassett 🏡\n\n"
            "Big gardens, mature trees, and everything from 1930s detacheds to modern "
            "infill. I never know what I'm walking into until the cupboard opens.\n\n"
            "What I see a lot up there: system boilers with cylinders, long pipe runs to the "
            "far end of the house, and one radiator in the coldest room that never keeps up. "
            "Usually balancing, not anything expensive.\n\n"
            "Bigger houses mean the heating works harder. A system that limps through a mild "
            "autumn in a flat will show itself in a four-bed with bay windows.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "tw": (
            "Covering Bassett 🏡\n\n"
            "System boilers, cylinders, long pipe runs, and one radiator at the far end "
            "that never keeps up.\n\n"
            "Usually balancing — not anything expensive.\n\n"
            "Servicing across SO16 before the cold.\n\n{L}"
        ),
        "gb": (
            "Bassett has some of the most varied housing stock in Southampton, from 1930s "
            "detached houses to modern infill, and the heating systems vary just as much. "
            "The common pattern up there is a system boiler paired with a hot water "
            "cylinder, long pipe runs to the far end of the property, and one radiator in "
            "the coldest room that never quite keeps up. That last one is usually a "
            "balancing issue rather than anything expensive. Larger houses also ask more of "
            "a heating system, so a boiler that coped in a mild autumn can struggle in a "
            "four-bedroom home with older windows. If the system has not been serviced this "
            "year, the diary is far more open now than it will be once temperatures drop."
        ),
        "ig_tags": ["#Bassett", "#SO16", "#BoilerService", "#LocalPlumber"],
    },

    # ---- 09 | 08:07 | tips -------------------------------------------------
    {
        "pillar": "tips",
        "topic": "Bleed your radiators before the first proper burn",
        "slug": "radiators",
        "link": "p220-bleed-before-first-burn",
        "itype": "asset",
        "ihint": "asset:radiator",
        "caption": "Bleed the rads before the cold ♨️",
        "pos": "upper third",
        "fb": (
            "♨️ Bleed your radiators now, not in the first cold week.\n\n"
            "Air collects in a heating system all summer while it's sat doing nothing. Come "
            "the first proper burn, that air is sat at the top of your rads stopping them "
            "heating and making the boiler work harder for less.\n\n"
            "How to do it properly:\n\n"
            "1️⃣ Heating off, system cool\n"
            "2️⃣ Start with the radiator furthest from the boiler\n"
            "3️⃣ Bleed key into the square socket at the top corner, quarter turn, cloth "
            "underneath\n"
            "4️⃣ Let the hiss run until water comes, then close it\n"
            "5️⃣ Work back towards the boiler, upstairs last\n"
            "6️⃣ Check the pressure afterwards — bleeding drops it\n\n"
            "That last step is the one everybody forgets, then wonders why the boiler locks "
            "out the next morning.\n\n"
            "Save this for when you need it."
        ),
        "ig": (
            "Bleed your radiators before the first proper burn ♨️\n\n"
            "Air collects all summer while the system sits idle. Come the first cold week "
            "it's sat at the top of your rads stopping them heating.\n\n"
            "1️⃣ Heating off, system cool\n"
            "2️⃣ Start furthest from the boiler\n"
            "3️⃣ Key in the square socket at the top corner, quarter turn, cloth underneath\n"
            "4️⃣ Hiss, then water, then close it\n"
            "5️⃣ Work back towards the boiler, upstairs last\n"
            "6️⃣ Check the pressure after — bleeding drops it\n\n"
            "Step six is the one everyone forgets.\n\n"
            "Save this for when you need it."
        ),
        "tw": (
            "Bleed the rads before the first cold week ♨️\n\n"
            "System cool. Start furthest from the boiler. Quarter turn, cloth underneath, "
            "close when water comes. Upstairs last.\n\n"
            "Then check the pressure — everyone forgets that bit.\n\n{L}"
        ),
        "gb": (
            "Air gathers in a heating system over the summer while it sits idle, and it ends "
            "up trapped at the top of your radiators where it stops them heating properly "
            "and makes the boiler work harder for less. Bleeding them before the first "
            "proper cold spell is a ten minute job. Turn the heating off and let the system "
            "cool, start with the radiator furthest from the boiler, fit the bleed key into "
            "the small square socket at the top corner and open it a quarter turn with a "
            "cloth underneath. When the hiss turns to water, close it. Work back towards the "
            "boiler and do upstairs last. Afterwards, check the pressure, because bleeding "
            "always drops it. Covering Southampton and nearby postcodes."
        ),
        "ig_tags": ["#Radiators", "#HeatingTips", "#HomeMaintenance", "#WarmHome"],
    },

    # ---- 10 | 13:07 | personal --------------------------------------------
    {
        "pillar": "personal",
        "topic": "The noise I dread hearing",
        "slug": "boiler-repair",
        "link": "p221-noise-i-dread",
        "itype": "brand",
        "ihint": "brand:wes_with_tools",
        "caption": "The noise I dread hearing 👂",
        "fb": (
            "👂 There's one noise that changes my whole mood on a job.\n\n"
            "Not the kettling. Not the banging pipes. Those are annoying but they're "
            "solvable and I know exactly where I'm going with them.\n\n"
            "It's the drip.\n\n"
            "A slow, steady drip from somewhere you can't see, in a house where nobody has "
            "noticed anything wrong. Because that drip has been going for months. It's found "
            "a joist, or the underside of a floorboard, or the back of a plasterboard wall, "
            "and it's been quietly working at it the whole time.\n\n"
            "The boiler fault I was called out for takes an hour. The drip is the "
            "conversation nobody was expecting to have.\n\n"
            "If you ever hear water where there shouldn't be water — even faintly, even "
            "once — don't file it under 'probably nothing'. Get someone to look while it's "
            "still cheap.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "The noise I dread hearing 👂\n\n"
            "Not kettling. Not banging pipes. Those are annoying but I know where I'm going "
            "with them.\n\n"
            "It's the drip.\n\n"
            "Slow, steady, from somewhere you can't see, in a house where nobody's noticed "
            "anything. Because it's been going for months — into a joist, or the underside "
            "of a floorboard, quietly working away.\n\n"
            "The fault I was called for takes an hour. The drip is the conversation nobody "
            "expected.\n\n"
            "Hear water where there shouldn't be water? Don't file it under probably "
            "nothing."
        ),
        "tw": (
            "The noise I dread hearing 👂\n\n"
            "Not kettling. Not banging pipes. It's the slow drip from somewhere you can't "
            "see, in a house where nobody's noticed.\n\n"
            "Because it's been going months.\n\n{L}"
        ),
        "gb": (
            "There is one sound on a job that changes my mood completely, and it is not "
            "kettling or banging pipework. Those are noisy but straightforward. It is the "
            "slow, steady drip from somewhere out of sight in a house where nobody has "
            "noticed anything wrong, because it means the water has been going for months "
            "into a joist, the underside of a floorboard or the back of a plasterboard wall. "
            "The fault I was actually called out for might take an hour. The hidden leak is "
            "the conversation the customer was not expecting. If you ever hear running or "
            "dripping water where there should not be any, even faintly, have it looked at "
            "while it is still an inexpensive problem."
        ),
        "ig_tags": ["#TradeLife", "#LeakDetection", "#BoilerRepair", "#HomeTips"],
    },

    # ---- 11 | 18:07 | work -------------------------------------------------
    {
        "pillar": "work",
        "topic": "Real job — combi swap in a Highfield terrace",
        "slug": "combi-install",
        "link": "p222-highfield-combi-swap",
        "itype": "work",
        "ihint": "work:install",
        "caption": "New combi, old terrace 🔧",
        "fb": (
            "🔧 Real job: combi swap in a Highfield terrace.\n\n"
            "Old back-boiler behind the fireplace, hot water cylinder eating half the airing "
            "cupboard, and a pipe layout that had clearly been added to by four different "
            "people over forty years.\n\n"
            "The install itself is the straightforward part. The work is in the planning — "
            "where the flue goes when you've got a neighbour's window two metres away, how "
            "you get a condensate run to a decent drain, whether the existing gas supply "
            "will carry the new demand.\n\n"
            "Answer on that last one was no, so a new gas run went in as part of the job. "
            "Better to find that out at the quote stage than halfway through a "
            "commissioning.\n\n"
            "Result: cylinder gone, airing cupboard back, and a system the next engineer can "
            "actually understand.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "Real job — combi swap in a Highfield terrace 🔧\n\n"
            "Old back-boiler behind the fireplace, cylinder eating half the airing cupboard, "
            "and pipework added to by four different people over forty years.\n\n"
            "The install is the easy bit. The work is the planning — where the flue goes "
            "with a neighbour's window two metres away, how you get a condensate run to a "
            "decent drain, whether the gas supply will carry the new demand.\n\n"
            "It wouldn't, so a new gas run went in. Better found at quote stage than "
            "mid-commissioning.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "tw": (
            "Real job: combi swap in a Highfield terrace 🔧\n\n"
            "Back-boiler out, cylinder gone, airing cupboard back.\n\n"
            "The install is the easy bit. Flue position, condensate run and gas supply are "
            "where the thinking goes.\n\n{L}"
        ),
        "gb": (
            "A recent installation in a Highfield terrace: an old back boiler behind the "
            "fireplace, a hot water cylinder taking up half the airing cupboard, and "
            "pipework that had clearly been extended by several different people over forty "
            "years. Fitting the new combi is the straightforward part of a job like this. "
            "The real work happens in the planning — deciding where the flue can legally and "
            "safely terminate when a neighbour's window is two metres away, finding a proper "
            "route for the condensate to a suitable drain, and checking whether the existing "
            "gas supply can carry the new appliance's demand. In this case it could not, so "
            "an upgraded gas run formed part of the quoted work rather than a surprise "
            "mid-job."
        ),
        "ig_tags": ["#CombiBoiler", "#BoilerInstall", "#Highfield", "#RealJob"],
    },

    # ---- 12 | 08:07 | trust -------------------------------------------------
    {
        "pillar": "trust",
        "topic": "Why I explain before I fix",
        "slug": "boiler-repair",
        "link": "p223-explain-before-i-fix",
        "itype": "brand",
        "ihint": "brand:wes_with_tools",
        "caption": "I explain it before I fix it 🗣️",
        "fb": (
            "🗣️ I don't start work until you know what I'm doing and why.\n\n"
            "Not because I'm being thorough for the sake of it. Because the alternative is a "
            "customer standing in their own kitchen watching a stranger take their boiler "
            "apart with no idea what's happening or what it's going to cost.\n\n"
            "So the order goes: find the fault, show you the fault, tell you what it takes "
            "to put right, give you the price, then start.\n\n"
            "If there's a cheaper option that's honest, you hear it. If a part is on its way "
            "out but isn't the cause today, you hear that too — with no pressure to do it "
            "now.\n\n"
            "You should never have to take my word for what's wrong. You should be able to "
            "see it.\n\n"
            "The £100 diagnostic covers the visit and the diagnosis, and any repair is "
            "quoted separately before I touch it.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "I explain it before I fix it 🗣️\n\n"
            "Not for the sake of being thorough. Because the alternative is you stood in "
            "your own kitchen watching a stranger dismantle your boiler with no idea what's "
            "happening or what it'll cost.\n\n"
            "The order: find the fault → show you the fault → explain the repair → give you "
            "the price → then start.\n\n"
            "Cheaper honest option? You hear it. Part on its way out but not today's "
            "problem? You hear that too, with no pressure.\n\n"
            "You shouldn't have to take my word for what's wrong. You should see it.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "tw": (
            "I explain it before I fix it 🗣️\n\n"
            "Find the fault. Show you the fault. Explain the repair. Give the price. Then "
            "start.\n\n"
            "You shouldn't have to take my word for what's wrong — you should be able to see "
            "it.\n\n{L}"
        ),
        "gb": (
            "I do not start work until the customer understands what is wrong and what it "
            "will cost. The order is always the same: find the fault, show it to you, "
            "explain what putting it right involves, give a clear price, and only then pick "
            "up a spanner. If there is a cheaper option that is genuinely sensible, you will "
            "hear about it. If a component is nearing the end of its life but is not the "
            "cause of today's problem, you will hear that too, with no pressure to deal with "
            "it now. The hundred pound diagnostic covers the visit and the diagnosis, and "
            "any repair is quoted separately before any work begins. Covering Southampton "
            "and surrounding postcodes."
        ),
        "ig_tags": ["#HonestTrade", "#BoilerRepair", "#NoSurprises", "#LocalPlumber"],
    },

    # ---- 13 | 13:07 | personal ---------------------------------------------
    {
        "pillar": "personal",
        "topic": "What I do when I get it wrong",
        "slug": "plumbing",
        "link": "p224-when-i-get-it-wrong",
        "itype": "brand",
        "ihint": "brand:wes_portrait",
        "caption": "What happens when I get it wrong 🙋🏿‍♂️",
        "fb": (
            "🙋🏿‍♂️ I get things wrong. Here's what happens when I do.\n\n"
            "I go back. I fix it. I don't charge for the second visit.\n\n"
            "That's it. No paperwork battle, no debate about whether it was really my fault, "
            "no suggesting the customer must have done something.\n\n"
            "Because here's the thing about working for yourself — my name is on the van, "
            "the invoice and the review. There's nowhere to hide and no head office to point "
            "at. If I fitted it and it's failed, that's mine.\n\n"
            "It's happened. A fitting I was sure of that wasn't quite sure of me. A "
            "diagnosis I closed too early. Both times the customer got a phone call from me "
            "before they had to chase.\n\n"
            "You can't promise you'll never make a mistake. You can promise how you'll "
            "behave when you do.\n\n"
            "Tag someone who needs this."
        ),
        "ig": (
            "What I do when I get it wrong 🙋🏿‍♂️\n\n"
            "I go back. I fix it. I don't charge for the second visit.\n\n"
            "That's it. No paperwork battle. No debate about whether it was really my fault. "
            "No suggesting the customer must have done something.\n\n"
            "Working for yourself means your name is on the van, the invoice and the review. "
            "No head office to point at. If I fitted it and it failed, it's mine.\n\n"
            "It's happened. Both times the customer got a call from me before they had to "
            "chase.\n\n"
            "You can't promise you'll never make a mistake. You can promise how you behave "
            "when you do."
        ),
        "tw": (
            "What I do when I get it wrong 🙋🏿‍♂️\n\n"
            "I go back. I fix it. I don't charge for the second visit.\n\n"
            "No head office to point at. My name's on the van, the invoice and the review.\n\n"
            "{L}"
        ),
        "gb": (
            "Everyone in this trade makes mistakes eventually. What matters is what happens "
            "next. If something I have fitted fails, I go back, I put it right, and I do not "
            "charge for the return visit. There is no argument about whether it was really "
            "my fault and no suggestion that the customer must have done something. Working "
            "for yourself means your name is on the van, the invoice and the review, so "
            "there is no head office to hide behind. It has happened to me — a fitting I was "
            "confident about, and a diagnosis I closed too early. On both occasions the "
            "customer heard from me before they had to chase. Twelve month workmanship "
            "guarantee across Southampton."
        ),
        "ig_tags": ["#HonestTrade", "#SoleTrader", "#Accountability", "#Plumbing"],
    },

    # ---- 14 | 18:07 | cost_reveal -------------------------------------------
    {
        "pillar": "cost_reveal",
        "topic": "Pre-winter service against an emergency callout",
        "slug": "boiler-service",
        "link": "p225-service-vs-callout-cost",
        "itype": "asset",
        "ihint": "asset:heatex",
        "caption": "Service now vs breakdown later 💷",
        "pos": "upper third",
        "fb": (
            "💷 Let's do the actual numbers, because nobody ever does.\n\n"
            "A boiler service before the season starts: £85. Booked at a time that suits "
            "you, in a warm house, with nothing at stake.\n\n"
            "An emergency callout when it fails in the cold: £100 diagnostic, plus parts, "
            "plus whatever the repair is quoted at, plus the days you spend cold while parts "
            "are sourced because half of Southampton is calling the same suppliers that "
            "week.\n\n"
            "And the fault that took the boiler out? Very often something a service would "
            "have caught — a clogging heat exchanger, a tired pump, a seal starting to weep, "
            "pressure quietly dropping since spring.\n\n"
            "The picture here is two heat exchangers from the same model. One serviced. One "
            "not. That's what the money is actually buying.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "ig": (
            "Let's do the actual numbers 💷\n\n"
            "Service before the season: £85. Booked when it suits you, warm house, nothing "
            "at stake.\n\n"
            "Emergency callout mid-winter: £100 diagnostic, plus parts, plus the repair "
            "quote, plus days cold while parts are sourced — because half of Southampton is "
            "ringing the same suppliers.\n\n"
            "And the fault that took it out is very often something a service catches. A "
            "clogging heat exchanger. A tired pump. A seal starting to weep.\n\n"
            "Two heat exchangers, same model. One serviced, one not.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "tw": (
            "The actual numbers 💷\n\n"
            "Service before the season: £85, booked when it suits you.\n\n"
            "Breakdown in the cold: £100 diagnostic + parts + repair + days waiting while "
            "everyone rings the same suppliers.\n\n{L}"
        ),
        "gb": (
            "It is worth comparing the two numbers properly. An annual boiler service booked "
            "ahead of the heating season costs eighty five pounds, at a time that suits you, "
            "in a warm house, with nothing at stake. A breakdown in the middle of winter "
            "starts with a hundred pound diagnostic, then parts, then the quoted repair, "
            "then however many cold days pass while components are sourced — and in a cold "
            "week every engineer in Southampton is calling the same suppliers. The fault "
            "that caused the failure is frequently something a service would have picked up: "
            "a heat exchanger clogging with debris, a tired pump, a seal beginning to weep, "
            "or pressure that has been quietly dropping since spring. Booking early is the "
            "cheaper decision almost every time."
        ),
        "ig_tags": ["#BoilerService", "#HeatingCosts", "#WinterPrep", "#HomeMaintenance"],
    },

    # ---- 15 | 08:07 | personal (asset) ---------------------------------------
    {
        "pillar": "personal",
        "topic": "The tool everyone gets wrong",
        "slug": "radiators",
        "link": "p226-tool-everyone-gets-wrong",
        "itype": "asset",
        "ihint": "asset:tools",
        "caption": "The tool everyone gets wrong 🔧",
        "pos": "upper third",
        "fb": (
            "🔧 The tool everyone gets wrong is the adjustable spanner.\n\n"
            "Not because it's a bad tool. Because of how people use it.\n\n"
            "Nine times out of ten I'm called to a fitting that's been rounded off by an "
            "adjustable that wasn't tightened onto the nut properly. The jaws had a bit of "
            "play, the spanner slipped under load, and now a ten minute job is a "
            "cut-it-out-and-start-again job.\n\n"
            "Two rules if you own one:\n\n"
            "🔩 Wind the jaws right up so there's zero movement on the nut before you pull\n"
            "🔩 Pull towards the fixed jaw, never the adjustable one\n\n"
            "And for anything you actually care about — radiator valves, compression "
            "fittings, tap connectors — use a proper spanner in the right size. The "
            "adjustable is for the nut you didn't expect.\n\n"
            "Save this for when you need it."
        ),
        "ig": (
            "The tool everyone gets wrong 🔧\n\n"
            "The adjustable spanner. Not a bad tool — it's how people use it.\n\n"
            "Most rounded-off fittings I'm called to were rounded by an adjustable that "
            "wasn't wound up tight. Jaws had play, spanner slipped under load, and a ten "
            "minute job became a cut-it-out job.\n\n"
            "Two rules:\n"
            "🔩 Wind the jaws right up — zero movement before you pull\n"
            "🔩 Pull towards the fixed jaw, never the adjustable one\n\n"
            "For anything you care about, use a proper spanner in the right size.\n\n"
            "Save this for when you need it."
        ),
        "tw": (
            "The tool everyone gets wrong 🔧\n\n"
            "The adjustable spanner. Jaws with play + load = a rounded fitting and a much "
            "bigger job.\n\n"
            "Wind it right up. Pull towards the fixed jaw.\n\n{L}"
        ),
        "gb": (
            "The most misused tool in any home toolbox is the adjustable spanner. It is not "
            "a bad tool, but the way it is usually handled causes damage. A large share of "
            "the rounded-off fittings I am called out to were rounded by an adjustable that "
            "had not been wound fully onto the nut. A small amount of play in the jaws, plus "
            "force, and the spanner slips — turning a ten minute job into cutting the "
            "fitting out and starting again. Two rules make it safe: wind the jaws up until "
            "there is no movement at all before applying force, and always pull towards the "
            "fixed jaw rather than the adjustable one. For radiator valves and compression "
            "fittings, use a correctly sized spanner instead."
        ),
        "ig_tags": ["#Tools", "#DIYTips", "#Plumbing", "#Radiators"],
    },

    # ---- 16 | 13:07 | personal ------------------------------------------------
    {
        "pillar": "personal",
        "topic": "The customer who still texts me at Christmas",
        "slug": "boiler-service",
        "link": "p227-texts-me-at-christmas",
        "itype": "brand",
        "ihint": "brand:wes_with_phone",
        "caption": "She still texts me every Christmas 💬",
        "fb": (
            "💬 There's a lady in Shirley who texts me every Christmas.\n\n"
            "Nothing about heating. Just a message asking how the family is and telling me "
            "what her grandchildren are up to.\n\n"
            "I fitted her boiler years ago. She'd had three quotes and picked mine, and it "
            "wasn't the cheapest. She told me afterwards she chose me because I was the only "
            "one who took my boots off without being asked.\n\n"
            "That's it. That's the whole reason.\n\n"
            "I think about that a lot when people ask how you build a business without an "
            "advertising budget. It isn't clever marketing. It's turning up, being decent, "
            "and treating someone's home like it belongs to someone.\n\n"
            "She still books her service with me every year. I've never once had to remind "
            "her.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "ig": (
            "There's a lady in Shirley who texts me every Christmas 💬\n\n"
            "Nothing about heating. Just asking how the family is and telling me what her "
            "grandchildren are up to.\n\n"
            "I fitted her boiler years ago. She'd had three quotes and mine wasn't the "
            "cheapest. She told me afterwards she chose me because I was the only one who "
            "took my boots off without being asked.\n\n"
            "That's the whole reason.\n\n"
            "People ask how you build a business with no ad budget. It isn't clever "
            "marketing. It's treating someone's home like it belongs to someone.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "tw": (
            "A lady in Shirley texts me every Christmas 💬\n\n"
            "I fitted her boiler years ago. Three quotes, mine wasn't the cheapest.\n\n"
            "She picked me because I took my boots off without being asked.\n\n"
            "That's the whole reason.\n\n{L}"
        ),
        "gb": (
            "A customer in Shirley sends me a message every Christmas. Nothing to do with "
            "heating — she just asks after the family and tells me what her grandchildren "
            "are up to. I fitted her boiler several years ago. She had three quotes and mine "
            "was not the cheapest, and she told me afterwards that she chose me because I "
            "was the only one who took his boots off at the door without being asked. That "
            "was the entire reason. People often ask how a sole trader builds a customer "
            "base without an advertising budget. It is not clever marketing. It is turning "
            "up when you said you would and treating someone's home as though it belongs to "
            "someone. She still books her annual service every year."
        ),
        "ig_tags": ["#Shirley", "#LocalTrade", "#BoilerService", "#WordOfMouth"],
    },

    # ---- 17 | 18:07 | local — mascot landmark ----------------------------------
    {
        "pillar": "local",
        "topic": "Where's Wes today? — Town Quay",
        "slug": "boiler-repair",
        "link": "p228-wes-town-quay",
        "itype": "asset",
        "ihint": "asset:logo_mascot",
        "caption": "Where's Wes today? ⚓",
        "scene": (
            "A photograph of Town Quay in Southampton — the waterfront with the Isle of "
            "Wight ferry terminal, moored boats, harbour railings and the water beyond, "
            "grey-blue coastal light"
        ),
        "fb": (
            "⚓ Where's Wes today?\n\n"
            "Town Quay. Parked up for ten minutes between jobs watching the ferry go out, "
            "which is honestly one of the better ways to eat a sandwich in this city.\n\n"
            "There's something about the waterfront that reminds you how much salt air this "
            "place throws at everything. It gets into external pipework, flue terminals, "
            "outside taps, boiler cases in garages. Properties near the water always show it "
            "first — a bit more corrosion, a bit more seizing, fittings that don't want to "
            "move when you need them to.\n\n"
            "If you're down near the front and your outside tap or flue terminal is looking "
            "rough, it's worth a look before the wet months arrive.\n\n"
            "Where should the wrench show up next? Drop a landmark below and I'll see what I "
            "can do.\n\n"
            "Comment QUOTE and I'll DM you my booking link."
        ),
        "ig": (
            "Where's Wes today? ⚓\n\n"
            "Town Quay. Ten minutes between jobs watching the ferry go out — one of the "
            "better ways to eat a sandwich in this city.\n\n"
            "The waterfront reminds you how much salt air this place throws at everything. "
            "External pipework, flue terminals, outside taps, boiler cases in garages. "
            "Properties near the water always show it first — more corrosion, more seizing, "
            "fittings that won't move when you need them to.\n\n"
            "Down near the front with a rough-looking outside tap? Worth a look before the "
            "wet months.\n\n"
            "Where next? Drop a landmark below."
        ),
        "tw": (
            "Where's Wes today? ⚓\n\n"
            "Town Quay, ten minutes between jobs watching the ferry go.\n\n"
            "Salt air is brutal on external pipework, flue terminals and outside taps. "
            "Waterfront homes always show it first.\n\n{L}"
        ),
        "gb": (
            "Town Quay is a good reminder of something that affects a lot of Southampton "
            "properties: salt air. Homes near the water consistently show more corrosion on "
            "external pipework, flue terminals, outside taps and boiler casings kept in "
            "garages. Fittings seize sooner, brass dulls faster, and components that should "
            "turn freely often will not when they are needed. If you live near the "
            "waterfront it is worth checking anything exposed before the wet months arrive — "
            "an outside tap that will not shut properly or a corroded flue terminal is far "
            "easier to deal with now than in the middle of winter. Covering Southampton and "
            "the surrounding postcodes for repairs, servicing and installations."
        ),
        "ig_tags": ["#TownQuay", "#Southampton", "#Waterfront", "#LocalPlumber"],
    },

    # ---- 18 | 08:07 | tips ------------------------------------------------------
    {
        "pillar": "tips",
        "topic": "Check your boiler pressure after a summer off",
        "slug": "boiler-service",
        "link": "p229-pressure-after-summer",
        "itype": "asset",
        "ihint": "asset:boiler",
        "caption": "Check your pressure after summer 📉",
        "fb": (
            "📉 Go and look at your boiler's pressure gauge. I'll wait.\n\n"
            "A cold system should read somewhere between 1 and 1.5 bar. Most boilers lock "
            "themselves out below about 0.5.\n\n"
            "Here's why now matters. Over the summer your heating has barely run, so a slow "
            "loss of pressure produces no symptoms at all — no cold rads, no noise, nothing. "
            "The needle just creeps down quietly for months.\n\n"
            "Then the heating goes on properly, the boiler asks the system for everything "
            "it's got, and it locks out on low pressure in the first cold week of the year.\n\n"
            "If yours has dropped since spring, that's not normal. Water has gone somewhere. "
            "Topping it up gets you going, but it doesn't answer the question of where.\n\n"
            "Two minutes today. Genuinely worth it.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "ig": (
            "Go and look at your pressure gauge 📉\n\n"
            "Cold system should read 1 to 1.5 bar. Most boilers lock out below about 0.5.\n\n"
            "Here's why now matters. Over summer the heating barely runs, so a slow pressure "
            "loss produces no symptoms at all. The needle just creeps down for months.\n\n"
            "Then the heating goes on properly, the boiler asks for everything, and it locks "
            "out in the first cold week.\n\n"
            "Dropped since spring? That isn't normal — water has gone somewhere. Topping up "
            "gets you going but doesn't answer where.\n\n"
            "Comment SERVICE and I'll DM you my service-booking link."
        ),
        "tw": (
            "Check your boiler pressure 📉\n\n"
            "Cold system: 1-1.5 bar. Under 0.5 and it locks out.\n\n"
            "A summer of barely running hides a slow loss — no symptoms until the first cold "
            "week.\n\n"
            "Dropped since spring? Water went somewhere.\n\n{L}"
        ),
        "gb": (
            "A cold heating system should show somewhere between 1 and 1.5 bar on the "
            "pressure gauge, and most boilers will lock themselves out below roughly 0.5 "
            "bar. The reason to check now rather than later is that a slow loss of pressure "
            "produces no symptoms while the heating is barely being used. The needle simply "
            "creeps down over the summer months with nothing to alert you. Then the heating "
            "is switched on properly, the boiler demands everything the system has, and it "
            "shuts down on low pressure during the first genuinely cold week of the year. If "
            "yours has dropped since spring, that is not normal wear — water has escaped "
            "somewhere and is worth investigating. Covering Southampton and nearby areas."
        ),
        "ig_tags": ["#BoilerPressure", "#HeatingTips", "#BoilerService", "#WinterPrep"],
    },

    # ---- 19 | 13:07 | personal ---------------------------------------------------
    {
        "pillar": "personal",
        "topic": "The thing homeowners apologise for that they shouldn't",
        "slug": "plumbing",
        "link": "p230-stop-apologising",
        "itype": "brand",
        "ihint": "brand:wes_portrait",
        "caption": "Please stop apologising for this 🙃",
        "fb": (
            "🙃 The thing people apologise to me for, constantly, that they never need to.\n\n"
            "The state of the cupboard.\n\n"
            "Every single week. I open an airing cupboard or crouch down under a sink and "
            "someone behind me says 'sorry about the mess' before I've even looked at "
            "anything.\n\n"
            "Listen. I have crawled through lofts full of forty years of Christmas "
            "decorations. I've moved a hoover, a bag of tennis balls and a box of "
            "photographs to reach a stopcock. I once found a bicycle in front of a boiler.\n\n"
            "None of it registers. I'm looking at pipework, not at your storage.\n\n"
            "The only thing that genuinely helps me is being able to physically reach the "
            "appliance. That's it. If I can get to it, I'm happy.\n\n"
            "So please, stop apologising. Put the kettle on instead.\n\n"
            "Tag someone who does this."
        ),
        "ig": (
            "The thing people apologise to me for that they never need to 🙃\n\n"
            "The state of the cupboard.\n\n"
            "Every single week. I open an airing cupboard or crouch under a sink and someone "
            "says 'sorry about the mess' before I've even looked.\n\n"
            "I've crawled through lofts full of forty years of Christmas decorations. Moved "
            "a hoover, a bag of tennis balls and a box of photographs to reach a stopcock. "
            "Once found a bicycle in front of a boiler.\n\n"
            "None of it registers. I'm looking at pipework, not your storage.\n\n"
            "Just let me reach the appliance. That's all.\n\n"
            "Tag someone who does this."
        ),
        "tw": (
            "The thing people apologise to me for that they never need to 🙃\n\n"
            "The state of the cupboard.\n\n"
            "I've moved a hoover, tennis balls and a box of photos to reach a stopcock. "
            "Once found a bicycle in front of a boiler.\n\n{L}"
        ),
        "gb": (
            "Almost every week a customer apologises to me for the state of a cupboard "
            "before I have even looked inside it. The airing cupboard, the space under the "
            "sink, the loft hatch — someone always says sorry about the mess. It genuinely "
            "does not register. I have crawled through lofts packed with decades of "
            "Christmas decorations, moved a hoover and a box of old photographs to reach a "
            "stopcock, and once found a bicycle parked in front of a boiler. None of it "
            "matters to the job. The only thing that actually helps is being able to "
            "physically reach the appliance, so clearing a path to it is worth far more than "
            "tidying anything else. Covering Southampton and surrounding postcodes."
        ),
        "ig_tags": ["#TradeLife", "#Plumbing", "#HomeTruths", "#LocalPlumber"],
    },
]
