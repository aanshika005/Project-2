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

> **Revised in unit 4:** Given a query that matches, the listing passed to
> suggest_outfit and create_fit_card is the same listing as
> session["selected_item"] (same id), and the fit card names that item's price
> and platform. selected_item equals session["search_results"][0] unless the
> pricey branch recorded a switch in session["switched_from"]. 5 of 5 tries.
>
> **Why revised:** I wrote the original before building my stretch second
> branch. That branch deliberately swaps a pricey top match for a cheaper one
> from the top 3, so whenever it fires, the original wording fails even though
> the item is passed along correctly. That makes it unmeasurable as a state
> check, not just unmet. The target stays 5 of 5. The unit 4 run uses a query
> that doesn't trigger the switch, so the original wording is still tested
> as written.


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

---

---

# Capstone criteria: category-aware retrieval

These are the five criteria for the extension unit. The five above belong to the original agent and stay as they are.

**What is being tested:** `search_listings(..., strategy="category")`, the second retrieval strategy, and the run log around it.

**An honest note on order.** I wrote these after Milestone 2, so I already know how `category` did on my 35 labeled queries (33 of 34 ranked queries right at rank 1, against 28 of 34 for `keyword`). I wrote the garment lexicon with those queries in view, so those numbers can't be the test. Criterion 1 is therefore judged on a **fresh set** (criterion 2 also covers the 35 earlier queries, since a regression check is meaningful on any queries): at least 15 queries that I will write after committing this file and before running either strategy on them, in my own words, each naming a garment type, each labeled by hand against `data/listings.json` with the rubric in `eval/retrieval_dev.json`, and written without opening the family list in `retrieval.py`. The set goes in `eval/retrieval_fresh.json`. The other three criteria are judged on runs I haven't done yet.

---

## 1. The new strategy finds the right garment first

On the fresh set, `strategy="category"` returns, at rank 1, a listing whose id is in that query's `relevant` list for at least **13 of 15** queries (87%). If I write more than 15, the same 87%, rounded up. The `relevant` ids are written into `eval/retrieval_fresh.json` before either strategy is run on the set, and are not changed afterwards.

**How it is measured:** `python eval_retrieval.py` over the fresh file; top-1 correct is counted per query.

**Why this target:** Not 15 of 15, because `category` only knows 22 garment families, so a fresh query that uses a word I didn't list ("skirt", say) falls back to plain keyword scoring, and I already know one failure class: a modifier word loses to the garment type ("linen pants" returns cargo pants first). Not 11 of 15 (73%), because `keyword` got 28 of 34 (82%) on the earlier sets, and a target below that would let the extension be worse than the thing it extends and still pass.

## 2. It never turns a right answer into a wrong one

On the fresh set and on the 35 earlier queries, there are **0 queries** where `keyword`'s rank-1 listing is in the `relevant` list but `category`'s is not.

**How it is measured:** the per-query table from `python eval_retrieval.py`; the "WORSE" marker must appear on no row.

**Why this target:** Zero, not "few", because `category` only reorders: it uses the same price and size filters and the same keyword score, and adds a garment-type step. A right answer demoted by that step is a design bug, not noise, and the search involves no model, so nothing random can cause it. (Today it holds on the 35: category changed the rank-1 listing on 5 of 35 and made none worse.)

## 3. A bad input to the new strategy stops cleanly

For these 5 inputs, the agent stops without an exception reaching the caller, **the run is logged** (outcome `search_failed` or `no_results`), and the message shown to the user is non-empty, in **5 of 5**: `strategy="semantic"`, `strategy=""`, `strategy="CATEGORY"`, and the queries `""` and `"   "` (spaces only) run with `strategy="category"`. For the three bad strategy values, the message must also name both valid choices (`keyword` and `category`). Uppercase is rejected on purpose: strategy names are exact, so `"CATEGORY"` is a bad input, not a spelling variant to accept.

**How it is measured:** call `run_agent` directly with each input, with `FITFINDR_RUN_LOG` pointing at a scratch file; check that no exception escapes, read the last record's `outcome` and `error`, and search the message for both strategy names. The observed messages go in the results, not in this file.

**Why this target:** 5 of 5, because none of it involves the model: the strategy is validated in `retrieval.rank`, travels over MCP, and comes back as a tool error, and the empty queries never reach scoring. If any of the five escapes as a traceback or leaves no record, a user on the bad path sees a crash instead of a message, and I would not see it in the log. Exact-match names, not case-insensitive, because there are only two strategies and a typo like `"Category"` is better answered with the list of valid names than by guessing what was meant.

## 4. The new strategy makes no extra model calls

In each of 10 cache-off runs of `python app.py ask` with `--strategy category` that complete, `model_calls` in the run record is exactly **2**, the same as `keyword`.

**How it is measured:** `python measure_cost.py --strategy category`; read the "Model calls per run" row (min and max must both be 2.0) in the `results/cost_*.md` file.

**Why this target:** The extension is a few lines of sorting inside the search step, so it shouldn't touch the model at all. Any other count means I wired it into the wrong place, and each extra call costs about 400 tokens and a second, so it would also eat the 15-requests-a-minute limit faster. Exactly 2 rather than "about 2" because the count is deterministic (suggest, then fit card); only the latency is noisy, which is why time is not a criterion.

## 5. Every run leaves a record, including the ones that fail

After 20 runs in one session, **8 that complete, 5 that match nothing, 4 with a bad API key, and 3 with a bad strategy**, the log gains **exactly 20 lines**, every line parses as JSON and contains all **23 documented fields**, and the `outcome` of each matches what I caused: `completed` ×8, `no_results` ×5, `model_unavailable` ×4, `search_failed` ×3. Every non-completed run has a non-null `error`. Target: **20 of 20** runs.

**How it is measured:** note `wc -l` on `logs/fitfindr_runs.jsonl` before and after, then check the new lines with a short script against the field list at the top of `runlog.py`.

**Why this target:** 20 of 20, because the record is written in one place (`run_agent`) on every path, so a miss would mean a path that escapes it. The cost of being wrong is high and silent: a run that fails and leaves no line is exactly the failure I can't diagnose later, and the diagnosis in the next milestone depends on this log. The mix is chosen so each failure path in the loop is exercised at least three times, not just once.
