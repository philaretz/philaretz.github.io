# philaretz.github.io — dark mode

Status: implemented, live. Companion to the original design handoff
(`theme.css` → `_sass/bespoke/*.scss`) — read that first for the base
system (fonts, layout, component shapes). This file covers only what's
different for dark mode: the palette, and the toggle.

## Palette

Same warm, low-chroma neutral hue (oklch hue 150) as light mode, values
inverted, plus the accent lightened to keep contrast on a dark ground.
Defined in `_sass/bespoke/_tokens.scss`.

|              | Light                        | Dark                          |
|--------------|-------------------------------|--------------------------------|
| `--bg`       | `oklch(97.3% 0.008 150)`      | `oklch(19% 0.010 150)`         |
| `--text`     | `oklch(23% 0.014 150)`        | `oklch(93% 0.006 150)`         |
| `--text-muted` | `oklch(48% 0.012 150)`      | `oklch(65% 0.014 150)`         |
| `--border`   | `oklch(89% 0.01 150)`         | `oklch(30% 0.014 150)`         |
| `--accent`   | `#4a7c64`                     | `oklch(70% 0.10 150)`          |

The accent is deliberately *not* the same literal color in both modes —
`#4a7c64` at light-mode lightness reads too dark/muddy against a near-black
background, so the dark variant is the same hue/chroma lifted to ~70%
lightness (a lighter sage/mint). Everything else in both palettes is
oklch so lightness/chroma stay comparable and swapping either palette's
values is a self-contained edit.

Every component is built entirely from these five custom properties (no
component-level hardcoded colors), so nothing beyond `_tokens.scss` needed
to change for dark mode to work correctly across the whole site — this
was true by construction, not something retrofitted.

## How a page ends up dark

Three ways in, all defined in `_tokens.scss`:

1. **OS preference, no explicit choice** — `@media (prefers-color-scheme:
   dark)` targeting `:root:not([data-theme="light"])`.
2. **Explicit "Dark"** — `:root[data-theme="dark"]`, set regardless of OS
   preference.
3. **Explicit "Light"** — the `:not([data-theme="light"])` guard on the
   media-query rule means an explicit light choice always wins over a
   dark OS preference.

"System" is the *absence* of `data-theme` — choosing it removes the
attribute and clears the stored preference, handing control back to
`prefers-color-scheme`.

## The toggle

Three-button segmented control in the header
(`_includes/bespoke/theme-toggle.html`, styled in `_chrome.scss` as
`.theme-toggle`), inline SVG icons (sun / moon / monitor — no emoji, no
icon font dependency). Behavior lives in `assets/js/theme-toggle.js`:

- Click a button → `localStorage.theme` is set to `light`/`dark`, or
  removed for `system` → `data-theme` is set/removed on `<html>` to match
  → the `.active` class moves to the clicked button.
- On every page load, a small **blocking, non-deferred** script at the
  top of `<head>` (`_layouts/bespoke.html`) reads `localStorage.theme`
  and sets `data-theme` before the stylesheet paints — this is what
  prevents a flash of the wrong theme on navigation. The full toggle
  script (`assets/js/theme-toggle.js`) is `defer`red and only needed for
  interactivity and keeping the three buttons' active-state in sync; it
  isn't on the critical rendering path.
- The choice is per-browser (`localStorage`), not per-page — it persists
  across navigation automatically since every page reads the same key.

## Known gaps

- **Favicon / `theme-color` meta**: still a single light-mode value
  (`_includes/head/custom.html`); doesn't adapt to dark mode. Low
  priority — affects only the browser chrome (tab icon, address bar
  tint), not the page itself.
- **OG/social preview image**: still unset (`_config.yml`'s `og_image`),
  same pre-existing gap noted in the original design handoff — whichever
  image eventually fills it should probably work on both light and dark
  share-card backgrounds, or just pick one palette deliberately.
- **Print stylesheet**: `_sass/bespoke/_cv.scss`'s `@media print` block
  drops backgrounds already (print is print, regardless of which theme
  was active on screen) — no dark-specific work needed there.
