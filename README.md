# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr is a command-line agent for secondhand shopping. You describe what you want in plain language, like `'vintage graphic tee under $30'` or `'platform sneakers size 8'`, and it pulls out the item, size and max price, then searches 40 thrift listings from Depop, ThredUp and Poshmark for the best match. It hands that item to the model, which suggests one or two outfits using pieces you already own (or general styling ideas if your wardrobe is empty), and then writes a short caption you could post about the find. If nothing matches, it stops before calling the model and tells you what to change, such as a higher price, a different size or other keywords.
---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 mock listings by optional price ceiling and size, then ranks what's left by how many keywords it shares with the description. Search words in the title score 2 points each, and words found only in the description, category, style tags, colors or brand score 1. Listings scoring 0 are dropped, and ties go to the cheaper item.
- **Inputs:** `description` (str, keywords like "vintage graphic tee"); `size` (str or None, e.g. "M"; matched case-insensitively against whole size tokens, so "M" matches "S/M" and "M/L" but not "US 9", and "One Size" listings match any size; None skips the size filter); `max_price` (float or None, US dollars, inclusive; None skips the price filter).
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listings, best match first, each with `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str or None), `platform` (str: depop / thredUp / poshmark).
- **When it has nothing:** Returns an empty list `[]`. Never None, never an exception. The loop checks for `[]` and stops before calling `suggest_outfit`.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the thrifted item, naming pieces the user already owns.
- **Inputs:** `new_item` (dict, one listing dict from `search_listings`); `wardrobe` (dict with an `items` key holding a list of wardrobe item dicts; the list may be empty).
- **Returns:** A non-empty `str` of outfit suggestions written in plain text, each pairing the new item with specific pieces from `wardrobe["items"]`.
- **When it has nothing:** If `wardrobe["items"]` is empty, it still returns a non-empty `str` of general styling advice for the item (what kinds of pieces and colors pair with it). It never returns `""`. If the model is unreachable, it raises `ModelUnavailable`, which `run_agent` handles.

### `create_fit_card`

- **What it does:** Asks the model for a short, social-post-style caption about the find and the outfit.
- **Inputs:** `outfit` (str, the text returned by `suggest_outfit`); `new_item` (dict, the same listing dict passed to `suggest_outfit`).
- **Returns:** A `str` caption of two to four sentences that mentions the item's `title`, `price` and `platform` once each and describes the vibe. It varies between runs (TEMPERATURE 0.9).
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns the fixed string `"Can't write a fit card: no outfit suggestion was provided."` without calling the model. If the model is unreachable, it raises `ModelUnavailable`, which `run_agent` handles.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that tells the user what to change (for example, "No listings matched 'sequin cowboy boots' in size S under $10. Try a higher max price, a different size, or fewer keywords.") and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, take the first result (the best match) as `session["selected_item"]` and go to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent` (the `search` step in the `while` loop)

**How the query is parsed:** Regex in `agent.py::parse_query`. It pulls a max price (`$30`, `under $30`, `under 30`) and a size (`size M`, `in size M`; bare numbers become `US 8`), removes them, strips filler like "looking for", and uses the rest as the description.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` → *branch:* `error` and stop if empty, else `selected_item` → `outfit_suggestion` → `fit_card`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Vintage Band Tee — Faded Grey — $19.0 on depop

  Outfit:   Hey there! That vintage band tee is a total closet staple and will fit right into your wardrobe. Here are two ways to style it using pieces you already own:

Outfit 1: Effortless Streetwear
Tuck the vintage band tee into your baggy straight-leg jeans, dark wash. Cinch your waist with the brown leather belt, and toss on your vintage black denim jacket (slightly cropped). Finish the look with your chunky white sneakers and the black crossbody bag for an easy, everyday vibe.

Outfit 2: Grunge Contrast
Pair the vintage band tee with your wide-leg khaki trousers for a cool mix of textures. Layer your black cropped zip hoodie open over top, and lace up your black combat boots to lean into that authentic 90s edge.

  Fit card: Found this faded grey vintage band tee on depop for just $19 and the wash on it is so good. It has that perfectly worn-in 90s grunge feel that goes with everything. Grab it before I change my mind and keep it! 🖤🎸 #thrifted #bandtee #depop

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Hey! Those vintage Levi's 501 jeans are an absolute closet staple and will fit right in. Here is how you can style them using what you already own:

Outfit 1:
Tuck your white ribbed tank top into the Levi's 501 jeans. Add the brown leather belt, and finish with the chunky white sneakers and black crossbody bag. It is a classic, effortless look.

Outfit 2:
Pair the jeans with your black cropped zip hoodie and layer the vintage black denim jacket on top for a cool double-denim vibe. Step into your black combat boots to complete this edgy, streetwear-inspired outfit.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

Found my dream pair of Vintage Levi's 501 Jeans — Medium Wash and honestly I'm never taking them off. They have that perfect broken-in 90s streetwear vibe and I'm just planning to live in these with crisp white sneakers. Snagged them on depop for $38 which feels like an absolute steal. 👖✨

#levis501 #vintagedenim #depopseller
```

---

## Stretch Features

Declared before building. Each one is built in a later commit.

