# Common Ground Design

## Subject and Job

Subject: choosing a film for a group with different tastes. Audience: friends
and small movie clubs. Job: compare actual per-person recommendation evidence
and choose a compromise without hiding the person least represented.

Utilitarian treatment with cinematic artwork on repeated film items. Reading
order: the shared pick, each person's evidence, then alternate picks and vetoes.
The editable group remains alongside results on desktop and precedes them on
mobile. No landing page, decorative feature cards or nested cards.

## Tokens

- Cool paper `#f4f7f6`, panel white `#ffffff`, ink `#18242a`, muted ink
  `#536267`, cinema teal `#006f68`, warning rust `#a5481d`.
  Boundary grey `#738680` provides at least 3:1 control contrast.
- Compact Georgia wordmark; Avenir Next/system sans for the application;
  SFMono-Regular/system monospace for query and rank metadata.
- Fixed type scale: 12, 14, 16, 20, 28 pixels. No viewport-scaled type or tracking.
- Spacing: 4, 8, 12, 16, 24, 32 pixels. Inputs and buttons 44px minimum.
  Posters use a stable 1:2 aspect; radii at most 6px.
- Dark tokens: ground `#151d1e`, panel `#202a2b`, ink `#edf3f1`, muted
  `#bdcbc6`, accent `#7dd6c8`, warning `#f2b993`. Both explicit theme choices
  override the system preference.

## Content Skeleton

Compact identity/mode/theme header. Group names, selected cultural anchors and
anchor search in the left column. Result summary and source status on the right.
Repeated candidate rows contain a poster, name, per-person ranks and veto action.
Expandable query log and a downloadable evidence packet complete the workspace.

The preview's film names, IDs, rankings and illustrations are fictional. They
must never be presented as live Qloo responses or reused as live entity IDs.

## Artwork

`frontend/public/preview-films.png` is a single native ImageGen triptych,
generated 8 Oct 2026, used only on fictional-preview film items. Original prompt:

> A single cinematic triptych contact sheet for fictional film-poster artwork
> in an explicitly labelled synthetic movie-night preview. Three equal-width
> vertical panels, edge to edge: teal coastal ferry at dusk with two travellers;
> crimson Japanese railway platform and distant traveller; golden observatory
> in a pine forest. Original painterly-screenprinted festival-poster style,
> differentiated colours, clean silhouettes, readable at thumbnail size.
> No writing, titles, logos, watermarks, brands or real actors' likenesses.

Built-in ImageGen was used, not an API/CLI fallback. Live film items may show
their returned image or a labelled missing-artwork state; generated preview
artwork is never substituted for a real film's poster.

## Verification

Check light/dark and desktop/mobile, overflow, keyboard focus, theme and mode
switching, add/remove member, search/selection, veto/replan, JSON export,
empty/no-common-result and missing-key errors. Live claims require a real-key
smoke test after the requested key arrives.
