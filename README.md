# RESOLVE Map

Interactive map of farmer-survey results, satellite fire detections and protected areas for
Mount Lebanon (Chouf) and the Beqaa, Lebanon. Public site: <https://esduaub2025.github.io/Resolve-Mapping/>

## How it is organised

```
dictionary/   field dictionary, controlled vocabularies, survey instruments, dataset cards (YAML)
ref/          locality gazetteer: survey village spellings -> official cadastral units (OCHA COD-AB)
resolve/      Python pipeline: adapters -> validation -> disclosure control -> releases
public/       the static website (MapLibre, no build step) + public/data (the public release)
tests/        privacy invariants, public-release checks, dictionary and pipeline unit tests
research/     withdrawn ML experiments (not published, not maintained)
docs/         architecture, data dictionary, metrics, decisions
```

Survey data never lives in this repository. Raw files, the respondent ID registry, the
standardized records and the research release are kept in a separate **private data store**
(by default `../RESOLVE-data-private`, or set `RESOLVE_PRIVATE_DATA`).

## Privacy model

Respondents consented to **research use only**. Therefore:

| Tier | What | Where |
|---|---|---|
| Identity | names, phone numbers | private store only (`staging/survey_identity.json`) |
| Research | standardized individual records with ID, name and phone, all villages, free text, GPS farm points | private store; viewed locally with `python -m resolve serve --tier research` |
| Public | summaries of at least **k = 5** respondents per village (cadastral unit) or district; sensitive indicators (income, age, gender, costs) at district level only; one pin per respondent carrying only the random ID and farming-practice answers, placed at the village they reported (or where they said their land is), never at the farm; analysis insights; fire and protected-area layers | `public/data`, deployed to GitHub Pages |

Every respondent has a random, stable **ID** (e.g. `CH-0EXAMP`, `BQ-0EXAMP`) that replaces the
name everywhere outside the identity table. Names, phone numbers, farm locations, free text and
sensitive answers never reach the public site; `tests/` fail the build if they do.

## Common tasks

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt

python -m resolve build                 # adapters -> validation -> public + research releases
python -m resolve serve --tier public    # http://127.0.0.1:8000  (what Pages serves)
python -m resolve serve --tier research # local research view with identities (127.0.0.1 only)
python -m pytest                        # all checks (run before committing public/data)
python -m resolve metrics               # measures for docs/metrics.md
python -m resolve docs                  # regenerate docs/data-dictionary.md
python -m resolve gazetteer             # regenerate ref/localities.csv after editing aliases
python -m resolve raw-manifest          # record hashes after adding a raw file version
```

A build is deterministic: rebuilding from the same private store gives byte-identical
`public/data`. Review items (unmapped answers, conflicting duplicates, unresolved villages)
are written to `<private store>/staging/review_issues.json`; critical problems stop the build.

## Adding data

- **A new survey wave**: add the raw file under `<private store>/raw/<source>/<version>/`,
  describe it in `dictionary/instruments.yaml`, add its columns to the `sources` of each field in
  `dictionary/fields.yaml`, add any new village spellings to `ref/locality_aliases.csv`, run
  `python -m resolve gazetteer` and `python -m resolve build`. No frontend change is needed.
- **A new answer option**: add a code with `en`/`ar` labels and `match` patterns to
  `dictionary/vocabularies.yaml`.
- **A new reference layer**: add an adapter in `resolve/reference.py`, a dataset card in
  `dictionary/datasets.yaml` and a layer entry in `resolve/publish.py`; the map renders it from
  `catalog.json` using one of the generic renderers (`polygons`, `points`, `survey_summary`).

## Deployment

GitHub Pages deploys from the `main` branch (repository root). The root `index.html` redirects
to the map in `public/`. Every tracked file is therefore publicly served, which is why the privacy
tests check the whole repository and survey data lives only in the private store.

GitHub Actions (`.github/workflows/pages.yml`) runs all tests on every push and pull request. Its
deploy job, which would publish only `public/`, is optional: it runs only if Pages is switched to
"GitHub Actions" and the repository variable `PAGES_FROM_ACTIONS` is `true`. Note that branch
deployment publishes a push even when the tests fail, so run `python -m pytest` before pushing.

## Data sources and licences

See the dataset cards in `dictionary/datasets.yaml` (shown in the map under ⓘ). Admin boundaries:
OCHA COD-AB Lebanon (CC BY-IGO). Protected areas: WDPA (UNEP-WCMC/IUCN) terms of use. Fire
detections: legacy file, probably NASA FIRMS (source to be re-confirmed). Basemaps: Esri, OpenStreetMap.