- **Fourth tool — `compare_prices(item, listings)`:** compares the chosen item's
  price against every other listing in the same category. Returns a dict with
  `price`, `category`, `compared_with` (int), `median` (float),
  `cheaper_than_pct` (int, 0–100) and `verdict` ("good deal" / "about average" /
  "pricey"). With fewer than 3 other listings in the category it returns
  `compared_with: 0` and `verdict: "not enough similar listings"`.
- **Second branch — pricey top match:** after `compare_prices`, if the verdict is
  "pricey" and another search result is cheaper, the loop switches
  `selected_item` to the cheapest of those and records the original in
  `session["switched_from"]`. Otherwise it keeps the top match.
  *Built with one refinement:* candidates are limited to the **top 3 search
  results in the same category** as the top match. Without that, a pricey
  "90s Leather Bomber" got swapped for a leather belt.
- **Style memory:** the wardrobe is saved to `data/saved_wardrobe.json`.
  `python app.py ask '...' --keep` adds the found item to it, and later runs
  load it automatically, so outfit suggestions can use items kept in earlier runs.

### Evidence

**Fourth tool called + second branch taken:** the top match was pricey, so
the loop switched to a cheaper tee from the top 3 results in the same category.

```
$ python app.py ask 'graphic tee under $30'

  Switched: top match Graphic Tee — 2003 Tour Bootleg Style ($24.0) was pricey for its category
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  Price:    good deal: median $21.5 across 14 other tops, cheaper than 71%

  Outfit:   Outfit one is all about that classic Y2K contrast. Pair the Y2K Baby Tee with your baggy straight-leg jeans, dark wash. Add your black cropped zip hoodie for a cool layering piece. Finish this look off with your chunky white sneakers and your black crossbody bag to keep it practical and cute. 

Outfit two gives a softer, vintage-meets-streetwear vibe. Wear the Y2K Baby Tee tucked into your wide-leg khaki trousers, and cinch the waist using your brown leather belt. Throw on your vintage black denim jacket for an extra layer, and step into your black combat boots to ground the pastel butterfly print with some edge.

  Fit card: Found this dreamy Y2K Baby Tee — Butterfly Print and I'm obsessed with the pastel colors. It's giving major nostalgic vibes and I'm listing it on depop for just $18. Grab it before I change my mind and keep it for myself! 🦋✨

#y2kstyle #depopseller #babytee
2 model calls this session, 558 prompt + 206 output tokens
```

**Branch not taken:** pricey, but no cheaper outerwear in the top 3, so it keeps the top match.

```
$ python app.py ask '90s leather bomber'

  Found:    90s Leather Bomber — Black — $75.0 on depop
  Price:    pricey: median $40 across 7 other outerwear, cheaper than 0%

  Outfit:   Hey there! That 90s leather bomber is such a versatile find and will instantly level up your wardrobe. Here are two easy ways to style it using what you already own:

Outfit 1: Edge it up. Pair the 90s Leather Bomber with your white ribbed tank top tucked into the baggy straight-leg jeans, dark wash. Slip on the chunky white sneakers and finish the look with the black crossbody bag for a classic, effortless 90s off-duty model vibe.

Outfit 2: Play with textures. Layer the 90s Leather Bomber over the oversized grey crewneck sweatshirt, paired with the wide-leg khaki trousers. Ground the slouchy silhouette with your black combat boots for a cool, grungy contrast between the tough leather and soft knit. 

You are going to wear this jacket on repeat!

  Fit card: Found the ultimate 90s Leather Bomber on depop for $75 and I'm obsessed. Total off-duty model energy and it goes with literally everything. 

#thriftfinds #vintageleather #depopshop

2 model calls this session, 588 prompt + 220 output tokens
```

**Style memory, run 1 (stores):** an empty wardrobe, so the outfit is general advice. `--keep` saves the found tee.

```
$ python app.py ask 'graphic tee under $30' --empty-wardrobe --keep

(running with an empty wardrobe — saved wardrobe ignored)

  Switched: top match Graphic Tee — 2003 Tour Bootleg Style ($24.0) was pricey for its category
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  Price:    good deal: median $21.5 across 14 other tops, cheaper than 71%

  Outfit:   Hey there! That Y2K butterfly baby tee is such a fun find. Since it has those lovely pink and purple graphics on white, let us style it two ways.

Outfit one leans into the vintage Y2K vibe. Pair the tee with low-rise medium-wash denim flare jeans. Add a small pink shoulder bag and white chunky platform sneakers to complete the look.

Outfit two plays up the cottagecore crossover. Tuck the baby tee into a green floral print midi skirt. Layer a light cream cardigan over your shoulders and slip on some brown leather strappy sandals. 

Both options are super wearable and let the tee shine! Which vibe feels more like you?

  Fit card: Found this little Y2K butterfly baby tee and I am obsessed. It’s listed on my depop for just $18 and is giving total nostalgic spring energy. 🦋 #y2k #thrifted #babytee

  Kept:     Y2K Baby Tee — Butterfly Print — saved wardrobe now has 1 item

2 model calls this session, 402 prompt + 184 output tokens
```

