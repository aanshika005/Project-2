#!/usr/bin/env python3
"""
Retrieval eval: does the "category" strategy find the right thing more often
than the "keyword" strategy, and does "keyword" still behave exactly as before?

    python eval_retrieval.py                      compare both strategies, write the run record
    python eval_retrieval.py --label after        name the run (goes in the file name)
    python eval_retrieval.py --check-baseline     keyword must match the pre-change snapshot
    python eval_retrieval.py --query 'corduroy jacket' [--size M] [--max-price 40]
                                                  one query, both strategies side by side

Needs only Python 3.11+ and the standard library: no API key, no network, no
model. It does not call the agent; it measures retrieval alone.

Inputs   eval/retrieval_heldout.json   21 labeled queries, written first
         eval/retrieval_dev.json       14 labeled queries, written second (includes the failures the
                                       README already named). Both sets were written before any
                                       strategy code; nothing was changed after seeing results.
Outputs  results/retrieval_<time>_<label>.jsonl   one JSON object per line (the run record)
         results/retrieval_<time>_<label>.md      the same numbers as tables
"""

import argparse
import datetime as dt
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

import retrieval

ROOT = Path(__file__).parent
SPLIT_FILES = {"dev": ROOT / "eval" / "retrieval_dev.json",
               "heldout": ROOT / "eval" / "retrieval_heldout.json",
               "fresh": ROOT / "eval" / "retrieval_fresh.json"}
# --set old (default) = the 35 queries from the extension unit; --set fresh = the capstone set.
SETS = {"old": ("dev", "heldout"), "fresh": ("fresh",)}
SNAPSHOT = ROOT / "eval" / "baseline_keyword_snapshot.json"
TIMING_REPS = 30


def load_queries(which: str = "old") -> list[dict]:
    out = []
    for split in SETS[which]:
        out.extend(json.loads(SPLIT_FILES[split].read_text(encoding="utf-8"))["queries"])
    return out


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def git_head() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=5)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return out.stdout.strip() + (" (uncommitted changes)" if dirty else "")
    except Exception:  # noqa: BLE001 — a missing git is not worth failing for
        return "unknown"


def search(q: dict, strategy: str) -> list[dict]:
    return retrieval.rank(q["description"], q["size"], q["max_price"], strategy=strategy)


def score_query(q: dict, ids: list[str]) -> dict:
    """Metrics for one ranked list. Relevance comes from the hand labels."""
    if q["expect_empty"]:
        return {"kind": "expect_empty", "correct": len(ids) == 0}
    rel = set(q["relevant"])
    first = next((i for i, x in enumerate(ids) if x in rel), None)
    top3 = ids[:3]
    return {
        "kind": "ranked",
        "top1": bool(ids) and ids[0] in rel,
        "rr": 0.0 if first is None else 1.0 / (first + 1),
        "recall3": len(set(top3) & rel) / min(3, len(rel)),
        "wrong3": sum(1 for x in top3 if x not in rel),
    }


def timed_ms(q: dict, strategy: str) -> float:
    """Median wall time of one search, milliseconds. Includes reading listings.json."""
    runs = []
    for _ in range(TIMING_REPS):
        t0 = time.perf_counter()
        search(q, strategy)
        runs.append((time.perf_counter() - t0) * 1000)
    return statistics.median(runs)


def aggregate(rows: list[dict]) -> dict:
    ranked = [r["metrics"] for r in rows if r["metrics"]["kind"] == "ranked"]
    empty = [r["metrics"] for r in rows if r["metrics"]["kind"] == "expect_empty"]
    mean = lambda key: sum(m[key] for m in ranked) / len(ranked) if ranked else None  # noqa: E731
    return {
        "n_ranked": len(ranked),
        "top1": mean("top1"),
        "mrr": mean("rr"),
        "recall3": mean("recall3"),
        "wrong3": mean("wrong3"),
        "n_expect_empty": len(empty),
        "empty_correct": sum(m["correct"] for m in empty),
    }


