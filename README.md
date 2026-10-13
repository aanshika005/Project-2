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

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



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

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