**Style memory, run 2 (shaped by run 1):** no flags, so the agent loads the saved wardrobe. Both outfits are built around the Y2K Baby Tee kept in run 1.

```
$ python app.py ask 'baggy jeans'

(using your saved wardrobe: 1 item in data/saved_wardrobe.json)

  Switched: top match Baggy Carpenter Jeans — Dark Wash ($36.0) was pricey for its category
  Found:    Straight Leg Black Jeans — Faded — $30.0 on thredUp
  Price:    about average: median $30 across 9 other bottoms, cheaper than 44%

  Outfit:   Hey there! You are going to get so much wear out of these Levi's. Since they have that cool, faded vintage wash, they are the ultimate grunge-meets-classic staple. 

Outfit 1: Contrast and cute. Pair the faded black jeans with your Y2K Baby Tee — Butterfly Print. The pastel butterfly print adds a fun pop of pink and purple against the dark denim. Throw on chunky platform sneakers and a little black shoulder bag to lean into that effortless 2000s street style.

Outfit 2: Monochromatic grunge. Tuck the Y2K Baby Tee — Butterfly Print right into the waistband of the jeans to define your shape. Add a beat-up leather jacket and some combat boots to really highlight the edgy, vintage vibe of the denim. Have fun styling them!

  Fit card: scored these faded black levi's straight leg jeans on thredup for just $30 and the worn-in grunge vibe is unreal. already planning to wear them with a baby tee and beat-up combat boots all fall. 🖤👖

#thriftfinds #levis #grungefashion

2 model calls this session, 471 prompt + 227 output tokens
```

**Reset afterwards:**

```
$ python app.py wardrobe --clear

Saved wardrobe deleted.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to finish `search_listings` using the size-matching helpers I'd already started (`_keywords`, `_size_tokens`, `_size_matches`).
- *What came back:* Before writing the function, it pointed out two bugs in my helpers. `re` was never imported, so every search would crash with a `NameError`. And `p.strip().upper` was missing its `()`, so it stored the method instead of the uppercase text, and size matching could never work. It also tested the finished function on a copy of my repo and explained that "boots size US 8" returning nothing was correct, because the only boots in the data are size US 8.5.
- *What I changed:* I fixed both bugs, then asked it to explain each helper line by line, especially the parentheses regex `\([^)]*\)` and the scoring formula, so I understood the code before committing it. Seeing that bare numbers didn't match shoe sizes also shaped my parser later: `parse_query` turns "size 8" into "US 8".

**Moment 2**

- *What I asked for:* I asked Claude to check whether my Milestone 2 spec was complete, using the milestone's own test: could someone else build each tool from what I wrote?
- *What came back:* It compared my Tool Inventory against the actual code and found three gaps. My `search_listings` ranking said "ranks by keywords" without saying how. And both `suggest_outfit` and `create_fit_card` claimed they "never raise", which was false, because `generate()` raises `ModelUnavailable` when the model is unreachable.
- *What I changed:* I added the exact scoring rule (title words worth 2 points, other fields 1, zero-score listings dropped, ties go to the cheaper item) and rewrote both "never raises" lines to name `ModelUnavailable`. Then I added a `ModelUnavailable` handler to `run_agent` so the README's claim that `run_agent` handles it is actually true. That showed me a spec can be wrong even when the code works.

**Moment 3 (Unit 4)**

- *What I asked for:* I asked Claude to write `scenarios.py` for my five criteria.
- *What came back:* Before writing them, it pointed out that criterion 3 conflicted with my stretch branch. Criterion 3 compares the item passed on with `search_results[0]`, but the pricey-match branch I built after writing it deliberately selects a different item. So the criterion would fail by design even when state works. It also pointed out that criteria 4 and 5 say "5 different queries", which one scenario run 5 times can't test.
- *What I changed:* I added a "Revised in unit 4" note under criterion 3 in `criteria.md`, without editing the original, and committed it before running anything. I gave criteria 4 and 5 five scenarios each, judging Try *t* across the five *t*-th runs.

**Moment 4 (Unit 4)**

- *What I asked for:* I asked Claude to help me mark 15 scenarios × 5 tries from a 3,658-line results file.
- *What came back:* It wrote a script to check each try. Its first check flagged criterion 2 as failing because the trace contained `suggest_outfit`, but that was the note text "stopping before suggest_outfit", not a real step. It also reported every criterion as passing, so I had it confirm the cards were really different across tries and show me actual cards rather than trusting its sentence counter.
- *What I changed:* I made the criterion 2 check look for an actual `suggest_outfit` step. Reading the real cards is how I found the seller-voice problem, which became my improvement. I also fixed my seller-voice count from 15 to 17 of 65 once I'd settled on one written definition of what counts.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

All runs: `python run_eval.py --label before` (`run_eval.py::main`, which calls `agent.py::run_agent` for every try), 5 tries per scenario, caching off, temperature 0.9. Full log: `results/run_2026-10-13_1456_before.md`.

Criteria 4 and 5 each say "5 different queries", so each has five scenarios (A–E) in `scenarios.py`. **Try *t* is judged across the five *t*-th runs together**, so every try covers five different queries.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item search found is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card reads like a caption about the right item | 4 of 5 cards per try, distinct openings | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Search never breaks its own filters | 0 violations | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The model really was re-run each time: in every fit-card scenario, all 5 cards are different.

**Was criterion 4 a real test?** Yes, even though it passed 25 of 25. Nothing in my code enforces any part of it. `tools.py::create_fit_card` only *asks* the model for 2–4 sentences, the exact price and the platform, then returns whatever comes back, at temperature 0.9 with caching off. Each card could fail in several independent ways: a fifth sentence, the price written as "19 bucks" or "about twenty dollars", the platform left out, or two of the five items opening with the same template sentence. The same run shows the model does drift from the prompt in ways it wasn't held to: 17 of 65 cards talk like the seller ("Just listed it on my depop"), and one hashtag came out garbled (`#9ᅩsstyle`). So the criterion could have caught a failure. It passed because the prompt states those three requirements explicitly, and the model followed them every time. What it doesn't measure is the card's *voice*, which is where the real failure turned out to be.

