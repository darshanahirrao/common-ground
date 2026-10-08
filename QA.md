# Verification: 8 October 2026

## Completed Locally

- `uv run pytest -q`: 43 passed, including HTTP and official MCP SDK discovery.
- `uv run ruff check .`: passed.
- `npm run check-design`: light/dark token completeness and contrast passed.
- `npm run build`: production build passed; npm reported zero vulnerabilities
  at install time. This is not a guarantee against future advisories.
- Native Codex in-app browser tested the production build at
  `http://127.0.0.1:8841/`.
- Initial three-person fictional preview chose Night Ferry. Vetoing it chose
  Moon Atlas. Restoring the veto cleared the old result; recomputing chose
  Night Ferry again.
- Search found Paper Streets and selecting it added an anchor to Asha.
- Add-person stopped at six; remove-person stopped at two. Missing anchors
  disabled planning rather than silently dropping a person.
- Switching to Qloo Live removed synthetic anchors. Search with no key showed
  the key-pending error and did not substitute fictional results.
- Query-evidence disclosure showed per-person pages, timestamp and rank-score
  caveats. Download produced a readable JSON file marked `source: synthetic`.
- Visually inspected desktop light/dark and mobile dark at 390px, light at
  320px. Narrow layouts had no horizontal overflow or overlapping controls.
  Generated posters rendered. Browser console had no captured warnings/errors.

Screenshots are kept outside this public repository under
`../evidence/2026-10-08/common-ground-*.jpg`. No real Qloo responses are published.

## Not Yet Completed

- No approved Qloo key, real API request or real-entity/image validation.
- No conversational run in an external MCP agent host.
- No public hosted application or deployed abuse-control verification.
- No final competition project entry; registration and API request are complete.
- Keyboard/screen-reader accessibility audit is not complete.
- No paid work, prize, awarded amount or income demonstrated by this prototype.

Before submission, complete these gates, rerun tests and browser QA on the public
URL, and keep the app available through the official judging period.
