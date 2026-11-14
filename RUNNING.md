# Running FitFindr

Everything about how the starter works and how to use it.

---

## Run it (Path B: local, with logs)

FitFindr runs on my machine, started by one command, and every run appends a
structured record to `logs/fitfindr_runs.jsonl`. There is no hosted URL.

**Start it** (from the repo root, virtual environment active):

```bash
python app.py ask 'vintage graphic tee under $30'
```

It prints the match, the outfit and the fit card, and one JSON line lands in the log.
Try `--strategy category` for the second retrieval strategy, and `--trace` for the loop step by step.

**What the environment needs**

| | |
|---|---|
| Python | 3.11, 3.12 or 3.13 (not 3.14). Developed and tested on 3.13 |
| Packages | pinned in `requirements.txt`: `python-dotenv>=1.0,<1.2`, `google-genai>=1.0,<2.0`, `mcp>=1.0,<2.0` (MCP 2.x breaks `mcp_server.py`), `flask>=3.0,<4.0`, `gunicorn>=21.2,<24.0` |
| Model | none on disk. The outfit and fit card come from the hosted Gemini API (`gemini-3.5-flash-lite`, set in `config.py`), so there are no model files to download. Needs a free `GEMINI_API_KEY` in `.env` and an internet connection |
| Data | `data/listings.json`, 19 KB, in the repo |
| Limits | the free tier allows 15 requests a minute; `generate.py` waits when it hits that, and the log records how long it waited (`wait_ms`) |

**From a clean checkout, the exact steps**

```bash
git clone https://github.com/aanshika005/Project-2.git fitfindr-fresh
cd fitfindr-fresh
python3 -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                  # then paste your key into .env
python test.py                        # should end with everything passing
python app.py ask 'vintage graphic tee under $30'
python runlog.py show -n 1            # the record that run just wrote
```

**Without an API key** you can still run the retrieval half, which needs only
Python 3.10+ and the standard library: `python eval_retrieval.py`
(see "Extension: category-aware search" below).

**The run log**

| Command | What it does |
|---|---|
| `python runlog.py show -n 12` | The last 12 runs, one JSON object per line |
| `python runlog.py summary` | Counts by outcome, mean time and tokens |
| `python measure_cost.py` | Runs the agent 10 times with the cache off and writes `results/cost_<time>.md` (the cost of one run) |
| `FITFINDR_RUN_LOG=off python run_eval.py --label x` | Run the 75-run eval without adding 75 lines to the log |
| `FITFINDR_RUN_LOG=/tmp/x.jsonl python app.py ask '...'` | Send records to another file |

Each record has: `ts`, `run_id`, `entrypoint`, `query`, `strategy`, `parsed`, `wardrobe_items`,
`outcome`, `error`, `n_results`, `selected`, `switched_from`, `price_verdict`, `fit_card_chars`,
`duration_ms`, `step_ms`, `wait_ms`, `model_calls`, `cache_hits`, `prompt_tokens`, `output_tokens`,
`model`, `python`. `outcome` is one of `completed`, `no_results`, `search_failed`,
`model_unavailable`, `crashed`, `interrupted`; a run that fails writes a record like any other.
The full field list is at the top of `runlog.py`.

---

## Before your first class

Setup happens **before class**. The [environment setup page](../pages/ide_setup)
has the per-operating-system commands and the exact versions.

**Same API key you set up in unit 1.** Nothing new to sign up for. There is one
new package — the MCP SDK, for unit 4 — and it installs with everything else.

