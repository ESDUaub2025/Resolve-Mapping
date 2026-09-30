# Development guide

## Layout

```
dictionary/   field dictionary, controlled vocabularies, survey instruments, dataset cards (YAML)
ref/          gazetteer: village spellings -> official cadastral units, settlement points
resolve/      Python pipeline: adapters -> analysis -> validation -> disclosure control -> releases
public/       the static website (MapLibre, no build step) and public/data (the public release)
tests/        privacy, release, dictionary, analysis and frontend tests; tests/e2e browser test
docs/         architecture, data dictionary, metrics, decisions
```

Survey data is never stored in this repository. The pipeline reads it from a separate private
data store whose location is given by the `RESOLVE_PRIVATE_DATA` environment variable.

## Commands

```bash
pip install -r requirements.txt -r requirements-dev.txt

python -m resolve build                  # full pipeline: public release + local research release
python -m resolve serve --tier public    # preview the public site on http://127.0.0.1:8000
python -m resolve serve --tier research  # local-only research view (needs the private store)
python -m resolve site                   # regenerate the root index.html from public/index.html
python -m resolve docs                   # regenerate docs/data-dictionary.md
python -m resolve metrics                # quality metrics for docs/metrics.md
python -m resolve gazetteer              # rebuild ref/localities.csv after editing aliases
python -m resolve settlements            # refresh village points from OpenStreetMap (network)
python -m resolve raw-manifest           # record hashes after adding a raw data version
python -m pytest                         # all checks - run before every push
node tests/e2e/smoke.mjs                 # browser end-to-end test (Chrome)
```

Builds are deterministic: the same inputs give byte-identical files in `public/data`.

## Adding data

- **New survey wave:** describe it in `dictionary/instruments.yaml`, map its columns in the
  `sources` of each field in `dictionary/fields.yaml`, add new village spellings to
  `ref/locality_aliases.csv`, then run `gazetteer`, `settlements` and `build`.
- **New answer option:** add a code with English/Arabic labels and match patterns to
  `dictionary/vocabularies.yaml`.
- **New reference layer:** add an adapter in `resolve/reference.py`, a dataset card in
  `dictionary/datasets.yaml` and a layer entry in `resolve/publish.py`; the map renders it with a
  generic renderer (`polygons`, `points`, `pins`, `survey_summary`) without code changes.

## Deployment

GitHub Pages deploys the `main` branch (repository root); `index.html` at the root is generated
from `public/index.html`. Every tracked file is public, so the privacy tests cover the whole
repository. Branch deployment publishes even if tests fail - run `python -m pytest` before pushing.
