"""Run the five capstone criteria once (one "trial") and save the counts.

    python run_capstone.py --trial 1 2>&1 | tee results/capstone/trial1_raw.txt
    python run_capstone.py --trial 2 2>&1 | tee results/capstone/trial2_raw.txt
    python run_capstone.py --trial 3 2>&1 | tee results/capstone/trial3_raw.txt
    python run_capstone.py --table          # builds the run log table from the three trials

Nothing is changed between trials. Criteria are the ones in criteria.md under
"Capstone criteria". Needs the full environment from RUNNING.md (packages, GEMINI_API_KEY).
Each trial makes real model calls (cache is switched off) and takes a few minutes, because
of the 15-requests-a-minute limit.

Per trial, per criterion, what is run:
  1  eval/retrieval_fresh.json through strategy=category            (no model; deterministic)
  2  all 35 old queries + the fresh set through both strategies     (no model; deterministic)
  3  5 bad inputs through run_agent                                  (no model call is reached)
  4  10 full runs with strategy=category, cache off                  (20 real model calls)
  5  20 mixed runs: 8 complete, 5 match nothing, 4 bad API key, 3 bad strategy
Records go to logs/capstone_trialN_c{3,4,5}.jsonl.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

os.environ["AI201_CACHE"] = "0"          # before config is imported: every model run is a real run

ROOT = Path(__file__).parent
OUT = ROOT / "results" / "capstone"
FIELDS = {"ts", "run_id", "entrypoint", "query", "strategy", "parsed", "wardrobe_items", "outcome",
          "error", "n_results", "selected", "switched_from", "price_verdict", "fit_card_chars",
          "duration_ms", "step_ms", "wait_ms", "model_calls", "cache_hits", "prompt_tokens",
          "output_tokens", "model", "python"}
C4_QUERIES = ["vintage band tee", "90s track jacket in size M", "silk slip dress",
              "platform sneakers size 8", "denim jacket under $50"]
GOOD = C4_QUERIES + ["flannel shirt", "denim shorts", "velvet blazer"]       # 8 completing queries
NOTHING = ["denim jacket under $5", "silk dress under $5", "sneakers under $5",
           "hoodie under $5", "jeans under $5"]                                # cheapest listing is $12
BAD_STRATEGY = ["semantic", "", "CATEGORY"]


def head(n, text):
    print(f"\n{'=' * 70}\nCRITERION {n}: {text}\n{'=' * 70}")


def ok_top1(m):
    return m.get("top1", m.get("correct"))


def c1_c2():
    import eval_retrieval as E
    fresh = E.load_queries("fresh")
    scoreable = [q for q in fresh if not q["expect_empty"]]
    hit = 0
    head(1, "category puts a labeled-relevant listing at rank 1 (fresh set)")
    for q in scoreable:
        ids = [r["item"]["id"] for r in E.search(q, "category")]
        good = ok_top1(E.score_query(q, ids))
        hit += bool(good)
        print(f"  {q['id']} {q['query']!r:34} top-1={ids[0] if ids else '-':8} {'OK' if good else 'MISS'}")
    need = math.ceil(13 / 15 * len(scoreable))
    print(f"  -> {hit} of {len(scoreable)} (target {need})")
    head(2, "no query where keyword's top result is right and category's is not")
    worse, checked = [], 0
    for q in E.load_queries("old") + fresh:
        k = ok_top1(E.score_query(q, [r["item"]["id"] for r in E.search(q, "keyword")]))
        c = ok_top1(E.score_query(q, [r["item"]["id"] for r in E.search(q, "category")]))
        checked += 1
        if k and not c:
            worse.append(q["id"])
    print(f"  -> {len(worse)} regressions in {checked} queries {worse}")
    return ({"hit": hit, "n": len(scoreable), "need": need},
            {"worse": len(worse), "checked": checked, "ids": worse})


def fresh_log(path):
    path.parent.mkdir(exist_ok=True)
    path.write_text("")
    os.environ["FITFINDR_RUN_LOG"] = str(path)
    return path


def read_log(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def c3(trial):
    import runlog
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe
    path = fresh_log(ROOT / "logs" / f"capstone_trial{trial}_c3.jsonl")
    head(3, "bad inputs to the new strategy stop cleanly")
    cases = [("corduroy jacket", "semantic", True), ("corduroy jacket", "", True),
             ("corduroy jacket", "CATEGORY", True), ("", "category", False), ("   ", "category", False)]
    passed = 0
    for query, strategy, needs_names in cases:
        print(f"\n  input: query={query!r} strategy={strategy!r}")
        try:
            s = run_agent(query, get_example_wardrobe(), strategy=strategy)
        except Exception as e:                                   # noqa: BLE001
            print(f"  ESCAPED: {type(e).__name__}: {e}  -> FAIL")
            continue
        rec = runlog.read(path)[-1] if runlog.read(path) else {}
        msg = s.get("error") or ""
        reasons = []
        if rec.get("outcome") not in ("search_failed", "no_results"):
            reasons.append(f"logged outcome {rec.get('outcome')!r}")
        if not msg.strip():
            reasons.append("empty message")
        if needs_names and not ("keyword" in msg and "category" in msg):
            reasons.append("message does not name both keyword and category")
        print(f"  outcome={rec.get('outcome')!r}  message={msg!r}")
        print(f"  -> {'PASS' if not reasons else 'FAIL: ' + '; '.join(reasons)}")
        passed += not reasons
    print(f"\n  -> {passed} of {len(cases)}")
    return {"pass": passed, "n": len(cases)}


def c4(trial):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe
    path = fresh_log(ROOT / "logs" / f"capstone_trial{trial}_c4.jsonl")
    head(4, "10 category runs, each completed run makes exactly 2 model calls")
    for i in range(10):
        run_agent(C4_QUERIES[i % 5], get_example_wardrobe(), strategy="category")
    recs = read_log(path)
    good = [r for r in recs if r["outcome"] == "completed" and r["model_calls"] == 2]
    print("\n  run  outcome       model_calls  cache_hits")
    for n, r in enumerate(recs, 1):
        print(f"  {n:>3}  {r['outcome']:<13} {r['model_calls']:<12} {r['cache_hits']}")
    print(f"\n  -> {len(good)} of {len(recs)} completed with exactly 2 model calls")
    return {"pass": len(good), "n": 10, "records": len(recs)}


def c5(trial):
    import generate
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe
    path = fresh_log(ROOT / "logs" / f"capstone_trial{trial}_c5.jsonl")
    head(5, "20 mixed runs each leave exactly one valid record")
    plan = []
    for i in range(8):
        plan.append((GOOD[i], "category", "completed", None))
        if i < 5:
            plan.append((NOTHING[i], "category", "no_results", None))
        if i < 4:
            plan.append((GOOD[i + 3], "category", "model_unavailable", "bad-key"))
        if i < 3:
            plan.append(("corduroy jacket", BAD_STRATEGY[i], "search_failed", None))
    real_key = os.environ.get("GEMINI_API_KEY")
    for query, strategy, _, mode in plan:
        if mode == "bad-key":
            os.environ["GEMINI_API_KEY"] = "not-a-real-key-capstone"
            generate._client = None
        try:
            run_agent(query, get_example_wardrobe(), strategy=strategy)
        except Exception as e:                                   # noqa: BLE001
            print(f"  ESCAPED on {query!r}/{strategy!r}: {type(e).__name__}: {e}")
        finally:
            if mode == "bad-key":
                if real_key is None:
                    os.environ.pop("GEMINI_API_KEY", None)
                else:
                    os.environ["GEMINI_API_KEY"] = real_key
                generate._client = None
    recs = read_log(path)
    print(f"\n  log lines: {len(recs)} (expected {len(plan)})")
    passed = 0
    for n, ((query, strategy, want, _), r) in enumerate(zip(plan, recs), 1):
        why = []
        if set(r) != FIELDS:
            why.append(f"fields differ: missing {sorted(FIELDS - set(r))} extra {sorted(set(r) - FIELDS)}")
        if r.get("outcome") != want:
            why.append(f"outcome {r.get('outcome')!r}, wanted {want!r}")
        if want != "completed" and not r.get("error"):
            why.append("error is empty")
        print(f"  {n:>2} {want:<18} got {r.get('outcome'):<18} {'PASS' if not why else 'FAIL ' + '; '.join(why)}")
        passed += not why
    if len(recs) != len(plan):
        passed = min(passed, len(recs))                      # a missing line is itself a failure
    print(f"\n  -> {passed} of {len(plan)} runs; log lines {len(recs)} of {len(plan)}")
    return {"pass": passed if len(recs) == len(plan) else passed, "n": len(plan), "lines": len(recs)}


def table():
    trials = [json.loads((OUT / f"trial{i}.json").read_text()) for i in (1, 2, 3)]
    rows = [
        ("1. category finds the right garment first (fresh set)", lambda t: f"{t['c1']['need']} of {t['c1']['n']}",
         lambda t: f"{t['c1']['hit']}/{t['c1']['n']}", lambda t: t["c1"]["hit"] >= t["c1"]["need"]),
        ("2. never turns a right answer into a wrong one", lambda t: "0 regressions",
         lambda t: f"{t['c2']['worse']} in {t['c2']['checked']}", lambda t: t["c2"]["worse"] == 0),
        ("3. bad input to the new strategy stops cleanly", lambda t: "5 of 5",
         lambda t: f"{t['c3']['pass']}/{t['c3']['n']}", lambda t: t["c3"]["pass"] == t["c3"]["n"]),
        ("4. no extra model calls", lambda t: "10 of 10",
         lambda t: f"{t['c4']['pass']}/{t['c4']['n']}", lambda t: t["c4"]["pass"] == t["c4"]["n"]),
        ("5. every run leaves a record, including failures", lambda t: "20 of 20",
         lambda t: f"{t['c5']['pass']}/{t['c5']['n']}", lambda t: t["c5"]["pass"] == t["c5"]["n"]
         and t["c5"]["lines"] == t["c5"]["n"]),
    ]
    L = ["| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |", "|---|---|---|---|---|---|"]
    for name, target, show, met in rows:
        verdict = "MET" if all(met(t) for t in trials) else "MISSED"
        L.append(f"| {name} | {target(trials[0])} | " + " | ".join(show(t) for t in trials) + f" | {verdict} |")
    text = "\n".join(L) + "\n"
    print(text)
    (OUT / "run_log.md").write_text(text)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--trial", type=int, choices=(1, 2, 3))
    p.add_argument("--table", action="store_true")
    a = p.parse_args()
    if a.table:
        return table()
    if not a.trial:
        p.error("give --trial N or --table")
    r1, r2 = c1_c2()
    r3 = c3(a.trial)
    r4 = c4(a.trial)
    r5 = c5(a.trial)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"trial{a.trial}.json").write_text(json.dumps(
        {"trial": a.trial, "c1": r1, "c2": r2, "c3": r3, "c4": r4, "c5": r5}, indent=1))
    print(f"\nsaved results/capstone/trial{a.trial}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
