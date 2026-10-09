# Common Ground

A group movie-planning tool and MCP server. Each person gets an independent
Qloo recommendation query; the planner chooses the strongest shared evidence
for the person who would otherwise be least represented, with hard vetoes.

## Current Status

Development started on 8 Oct 2026 for the Qloo Agentic Hackathon. Registration
is confirmed and the approved key arrived on 9 Oct. **Real search, shared movie
planning, veto/replan and both MCP tools have now passed live validation.**
External hosting and final submission are not complete. Preview mode still uses
entirely fictional films, IDs, rankings and generated artwork; Qloo Live never
substitutes that preview. No paid LLM API, trade, wallet or subscription is needed.

## Run

Requires Python 3.11+, uv and Node 22+.

```bash
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
uv run uvicorn common_ground.api:app --host 127.0.0.1 --port 8841
```

Open http://127.0.0.1:8841. Preview and Qloo Live are distinct modes. Live mode
fails clearly when no key is configured and never silently substitutes fixtures.
Set `QLOO_API_KEY` in the server's environment once access is approved. Do not
paste it into the UI, URL or git. The server only calls
`https://hackathon.api.qloo.com` with the documented `X-Api-Key` header.

## Agent Interface

```bash
uv run python -m common_ground.mcp_server
```

The official MCP Python SDK exposes two tools over stdio:

- `search_cultural_anchors`: live `/search` lookup, returning identity choices.
- `plan_movie_night`: 2-6 people with confirmed Qloo anchors, hard veto IDs and
  an explicit full-evidence requirement. Calls `/v2/insights` for each person,
  broadening retrieval by one page if shared evidence is absent.

The same planner backs the browser and HTTP API at `/docs`. No paid LLM client
is embedded. An MCP host can provide the conversational agent independently;
this is an agentic tool, not a standalone LLM chatbot. Search includes entity
type and film year where Qloo supplies them, so the host or person can distinguish
identically named films, artists and albums before planning.

Opt-in verification launches a separate real MCP server process over stdio:

```bash
uv run python scripts/check-live-mcp.py
```

Set `QLOO_API_KEY` privately first, or pass `--key-file /absolute/private/config.json`
with an `apiKey` field. The check resolves two explicitly identified films for
fictional participants, calls the planning tool and vetoes the first result.
It prints only validation counts, not Qloo datasets or credentials. It is a
real protocol/client check, not evidence of an external conversational host UI.

## Ranking and Honesty

Use `61/(60+rank)` per person's returned list, zero for an unreturned candidate.
Rank by the weakest score, then coverage, then mean score, with deterministic
ID tie-breaking. Also return the average-first alternative for comparison.
These are **rank scores, not enjoyment probabilities**. Missing evidence is not
dislike. The tool does not verify availability, content suitability or runtime.

All anchor IDs and explicit vetoes are excluded locally even if the upstream
filter is ignored. Any participant's API failure fails the entire plan rather
than dropping that person. Full-evidence mode never invents a shared option.
The downloadable evidence packet includes source, timestamp, per-person ranks,
query pages and exclusions. Preview records remain explicitly synthetic.

## Tests

```bash
uv run ruff check .
uv run pytest -q
npm --prefix frontend run check-design
npm --prefix frontend run build
```

Tests cover fair-vs-average ranking, vetoes, absent evidence, per-person failures,
bounded broadening, group validation, exact documented API requests, schema
failures, secret-safe errors, no redirect/paid fallback, missing-key behavior,
the HTTP workflow and official-SDK MCP discovery. Protocol fixtures are fictional.
The dated local browser verification and remaining gates are in `QA.md`.

## Security and Deployment Gate

Keys stay server-side. Responses are not persisted or logged by this app;
do not add real Qloo datasets or evidence exports to a public repository.
The API applies a small process-local request cap, an actual streamed-body size
limit, host validation and security headers, and disables response caching.
Actual Qloo calls are additionally capped at 60 per minute and 500 per hour
per process, including failed calls. These limits are local controls, not the
sponsor's published quota or a distributed defense; they reset on restart.
Keep a single worker for the free demo. Custom hosts must be explicitly set in
`ALLOWED_HOSTS`; Render's exact supplied hostname is accepted automatically,
without allowing arbitrary `*.onrender.com` origins.

`render.yaml` and the two `scripts/render-*.sh` files prepare a free single-worker
deployment with locked dependencies and no HTTP access logs. Store the key only
in the host's private server environment. Do not add a payment method, select
a paid plan or enable paid overages. Render's free service can sleep while idle;
its cold start and actual hosted behavior still need testing before submission.

Before a final competition entry: finish authorized zero-cost hosting, run
end-to-end desktop/mobile QA on its public URL and verify the entry form.
Keep the app operational through the official judging period, ending
16 November 2026. Registration alone does not satisfy these requirements.

The hackathon key is restricted to hackathon purposes, not paid services. Qloo
data is not licensed by this repository's MIT license. Preview artwork was made
with native ImageGen; prompt and visual decisions are in `DESIGN.md`.

## Primary References

- [Official competition](https://qloo.devpost.com/)
- [Official rules](https://qloo.devpost.com/rules)
- [Hackathon API guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide)
- [Entity search contract](https://docs.qloo.com/reference/get-search)
- [Insights contract](https://docs.qloo.com/reference/insights-api-deep-dive)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