**Real output from one try** (Try 1 of each criterion), as produced by `agent.py::run_agent`. The traces come from `trace.step()` calls inside it.

**Criterion 1:** completed all three tools and returned a fit card.

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print … +7 more
      →    branch: found, continuing
[3] select
      out: Vintage Band Tee — Faded Grey ($19.0, depop)
      →    top search result
[4] compare_prices
      in:  Vintage Band Tee — Faded Grey ($19.0, depop)
      out: about average (median $21.5 across 14 other tops)
      →    branch: keeping the top match
[5] suggest_outfit
      in:  Vintage Band Tee — Faded Grey + wardrobe of 10 items
      out: Hey there! I am so excited you are eyeing this vintage band tee. It fits your grunge and streetwear vibe so we…
[6] create_fit_card
      in:  Vintage Band Tee — Faded Grey
      out: Obsessed with the 90s grunge energy of this Vintage Band Tee in Faded Grey. Snagged it for just $19 and it's o…
      →    done

Fit card:
Obsessed with the 90s grunge energy of this Vintage Band Tee in Faded Grey. Snagged it for just $19 and it's officially live on my depop shop. Perfect for anyone trying to nail that effortless streetwear look. 🎸🖤 #thrifthaul #bandtee #depop
```

**Criterion 2:** stopped at step 2 with a message naming what to change. No `suggest_outfit` step.

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

session["error"]: No listings matched 'designer ballgown' in size XXS under $5. Try a different size, a higher max price or different keywords.
session["fit_card"]: None
```

**Criterion 3:** the same listing at every step: first search result, `select`, `suggest_outfit`'s input and `create_fit_card`'s input. The trace shows titles rather than ids, but all 40 titles in `data/listings.json` are unique, so a title identifies exactly one listing. The fit card names its price ($40) and platform (thredUp).

```
[1] parse_query
      in:  90s windbreaker
      out: description='90s windbreaker', size=None, max_price=None
[2] search_listings (via MCP)
      in:  description='90s windbreaker', size=None, max_price=None
      out: 8 items: Vintage Windbreaker — Color Block Purple/Teal, 90s Silk Slip Dress — Floral, Midi Length, 90s Track Jacket — Navy/White Stripe … +5 more
      →    branch: found, continuing
[3] select
      out: Vintage Windbreaker — Color Block Purple/Teal ($40.0, thredUp)
      →    top search result
[4] compare_prices
      in:  Vintage Windbreaker — Color Block Purple/Teal ($40.0, thredUp)
      out: about average (median $42 across 7 other outerwear)
      →    branch: keeping the top match
[5] suggest_outfit
      in:  Vintage Windbreaker — Color Block Purple/Teal + wardrobe of 10 items
      out: Hey there! That 90s color block windbreaker is such a fun find. Here are two easy, practical outfits using wha…
[6] create_fit_card
      in:  Vintage Windbreaker — Color Block Purple/Teal
      out: Found this sick 90s color block windbreaker on thredUp for $40 and honestly I'm obsessed. The purple and teal …
      →    done

Fit card:
Found this sick 90s color block windbreaker on thredUp for $40 and honestly I'm obsessed. The purple and teal combo has such great retro streetwear energy. Can't wait to style this over baggy denim or layer it with some khakis. 

#thrdfind #vintagefashion #90sstyle
```

**Criterion 4:** the five fit cards from Try 1, one per item. Each is 2–4 sentences, contains the exact price and platform, and has a different opening.

```
Vintage Band Tee — Faded Grey ($19.0, depop)
Found the ultimate faded grey vintage band tee for just $19 and I'm obsessed with this grunge streetwear energy. It’s got that perfect lived-in wash that’s so hard to find. Just listed it on my depop so grab it before I change my mind 💀 

#depop #vintagestyle #bandtee

90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
Obsessed with this vintage Champion 90s Track Jacket — Navy/White Stripe. Snagged it on poshmark for $45 and the sporty streetwear vibe is just too good. Perfect for throwing over baggy denim or trousers. 🏃‍♀️✨ 

#thriftfinds #streetwear #vintagestyle

90s Silk Slip Dress — Floral, Midi Length ($30.0, depop)
Obsessed with this 90s silk slip dress and how the floral midi length gives total grunge-meets-cottagecore vibes. I just listed it on depop for $30 and honestly might cry if someone else doesn't buy it first. 🌸✨ 

#vintagefashion #9ᅩsstyle #depopshop

Platform Sneakers — White Chunky Sole ($48.0, poshmark)
Found these chunky white Platform Sneakers on Poshmark for $48 and my Y2K streetwear obsession is officially cured. Can't wait to style them with baggy denim and a vintage jacket. 

👟✨ 
#Y2Kstyle #ThriftFinds #Streetwear

Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
scored this vintage cropped light wash Wrangler denim jacket on Poshmark for $42 and the 90s streetwear vibes are so good. can't wait to layer this over everything this season. 🧥✨

#thrifty #denimjacket #poshmarkfinds
```

