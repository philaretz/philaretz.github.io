# CV pipeline. Every trigger — the weekly scheduled task, the Run workflow
# button, "update my CV" in chat — runs `make all`. That is what makes them
# impossible to disagree.
#
#   make all       sync, rebuild, render, compile, check
#   make preview   render + compile offline from the fixture (no network)
#   make check     guardrails only
#
# ENGINE: xelatex by default because it works everywhere fontspec does.
# lualatex is equally fine if your TeX has luaotfload (MacTeX does).

ENGINE ?= xelatex
PY     ?= python3
LATEX   = latexmk -$(ENGINE) -interaction=nonstopmode -halt-on-error -cd

.PHONY: all sync cv-json site pdf preview check clean

all: sync cv-json site pdf check

sync:
	$(PY) tools/sync_inspire.py

cv-json:
	$(PY) tools/build_cv.py

site:
	$(PY) tools/render.py --target web

pdf:
	$(PY) tools/render.py --target cv resume
	$(LATEX) build/cv.tex
	$(LATEX) build/resume.tex
	@mkdir -p files
	cp build/cv.pdf files/cv.pdf
	cp build/resume.pdf files/resume.pdf

# Offline loop for template work: no Notion, no INSPIRE, no network.
preview:
	$(PY) tools/render.py --all --from fixtures/cv.sample.json
	$(LATEX) build/cv.tex
	$(LATEX) build/resume.tex

check:
	$(PY) tools/check.py

clean:
	rm -rf build
