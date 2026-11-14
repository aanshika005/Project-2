# Criterion 3 results: bad inputs to the new strategy (2026-11-14)

Judged against the committed wording of criterion 3 in `criteria.md` ("add capstone criteria"). Criterion not changed after seeing these results.
Method: `run_agent` called directly (`python app.py ask` for the `"  "` row), `FITFINDR_RUN_LOG=/tmp/crit3.jsonl`, Python 3.13.2, real MCP server.
Note: `python app.py ask ''` is not a test of `""`: the CLI treats an empty argument as "no query" and opens the interactive prompt. The `""` row below was run through `run_agent` directly.

| # | Input | Exception escaped? | Logged (outcome) | Message non-empty | Names both `keyword` and `category` | Pass |
|---|---|---|---|---|---|---|
| 1 | query `"  "`, strategy=category (CLI) | no | no_results | yes | n/a | yes |
| 2 | query `""`, strategy=category | no | no_results | yes | n/a | yes |
| 3 | strategy `"semantic"` | no | search_failed | yes | **no** | **no** |
| 4 | strategy `""` | no | search_failed | yes | **no** | **no** |
| 5 | strategy `"CATEGORY"` | no | search_failed | yes | **no** | **no** |

**Result: 2 of 5. Target (5 of 5) missed.**

What held: nothing crashed and every run left a record (5 of 5 on those two checks).
What failed: for all three bad strategy values the user sees the generic MCP message:

    Couldn't search the listings. Couldn't call 'search_listings' over MCP: unhandled errors in a TaskGroup (1 sub-exception)
    Check that mcp_server.py runs on its own first: ...

The text from `retrieval.rank` ("Unknown search strategy 'semantic'. Choose one of: keyword, category.") never reaches the user, and the advice given (check that the server runs) is wrong: the server was fine and the input was bad.

Observed messages for the empty queries:
- `""` and `"  "`: "No listings matched your search. Try different keywords." (both parse to an empty description, still go through the MCP search and return `[]`, ~500 ms.)

Also noted: the reason text of criterion 3 says empty queries "never reach scoring"; the trace shows they do reach the MCP `search_listings` call. The target is unaffected; the reason is inaccurate.

Not yet diagnosed: where the `ValueError` text is lost (server tool error -> MCP client TaskGroup wrapper -> generic `MCPError` handler in `agent.py` is the suspect, unconfirmed).
