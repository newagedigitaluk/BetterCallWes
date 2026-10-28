"""Content for batch v5 (Sep-Oct 2026). Built by build_batch_v5.py.

Brief from Wes, 2026-09-24:
  - small jobs only: boiler servicing and repair, no installs
  - every post ends on a WhatsApp message (lands in ServiceM8, the booking
    assistant books it). No "comment QUOTE" lines.
  - seven formats: fault codes, heating-season timing, what a service costs,
    checks before booking, real jobs, local group questions, Wes on real jobs
  - real photos first; AI only puts Wes into his own job photos, or covers
    kit we have no photo of, and every image is checked before it goes out

Facts are taken from the pricing page and the fault-code database in
../Boiler Fault Codes. `check` notes are things Wes needs to confirm.

img:
  gen:<name>    scratch render from GPT Image 2.5 (copied into images/v5/src)
  work:<file>   Brand Images/Work Images
  brand:<file>  Brand Images
  card:hx       composite built in build_batch_v5.py
"""

NUM = "07700 155 655"

POSTS = [
    # 1 ─────────────────────────────────────────────────────────────────
    dict(
        key="heating-on", fmt="season", pillar="tips", slug="boiler-service",
        img=dict(src="gen:thermostat", banner="Heating on for the first time?", pos="bottom"),
        wa="Hi Wes, I'd like to book a boiler service.",
        body="""Putting the heating on for the first time since spring? Give it a proper test before you actually need it.

Turn the thermostat up a few degrees above the room temperature and leave it 20 minutes. Then walk round and feel every radiator.

Warm all over is what you want. Cold at the top means air, and you can bleed that yourself. Cold along the bottom usually means sludge. If nothing comes on at all, look at the pressure gauge on the boiler before anything else.

If it's been more than a year since the last service, book it now. The first cold week is when everyone rings round at once.""",
        cta="WhatsApp {num} to book a service.",
        tags="#Southampton #BoilerService #CentralHeating #GasSafe",
    ),
    # 2 ─────────────────────────────────────────────────────────────────
    dict(
        key="check-first", fmt="checks", pillar="tips", slug="boiler-repair",
        img=dict(src="work:IMG_1896.JPG", banner="Check these before you book", pos="bottom", anchor=0.0),
        wa="Hi Wes, my boiler has stopped working.",
        body="""Boiler stopped? Four things to check before you book anyone. Worth saving for later.

1. Pressure. Look at the gauge on the front. With the heating off it should sit around 1 to 1.5 bar. Below 1, a lot of boilers switch themselves off.

2. Gas. Does the hob light? If you're on a prepayment meter, check the credit.

3. Thermostat. Is it actually asking for heat? Flat batteries in a wireless stat catch people out every winter.

4. Reset. Press it once. If the fault comes straight back, leave it.

If all four check out and it still won't go, that's when you need an engineer.""",
        cta="WhatsApp {num} and get booked in.",
        tags="#Southampton #BoilerRepair #BoilerPressure #GasSafe",
    ),
    # 3 ─────────────────────────────────────────────────────────────────
    dict(
        key="vaillant-f28", fmt="fault_code", pillar="tips", slug="boiler-repair",
        img=dict(src="gen:vaillant_reset", banner="Vaillant showing F.28?", pos="top"),
        wa="Hi Wes, my Vaillant is showing F.28.",
        body="""F.28 on a Vaillant means it tried to light and couldn't. Vaillant's own manual calls it "ignition unsuccessful".

Before you ring anyone, check the gas is on by trying the hob. On a prepayment meter, check there's credit. On a frosty morning, a frozen condensate pipe outside can cause it too.

Then press reset once. If F.28 comes back, stop resetting, because doing it over and over won't fix it. The usual culprits are the ignition electrode, its lead, or the gas valve, and that needs someone to look at it.""",
        cta="WhatsApp a photo of the display to {num} to get it booked in.",
        tags="#Southampton #Vaillant #BoilerRepair #GasSafe",
    ),
    # 4 ─────────────────────────────────────────────────────────────────
    dict(
        key="electrodes", fmt="real_job", pillar="work", slug="boiler-repair",
        img=dict(src="work:IMG_1753.jpg", banner="Why it wouldn't light", pos="top", anchor=0.4),
        wa="Hi Wes, my boiler keeps failing to light.",
        check="Is this right: worn ignition electrodes and a hardened burner door seal, both replaced? Which make was it?",
        body="""These came out of a boiler that kept failing to light.

The ignition electrodes, the metal pins that make the spark, had worn. The burner door seal had gone hard too. Both got replaced and it fired first time.

If your boiler clicks away trying to light and then locks out, this is one of the first places to look.""",
        cta="WhatsApp {num} to get yours looked at.",
        tags="#Southampton #BoilerRepair #RealJob #GasSafe",
    ),
    # 5 ─────────────────────────────────────────────────────────────────
    dict(
        key="service-100", fmt="service_price", pillar="cost_reveal", slug="boiler-service",
        img=dict(src="gen:service_torch", banner="What a £100 service covers", pos="bottom"),
        wa="Hi Wes, I'd like to book a boiler service.",
        check="Does this list match what you actually do on a standard service?",
        body="""A standard boiler service with me is £100 and takes 45 minutes to an hour. This is what you're paying for.

The case comes off. I check the burner, the heat exchanger and the seals, and clean what needs it. I clear the condensate trap. I test the flue gases with an analyser, which tells me whether it's burning cleanly and safely. Gas pressure gets checked, and so do the safety devices.

You get a written report at the end.

If it's been neglected and the burner and heat exchanger need properly stripping and cleaning, that's the full strip-down service at £160. If yours needs it, I'll tell you before I do it.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #BoilerService #GasSafe #HeatingEngineer",
    ),
    # 6 ─────────────────────────────────────────────────────────────────
    dict(
        key="gas-detector", fmt="group_question", pillar="local", slug="gas-leak",
        img=dict(src="gen:meter_sunburst", banner="Smell gas? Don't borrow a detector", pos="top"),
        wa="Hi Wes, the gas emergency service has made my gas safe and I need a repair.",
        body="""Someone in a local Facebook group asked if anyone had a gas detector they could borrow.

If you can smell gas, please don't go looking for one. Do this instead.

Turn the gas off at the meter. The lever by the meter goes across the pipe to shut it.
Open doors and windows.
Don't touch light switches or anything electrical, and no naked flames.
Ring the National Gas Emergency Service on 0800 111 999. It's free, 24 hours a day.

They'll come out and make it safe. Once they have, I can find the fault and fix it.""",
        cta="For the repair afterwards, WhatsApp {num}.",
        tags="#Southampton #GasSafety #GasSafe #Hampshire",
    ),
    # 7 ─────────────────────────────────────────────────────────────────
    dict(
        key="whatsapp", fmt="personal", pillar="personal", slug="boiler-repair",
        img=dict(src="brand:IMG_1250.JPG", banner="WhatsApp me. Here's what happens.", pos="bottom", anchor=0.35),
        wa="Hi Wes, I'd like to book a job.",
        body="""The quickest way to get me booked is a WhatsApp.

Send a message to 07700 155 655 saying what's wrong. If there's a code on the boiler, add a photo of the display.

My booking assistant replies, asks the questions I'd ask, and offers you times from my actual diary. Pick one and you're booked. No voicemail, no waiting for a call back.

Your photos go straight onto the job, so I turn up knowing what I'm looking at.""",
        cta="WhatsApp {num}.",
        tags="#Southampton #Plumber #BoilerRepair #GasSafe",
    ),
    # 8 ─────────────────────────────────────────────────────────────────
    dict(
        key="pressure-dropped", fmt="season", pillar="tips", slug="boiler-repair",
        img=dict(src="gen:wes_boiler", banner="Pressure dropped over summer?", pos="top"),
        wa="Hi Wes, my boiler keeps losing pressure.",
        body="""Heating back on and the boiler's showing low pressure? Summer is when slow leaks show up, because nobody's looking at the gauge.

With the heating off, the needle should sit around 1 to 1.5 bar. If it's under 1, you can usually top it up yourself with the filling loop under the boiler. Open it slowly, watch the gauge, and close it firmly at about 1.5. Your boiler manual shows where it is on your model.

Topping up once after bleeding radiators is normal. Doing it every few weeks isn't. The water is going somewhere, often out through the pressure relief valve, or a slow weep at a valve somewhere. That's a repair worth doing before winter.""",
        cta="WhatsApp {num} to get it found and fixed.",
        tags="#Southampton #BoilerPressure #BoilerRepair #GasSafe",
    ),
    # 9 ─────────────────────────────────────────────────────────────────
    dict(
        key="ideal-l2", fmt="fault_code", pillar="tips", slug="boiler-repair",
        img=dict(src="gen:ideal_logic", banner="Ideal showing L2?", pos="top"),
        wa="Hi Wes, my Ideal boiler is showing L2.",
        body="""L2 on an Ideal Logic is an ignition lockout. The boiler tried to light, didn't see a flame, and gave up.

The checks are the same as any ignition fault. Make sure the gas is on and the hob lights. On a prepayment meter, check the credit. In cold weather, look at the plastic condensate pipe outside, because a frozen one can cause this on a lot of boilers.

Press reset once. If L2 comes back, don't keep resetting. It needs someone to look at the ignition side.""",
        cta="WhatsApp a photo of the display to {num} to get it booked in.",
        tags="#Southampton #IdealBoiler #BoilerRepair #GasSafe",
    ),
    # 10 ────────────────────────────────────────────────────────────────
    dict(
        key="heat-exchanger", fmt="real_job", pillar="work", slug="boiler-repair",
        img=dict(src="card:hx", banner="Heat exchanger swap", pos="top"),
        wa="Hi Wes, I'd like my boiler looked at.",
        check="Right that this was a heat exchanger replacement (new one left, the one that came out right)? Anything about the job worth adding?",
        body="""Heat exchanger swap. The new one is at the top. The one that came out is underneath.

The heat exchanger is where the burner's heat passes into your heating water. Look at the corrosion and deposits on the old one. That builds up over years, and the boiler burns less efficiently the whole time it's happening.

Servicing won't make a heat exchanger last forever, but catching build-up early is a lot cheaper than replacing one.""",
        cta="WhatsApp {num} to book a service or a repair.",
        tags="#Southampton #BoilerRepair #RealJob #GasSafe",
    ),
    # 11 ────────────────────────────────────────────────────────────────
    dict(
        key="bleed-rads", fmt="season", pillar="tips", slug="radiators",
        img=dict(src="gen:bleed_rad", banner="Cold at the top? Bleed it.", pos="bottom"),
        wa="Hi Wes, my radiators aren't heating properly.",
        body="""Radiator warm at the bottom and cold at the top? That's trapped air, and you can sort it yourself in five minutes.

Turn the heating off and let the radiators cool. Put the bleed key in the valve at the top corner and hold a cloth under it. Turn it a quarter turn anticlockwise. You'll hear air hiss out. When water starts to come out, close it.

Then check the boiler pressure. Bleeding lets water out, so it often needs topping back up to about 1 to 1.5 bar.

Cold along the bottom and warm at the top is a different problem. That's usually sludge, and bleeding won't touch it.""",
        cta="If it's more than air, WhatsApp {num}.",
        tags="#Southampton #Radiators #CentralHeating #GasSafe",
    ),
    # 12 ────────────────────────────────────────────────────────────────
    dict(
        key="older-boiler", fmt="group_question", pillar="local", slug="boiler-service",
        img=dict(src="work:IMG_4990.jpg", banner="Older boiler? Still worth a service", pos="top", anchor=0.25),
        wa="Hi Wes, I'd like to book a service on an older boiler.",
        check="Photo is an older boiler with the case off, not a Potterton Promax. Fine as a general image?",
        body="""Someone in a local group asked who'd service their Potterton Promax.

There's an idea that older boilers are past the point of servicing. It's the other way round. The older it is, the more a yearly check matters. Seals age and burners get dirty, and left alone a small fault turns into a breakdown.

An older boiler that's looked after can keep running safely for years. A standard service is £100 whatever the age. A back boiler is £120.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #BoilerService #GasSafe #Hampshire",
    ),
    # 13 ────────────────────────────────────────────────────────────────
    dict(
        key="no-hot-water", fmt="checks", pillar="tips", slug="boiler-repair",
        img=dict(src="work:IMG_1771.JPG", banner="Heating works but no hot water?", pos="bottom", anchor=0.3),
        wa="Hi Wes, my heating works but I've got no hot water.",
        check="Is IMG_1771 a diverter valve assembly?",
        body="""Radiators hot, but the taps run cold? On a combi, the usual suspect is the diverter valve. It's the part that switches the boiler between heating and hot water. This is one I took out.

Two things to check first. Is the pressure above 1 bar? Is the hot tap fully open? Some combis won't fire for hot water on a trickle.

If both are fine, it's likely the diverter. On my price list a diverter valve replacement is £180 to £250, parts and labour.""",
        cta="WhatsApp {num} to get it booked in.",
        tags="#Southampton #CombiBoiler #BoilerRepair #GasSafe",
    ),
    # 14 ────────────────────────────────────────────────────────────────
    dict(
        key="before-the-cold", fmt="season", pillar="tips", slug="boiler-service",
        img=dict(src="gen:clipboard_vaillant", banner="Book it before the cold week", pos="bottom"),
        wa="Hi Wes, I'd like to book a boiler service.",
        body="""Every year it goes the same way. The first properly cold week, boilers that have sat idle all summer get switched on hard, and the ones that were struggling give up.

A service now is £100. A breakdown in the first cold snap means a cold house while you wait, and then the repair on top.

If yours hasn't been serviced in the last 12 months, now's the time.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #BoilerService #GasSafe #Winter",
    ),
    # 15 ────────────────────────────────────────────────────────────────
    dict(
        key="baxi-e133", fmt="fault_code", pillar="tips", slug="boiler-repair",
        img=dict(src="brand:IMG_1253.JPG", banner="Baxi showing E133?", pos="top", anchor=0.2),
        wa="Hi Wes, my Baxi is showing E133.",
        body="""E133 on a Baxi means the boiler has lost its gas supply or its flame. Baxi's manual calls it "interruption of gas supply or flame failure".

Check the gas is on by trying the hob. On a prepayment meter, check the credit, because sometimes that's all it is. In a cold snap, check the condensate pipe outside hasn't frozen.

Then reset once. If E133 keeps coming back with the gas definitely on, it needs an engineer.""",
        cta="WhatsApp a photo of the display to {num} to get it booked in.",
        tags="#Southampton #Baxi #BoilerRepair #GasSafe",
    ),
    # 16 ────────────────────────────────────────────────────────────────
    dict(
        key="inhibitor", fmt="real_job", pillar="work", slug="central-heating",
        img=dict(src="work:IMG_1851.JPG", banner="What goes back in", pos="bottom", anchor=0.3),
        wa="Hi Wes, I keep having to top up my boiler pressure.",
        check="What was this job? After a flush, or a filter clean?",
        body="""Inhibitor going into a system after work on it.

It's a chemical that stops the inside of your radiators and boiler corroding. That corrosion is where black sludge comes from.

Every time the system is drained, or topped up with fresh water, the inhibitor gets diluted a bit more. So if you're topping up your pressure every few weeks, you're also slowly washing out the protection.

Two good reasons to get a pressure leak found rather than living with it.""",
        cta="WhatsApp {num} to get it looked at.",
        tags="#Southampton #CentralHeating #RealJob #GasSafe",
    ),
    # 17 ────────────────────────────────────────────────────────────────
    dict(
        key="check-engineer", fmt="group_question", pillar="trust", slug="gas-safety",
        img=dict(src="brand:IMG_1248.JPG", banner="How to check a gas engineer", pos="bottom", anchor=0.2),
        wa="Hi Wes, I'd like to book some gas work.",
        body=""""Looking for a reliable gas fitter near me." That one comes up in local groups a lot.

Whoever you find, check their Gas Safe ID card before they touch anything gas. The front has their photo, their licence number and an expiry date. The back lists the work they're qualified to do, like boilers or cookers.

You can check any engineer on the Gas Safe Register website, or by calling 0800 408 5500. It takes a minute.

Anyone genuine will be happy to show you. I'll show you mine on the doorstep.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #GasSafe #GasEngineer #Hampshire",
    ),
    # 18 ────────────────────────────────────────────────────────────────
    dict(
        key="cp12", fmt="service_price", pillar="cost_reveal", slug="cp12",
        img=dict(src="gen:meter_flare", banner="Landlords: CP12 from £90", pos="top"),
        wa="Hi Wes, I need a landlord gas safety certificate (CP12).",
        body="""Landlords, your gas safety certificate has to be renewed every 12 months, and your tenants need a copy.

With me a CP12 is £90, covering up to two gas appliances. Extra appliances like a hob or gas fire are £20 to £50 each.

You can have the check done up to two months before the old one runs out and keep the same renewal date, so there's no reason to leave it to the last week.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #Landlords #CP12 #GasSafe",
    ),
    # 19 ────────────────────────────────────────────────────────────────
    dict(
        key="prv-pipe", fmt="checks", pillar="tips", slug="boiler-repair",
        img=dict(src="work:IMG_1774.JPG", banner="Pipe dripping outside?", pos="top", anchor=0.5),
        wa="Hi Wes, there's a pipe dripping outside from my boiler.",
        check="Is IMG_1774 a pressure relief discharge pipe?",
        body="""Copper pipe poking out of your wall that drips, or a green stain on the brick under it? That's usually the pressure relief pipe from your boiler.

When the pressure inside gets too high, the relief valve lets water out through that pipe so nothing gets damaged. If it's dripping regularly, something is pushing the pressure up. Common causes are an expansion vessel that's lost its charge, or a filling loop left slightly open.

Worth a look: does your boiler's pressure climb above 2.5 bar when the heating's on?

On my price list an expansion vessel recharge is £100 to £160.""",
        cta="WhatsApp {num} to get it sorted.",
        tags="#Southampton #BoilerRepair #BoilerPressure #GasSafe",
    ),
    # 20 ────────────────────────────────────────────────────────────────
    dict(
        key="worcester-ea", fmt="fault_code", pillar="tips", slug="boiler-repair",
        img=dict(src="gen:worcester_panel", banner="Worcester showing EA?", pos="top"),
        wa="Hi Wes, my Worcester is showing an EA fault code.",
        body="""EA 227 or EA 229 on a Worcester Greenstar is an ignition fault. The boiler tried to light and couldn't detect a flame. On some models it tries up to five times before locking out.

Same checks as any ignition fault. Is the gas on at the hob? Credit on a prepayment meter? In frosty weather, is the condensate pipe outside frozen?

Reset it once. On a lot of Greenstars that's the reset button, and on some older ones you turn the control knob fully anticlockwise and back. If the code comes straight back, leave it and get it looked at.""",
        cta="WhatsApp a photo of the display to {num} to get it booked in.",
        tags="#Southampton #WorcesterBosch #BoilerRepair #GasSafe",
    ),
    # 21 ────────────────────────────────────────────────────────────────
    dict(
        key="sludge", fmt="season", pillar="tips", slug="power-flush",
        img=dict(src="work:IMG_1383.JPG", banner="Cold at the bottom? That's sludge", pos="top", anchor=0.6),
        wa="Hi Wes, my radiators are cold at the bottom.",
        check="Is IMG_1383 a flush in progress?",
        body="""Radiators warm at the top and cold along the bottom? That's usually sludge. It's black iron oxide that settles in the bottom of the panels, and bleeding won't shift it.

It builds up over years, faster if the inhibitor has been watered down by lots of topping up. It also makes the boiler work harder than it should.

The fix is flushing it out of the system. This is one mid-flush with the hoses on. If you want to know how bad yours is first, a system health check with a water test is £130.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #PowerFlush #Radiators #GasSafe",
    ),
    # 22 ────────────────────────────────────────────────────────────────
    dict(
        key="what-to-send", fmt="group_question", pillar="local", slug="boiler-repair",
        img=dict(src="brand:IMG_1256.JPG", banner="Boiler playing up? Send me this", pos="top", anchor=0.25),
        wa="Hi Wes, my boiler is playing up. Here are the details:",
        body=""""Bit of an issue with my parents' Worcester combi." Posts like that come up in local groups all the time, and the first replies are always questions.

If you message me, these four things let me work out what's wrong and bring the right parts:

The make and model. It's on the front, or on a label underneath.
Any code on the display. A photo is perfect.
What the pressure gauge says.
Whether you've lost heating, hot water or both.""",
        cta="WhatsApp them to {num}.",
        tags="#Southampton #BoilerRepair #Plumber #GasSafe",
    ),
    # 23 ────────────────────────────────────────────────────────────────
    dict(
        key="strip-down", fmt="service_price", pillar="cost_reveal", slug="boiler-service",
        img=dict(src="work:IMG_2259.JPG", banner="Why the £160 service exists", pos="bottom", anchor=0.3),
        wa="Hi Wes, I'd like to book a strip-down service.",
        check="What was this job? OK to call it a strip-down candidate?",
        body="""Case off on an older boiler. That brown crust across the heat exchanger fins is years of build-up.

It still worked, which is the problem. A boiler like this carries on quietly burning more gas than it should, until one day it doesn't.

A standard service at £100 checks everything and cleans what's needed. When the burner and heat exchanger need properly stripping and cleaning like this, it's the full strip-down service at £160.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #BoilerService #GasSafe #HeatingEngineer",
    ),
    # 24 ────────────────────────────────────────────────────────────────
    dict(
        key="warranty", fmt="service_price", pillar="cost_reveal", slug="boiler-service",
        img=dict(src="work:IMG_1381.JPG", banner="Your warranty probably needs this", pos="top", anchor=0.4),
        wa="Hi Wes, I'd like to book an annual service for my boiler warranty.",
        body="""Got a newer boiler with a long warranty? Read the small print. Most manufacturers make a yearly service by a Gas Safe engineer a condition of the warranty.

Skip a year and the cover can be void, which you'll only find out when you try to claim for a big repair.

A yearly service is £100. Keep the paperwork somewhere you'll find it.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #BoilerService #WorcesterBosch #GasSafe",
    ),
    # 25 ────────────────────────────────────────────────────────────────
    dict(
        key="kettling", fmt="season", pillar="tips", slug="boiler-repair",
        img=dict(src="work:IMG_1140.JPG", banner="Boiler sounds like a kettle?", pos="bottom", anchor=0.35),
        wa="Hi Wes, my boiler is making a kettle noise.",
        body="""Rumbling, or a noise like a kettle coming to the boil? That's called kettling.

It happens when water overheats in part of the heat exchanger, usually because scale or sludge is restricting the flow. Southampton's hard water doesn't help.

It's not an emergency, but it is a boiler working harder than it should, and it tends to get worse. Get it looked at before winter rather than during it.""",
        cta="WhatsApp {num} to get it booked in.",
        tags="#Southampton #BoilerRepair #HardWater #GasSafe",
    ),
    # 26 ────────────────────────────────────────────────────────────────
    dict(
        key="stopcock", fmt="group_question", pillar="local", slug="plumbing",
        img=dict(src="gen:stopcock", banner="Do you know where yours is?", pos="top"),
        wa="Hi Wes, my stopcock won't turn.",
        body=""""Our kitchen pipe has just burst." That's a real post from a local group, and the first thing anyone needs in that moment is the stopcock.

It's usually under the kitchen sink, where the water main comes up through the floor. Sometimes it's in a downstairs loo or under the stairs. Find yours today, before you need it, and check it turns.

Clockwise shuts it off. If it's seized solid, don't force it. A stuck stopcock is a small job to replace.""",
        cta="If yours won't budge, WhatsApp {num}.",
        tags="#Southampton #Plumber #Stopcock #Winter",
    ),
    # 27 ────────────────────────────────────────────────────────────────
    dict(
        key="mag-filter", fmt="real_job", pillar="work", slug="boiler-service",
        img=dict(src="work:IMG_1468.JPG", banner="When was yours last emptied?", pos="bottom", anchor=0.4),
        wa="Hi Wes, I'd like to book a service and filter clean.",
        check="Do you clean the magnetic filter on a standard service? If not, I'll change the last line.",
        body="""That black cylinder on the pipes under a lot of boilers is a magnetic filter. It catches bits of iron sludge moving round your system before they reach the boiler.

It only works if someone empties it. Left for years, it fills up and stops catching anything.

If you've got one and can't remember the last time it was cleaned out, mention it when you book your service.""",
        cta="WhatsApp {num} to book.",
        tags="#Southampton #BoilerService #CentralHeating #GasSafe",
    ),
    # 28 ────────────────────────────────────────────────────────────────
    dict(
        key="low-pressure-codes", fmt="fault_code", pillar="tips", slug="boiler-repair",
        img=dict(src="gen:gauge_crouch", banner="Low pressure? Here are the codes", pos="top"),
        wa="Hi Wes, my boiler is showing a low pressure code.",
        body="""Low water pressure is behind a lot of boiler lockouts, and each brand shows it with a different code.

Vaillant: F.22
Ideal Logic: F1
Baxi: E119

Most boilers have a pressure gauge on the front too. With the heating off it should read about 1 to 1.5 bar.

If it's low, top it up with the filling loop and reset. If it keeps dropping, there's a leak somewhere, and that's the bit that needs finding.""",
        cta="WhatsApp {num} to get the leak found.",
        tags="#Southampton #BoilerPressure #BoilerRepair #GasSafe",
    ),
    # 29 ────────────────────────────────────────────────────────────────
    dict(
        key="clocks-back", fmt="season", pillar="tips", slug="heating-controls",
        not_before="2026-10-21", not_after="2026-10-24",
        img=dict(src="work:IMG_1733.JPG", banner="Clocks go back this Sunday", pos="bottom", anchor=0.4),
        wa="Hi Wes, my heating timer needs looking at.",
        body="""The clocks go back this Sunday, 25 October.

Smart thermostats and most newer timers change on their own. Older timers and a lot of basic programmers don't, so for the next few months your heating would come on an hour out.

Check it on Sunday morning. If the heating came on at 5 when you set it for 6, that's your answer. It's usually just the time setting, and the manual shows you how.

If the timer's dead or the display's gone blank, that's a quick swap.""",
        cta="WhatsApp {num} if yours needs replacing.",
        tags="#Southampton #CentralHeating #ClocksGoBack #GasSafe",
    ),
    # 30 ────────────────────────────────────────────────────────────────
    dict(
        key="frozen-condensate", fmt="season", pillar="emergency", slug="boiler-repair",
        not_before="2026-10-26",
        img=dict(src="gen:condensate_frost", banner="Frozen pipe? Warm water, not boiling", pos="top"),
        wa="Hi Wes, my boiler has stopped and I think the condensate pipe is frozen.",
        body="""One of the most common winter breakdowns isn't a broken boiler at all. It's a frozen condensate pipe.

Modern boilers drain water out through a plastic pipe, usually down an outside wall. In a hard frost it freezes, the water backs up, and the boiler locks out, often with an ignition fault code.

The fix: pour warm water, not boiling, slowly along the outside section of the pipe until it thaws. Boiling water can crack it. Then reset the boiler.

If yours freezes every winter, the pipe can be insulated or rerouted so it stops happening.""",
        cta="WhatsApp {num} if it won't come back on.",
        tags="#Southampton #BoilerRepair #Winter #GasSafe",
    ),
]


