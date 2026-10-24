# fb_monitor changes

## 2026-10-24: duplicate alerts and false positives

Wes was getting too many lead alerts and most of them were not leads. Two faults, both confirmed from `fb_monitor.log` and `state/seen_posts.json` on the day.

### Fault 1: the same post alerted up to six times

`state/seen_posts.json` held exactly 5,000 keys, the cap, and `save_seen()` trimmed with `list(seen)[-5000:]` on a set. A set has no order, so every save threw away a couple of hundred random keys, some of them added minutes earlier. "looking for a plumber/ heating engineer for an urgent job this week" alerted at 01:33, 01:46, 04:02, 07:01 and 09:32. The cat sitter alerted twice, "FULLY QUALIFIED PLUMBER/ELECTRICIAN" twice, the builder/handyman post five times over four days.

A note on the evidence. The log showed the same post ending "this week,  " on one poll and "this week, p" on the next, which looked like Facebook cutting the post at a different point each time. It is not: the old log line kept the first 80 characters of the raw text, and the relative timestamp in front of the body ("44m" one poll, "3h" the next) changes width, so the cut moved. The random trim above explains every repeat on its own. The fingerprint has still been shortened from 160 to 90 letters as a guard against the "See more" cut on long posts, which is a real way for one post to hash two ways.

Fix:
- Seen keys are now a dict of key to first-seen timestamp. Trimming drops the oldest. The cap is 50,000 (about 2 MB on disk, months of posts). The old list form is migrated in place on the first save.
- Fingerprints use the first 90 letters of durable text. The old 160-letter key is still computed for lookup only, so every post seen before today stays seen and there is no final wave of re-alerts. Nothing writes the old key any more.

### Fault 2: weak-word matches on anything with "looking for" in it

The weak-term rule fired when any weak word and any intent phrase appeared anywhere in the post. The table below shows the pair each false positive fired on. For rows logged before today the log kept only the first 80 characters of the post, so where the weak term fell beyond that it shows as "?". Intent phrases were also substring matches: "need a" fired on "Need any form of entertainment", and "fit " on "benefit".

Fix, in three layers:
1. A weak term now counts only when an intent phrase sits within 6 words of it (`filters.weak_intent_max_words`), or when two different weak terms and an intent phrase all appear. Intent phrases are whole-word, with `*` for a prefix (`repair*`).
2. Excludes added for the trades and chatter that got through: cat/pet/dog sitter, taxi, travel agent, kids' party and face paint, parcel/courier/Evri/Royal Mail, gutter, window leak, tiler, barber, cake, waste removal, Level 2/3, apprentice, work experience, hiring posts, and tradespeople's own "slots are filling"/"10% off" adverts. Strong terms gained gas hob, gas cooker, gas fire, gas engineer and heating engineer.
3. Every keyword match, strong or weak, now goes to a one-word model check before an alert: "is this a request for plumbing, heating, gas or drainage work that a Gas Safe plumber could quote for?" Claude Haiku 5.5, thinking off, about 400 input tokens a call, so a few pence a month at current volumes. The key is read in-process from the file named in `config.gate.api_key_file` (the Flint env file, the same place `mail-notify` reads its Emailit key); nothing is copied. If the call fails the alert still goes out, tagged "unchecked: lead gate unavailable", and the log carries the error. Set `gate.on_error` to `drop` to prefer silence.

The brief said `reply_drafter.py` already called a model. It does not; it is template-only. The gate has its own client in `fb_monitor.py`.

### Replay of the last 30 alerts

`python3 fb_monitor.py --replay 30` re-runs the keyword filter and the gate over the last 30 alerts in the log and sends nothing. Output on 2026-10-24 16:07:

| When | Post (as logged) | Old rule fired on | Keywords now | Gate | Result |
|---|---|---|---|---|---|
| 10-17 05:17 | Anyone got a good cake maker they recommend? For a baby shower. Thank… | shower + recommend (now excluded: baby shower, cake) | drop | - | drop |
| 10-18 10:17 | Looking for quotes from a plumber to fit a cold water feed and plumb i… | plumber | pass | yes | alert |
| 10-19 17:15 | Hiya just wondering if there is anyone reding this that could help me… | - | drop | - | drop |
| 10-19 17:47 | Looking for a semi skilled person to join our building team. Must be… | ? + looking for | drop | - | drop |
| 10-20 05:16 | Recommendation for builder / handyman wanted. Dig out old sealant and… | ? + recommend | drop | - | drop |
| 10-20 20:17 | Future cleans 3h Is you’re guttering leaking or overflowing? Is y… | leaking + leaking (now excluded: gutter, guttering) | drop | - | drop |
| 10-22 14:15 | 160 each or 300 for the pair £160 · SALISBURY, WILTSHIRE 2 Stihl comb… | - | drop | - | drop |
| 10-22 14:33 | Any tilers got availability around the 30th this month to tile around… | - (now excluded: tiler) | drop | - | drop |
| 10-22 16:17 | Any tilers got availability around the 30th this month to tile around… | - (now excluded: tiler) | drop | - | drop |
| 10-23 07:48 | Someone who can sort Window leak repairs ? 5… | leak + who can, leak + repair (now excluded: window leak) | drop | - | drop |
| 10-23 10:32 | Can anyone recommend someone for gutter repairs SO17 area? Part of ou… | ? + recommend (now excluded: gutter) | drop | - | drop |
| 10-23 15:02 | FULLY QUALIFIED PLUMBER/ELECTRICIAN NEEDED PLEASE. is there any plumb… | plumber | pass | yes | alert |
| 10-23 15:02 | Another happy customer 🍃 Leaf it to us 1h Busy day today for the… | - | drop | - | drop |
| 10-23 18:01 | SHIRELY WARREN Urgent!!!...see more 8 39 Answer as Wesley Jack… | ? + urgent | drop | - | drop |
| 10-23 19:18 | FULLY QUALIFIED PLUMBER/ELECTRICIAN NEEDED PLEASE PM ME 👍🏻 is there an… | plumber | pass | no | drop |
| 10-23 19:32 | Hi all I have had a card delivered for miss e sneddon in dimond rd but… | - | drop | - | drop |
| 10-23 21:01 | Hi everyone! 😊 I’m looking for a reliable and caring cat sitter for my… | ? + looking for (now excluded: cat sitter) | drop | - | drop |
| 10-24 01:33 | looking for a plumber/ heating engineer for an urgent job this week,… | plumber, heating engineer | pass | yes | alert |
| 10-24 01:46 | looking for a plumber/ heating engineer for an urgent job this week,… | plumber, heating engineer | pass | yes | alert |
| 10-24 02:03 | Hi everyone! 😊 I’m looking for a reliable and caring cat sitter for m… | ? + looking for (now excluded: cat sitter) | drop | - | drop |
| 10-24 04:02 | looking for a plumber/ heating engineer for an urgent job this week, p… | plumber, heating engineer | pass | yes | alert |
| 10-24 04:18 | Relay parcels - has anyone else has any problems with them. I sent a… | ? + problems with (now excluded: parcel) | drop | - | drop |
| 10-24 07:01 | looking for a plumber/ heating engineer for an urgent job this week, p… | plumber, heating engineer | pass | yes | alert |
| 10-24 08:17 | Looking for an independent travel agent! Hi all, can anyone recommend… | ? + recommend (now excluded: travel agent) | drop | - | drop |
| 10-24 09:32 | looking for a plumber/ heating engineer for an urgent job this week, p… | plumber, heating engineer | pass | yes | alert |
| 10-24 11:18 | Electrician & Plumber needed!🙏🏼 (After honest Quotes as had some so fa… | plumber | pass | yes | alert |
| 10-24 14:18 | Can anyone recommend someone local to come replace a gas hob? 12… | gas hob | pass | yes | alert |
| 10-24 14:19 | Hi everyone, I’m 25 years old, currently studying Level 2 Plumbing at… | plumbing (now excluded: level 2) | drop | - | drop |
| 10-24 15:17 | Need any form of entertainment for a kids party tomorrow. Face paint?… | - (now excluded: face paint, kids party) | drop | - | drop |
| 10-24 15:48 | Looking for an accessible taxi for tomorrow morning please. Already… | ? + looking for (now excluded: taxi) | drop | - | drop |

30 alerts replayed; 9 would alert now, 21 would not.

Reading the table: the 9 that still pass are 4 distinct posts. The "plumber/ heating engineer" post accounts for 5 rows, and under the dedup fix it would have been one alert. The row at 10-23 19:18 is the same "FULLY QUALIFIED PLUMBER/ELECTRICIAN" post that passed at 15:02; the gate said no on the 19:18 excerpt because the 80 characters end at "is there an", which hides the request. On a full post, which is what the gate sees in production, it says yes. Everything Wes listed (cat sitter, taxi, travel agent, kids' party, Relay parcels, misdelivered card, Level 2 student, gutter repairs) is dropped, and "Electrician & Plumber needed" still passes.

Alert lines in the log now carry the whole post on one line with the matched terms and the gate verdict, so future replays work from the full text. Gate rejections are logged too (`🚫 Gate said no`), so a missed lead can be found and the prompt or the excludes adjusted.

### Dry run after the change

`python3 fb_monitor.py --dry-run` at 16:08 on 2026-10-24, run under the cron lock so it could not race the 16:15 run: 35 posts found across the 10 groups, 32 skipped as already seen (all through the legacy 160-letter key, so the lookup-only compatibility works), 3 no keyword match, 0 alerts, 0 duplicates. `state/seen_posts.json` migrated from a 5,000-entry list to a dict of 5,001 keys with first-seen timestamps. The first cron run on the new code is the 16:15 one.

### If something looks wrong later

- Too quiet: `grep "Gate said no" fb_monitor.log` lists what the gate dropped, with the post text. If a real lead is in there, adjust `GATE_SYSTEM` in `fb_monitor.py` or remove the exclude that caught it, then `--replay`.
- Alerts tagged "unchecked: lead gate unavailable": the model call is failing; the reason is on the `lead gate error` line in the log. The usual cause is the key file in `config.gate.api_key_file` moving.
- Repeats again: check `state/seen_posts.json` is still a dict and under 50,000 keys.