**Criterion 5:** the search step from Try 1 of each query:

```
[2] search_listings (via MCP)
      in:  description='graphic tee', size=None, max_price=30.0
      out: 6 items: Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey … +3 more
      →    branch: found, continuing
[2] search_listings (via MCP)
      in:  description='top', size='S', max_price=20.0
      out: 1 items: Mesh Long-Sleeve Top — Black
      →    branch: found, continuing
[2] search_listings (via MCP)
      in:  description='jacket', size=None, max_price=45.0
      out: 3 items: Denim Jacket — Light Wash, Cropped, 90s Track Jacket — Navy/White Stripe, Shacket — Olive Canvas
      →    branch: found, continuing
[2] search_listings (via MCP)
      in:  description='sneakers', size='US 9', max_price=50.0
      out: 1 items: Low-Top Canvas Sneakers — Off-White
      →    branch: found, continuing
[2] search_listings (via MCP)
      in:  description='tee', size='L', max_price=25.0
      out: 2 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style
      →    branch: found, continuing
```

The trace shows only the first three titles, so I checked the full result lists by re-running `tools.py::search_listings` with the same parsed inputs (search calls no model, so it returns the same results every time). Every result is at or under the max price and passes the size rule, so there are 0 violations. "jacket under $45" includes the $45 track jacket, because the limit is inclusive.

```
graphic tee under $30  →  size=None, max_price=30.0
    $24    L                      Graphic Tee — 2003 Tour Bootleg Style
    $18    S/M                    Y2K Baby Tee — Butterfly Print
    $19    L                      Vintage Band Tee — Faded Grey
    $15    S/M                    Mesh Long-Sleeve Top — Black
    $26    L                      Vintage Graphic Hoodie — Faded Black
    $27    W29                    Low-Rise Cargo Pants — Khaki
top size S under $20  →  size='S', max_price=20.0
    $15    S/M                    Mesh Long-Sleeve Top — Black
jacket under $45  →  size=None, max_price=45.0
    $42    S                      Denim Jacket — Light Wash, Cropped
    $45    M                      90s Track Jacket — Navy/White Stripe
    $33    M/L                    Shacket — Olive Canvas
sneakers size 9 under $50  →  size='US 9', max_price=50.0
    $20    US 9                   Low-Top Canvas Sneakers — Off-White
tee size L under $25  →  size='L', max_price=25.0
    $19    L                      Vintage Band Tee — Faded Grey
    $24    L                      Graphic Tee — 2003 Tour Bootleg Style
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | **MET (5/5)** | All 5 tries finished with a fit card for the Vintage Band Tee. No try stopped early or crashed. |
| 2 | An impossible query stops before the second tool | 5 of 5 | **MET (5/5)** | All 5 traces are 2 steps and end with `branch: empty, stopping before suggest_outfit`. There's no `suggest_outfit` step, `fit_card` is `None`, and the message names three things to change. |
| 3 | The item search found is the item every later tool receives | 5 of 5 | **MET (5/5)** | In all 5 traces, the same title (Vintage Windbreaker — Color Block) is the first search result, `select`'s output, and the input to both `suggest_outfit` and `create_fit_card`. Titles are unique in the data, so that's one listing. Every card contains $40 and thredUp. |
| 4 | The fit card reads like a caption about the right item | ≥4 of 5 cards per try, distinct openings | **MET (5/5)** | In each try, all 5 cards (one per item) were 2–4 sentences long and contained the exact price and platform, and no two shared an opening sentence. That's 25 of 25 cards. |
| 5 | Search never breaks its own filters | 0 violations | **MET (5/5)** | In each try, all 5 queries returned the same result counts. Re-running `search_listings` on the same inputs listed every result: none over the max price, none in the wrong size. |

**Diagnoses**

**No criterion missed.** So there's no miss to diagnose, but the run still showed a real failure that my criteria weren't built to catch.

**Were my targets too low?** Partly.

- **Criteria 2, 3 and 5 test plain code** with no model involved, so 5 of 5 was the only honest target. They could only fail through a bug, and the bugs that existed (the missing `import re`, `.upper` without `()`) were fixed during the build.
- **Criterion 1's 4 of 5** left room for one free-tier rate-limit failure. Pacing in `generate.py` handled that, so the allowance wasn't needed.
- **Criteria 1 and 5 were also only run on queries I'd already checked would match.** The diagnostic `jeans size W30` returns nothing, even though Levi's 501s labelled `W30 L30` are in the data. `tools.py::_size_tokens` keeps "W30 L30" as one size, so a plain "W30" never matches it. That's a tool gap my criteria never tested.

**The criterion I'd tighten: #4.** It checks the card's *format* (length, price, platform, openings), which the prompt states outright, so it passed 25 of 25. It doesn't check the card's *voice*, and that's where it actually fails:

- **Where:** the model's output, from the prompt in `tools.py::create_fit_card`. The tool itself works.
- **What happens:** 17 of 65 cards (26%) are written as if the poster is **selling** the item, not showing off something they bought: "it's officially live on my depop shop", "Just listed it on my depop", "Grab it before I change my mind and keep it for myself".
- **The pattern, split by platform:**

  | Platform | Seller-voice cards |
  |---|---|
  | depop | 14 of 30 (47%) |
  | poshmark | 3 of 30 (10%) |
  | thredUp | 0 of 5 |

  That's one problem, not seventeen.
- **Mechanism:** the prompt gives the model a block that looks like a sales listing (`Item: … / Price: … / Platform: …`) and asks for "a caption about this thrift find", but **never says the poster bought it**. The model fills that gap with each platform's usual voice. Depop is a peer-to-peer app where people run their own "depop shop", so it most often writes as a seller. thredUp is a store you buy from, so it never does.

A tightened #4 would add: *"…and no card describes the item as listed, for sale or in the poster's shop."* I'm not changing the original criterion, because it wasn't broken: it measured exactly what it said it would. This is a gap, and it's the target for the improvement milestone.

**How "seller voice" was counted:** a card counts if it says the item is listed, for sale or in the poster's shop ("listed", "listing", "my depop / my shop"), or urges others to buy it before the poster keeps it ("before I change my mind", "keep it for myself"). I applied that to all 65 fit cards in `results/run_2026-10-13_1456_before.md`.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path:** 7 steps. The MCP call is step 2, and step 4 takes the second branch (pricey, so it switches to a cheaper top-3 match).

```
$ python app.py ask 'graphic tee under $30' --trace

