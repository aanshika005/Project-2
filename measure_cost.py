#!/usr/bin/env python3
"""
Measure what one FitFindr run costs.

    python measure_cost.py                 10 real runs, cache off
    python measure_cost.py --runs 20
    python measure_cost.py --price-in 0.10 --price-out 0.40     also show dollars, from YOUR prices
                                                                 (per million tokens; look them up for
                                                                 the model in config.MODEL)

What it does: runs the whole agent (search over MCP, outfit, fit card) N times
on five matching queries, round-robin, with the response cache OFF so every
run really calls the model. Each run writes its normal record to the run log
(logs/fitfindr_runs.jsonl); this script then averages those records.

The real costs of a run here are model tokens and seconds. On the free tier the
dollar cost is zero, so the dollar line only appears if you pass prices.
Tokens are what the service reported for these runs (generate.token_counts());
seconds are wall time measured around each run. Seconds are split into time
spent waiting on the 15-requests-a-minute limit and everything else, because
the first is the limiter, not the system.

Needs the full environment from RUNNING.md (packages, GEMINI_API_KEY).
"""

import argparse
import datetime as dt
from collections import Counter
import os
import statistics
import sys

os.environ["AI201_CACHE"] = "0"          # before config is imported: five tries must be five real answers

import config  # noqa: E402
import generate  # noqa: E402
import runlog  # noqa: E402
from agent import run_agent  # noqa: E402
from utils.data_loader import get_example_wardrobe  # noqa: E402

QUERIES = [
    "vintage band tee",
    "90s track jacket in size M",
    "silk slip dress",
    "platform sneakers size 8",
    "denim jacket under $50",
]


def stats(values):
    return (statistics.mean(values), statistics.median(values), min(values), max(values))


def main() -> int:
    p = argparse.ArgumentParser(description="Average the cost of N real agent runs.")
    p.add_argument("--runs", type=int, default=10)
    p.add_argument("--strategy", choices=["keyword", "category"], default="keyword")
    p.add_argument("--price-in", type=float, help="dollars per million input tokens")
    p.add_argument("--price-out", type=float, help="dollars per million output tokens")
    args = p.parse_args()

    if runlog.log_path() is None:
        print("The run log is switched off (FITFINDR_RUN_LOG). Turn it on: this script reads it.", file=sys.stderr)
        return 1

    start_index = len(runlog.read())
    started = dt.datetime.now()
    for i in range(args.runs):
        query = QUERIES[i % len(QUERIES)]
        print(f"run {i + 1}/{args.runs}: {query!r}", flush=True)
        run_agent(query, get_example_wardrobe(), strategy=args.strategy)

    mine = runlog.read()[start_index:]
    done = [r for r in mine if r["outcome"] == "completed"]
    counts = ", ".join(f"{n} {o}" for o, n in sorted(Counter(r["outcome"] for r in mine).items()))
    lines = [f"# Cost of one run — {started.strftime('%Y-%m-%d %H:%M')}\n",
             f"- Model: `{config.MODEL}`  ·  strategy: {args.strategy}  ·  cache: off  ·  Python {sys.version.split()[0]}",
             f"- {len(mine)} runs started, {len(done)} completed ({counts})",
             f"- Queries, round-robin: {QUERIES}",
             "- Measured from the run log: `duration_ms`, `wait_ms`, `model_calls`, `prompt_tokens`, `output_tokens` "
             "of each completed run. Averages are over completed runs only.\n"]
    if not done:
        lines.append("No run completed, so there is no cost to report. Look at the log: `python runlog.py show`.")
    else:
        rows = [
            ("Wall time per run (s)", [r["duration_ms"] / 1000 for r in done]),
            ("… of which waiting on the rate limit (s)", [r["wait_ms"] / 1000 for r in done]),
            ("… of which working (s)", [(r["duration_ms"] - r["wait_ms"]) / 1000 for r in done]),
            ("Model calls per run", [r["model_calls"] for r in done]),
            ("Prompt tokens per run", [r["prompt_tokens"] for r in done]),
            ("Output tokens per run", [r["output_tokens"] for r in done]),
            ("Total tokens per run", [r["prompt_tokens"] + r["output_tokens"] for r in done]),
        ]
        lines += ["| Per run | Mean | Median | Min | Max |", "|---|---|---|---|---|"]
        for label, vals in rows:
            m, med, lo, hi = stats(vals)
            lines.append(f"| {label} | {m:.1f} | {med:.1f} | {lo:.1f} | {hi:.1f} |")
        lines.append("")
        if args.price_in is not None and args.price_out is not None:
            pin = statistics.mean(r["prompt_tokens"] for r in done)
            pout = statistics.mean(r["output_tokens"] for r in done)
            dollars = (pin * args.price_in + pout * args.price_out) / 1_000_000
            lines.append(f"At ${args.price_in}/M input and ${args.price_out}/M output tokens (prices you supplied), "
                         f"one run is about ${dollars:.5f}. Those prices are not measured; the token counts are.")
        else:
            lines.append("Dollar cost: $0.00 on the free tier. Pass `--price-in` and `--price-out` to price the measured tokens.")
    text = "\n".join(lines) + "\n"
    print("\n" + text)
    out = config.ROOT / "results" / f"cost_{started.strftime('%Y-%m-%d_%H%M')}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out.relative_to(config.ROOT)}", file=sys.stderr)
    print(generate.usage(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