From inside this repo after you've forked and cloned it:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your key into .env
python test.py
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env         # then paste your key into .env
python test.py
```

**You're ready when `python test.py` passes.**

If it doesn't and you've made one honest attempt at the error, post the
**whole** output in the help channel.

> Activate the virtual environment every time you open a new terminal. You
> should see `(.venv)` at the start of your prompt.

---

## Your first five minutes

Start with the data. Your tools will only be as good as your understanding of
what they're reading, and ten minutes here saves an hour of confused debugging.

```bash
python app.py fields                    # what a listing and a wardrobe item hold
python app.py listings --full -n 6      # read six listings all the way through
python app.py examples                  # queries worth trying
python app.py ask 'vintage graphic tee under $30'
```

> **Quote your queries with single quotes**, on every operating system. In
> PowerShell, `"vintage graphic tee under $30"` in double quotes silently
> becomes `vintage graphic tee under ` — PowerShell reads `$30` as a variable
> and substitutes nothing. You get results with no price ceiling and no error
> saying so. Single quotes are literal in PowerShell, bash and zsh alike.

That last one runs the loop. All three tools are stubs, so it will tell you the
loop isn't built yet. **That's the correct starting position** — it runs, and it
does nothing.

---

## Every command

| Command | What it does |
|---|---|
| `python test.py` | Checks your environment. Run it whenever something feels off |
| `python app.py fields` | The fields a listing and a wardrobe item have — **Milestone 1** |
| `python app.py listings` | Browse the data. `--full` for whole records, `-n` for how many |
| `python app.py examples` | Queries worth trying, including one that matches nothing |
| `python app.py ask '...'` | Run the agent on one query — **single quotes** |
| `python app.py ask` | Keep asking until you press Enter on an empty line |
| `python agent.py` | Runs both example paths — one that matches, one that can't |
| `python mcp_server.py` | Starts your MCP server — **unit 4** |
| `python mcp_client.py` | Asks the server what it offers — **unit 4** |
| `python run_eval.py --label before` | Runs every scenario five times and writes the run log — **unit 4** |
| `python serve.py` | Serves the agent over HTTP instead of exiting — **unit 9** |

Useful flags on `ask`:

| Flag | What it does |
|---|---|
| `--trace` | Print the loop step by step, once you've added the trace calls |
| `--empty-wardrobe` | Run as a user with nothing saved — one of unit 4's failure modes |

---

## Which command goes with which milestone

### Unit 3 — the build

| Milestone | What you're doing | Where |
|---|---|---|
| 1 | Read the data, run the starter | `app.py fields`, `app.py listings --full`, `app.py ask` |
| 2 | Spec your three tools | README, **Tool Inventory** |
| 3 | Write your acceptance criteria | `criteria.md` |
| 4 | Build the three tools | `tools.py`, tested one at a time from a terminal |
| 5 | Wire the loop and the state | `agent.py::run_agent` |
| 6 | Write it up | README |

### Unit 4 — the test

| Milestone | What you're doing | Where |
|---|---|---|
| 1 | Move one tool onto MCP | `mcp_server.py`, then `mcp_client.call_tool` in `run_agent` |
| 2 | Break it on purpose, then trace it | `trace.py`, `app.py ask --trace` |
| 3 | Run your test | `scenarios.py`, then `run_eval.py --label before` |
| 4 | Call each criterion, diagnose the misses | README |
| 5 | Fix one thing and re-run | `run_eval.py --label after` |
| 6 | Say what's still broken | README |

---

## Running it somewhere else — **unit 9**

Everything above exits when the command finishes. A host has nothing to keep
running, so before you can deploy this you need something that stays up.
`serve.py` is that: the same `run_agent()`, behind two HTTP routes.

On your machine:

```bash
python serve.py
curl -X POST http://localhost:5000/ask \
  -H 'Content-Type: application/json' \
  -d '{"query": "vintage graphic tee under $30"}'