[1] parse_query
      in:  graphic tee under $30
      out: description='graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='graphic tee', size=None, max_price=30.0
      out: 6 items: Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey … +3 more
      →    branch: found, continuing
[3] select
      out: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      →    top search result
[4] compare_prices
      in:  Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      out: pricey (median $20.5 across 14 other tops)
      →    branch: pricey, switching to a cheaper top-3 match
[5] compare_prices
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: good deal (median $21.5 across 14 other tops)
      →    re-checked the new item
[6] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print + wardrobe of 10 items
      out: Outfit one is all about that classic Y2K contrast. Pair the Y2K Baby Tee with your baggy straight-leg jeans, d…
[7] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print
      out: Found this dreamy Y2K Baby Tee — Butterfly Print and I'm obsessed with the pastel colors. It's giving major no…
      →    done
```

**Empty search:** 2 steps. It stops right after the MCP search returns `[]`, before any model call.

```
$ python app.py ask 'designer ballgown size XXS under $12' --trace

[1] parse_query
      in:  designer ballgown size XXS under $12
      out: description='designer ballgown', size='XXS', max_price=12.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=12.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  No listings matched 'designer ballgown' in size XXS under $12. Try a different size, a higher max price or different keywords.

0 model calls this session
```

**On the MCP move:** I moved `search_listings` onto MCP with FastMCP over stdio (`mcp_server.py`) and swapped the direct call in `agent.py::run_agent` for `mcp_client.call_tool`. `python mcp_client.py` shows the server offers the tool with the inputs from my Tool Inventory:

```
$ python mcp_client.py

Asking mcp_server.py what it offers…

  search_listings
    Search 40 secondhand clothing listings (Depop, thredUp, Poshmark) by keywords,
    with an optional size and an optional max price in US dollars (inclusive).
    ...
    - description: string
    - size: string  (optional)
    - max_price: number  (optional)
```

The same query returned the same top match as in Unit 3 (Vintage Band Tee, $19, depop), so nothing behaved differently, except that each search is slightly slower because it starts the server. The trace labels it `search_listings (via MCP)`. I added an `MCPError` handler so that if the server can't be reached, the agent stops with a message instead of crashing.

### Failure Modes

All three triggered on purpose. None crashed or went silent, so no new handlers were needed. The handlers live in `agent.py::run_agent` (empty search and `ModelUnavailable`) and `tools.py::suggest_outfit` (empty wardrobe).

| Failure | How I triggered it | What the agent said | Handled? |
|---|---|---|---|
| Empty search | A query the data can't have | Stopped at step 2 and named what to change | Yes |
| Empty wardrobe | `--empty-wardrobe` | General styling advice, no crash, no empty string | Yes |
| Model unavailable | Changed one character of `GEMINI_API_KEY`, new query | Stopped at step 5, named the key as the problem and how to fix it | Yes |

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $12'

[1] parse_query
      in:  designer ballgown size XXS under $12
      out: description='designer ballgown', size='XXS', max_price=12.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=12.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  No listings matched 'designer ballgown' in size XXS under $12. Try a different size, a higher max price or different keywords.

0 model calls this session
```

**Empty wardrobe**

