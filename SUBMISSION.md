# Common Ground: Submission Draft

Not a final entry. The functional public demo URL and deployed QA must be added
before submission; do not submit a localhost URL or call hosting complete.

## Tagline

An evidence-first agent tool for a movie night that considers everyone.

## Inspiration

Group recommendations often hide a simple tradeoff: an excellent average can
still leave one person poorly represented. Common Ground makes that tradeoff
visible rather than treating the loudest preference as the entire group.
Its initial audience is small groups choosing a film together, and agents
helping those groups make a decision they can inspect and revise.

## What It Does

Each person confirms one to three cultural anchors from live Qloo search.
The tool queries Qloo independently for each person, then ranks shared movie
candidates by the weakest per-person reciprocal rank, coverage and average.
It shows the actual returned rank for each participant and lets any film be
vetoed before a new query. A bounded second page broadens retrieval when needed;
missing shared evidence produces an honest no-match result, not a fictional pick.

The browser app and official-SDK MCP server share the same planner. Agents can
resolve anchors and plan or replan through two structured tools. The app uses
no embedded paid LLM: it functions as an agentic tool that a conversational MCP
host can use, not as a claimed standalone conversational model.

## How It Is Built

Python, FastAPI, the official MCP Python SDK, React and Vite. Live requests use
Qloo's hackathon `/search` and `/v2/insights` endpoints. Keys remain server-side;
HTTP errors are sanitized and failed queries never fall back to preview data.
Entity type/year distinguish identity choices. Hard vetoes and selected anchors
are excluded locally as well as in the upstream query.

The query evidence records source, timestamp, pages, per-person ranks and
exclusions. `61/(60+rank)` is a transparent rank score, not an enjoyment
probability. An unreturned movie is missing evidence, not proof of dislike.
Streaming availability, runtime and suitability are not independently verified.

## Verified Work

Real Qloo search, full-evidence two-person planning and veto/replan have passed.
A divergent three-person scenario correctly reported no common evidence.
A separate stdio MCP process passed both live tools and veto exclusion.
59 automated tests pass, with local production-build desktop/mobile visual and
functional QA. Synthetic preview films/artwork are distinctly labelled and
never used as proof of real Qloo behavior. Public source is MIT-licensed;
the license does not relicense Qloo data or third-party film posters.

Development and QA used AI assistance. No users, commercial revenue, measured
preference outcomes or prize wins are claimed. A conversational-host UI demo
has not yet been verified.

## Limitations and Next Steps

Recommendations depend on bounded retrieval, so no match does not imply an
entire catalog lacks a possible compromise. Future evaluation should measure
whether groups prefer the weakest-first choice to an average-first choice;
no such benefit is claimed without real user testing.

Before final entry: publish the free app, test the public URL and cold start,
check the final form and preserve access through 16 November judging.
