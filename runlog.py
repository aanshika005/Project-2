"""
Structured run log: one JSON object per line, one line per agent run.

    python runlog.py show            the last 12 runs, one per line
    python runlog.py show -n 30
    python runlog.py summary         counts by outcome, and mean timings/tokens

`agent.py::run_agent` writes a record every time it finishes, whether the run
completed, found nothing, couldn't reach the model, or crashed. A run that dies
leaves a line, so a failure never shows up only as an absence.

Where it goes: logs/fitfindr_runs.jsonl (committed on purpose; it is the
evidence that the system ran). Set FITFINDR_RUN_LOG=/some/other/file to send it
elsewhere, or FITFINDR_RUN_LOG=off to stop logging (run_eval.py's 75-run
sweeps are easier to read that way).

Standard library only. Writing a record never raises: if the log can't be
written, one warning goes to stderr and the run carries on.

Fields (every record has all of them; missing values are null):
  ts              UTC time the run finished, ISO 8601
  run_id          8 hex characters, unique per run
  entrypoint      the script that started it (app.py, run_eval.py, measure_cost.py, serve.py)
  query           the raw input
  strategy        search strategy used: keyword | category
  parsed          description / size / max_price pulled out of the query
  wardrobe_items  how many pieces were in the wardrobe
  outcome         completed | no_results | search_failed | model_unavailable | crashed | interrupted
  error           the message the user saw, or "ExceptionType: text" for a crash
  n_results       how many listings search returned
  selected        id, title, price, platform of the item the run settled on
  switched_from   id of the original top match when the pricey branch swapped it
  price_verdict   good deal | about average | pricey | not enough similar listings
  fit_card_chars  length of the fit card, or null if none was written
  duration_ms     wall time of the whole run, including waiting on rate limits
  step_ms         wall time per loop step (parse, search, select, compare, suggest, fit_card)
  wait_ms         time spent sleeping for rate limits / retries (part of duration_ms)
  model_calls     requests actually sent to the model (cache hits excluded)
  cache_hits      answers reused from the cache
  prompt_tokens   tokens sent, as reported by the service
  output_tokens   tokens received, as reported by the service
  model, python   what it ran on
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT = Path(__file__).parent / "logs" / "fitfindr_runs.jsonl"
_warned = False


def log_path() -> Path | None:
    """Where records go right now, or None when logging is switched off."""
    setting = os.getenv("FITFINDR_RUN_LOG", "").strip()
    if setting.lower() in ("off", "0", "none"):
        return None
    return Path(setting) if setting else _DEFAULT


def new_run_id() -> str:
    return uuid.uuid4().hex[:8]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def write(record: dict) -> None:
    """Append one record. Never raises."""
    global _warned
    path = log_path()
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001 — logging must never break a run
        if not _warned:
            _warned = True
            print(f"  [runlog] couldn't write {path}: {exc}", file=sys.stderr)


def read(path: Path | None = None) -> list[dict]:
    """Every record in the log, oldest first. Skips lines that aren't JSON."""
    path = path or log_path() or _DEFAULT
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _mean(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return sum(values) / len(values) if values else None


def summary(records: list[dict]) -> str:
    if not records:
        return "no runs logged yet"
    by_outcome: dict[str, int] = {}
    for r in records:
        by_outcome[r["outcome"]] = by_outcome.get(r["outcome"], 0) + 1
    done = [r for r in records if r["outcome"] == "completed"]
    lines = [f"{len(records)} runs: " + ", ".join(f"{n} {k}" for k, n in sorted(by_outcome.items()))]
    if done:
        for label, key, scale, unit in (
            ("duration", "duration_ms", 1000, "s"), ("waiting on rate limits", "wait_ms", 1000, "s"),
            ("model calls", "model_calls", 1, ""), ("prompt tokens", "prompt_tokens", 1, ""),
            ("output tokens", "output_tokens", 1, ""),
        ):
            m = _mean([r.get(key) for r in done])
            if m is not None:
                lines.append(f"  mean {label} over {len(done)} completed runs: {m / scale:.1f}{unit}")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Read the FitFindr run log.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="print the last runs, one JSON object per line")
    s.add_argument("-n", type=int, default=12)
    sub.add_parser("summary", help="counts by outcome and mean timings")
    args = p.parse_args()
    records = read()
    if args.cmd == "show":
        for r in records[-args.n:]:
            print(json.dumps(r, ensure_ascii=False))
    else:
        print(summary(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