```
$ python app.py ask 'denim jacket under $50' --empty-wardrobe

(running with an empty wardrobe — saved wardrobe ignored)
[1] parse_query
      in:  denim jacket under $50
      out: description='denim jacket', size=None, max_price=50.0
[2] search_listings (via MCP)
      in:  description='denim jacket', size=None, max_price=50.0
      out: 7 items: Denim Jacket — Light Wash, Cropped, High-Waisted Denim Shorts — Cutoff, Denim Vest — Medium Wash, Studded … +4 more
      →    branch: found, continuing
[3] select
      out: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
      →    top search result
[4] compare_prices
      in:  Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
      out: about average (median $40 across 7 other outerwear)
      →    branch: keeping the top match
[5] suggest_outfit
      in:  Denim Jacket — Light Wash, Cropped + wardrobe of 0 items
      out: Hey there! That Wrangler denim jacket is such a great find. Here are two easy, everyday outfits you can build …
      →    empty wardrobe: general advice
[6] create_fit_card
      in:  Denim Jacket — Light Wash, Cropped
      out: Obsessed with this vintage cropped Wrangler denim jacket I just listed on Poshmark. It has the absolute best 9…
      →    done

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark
  Price:    about average: median $40 across 7 other outerwear, cheaper than 43%

  Outfit:   Hey there! That Wrangler denim jacket is such a great find. Here are two easy, everyday outfits you can build with pieces you probably already own.

Look one leans sporty and casual. Pair the jacket with a cozy grey marled hoodie underneath, some black high-waisted leggings or bike shorts, and chunky white sneakers. Toss on a canvas tote bag to finish the look.

Look two is effortless and a little retro. Wear it over a simple ribbed white baby tee, tucked into straight-leg olive green cargo pants, and finished off with well-loved canvas low-top sneakers like Converse. Add a simple silver hoop earring to tie it all together.

  Fit card: Obsessed with this vintage cropped Wrangler denim jacket I just listed on Poshmark. It has the absolute best 90s streetwear vibe and is only $42. Grab it before I change my mind and keep it for myself! 

#ThriftFind #VintageDenim #PoshmarkStyle

2 model calls this session, 396 prompt + 197 output tokens
```

**Model unavailable** (one character of the key changed; a new query, so nothing came from the cache)

```
$ python app.py ask 'silk dress under $40'

[1] parse_query
      in:  silk dress under $40
      out: description='silk dress', size=None, max_price=40.0
[2] search_listings (via MCP)
      in:  description='silk dress', size=None, max_price=40.0
      out: 2 items: 90s Silk Slip Dress — Floral, Midi Length, Silk Button-Down — Sage Green
      →    branch: found, continuing
[3] select
      out: 90s Silk Slip Dress — Floral, Midi Length ($30.0, depop)
      →    top search result
[4] compare_prices
      in:  90s Silk Slip Dress — Floral, Midi Length ($30.0, depop)
      out: about average (median $30 across 9 other bottoms)
      →    branch: keeping the top match
[5] suggest_outfit
      in:  90s Silk Slip Dress — Floral, Midi Length
      out: ModelUnavailable
      →    stopping: model unreachable

  Found an item, but couldn't get outfit ideas. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

1 model calls this session
```

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One prompt, in `tools.py::create_fit_card`. The system prompt now says the captions are "for someone who just BOUGHT a thrift find", written "in first person as the buyer", and that they should never say the item is listed, for sale or in your shop, or tell others to buy it. The user prompt now starts "I just bought this secondhand", and the data labels changed from `Price:` / `Platform:` to `Price I paid:` / `Bought on:`. Nothing else changed: no other tool, the loop, the temperature or the criteria. The change is its own commit ("Rewrite create_fit_card prompt"), made after the before-run was committed.

**Which failure it was meant to fix:** The seller-voice pattern from my diagnosis. 17 of 65 fit cards talked like the poster was selling the item (14 of 30 on depop), because the prompt never said who the poster was, and its `Price / Platform` block read like a sales listing.

### Run Log — After

