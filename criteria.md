# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->
Parsing and search are plain code, so a matching query always finds the same item. Each run then makes two Gemini calls, though, and on the free tier (15 requests a minute) a run can hit a rate limit that doesn't clear in time, or the model can fail to respond. I'm allowing one miss in five for that outside service, not for my own code.
---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->
This path never calls the model. Parsing, searching and the if not results check are all code that gives the same answer every time, so nothing random can make it fail. If it misses even once, my branch is broken, so anything less than 5 of 5 would hide a real bug.
---

## 3. The item search found is the item every later tool receives

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->
Given a query that matches, the listing passed to suggest_outfit and create_fit_card has the same id as session["search_results"][0], and the fit card names that item's price and platform. 5 of 5 tries.

**Why this target:**
Passing the item is plain code: selected_item is copied from the first result and read back out of the session, with no model involved. So any mismatch is a state bug, and 5 of 5 is the only honest target. I check the id rather than the outfit text, because the model rewords titles and the text can't prove which item it received.


---

## 4. The fit card reads like a caption about the right item

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->
Across 5 different matching queries, at least 4 of the 5 fit cards are 2–4 sentences long and contain the listing's exact price (like $19) and its platform name. No two of the 5 cards open with the same first sentence.

**Why this target:**
The prompt asks for all of this, but at temperature 0.9 the model sometimes adds a sentence or writes the price as "19 bucks". That's why I set 4 of 5 rather than 5. The different-opening rule is there because if the cache or a low temperature were making every card read like a template, I'd want this criterion to catch it.
---

## 5. Search never breaks its own filters

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->
For 5 queries that include a max price and/or a size, every listing in search_results costs at most the max price and passes the size rule (whole-size match, so "S" never matches "US 9"). That means 0 violations across all 5 queries.

**Why this target:**
Filtering is plain code with no model, so even one item over the price is a bug, not bad luck. I picked this one because a filter that leaks (like showing shoes when someone asked for a small top) makes the whole agent look broken. Criterion 1 can't catch it, because a leaky search still "finds something".
---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
