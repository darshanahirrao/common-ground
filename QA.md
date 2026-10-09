# Verification

## 9 October 2026: Real Integration

- Official hackathon key received and kept privately outside source control.
- Live `/search` returns a results list without a top-level `success` flag.
  Corrected that assumption while still rejecting explicit failure flags,
  invalid identities and invalid endpoint schemas. Added regression tests.
- Live entity types and film release years validated and shown in search/anchors.
- Two-person live planning returned eight full-evidence shared candidates.
  Veto/replan returned a different pick, preserving both people and exclusions.
- A deliberately divergent three-person scenario returned `no_common_ground`
  after six bounded queries. No common film or satisfaction score was invented.
- Separate MCP process over real stdio: discovery, two search-tool calls and
  two planning-tool calls passed against live Qloo; veto excluded the old pick.
  Reproducible opt-in check: `scripts/check-live-mcp.py`. This is protocol-client
  verification, not a claimed external conversational-host session.
- `uv run pytest -q`: 59 passed. Lint, design contrast and frontend build pass.
- Native browser tested the real production build at
  `http://127.0.0.1:8842/`: search/identity selection, full-evidence planning,
  actual posters, veto/replan and real JSON export passed.
- Export is marked `source: qloo`, preserves all people/exclusions and includes
  no credential field. Raw exports stay outside public source control.
- Visually inspected live results at 1280px desktop dark, 390px mobile dark
  and 320px mobile light. All eight posters loaded, no horizontal overflow,
  readable wrapped titles/rank tables and no captured console warnings/errors.
  The temporary viewport override was reset after QA.
- Actual-call minute/hour budget, its expiry and rejection before network access
  are tested. Exact hosted hostname and rejection of wildcard exposure are tested.
- Free Render blueprint/build/start scripts prepared. Hosting account terms and
  private key storage permission are awaiting Darshan's action-time confirmation;
  no account, paid service or hosted app was created by these file changes.

Live screenshots are outside this public repository under
`../evidence/2026-10-09/common-ground-live-*.jpg`.

## 8 October 2026: Preview

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

- No conversational run in an external MCP agent host.
- No public hosted application or deployed abuse-control verification.
- No final competition project entry; registration and API request are complete.
- Keyboard/screen-reader accessibility audit is not complete.
- No paid work, prize, awarded amount or income demonstrated by this prototype.

Before submission, complete these gates, rerun tests and browser QA on the public
URL, and keep the app available through the official judging period.