`python run_eval.py --label after` (`run_eval.py::main` → `agent.py::run_agent`): the same 15 scenarios, 5 tries each, caching off, temperature 0.9. Full log: `results/run_2026-10-13_1552_after.md`. Criteria 4 and 5 are judged the same way as before (Try *t* = the five queries' *t*-th runs).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item search found is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card reads like a caption about the right item | 4 of 5 cards per try, distinct openings | PASS | PASS | PASS | PASS* | PASS | MET (5/5) |
| 5. Search never breaks its own filters | 0 violations | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

\*In Try 4, only 4 of 5 cards passed: the slip dress card wrote its price as "thirty bucks" instead of "$30". That still meets the "≥4 of 5" target.

**Before vs after, side by side**

| Measure (same 15 scenarios × 5 tries) | Before | After |
|---|---|---|
| Criteria met | 5 of 5 | 5 of 5 |
| Seller-voice fit cards | **17 of 65 (26%)** | **1 of 65 (2%)**, a false positive (see below) |
| … on depop | 14 of 30 | 0 of 30 |
| … on poshmark | 3 of 30 | 1 of 30 |
| … on thredUp | 0 of 5 | 0 of 5 |
| Cards missing the exact price or platform | 0 of 65 | 1 of 65 |

**The same item before and after** (band tee, Try 1, from `tools.py::create_fit_card`):

```
BEFORE: Found the ultimate faded grey vintage band tee for just $19 and I'm obsessed with this grunge streetwear energy. It’s got that perfect lived-in wash that’s so hard to find. Just listed it on my depop so grab it before I change my mind 💀 

#depop #vintagestyle #bandtee

AFTER:  Scored this Vintage Band Tee — Faded Grey on depop for just $19 and I am obsessed. The fade is so good and it has that ultimate grunge streetwear vibe. 

#vintagefashion #thrifted #bandtee
```

**The one regression** (slip dress, Try 4):

```
Scored this gorgeous 90s Silk Slip Dress — Floral, Midi Length on depop for only thirty bucks and I am obsessed. The grunge-femme cottagecore vibe is just too good. Styling it with chunky sneakers and an oversized crewneck for maximum 90s energy. 🌸✨

#vintagefashion #90sstyle #thriftedstyle
```

**Did it help, and how do I know:** Yes. Seller-voice cards dropped from 17 of 65 to 1 of 65 (depop: 14/30 to 0/30), counted with the same definition on the same 15 scenarios × 5 tries. The one remaining match ("Score one for my Poshmark patience! Just snagged…") is written as a buyer, so on an actual read it's 0 of 65. All five criteria stayed MET. There was one small regression: one card wrote the price as "thirty bucks" instead of "$30", so cards missing the exact price went from 0 of 65 to 1 of 65. It still met criterion 4's "4 of 5" target, but it's the first criterion-4 card to fail in either run, and "Price I paid:" may invite that kind of casual phrasing. With a single case, I can't prove the new wording caused it.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

### Unit 4 Stretch Features

Declared before building. Each one is built in a later commit, in this order.

- **Second improvement — waist/length sizes:** `tools.py::_size_tokens` will also
  split sizes like `W30 L30` on spaces, so a search for `W30` matches them. My
  diagnosis named this gap (`jeans size W30` returns nothing). Measured the same
  way: `python run_eval.py --label after2`, compared with the `after` run. The W30
  diagnostic should find the Levi's 501s, and criterion 5 must stay at 0 violations.
- **Second tool on MCP — `compare_prices`:** registered in `mcp_server.py` and
  called from `agent.py::run_agent` through `mcp_client.call_tool`. It should return
  the same dict as the direct call; the trace will show `compare_prices (via MCP)`.
- **Retry with looser constraints:** when a search that included a size returns
  `[]`, the loop retries once through MCP without the size. If that finds
  something, it continues and says which filter it dropped (stored in
  `session["dropped_filter"]`); if not, it stops as before.

**No criterion is still missed.** All five were MET before and after the improvement. These are the problems I know about that my criteria don't catch, with what I'd do next and why I stopped:

- **Combined waist and length sizes never match a waist-only search** (`tools.py::_size_tokens`). `jeans size W30` returns nothing, even though Levi's 501s labelled `W30 L30` are in the data, because "W30 L30" is kept as one size. *What I'd do:* split W/L sizes on spaces, so `W30` matches `W30 L30`, then add a scenario for it to criterion 5. *Why I stopped:* the milestone allowed one change, and the diagnosis pointed at the fit card, not this.
- **The model invents wardrobe pieces** (`tools.py::suggest_outfit`, model output). In my style-memory run the saved wardrobe held only one item (the Y2K Baby Tee), yet the outfit added "chunky platform sneakers", "a beat-up leather jacket" and "combat boots", despite "Only use pieces from the list" in the prompt. *What I'd do:* write a criterion for it first (e.g. "every named piece is in `wardrobe['items']`"), then try a stricter prompt or check the output against the list. *Why I stopped:* no criterion measured it, so I couldn't fix it and measure it properly in one change.
- **The price might be written in words** (`tools.py::create_fit_card`, model output). After my prompt change, 1 of 65 cards said "thirty bucks" instead of "$30". *What I'd do:* add "write the price exactly as shown, with the $ sign" to the prompt and re-run criterion 4. *Why I stopped:* it's one card, still within target, and changing the prompt again would blur the before/after comparison for this unit.
- **Data labels skew the price check** (`data/listings.json`). The silk slip dress is labelled `bottoms`, so `compare_prices` judges it against jeans and skirts. *What I'd do:* fix the label, or add a `dresses` category. *Why I stopped:* it's a data problem, and the starter data is shared.
- **"Tops" is too broad for the price switch** (`agent.py::run_agent`, the `compare` step). A pricey "Vintage Graphic Hoodie" can be swapped for a band tee, because both count as tops. *What I'd do:* also require one shared title keyword between the original and the swap. *Why I stopped:* it's a stretch feature, and none of my five criteria covered it.
- **Keyword search can't tell what an item *is* from what it *mentions*.** "Corduroy jacket" returns corduroy pants first, and the mesh top ranks for "graphic tee" because its description mentions one. *What I'd do:* weight `category` matches more heavily, or match the category word against the query. *Why I stopped:* criteria 1 and 5 passed, so I had no measured miss to justify changing the ranking.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