```

On a host, the start command is:

```bash
gunicorn serve:app
```

| Thing | What it means |
|---|---|
| `PORT` | The host tells your app which port to listen on by setting this. Both `serve.py` and `gunicorn` read it, and `serve.py` falls back to `5000` on your machine. Don't hard-code a port |
| `POST /ask` | `{"query": "...", "wardrobe": {...}}` — wardrobe optional. Returns the session dict, `error` and all |
| `GET /health` | Says `ok` if the app is awake |
| It answers one request at a time | On purpose. A second request waits for the first to finish, and prints `[serve] another request is still running` while it waits. An MCP tool call starts a whole second Python process, and the free tier's 512 MB has no room for two of those at once — and `generate.py`'s rate-limit counting assumes one caller. The reasoning is written out in `serve.py` |
| `gunicorn serve:app`, exactly | Not `-k gevent`, not `-k eventlet`, not wrapped for uvicorn. `mcp_client.call_tool` uses `asyncio.run()`, which won't start inside a running event loop, so an async worker breaks **every** MCP call — and only once you've deployed it |
| The first request is slow | The free tier puts your app to sleep after about fifteen minutes of nothing. The next request wakes it up and waits for it — around a minute. Not a bug, and worth knowing before you demo it |

`serve.py` ships with **no logging and no timing in it**, on purpose. You add
that yourself in the follow-along, before you deploy — instrumenting first is
the point of the session.

---

## Where everything lives

| File | What it does |
|---|---|
| `config.py` | Every setting worth changing — **TEMPERATURE and the cache are at the top** |
| `tools.py` | Your three tools. **Stubs — you build these** |
| `agent.py` | The planning loop and the session. **Stub — you build this** |
| `generate.py` | The only thing that calls out to a service. Handles pacing and quota |
| `trace.py` | The trace helper, and the loop's stop condition |
| `app.py` | The command line |
| `serve.py` | The same agent over HTTP, for deploying — **unit 9** |
| `mcp_server.py` | Your MCP server — **unit 4, you register the tool** |
| `mcp_client.py` | Calling an MCP tool from your agent. Given to you |
| `scenarios.py` | What your test runs. **You fill this in** |
| `run_eval.py` | Runs the scenarios repeatedly and writes the run log |
| `criteria.md` | Your five acceptance criteria. **You fill this in** |
| `data/` | 40 listings and the wardrobe schema |
| `utils/data_loader.py` | Loading the data. Use this rather than reading the files yourself |
| `results/` | Run logs. **Commit these** — they're your evidence |

---

## The two settings people go looking for

Both are at the top of `config.py`, and the brief points at them by name.

If your fit cards come out **word-for-word identical** every time, it is one of:

- **`CACHE_ENABLED`** — while you build, identical prompts reuse the answer
  already received. That's deliberate; it makes debugging free. `run_eval.py`
  turns it off automatically.
- **`TEMPERATURE`** — at `0.0` the model gives you the same words every time.
  It ships at `0.9`.

---

## About rate limits

**This is the heaviest pair in the course for call volume.** Two of your three
tools call the model, so one agent run is several requests, and a few runs back
to back while debugging can cross the per-minute limit.

`generate.py` handles it:

- **It paces itself** and says when it's waiting. **A pause is the starter
  doing its job, not a bug.**
- **It reuses answers** to prompts already sent, while you build.
- **It stops** if a session makes an unreasonable number of calls, rather than
  draining your day's allowance. For an agent, that usually means a loop isn't
  ending — look for that before raising the number.
- **It counts your calls** and prints the total when you exit.

`config.MAX_ITERATIONS` is the loop's own stop condition. Your loop this unit
is short enough that you may never hit it. Keep it — a missing stop condition
is the most common architectural failure in production agents.

---

## When something goes wrong

| What you see | What it means |
|---|---|
| `The planning loop isn't built yet` | Correct, at the start. That's the TODO in `agent.py` |
| `No GEMINI_API_KEY found` | No `.env`, or the key wasn't pasted in. On Windows check it didn't save as `.env.txt` |
| A message saying the model couldn't be reached | Usually a bad key. This is also **exactly what unit 4 Milestone 2 asks you to trigger on purpose** |
| `[rate limit] ... Waiting 34s` | Working as intended. Leave it |
| `[serve] another request is still running` | Also working as intended. `serve.py` answers one request at a time; yours is queued behind one that's mid-run |
| `QuotaGuard: This session has made 300 requests` | A loop isn't ending. Find it before raising the budget |
| `The loop ran 11 times, past MAX_ITERATIONS` | Same thing, caught earlier |
| `The server doesn't offer a tool called '...'` | Nothing registered in `mcp_server.py` yet, or the name doesn't match |
| MCP returns a string where you expected a list | You're not going through `mcp_client.call_tool`, which unwraps it |
| Fit cards identical every run | `CACHE_ENABLED` or `TEMPERATURE`. See above |
| `--trace` prints nothing | You haven't added `trace.step()` calls yet — unit 4, Milestone 2 |
| `IncompleteFieldDefinitionWarning: Field 'lifespan'` | Harmless noise from the MCP library's dependencies. Not your code, not an error. Ignore it |
| A price ceiling you typed is being ignored | You used double quotes in PowerShell. `$30` vanished. Use single quotes |
| `UnicodeEncodeError: 'charmap' codec can't encode` | Shouldn't happen — `config.py` sets the console to UTF-8. If you see it, you're running a file that doesn't import `config` |

Still stuck after one honest attempt? Post in the help channel with the full
error, what you ran, and what you expected.

---

## Extension: category-aware search (Path B — local, with logs)

`search_listings` has a second retrieval strategy. `keyword` is the original
scoring and is still the default. `category` ranks listings of the garment type
the query names first ("corduroy jacket" puts jackets ahead of corduroy pants)
and lets a broad word like "pants" reach jeans and trousers.

**The one command that proves it works** (run it from the repo root):

```bash
python eval_retrieval.py
```

It needs **Python 3.10 or newer and nothing else**: standard library only, no
`pip install`, no `.env`, no API key, no network, no model files (nothing to
download; the data is `data/listings.json`, 19 KB). It ranks 35 hand-labeled
queries with both strategies, prints the tables, and writes a run record to
`results/retrieval_<date>_<time>.jsonl` (one JSON object per line: environment,
every query's ranked ids and scores, per-query metrics, timings, a summary) and
a `.md` copy of the tables. It takes about two seconds.

The full agent (outfit + fit card) needs the course environment from the top of
this file: Python 3.11–3.13, the packages pinned in `requirements.txt`
(`google-genai`, `mcp>=1,<2`, `python-dotenv`, `flask`, `gunicorn`), and a
`GEMINI_API_KEY` in `.env`. With that:

```bash
python app.py ask 'corduroy jacket' --strategy category --trace
```

| Command | What it does |
|---|---|
| `python eval_retrieval.py` | Compare both strategies on all labeled queries; write the run record |
| `python eval_retrieval.py --label after` | Same, with a name in the file name |
| `python eval_retrieval.py --check-baseline` | Check that `keyword` still returns exactly what it did before the change (42 saved cases). Exit code 1 if not |
| `python eval_retrieval.py --query 'pants' [--size M] [--max-price 40]` | One query, both strategies side by side, with scores |
| `python eval_retrieval.py --no-log` | Print the tables without writing files |
| `python app.py ask '...' --strategy category` | Run the whole agent with the new strategy (`keyword` is the default) |

---

## A note on committing

At least four new commits in unit 3, at least four more in unit 4. Your commit
history is what shows your criteria existed before your results did.

**Do not delete and recreate this repository.** You submit the same URL both
units.

`results/` is deliberately **not** in `.gitignore`.
