# RESOLVE Map – Interactive Agriculture, Water and Wildfire Map of Lebanon

**🌍 Open the map: <https://esduaub2025.github.io/Resolve-Mapping/>**

RESOLVE Map is a free, bilingual (English / العربية) interactive web map of farming practices in
**Mount Lebanon (Chouf and Aley)** and the **Beqaa valley (Zahle, West Beqaa, Baalbek)**. It brings
together a survey of more than 200 farmers with satellite **fire detections** and Lebanon's
**protected areas and nature reserves**, so that researchers, municipalities, cooperatives, NGOs and
farmers can see how water, energy, soil, pest control, crops and climate change play out village by
village.

> خريطة RESOLVE: خريطة تفاعلية مجانية باللغتين العربية والإنكليزية للممارسات الزراعية في الشوف وجبل
> لبنان والبقاع. تجمع نتائج استبيان لأكثر من 200 مزارع حول المياه والطاقة والتربة والمبيدات والمحاصيل
> والتغير المناخي، مع رصد الحرائق بالأقمار الصناعية والمحميات الطبيعية في لبنان.

## Why this map exists

Farmers in Lebanon face water scarcity, rising input costs and a changing climate, but information
about how they actually farm is scattered and rarely mapped. RESOLVE turns survey answers into
readable, comparable maps and evidence:

- Where is water most often **insufficient** during the growing season, and what goes with it?
- Where do farmers depend fully on **chemical fertilizers and pesticides**, and where are
  **low-input practices** (compost, manure, biological pest control) already used?
- Which **crops, energy sources and irrigation sources** dominate each village?
- How close are farming villages to **protected areas** and to recent **fire activity**?

## Features

- **Farmer pins** – one pin per survey respondent, placed at the village they reported (or where
  they said their land is). Pins show farming-practice answers only and are identified by a random
  ID. Grouped pins are drawn as small **donut charts** showing the mix of answers inside the group.
- **Village and district summaries** – colour-coded areas with the full distribution of answers for
  every question, the number of respondents, and what was not asked or not answered.
- **Farmer types** – four farmer profiles found by statistical clustering of farming practices
  (e.g. intensive well-and-diesel irrigation with heavy chemical use, or low-input vegetable plots).
- **Insights panel** – validated findings on **water stress** and **chemical dependence**, each with
  percentages, odds ratios, confidence intervals and plain-language caveats.
- **Filters and search** – filter pins by farmer type, water availability, water source, energy
  source, crops, fertilizer and pesticide use, land size, production level and cooperative
  membership; search pins by ID; live counts of what is shown.
- **Fire detections** – satellite thermal-anomaly detections (2024–2025) as clustered points or a
  density heatmap, with date and day/night filters.
- **Protected areas** – nature reserves, biosphere reserves and Ramsar wetlands with clear borders and names.
- **Bilingual and accessible** – full Arabic (right-to-left) and English interface, keyboard-accessible
  lists of every area and pin, colour-blind-safe palettes, and a mobile-friendly layout.
- **Transparent** – every layer has an ⓘ card with its source, licence, method and caveats.

## Privacy by design

The survey was collected for research. The public map never shows names, phone numbers, farm
locations, free-text answers or sensitive answers (income, age, gender, costs). Pins are placed at
the village level, not at farms; sensitive topics appear only as district-level summaries; and
automated tests check every release before publication.

## How it works

1. **Standardisation** – survey answers from two questionnaires (Chouf 2025–26 and Beqaa 2026) are
   mapped to one bilingual data dictionary with controlled answer codes, and every missing answer is
   labelled as *not provided*, *not asked* or *not applicable*.
2. **Geography** – reported village names (in Arabic and English, with many spellings) are matched to
   Lebanon's official cadastral areas (OCHA COD-AB) and to village locations from OpenStreetMap.
3. **Privacy and quality checks** – validation rules, disclosure control for summaries and automated
   tests run on every build; the public release is reproducible byte for byte.
4. **Analysis** – farmer typology (k-means with bootstrap stability testing) and region-adjusted
   association analysis (Mantel–Haenszel odds ratios with false-discovery control, validated with
   village-grouped cross-validation). Only results that pass these checks are published.
5. **Web map** – a lightweight static site built with [MapLibre GL JS](https://maplibre.org/); it
   reads a single catalogue file describing every layer, field, legend and filter.

## Data sources

| Layer | Source | Licence |
|---|---|---|
| Farmer survey | RESOLVE project surveys, Chouf / Mount Lebanon and Beqaa | Research use; published only as described above |
| Administrative and cadastral boundaries | [OCHA COD-AB Lebanon](https://data.humdata.org/dataset/cod-ab-lbn) (HDX) | CC BY-IGO |
| Village locations | [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors | ODbL |
| Fire detections | NASA FIRMS (VIIRS) active-fire data | Free to use with attribution |
| Protected areas | [Protected Planet / WDPA](https://www.protectedplanet.net/) (UNEP-WCMC & IUCN) | WDPA terms of use |
| Basemaps | Esri, OpenStreetMap | Provider terms |

## Project

RESOLVE is developed by the RESOLVE project team (ESDU, American University of Beirut) to support
evidence-based work on water, energy and food in Lebanese agriculture. For questions, data requests
or collaboration, please open an issue in this repository.

### For developers

The site is plain HTML, CSS and JavaScript (no build step) in `public/`; the data pipeline is a
Python package in `resolve/` driven by the data dictionary in `dictionary/`. Survey data is not
stored in this repository. Run the automated checks with:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Technical documentation: [development guide](docs/development.md) · [architecture](docs/architecture.md) ·
[data dictionary](docs/data-dictionary.md) · [design decisions](docs/decisions.md) ·
[quality metrics](docs/metrics.md).

**Keywords:** Lebanon agriculture map, Chouf farmers, Beqaa valley farming, Mount Lebanon, water
scarcity Lebanon, irrigation, agricultural survey, regenerative agriculture, pesticides and
fertilizers, climate change impacts, wildfire map Lebanon, NASA FIRMS, protected areas Lebanon,
nature reserves, Shouf Biosphere Reserve, interactive GIS map, MapLibre, خريطة زراعية لبنان،
مزارعو الشوف، البقاع، شح المياه، المحميات الطبيعية، حرائق لبنان
