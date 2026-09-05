# philaretz.github.io

Personal academic website for [Philipp Aretz](https://philaretz.github.io) — PhD student in theoretical high-energy physics at MIT. Built with Jekyll and deployed via GitHub Pages.

## What's here

- A bespoke design (`_sass/bespoke/`, `_layouts/bespoke*.html`, `_includes/bespoke/`) covering Home, Publications, Talks, CV, and Contact, with a light/dark/system theme toggle.
- A CV pipeline (`tools/`) that treats [Notion](https://notion.so) as the single source of truth for CV content: education, positions, publications, talks, awards, teaching, and service. A `Sections` database in Notion controls what appears where and how it's grouped. The pipeline:
  - syncs publications from INSPIRE-HEP into Notion (`tools/sync_inspire.py`),
  - renders Notion into `data/cv.json` (`tools/build_cv.py`),
  - and turns that into the Jekyll collections (`_publications/`, `_talks/`, `_data/cv.json`) and two LaTeX documents — a full academic CV and a one-page résumé — via Jinja2 templates under `templates/`.
- `.github/workflows/pages-build.yml` deploys the site on every push to `main`; `.github/workflows/cv-update.yml` runs the pipeline weekly and opens a PR with anything new from Notion.

See `Makefile` for the pipeline's entry points (`make sync`, `make cv-json`, `make site`, `make pdf`, `make check`, or `make all`).

## Running locally

```bash
bundle install
bundle exec jekyll serve -l -H localhost
```

The site will be available at `http://localhost:4000`. The CV pipeline itself needs Python 3.12+, a `NOTION_TOKEN` (for `make sync`/`make cv-json`), and a TeX distribution with `xelatex` (for `make pdf`).

## Credits

This site started from [Academic Pages](https://github.com/academicpages/academicpages.github.io), itself forked from the [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/) Jekyll theme, © 2016 Michael Rose, MIT licensed (see `LICENSE`). Very little of the original theme's chrome remains — the visual design, CV pipeline, and content are custom.