def run_eval(label: str, write: bool, which: str = "old") -> int:
    queries = load_queries(which)
    started = dt.datetime.now()
    header = {
        "type": "run", "label": label, "when": started.isoformat(timespec="seconds"),
        "python": platform.python_version(), "platform": platform.platform(),
        "git": git_head(), "listings_sha": sha(ROOT / "data" / "listings.json"),
        "query_files": {k: sha(SPLIT_FILES[k]) for k in SETS[which]},
        "n_queries": len(queries), "strategies": list(retrieval.STRATEGIES),
        "timing": f"median of {TIMING_REPS} calls per query, includes reading listings.json",
    }
    log = [header]
    rows = []
    for q in queries:
        for strategy in retrieval.STRATEGIES:
            ranked = search(q, strategy)
            ids = [r["item"]["id"] for r in ranked]
            row = {
                "type": "query", "id": q["id"], "split": q["split"], "strategy": strategy,
                "query": q["query"], "description": q["description"], "size": q["size"],
                "max_price": q["max_price"], "relevant": q["relevant"],
                "expect_empty": q["expect_empty"], "returned": ids,
                "scores": [r["score"] for r in ranked],
                "type_match": [r["type_match"] for r in ranked],
                "families": ranked[0]["families"] if ranked else retrieval.detect_families(q["description"]),
                "metrics": score_query(q, ids), "ms": round(timed_ms(q, strategy), 3),
            }
            rows.append(row)
            log.append(row)

    summary = {}
    splits = (*SETS[which], "all") if which == "old" else SETS[which]
    for split in splits:
        for strategy in retrieval.STRATEGIES:
            sel = [r for r in rows if r["strategy"] == strategy and (split == "all" or r["split"] == split)]
            agg = aggregate(sel)
            agg["median_ms"] = round(statistics.median(r["ms"] for r in sel), 3)
            summary[f"{split}/{strategy}"] = agg
    log.append({"type": "summary", **summary})

    md = render_markdown(header, rows, summary)
    print(md)
    if write:
        out_dir = ROOT / "results"
        out_dir.mkdir(exist_ok=True)
        stem = f"retrieval_{which if which != 'old' else ''}{'_' if which != 'old' else ''}{started.strftime('%Y-%m-%d_%H%M')}" + (f"_{label}" if label else "")
        (out_dir / f"{stem}.jsonl").write_text("\n".join(json.dumps(x) for x in log) + "\n", encoding="utf-8")
        (out_dir / f"{stem}.md").write_text(md, encoding="utf-8")
        print(f"\nwrote results/{stem}.jsonl and results/{stem}.md", file=sys.stderr)
    return 0


def pct(x):
    return "n/a" if x is None else f"{100 * x:.0f}%"