REELS = [
    dict(key="pressure", src="gen:wes_boiler", seconds=12,
         hook="Boiler pressure low? Here's the fix",
         body="1 to 1.5 bar with the heating off. Top up slowly with the filling loop.",
         caption="Pressure under 1 bar and the boiler's cut out? Top it up with the filling loop under the boiler, slowly, to about 1.5 with the heating off, then close it firmly.\n\nIf you're doing that every few weeks, there's a leak somewhere, and that's the repair."),
    dict(key="bleed", src="work:IMG_0700.JPG", seconds=12,
         hook="Radiator cold at the top?",
         body="Trapped air. Heating off, quarter turn on the bleed key, close it when water shows.",
         caption="Cold at the top is air. Heating off, bleed key in the top corner, quarter turn, close it when water comes out. Then check the boiler pressure, because bleeding drops it.\n\nCold along the bottom is sludge, and that's a different job."),
    dict(key="service-look", src="work:IMG_1139.JPG", seconds=12,
         hook="What a boiler service actually looks at",
         body="Burner, heat exchanger, seals, flue gases. £100 with a written report.",
         caption="Case off, burner and heat exchanger checked, seals checked, condensate trap cleared, flue gases tested with an analyser. £100, about 45 minutes to an hour, written report at the end."),
    dict(key="came-out", src="card:hx_old", seconds=12,
         hook="This came out of a boiler",
         body="Years of corrosion on a heat exchanger. Servicing catches it early.",
         caption="A heat exchanger that came out on a recent job. That corrosion builds up over years, and the boiler burns less efficiently the whole time.\n\nA yearly service catches it early."),
    dict(key="prv", src="work:IMG_1774.JPG", seconds=12,
         hook="Pipe dripping outside your house?",
         body="Usually the boiler's pressure relief pipe. Something is pushing the pressure too high.",
         caption="A copper pipe dripping out of the wall is usually the pressure relief pipe from your boiler. A regular drip means the pressure is going too high, often a flat expansion vessel. Expansion vessel recharge is £100 to £160 on my price list."),
    dict(key="f28", src="work:IMG_1863.JPG", seconds=12,
         hook="Vaillant showing F.28?",
         body="Ignition failure. Check the gas is on, reset once. If it comes back, stop.",
         caption="F.28 is Vaillant's ignition failure code. Check the hob lights, check prepayment credit, check the condensate pipe outside in frosty weather. Reset once. If it comes back, it needs an engineer."),
    dict(key="l2", src="work:IMG_1745.JPG", seconds=12,
         hook="Ideal boiler showing L2?",
         body="Ignition lockout. In winter, a frozen condensate pipe is a common cause.",
         caption="L2 on an Ideal Logic is an ignition lockout. Gas on? Credit on the meter? Condensate pipe frozen? Reset once, and if L2 comes back, get it looked at."),
    dict(key="ea", src="work:IMG_1447.JPG", seconds=12,
         hook="Worcester showing EA 227 or 229?",
         body="Ignition fault. Gas on? Reset once. Back again? Get it looked at.",
         caption="EA 227 and EA 229 are Worcester's ignition fault codes. The boiler tried to light and couldn't detect a flame. Check the gas, reset once, and if it's straight back, leave it for an engineer."),
    dict(key="clocks", src="work:IMG_1733.JPG", seconds=12,
         not_before="2026-10-21", not_after="2026-10-24",
         hook="Clocks go back Sunday 25 October",
         body="Older timers don't change themselves. Your heating could be an hour out.",
         caption="Clocks go back this Sunday. Smart stats change on their own, older timers don't. If your heating comes on an hour early next week, that's why. If the timer's dead, that's a quick swap."),
    dict(key="condensate", src="work:IMG_1899.JPG", seconds=12,
         not_before="2026-10-26",
         hook="Boiler died on a frosty morning?",
         body="Check the plastic pipe outside. Warm water, not boiling.",
         caption="Boiler locked out on a frosty morning? The plastic condensate pipe outside may have frozen. Pour warm water, not boiling, along it until it thaws, then reset the boiler."),
    dict(key="no-hot-water", src="work:IMG_1771.JPG", seconds=12,
         hook="Heating works but no hot water?",
         body="On a combi, the usual suspect is the diverter valve.",
         caption="Radiators hot, taps cold? On a combi that's usually the diverter valve, the part that switches between heating and hot water. Diverter valve replacement is £180 to £250 on my price list."),
    dict(key="whatsapp", src="brand:IMG_1258.JPG", seconds=12,
         hook="Quickest way to book me",
         body="WhatsApp 07700 155 655. A photo of the display helps.",
         caption="Send a WhatsApp to 07700 155 655 with what's wrong and a photo of the boiler display. My booking assistant offers you times from my actual diary and books you in."),
]
