/**
 * RESOLVE Map — Single Source of Truth
 * ======================================
 * Every theme color, layer ID, file path, and i18n key is defined HERE.
 * All other files (app.js, loader.js, Python scripts) read from this.
 *
 * To add a new theme:   add an entry to THEMES
 * To add a static layer: add an entry to STATIC_LAYERS
 * To add an AI layer:    add an entry to AI_LAYERS
 * Then run:  python scripts/validate_data.py
 */
(function () {
    'use strict';

    const MANIFEST = {

        // ── Version & caching ───────────────────────────────────────
        DATA_VERSION: '2.5.0',
        CACHE_EXPIRY_DAYS: 7,
        DB_NAME: 'ResolveMapDB',
        DB_VERSION: 1,
        DB_STORE: 'geojsonCache',

        // ── Production data URL (null = local) ──────────────────────
        // Set to e.g. 'https://pub-xxx.r2.dev/my-project/' for CDN
        PRODUCTION_DATA_URL: null,

        // ── Map defaults ────────────────────────────────────────────
        MAP_CENTER: [35.55, 33.72],   // [lng, lat]
        MAP_ZOOM: 10,
        MAP_MAX_ZOOM: 18,

        // ── Canonical survey themes ─────────────────────────────────
        // Each theme becomes a clustered point layer on the map.
        THEMES: {
            water: {
                layerId: 'water-points',
                canonicalFiles: [
                    'data/geojson/canonical/Water.canonical.geojson',
                    'data/geojson/canonical/Water_new.canonical.geojson'
                ],
                csvSources: {
                    ar: 'data/layers/Arabic/Water_1.0.csv',
                    en: 'data/layers/English/Water_1.0.en.csv'
                },
                color: '#1abc9c',
                pixelOffset: [0, 0],
                i18n: { en: 'Water', ar: 'المياه' },
                icon: 'water'      // key into iconSvgs (defined in app.js)
            },
            energy: {
                layerId: 'energy-points',
                canonicalFiles: [
                    'data/geojson/canonical/Energy.canonical.geojson',
                    'data/geojson/canonical/Energy_new.canonical.geojson'
                ],
                csvSources: {
                    ar: 'data/layers/Arabic/Energy_1.0.csv',
                    en: 'data/layers/English/Energy_1.0.en.csv'
                },
                color: '#f39c12',
                pixelOffset: [12, 12],
                i18n: { en: 'Energy', ar: 'الطاقة' },
                icon: 'energy'
            },
            food: {
                layerId: 'food-points',
                canonicalFiles: [
                    'data/geojson/canonical/Food.canonical.geojson',
                    'data/geojson/canonical/Food_new.canonical.geojson'
                ],
                csvSources: {
                    ar: 'data/layers/Arabic/Food_1.0.csv',
                    en: 'data/layers/English/Food_1.0.en.csv'
                },
                color: '#9b59b6',
                pixelOffset: [-12, -12],
                i18n: { en: 'Food', ar: 'الغذاء' },
                icon: 'food'
            },
            general: {
                layerId: 'general-points',
                canonicalFiles: [
                    'data/geojson/canonical/General_Info.canonical.geojson',
                    'data/geojson/canonical/General_Info_new.canonical.geojson'
                ],
                csvSources: {
                    ar: 'data/layers/Arabic/Generalinfo_1.0.csv',
                    en: 'data/layers/English/Generalinfo_1.0.en.csv'
                },
                color: '#2980b9',
                pixelOffset: [12, -12],
                i18n: { en: 'General', ar: 'عام' },
                icon: 'general'
            },
            regen: {
                layerId: 'regen-points',
                canonicalFiles: [
                    'data/geojson/canonical/Regenerative_Agriculture.canonical.geojson',
                    'data/geojson/canonical/Regenerative_Agriculture_new.canonical.geojson'
                ],
                csvSources: {
                    ar: 'data/layers/Arabic/Regenerative_1.0.csv',
                    en: 'data/layers/English/Regenerative_1.0.en.csv'
                },
                color: '#27ae60',
                pixelOffset: [-12, 12],
                i18n: { en: 'Regenerative Ag', ar: 'الزراعة التجديدية' },
                icon: 'regen'
            }
        },

        // ── Static layers (non-canonical) ───────────────────────────
        STATIC_LAYERS: {
            fire: {
                layerId: 'fire-points',
                rawLayerId: 'fire-points-raw',   // non-clustered for heatmap
                file: 'data/geojson/fire.geojson',
                color: '#e74c3c',
                pixelOffset: [0, 14],
                i18n: { en: 'Fire points', ar: 'نقاط الحرائق' },
                icon: 'fire'
            },
            preservations: {
                layerId: 'preservations-poly',
                file: 'data/geojson/Preservations.geojson',
                color: '#2ecc71',
                type: 'polygon',
                i18n: { en: 'Preservations', ar: 'المحميات' },
                icon: 'preservations'
            },
            farmers: {
                layerId: 'farmers-points',
                file: 'data/geojson/Model_Predictions.geojson',
                color: '#16a085',
                pixelOffset: [14, 0],
                i18n: { en: 'Farmers Survey', ar: 'استبيان المزارعين' },
                icon: 'farmers'
            }
        },

        // ── AI prediction layers ────────────────────────────────────
        AI_LAYERS: {
            regen: {
                layerId: 'ai-regen',
                sourceId: 'ai-predictions',
                predictionProp: 'Pred_Regen_Adoption',
                type: 'binary',
                colorMap: { '0': '#e74c3c', '1': '#27ae60' },
                i18n: { en: 'Regenerative Adoption', ar: 'تبني الزراعة التجديدية' },
                icon: 'aiRegen'
            },
            water: {
                layerId: 'ai-water',
                sourceId: 'ai-predictions',
                predictionProp: 'Pred_Water_Risk',
                type: 'binary',
                colorMap: { '0': '#27ae60', '1': '#e74c3c' },
                i18n: { en: 'Water Risk', ar: 'مخاطر الأمن المائي' },
                icon: 'aiWater'
            },
            econ: {
                layerId: 'ai-econ',
                sourceId: 'ai-predictions',
                predictionProp: 'Pred_Production_Level',
                type: 'ternary',
                colorMap: { '0': '#e74c3c', '1': '#f39c12', '2': '#27ae60' },
                i18n: { en: 'Economic Resilience', ar: 'المرونة الاقتصادية' },
                icon: 'aiEcon'
            },
            climate: {
                layerId: 'ai-climate',
                sourceId: 'ai-predictions',
                predictionProp: 'Pred_Climate_Vuln',
                type: 'ternary',
                colorMap: { '0': '#3498db', '1': '#9b59b6', '2': '#1abc9c' },
                i18n: { en: 'Climate Vulnerability', ar: 'الضعف المناخي' },
                icon: 'aiClimate'
            },
            // ── Unsupervised analysis layers ────────────────────────
            clusters: {
                layerId: 'ai-clusters',
                sourceId: 'ai-predictions',
                predictionProp: 'farmer_cluster',
                type: 'categorical',
                colorMap: { '0': '#3498db', '1': '#e67e22', '2': '#2ecc71' },
                i18n: { en: 'Farmer Clusters', ar: 'مجموعات المزارعين' },
                icon: 'aiCluster'
            },
            waterIdx: {
                layerId: 'ai-idx-water',
                sourceId: 'ai-predictions',
                predictionProp: 'idx_water_vulnerability',
                type: 'gradient',
                colorStops: [[0, '#27ae60'], [50, '#f39c12'], [100, '#e74c3c']],
                i18n: { en: 'Water Vulnerability Index', ar: 'مؤشر هشاشة المياه' },
                icon: 'aiWaterIdx'
            },
            agriIdx: {
                layerId: 'ai-idx-agri',
                sourceId: 'ai-predictions',
                predictionProp: 'idx_agricultural_capacity',
                type: 'gradient',
                colorStops: [[0, '#e74c3c'], [50, '#f39c12'], [100, '#27ae60']],
                i18n: { en: 'Agricultural Capacity', ar: 'القدرة الزراعية' },
                icon: 'aiAgriIdx'
            },
            sustainIdx: {
                layerId: 'ai-idx-sustain',
                sourceId: 'ai-predictions',
                predictionProp: 'idx_sustainability_practices',
                type: 'gradient',
                colorStops: [[0, '#e74c3c'], [50, '#f39c12'], [100, '#27ae60']],
                i18n: { en: 'Sustainability Practices', ar: 'ممارسات الاستدامة' },
                icon: 'aiSustainIdx'
            }
        },

        // ── Heatmap layer (special) ─────────────────────────────────
        HEATMAP: {
            layerId: 'fire-heatmap',
            sourceLayerId: 'fire-points-raw',
            i18n: { en: 'Fire Heatmap', ar: 'كثافة الحرائق' },
            icon: 'fire'
        },

        // ── AI Source ───────────────────────────────────────────────
        AI_SOURCE: {
            id: 'ai-predictions',
            file: 'data/geojson/Model_Predictions.geojson',
            promoteId: 'source_row'
        },

        // Boundary layer (generated by ML pipeline)
        BOUNDARY: {
            file: 'data/geojson/Farmers_Boundary.geojson'
        }
    };

    // ── Helper: build lookup maps from manifest ─────────────────
    // layerId → themeKey  (e.g. 'water-points' → 'water')
    MANIFEST._layerToTheme = {};
    for (const [key, cfg] of Object.entries(MANIFEST.THEMES)) {
        MANIFEST._layerToTheme[cfg.layerId] = key;
    }

    // themeKey → color  (includes static + ai)
    MANIFEST._colors = {};
    for (const [key, cfg] of Object.entries(MANIFEST.THEMES)) {
        MANIFEST._colors[key] = cfg.color;
    }
    for (const [key, cfg] of Object.entries(MANIFEST.STATIC_LAYERS)) {
        MANIFEST._colors[key] = cfg.color;
    }

    // Freeze after helpers are attached
    Object.freeze(MANIFEST);

    // Expose globally (consumed by loader.js, store.js, app.js)
    window.MANIFEST = MANIFEST;

})();
