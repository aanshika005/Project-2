"""
Judge a run_eval.py log against the five criteria in criteria.md, mechanically.

    python eval/judge_run_log.py results/run_2026-11-13_1300_regression.md

Run from the repo root. Standard library only. For each criterion it prints PASS/FAIL per try:
  1  all three tools ran and a fit card came back
  2  stopped early with a "Try ..." message, no suggest_outfit step, no fit card
  3  same title at search[0], select, suggest_outfit and create_fit_card (no switch); card has price + platform
  4  per try across the five cards: >=4 of 5 are 2-4 sentences with exact price and platform, no shared opening
  5  every search result is within price and size (re-ran retrieval.rank, keyword) and the logged result counts match
"""
import re, json, sys
sys.path.insert(0, ".")
import retrieval
t = open(sys.argv[1] if len(sys.argv) > 1 else "results/run_2026-11-13_1300_regression.md").read()
secs = {}
for m in re.finditer(r"^### (.+?)\n(.*?)(?=^### |\Z)", t, re.S | re.M):
    secs[m.group(1).strip()] = m.group(2)

def tries(body):
    out = []
    for m in re.finditer(r"\*\*Try (\d)\*\*\n(.*?)(?=\*\*Try \d\*\*|\Z)", body, re.S):
        blk = m.group(2)
        stopped = re.search(r"- stopped early: (yes.*|no)", blk).group(1)
        sel = re.search(r"- selected_item: (.*)", blk)
        card = re.search(r"Fit card:\n\n```\n(.*?)\n```", blk, re.S)
        trace = re.search(r"Trace:\n\n```\n(.*?)\n```", blk, re.S)
        out.append(dict(n=int(m.group(1)), stopped=stopped, sel=sel.group(1) if sel else None,
                        card=card.group(1).strip() if card else None, trace=trace.group(1) if trace else ""))
    return out

def title_price_platform(sel):
    m = re.match(r"(.*) \(\$([\d.]+), (\w+)\)", sel)
    return m.group(1), float(m.group(2)), m.group(3)

def body_sentences(card):
    lines = [l for l in card.splitlines() if l.strip() and not l.strip().startswith("#")]
    text = " ".join(lines)
    text = re.sub(r"(\s#\w+)+\s*$", "", text).strip()           # trailing hashtags on the same line
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text) if re.search(r"\w", s)]
    return sents

res = {}
# 1
r1 = [(x["n"], x["stopped"] == "no" and bool(x["card"])) for x in tries(secs["matching query completes"])]
res["1"] = r1
# 2
r2 = []
for x in tries(secs["impossible query stops early"]):
    ok = x["stopped"].startswith("yes") and "Try" in x["stopped"] and not re.search(r"\[\d+\] suggest_outfit", x["trace"]) and x["card"] is None
    r2.append((x["n"], ok))
res["2"] = r2
# 3
r3 = []
for x in tries(secs["state: item flows through"]):
    title, price, plat = title_price_platform(x["sel"])
    tr = x["trace"]
    first = re.search(r"\[2\] search_listings.*?out:\s+\d+ items: (.*?)(?: …| ?\n|,\s)", tr, re.S)
    first_title = re.search(r"\[2\] search_listings[^\n]*\n[^\n]*\n\s+out:\s+\d+ items: ([^,…]+?)(?:,| …|\n)", tr)
    sug_in = re.search(r"\[\d+\] suggest_outfit\n\s+in:\s+(.*?)(?: \+ wardrobe|\n)", tr)
    fit_in = re.search(r"\[\d+\] create_fit_card\n\s+in:\s+(.*)", tr)
    ok = (x["stopped"] == "no" and "switching" not in tr and first_title and first_title.group(1).strip() == title
          and sug_in and sug_in.group(1).strip() == title and fit_in and fit_in.group(1).strip() == title
          and re.search(r"\$%g(?!\d)" % price, x["card"]) and plat.lower() in x["card"].lower())
    r3.append((x["n"], bool(ok)))
res["3"] = r3
# 4
names = ["fit card A: band tee","fit card B: track jacket","fit card C: slip dress","fit card D: platform sneakers","fit card E: denim jacket"]
per = {k: tries(secs[k]) for k in names}
detail4 = []
r4 = []
for n in range(1, 6):
    good, firsts, missing = 0, [], 0
    for k in names:
        x = next(y for y in per[k] if y["n"] == n)
        if x["card"] is None:
            missing += 1; continue
        title, price, plat = title_price_platform(x["sel"])
        s = body_sentences(x["card"])
        okc = 2 <= len(s) <= 4 and re.search(r"\$%g(?!\d)" % price, x["card"]) and plat.lower() in x["card"].lower()
        good += bool(okc)
        firsts.append(s[0].strip().lower() if s else "")
        if not okc: detail4.append((n, k, len(s), x["card"][:140]))
    distinct = len(set(firsts)) == len(firsts)
    r4.append((n, good >= 4 and distinct and missing == 0, good, distinct, missing))
res["4"] = r4
# 5
qs = {"filters A: price only": ("graphic tee", None, 30.0), "filters B: size + price": ("top", "S", 20.0),
      "filters C: price, outerwear": ("jacket", None, 45.0), "filters D: shoe size + price": ("sneakers", "US 9", 50.0),
      "filters E: letter size + price": ("tee", "L", 25.0)}
expected = {}
viol = 0
for k, (d, s, p) in qs.items():
    got = retrieval.rank(d, s, p, strategy="keyword")
    expected[k] = len(got)
    for g in got:
        it = g["item"]
        if (p is not None and it["price"] > p) or not retrieval._size_matches(s, it["size"]): viol += 1
r5 = []
for n in range(1, 6):
    ok = True
    for k in qs:
        x = next(y for y in tries(secs[k]) if y["n"] == n)
        m = re.search(r"\[2\] search_listings[^\n]*\n[^\n]*\n\s+out:\s+(\d+) items", x["trace"])
        if not m or int(m.group(1)) != expected[k]: ok = False
    r5.append((n, ok and viol == 0))
res["5"] = r5
print(json.dumps({k: v for k, v in res.items()}, default=str))
print("criterion 4 failures:", detail4)
print("criterion 5 violations in recomputed lists:", viol, "expected counts:", expected)
# diagnostics for the README note
allt = {k: tries(v) for k, v in secs.items()}
print({k: sum(1 for x in v if x["stopped"].startswith("yes")) for k, v in allt.items() if any(x["stopped"].startswith("yes") for x in v)})