def render_markdown(header, rows, summary) -> str:
    L = []
    L.append(f"# Retrieval eval{' — ' + header['label'] if header['label'] else ''}\n")
    L.append(f"- When: {header['when']}  ·  Python {header['python']}  ·  {header['platform']}")
    L.append(f"- Git: {header['git']}  ·  listings.json sha {header['listings_sha']}  ·  "
             f"query files {header['query_files']}")
    L.append(f"- {header['n_queries']} labeled queries × {len(header['strategies'])} strategies. "
             f"Timing: {header['timing']}.\n")
    for split, title in (("dev", "Dev set (14 queries, written second; includes the failures the README already named)"),
                         ("heldout", "Held-out set (21 queries, written first)"),
                         ("fresh", "Fresh set (written for the capstone criteria, after they were committed)"),
                         ("all", "Both sets")):
        if f"{split}/keyword" not in summary:
            continue
        L.append(f"## {title}\n")
        L.append("| Strategy | Top-1 correct | MRR | Recall@3 | Wrong items in top 3 (mean) | Expect-empty correct | Median ms |")
        L.append("|---|---|---|---|---|---|---|")
        for strategy in retrieval.STRATEGIES:
            a = summary[f"{split}/{strategy}"]
            L.append(f"| {strategy} | {pct(a['top1'])} ({round(a['top1'] * a['n_ranked'])}/{a['n_ranked']}) | {a['mrr']:.2f} | {pct(a['recall3'])} | "
                     f"{a['wrong3']:.2f} | {a['empty_correct']}/{a['n_expect_empty']} | {a['median_ms']} |")
        L.append("")
    L.append("## Per query\n")
    L.append("✓ = top result is labeled relevant. Δ marks queries where the two strategies disagree on top-1.\n")
    L.append("| ID | Split | Query | Families detected | keyword top-1 | category top-1 | Δ |")
    L.append("|---|---|---|---|---|---|---|")
    by_id = {}
    for r in rows:
        by_id.setdefault(r["id"], {})[r["strategy"]] = r

    def cell(r):
        if r["expect_empty"]:
            return "[] ✓" if not r["returned"] else f"{r['returned'][0]} ✗"
        if not r["returned"]:
            return "[] ✗"
        return f"{r['returned'][0]} {'✓' if r['metrics']['top1'] else '✗'}"

    for qid, pair in by_id.items():
        k, c = pair["keyword"], pair["category"]
        k_ok = k["metrics"].get("top1", k["metrics"].get("correct"))
        c_ok = c["metrics"].get("top1", c["metrics"].get("correct"))
        delta = "better" if (c_ok and not k_ok) else "WORSE" if (k_ok and not c_ok) else ""
        L.append(f"| {qid} | {k['split']} | {k['query']} | {', '.join(c['families']) or '—'} | "
                 f"{cell(k)} | {cell(c)} | {delta} |")
    return "\n".join(L) + "\n"


def check_baseline() -> int:
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    bad = []
    for case in snap["cases"]:
        got = [r["item"]["id"] for r in retrieval.rank(
            case["description"], case["size"], case["max_price"], strategy="keyword")]
        if got != case["ids"]:
            bad.append((case["id"], case["description"], case["ids"], got))
    print(f"baseline snapshot from git {snap['git_head']}: {len(snap['cases'])} cases, "
          f"{len(snap['cases']) - len(bad)} identical, {len(bad)} different")
    for cid, desc, want, got in bad:
        print(f"  {cid} {desc!r}\n    snapshot: {want}\n    now:      {got}")
    return 1 if bad else 0


def show_query(args) -> int:
    from utils.data_loader import load_listings
    titles = {x["id"]: x["title"] for x in load_listings()}
    print(f"query: {args.query!r}  size={args.size}  max_price={args.max_price}")
    print(f"garment-type families detected: {retrieval.detect_families(args.query) or 'none (category falls back to keyword)'}\n")
    for strategy in retrieval.STRATEGIES:
        print(f"[{strategy}]")
        ranked = retrieval.rank(args.query, args.size, args.max_price, strategy=strategy)
        if not ranked:
            print("  (nothing matched)")
        for i, r in enumerate(ranked[:5], 1):
            extra = f"  type_match={r['type_match']}" if strategy == "category" else ""
            print(f"  {i}. {r['item']['id']}  score={r['score']}{extra}  {titles[r['item']['id']]}")
        print()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Compare retrieval strategies on labeled queries.")
    p.add_argument("--label", default="", help="a name for this run, used in the file name")
    p.add_argument("--no-log", action="store_true", help="print only; don't write results/ files")
    p.add_argument("--check-baseline", action="store_true",
                   help="verify strategy=keyword still matches the pre-change snapshot")
    p.add_argument("--set", dest="which", choices=sorted(SETS), default="old",
                   help="old = dev+heldout (default); fresh = eval/retrieval_fresh.json")
    p.add_argument("--query", help="run one query through both strategies")
    p.add_argument("--size")
    p.add_argument("--max-price", type=float)
    args = p.parse_args()
    if args.check_baseline:
        return check_baseline()
    if args.query:
        return show_query(args)
    return run_eval(args.label, write=not args.no_log, which=args.which)


if __name__ == "__main__":
    sys.exit(main())
