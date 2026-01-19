/**
 * Data Loader Module with IndexedDB Caching
 * ==========================================
 * Efficient client-side data loading and caching for GitHub Pages deployment.
 * Uses IndexedDB for browser-based storage (no server required).
 * 
 * Architecture:
 * - Load canonical GeoJSON files once
 * - Cache in IndexedDB with versioning
 * - Return cached data on subsequent loads
 * - Automatic cache invalidation based on file metadata
 */

const DataLoader = (function() {
    'use strict';

    // Configuration
    const CONFIG = {
        DB_NAME: 'ResolveMapDB',
        DB_VERSION: 1,
        STORE_NAME: 'geojsonCache',
        CACHE_EXPIRY_DAYS: 7,
        DATA_VERSION: '2.1.0' // Incremented for bilingual translation extraction (Jan 2026)
    };

    // Themes to load (canonical bilingual files - includes original + Beqaa Valley 2026)
    const THEMES = {
        water: {
            id: 'water-points',
            files: [
                'data/geojson/canonical/Water.canonical.geojson',
                'data/geojson/canonical/Water_new.canonical.geojson'
            ],
            color: '#1abc9c'
        },
        energy: {
            id: 'energy-points',
            file: 'data/geojson/canonical/Energy.canonical.geojson',
            color: '#f39c12'
        },
        food: {
            id: 'food-points',
            file: 'data/geojson/canonical/Food.canonical.geojson',
            color: '#e74c3c'
        },
        general: {
            id: 'general-points',
            files: [
                'data/geojson/canonical/General_Info.canonical.geojson',
                'data/geojson/canonical/General_Info_new.canonical.geojson'
            ],
            color: '#3498db'
        },
        regen: {
            id: 'regen-points',
            files: [
                'data/geojson/canonical/Regenerative_Agriculture.canonical.geojson',
                'data/geojson/canonical/Regenerative_Agriculture_new.canonical.geojson'
            ],
            color: '#27ae60'
        }
    };

    // Static layers (unchanged)
    const STATIC_LAYERS = {
        fire: 'data/geojson/fire.geojson',
        preservations: 'data/geojson/Preservations.geojson',
        predictions: 'data/geojson/Model_Predictions.geojson'
    };

    let db = null;

    /**
     * Initialize IndexedDB
     */
    function initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(CONFIG.DB_NAME, CONFIG.DB_VERSION);

            request.onerror = () => {
                console.warn('IndexedDB initialization failed, will use network only');
                resolve(null); // Graceful degradation
            };

            request.onsuccess = (event) => {
                db = event.target.result;
                console.log('✓ IndexedDB initialized');
                resolve(db);
            };

            request.onupgradeneeded = (event) => {
                const database = event.target.result;
                
                // Create object store with keyPath
                if (!database.objectStoreNames.contains(CONFIG.STORE_NAME)) {
                    const store = database.createObjectStore(CONFIG.STORE_NAME, { 
                        keyPath: 'key' 
                    });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                    store.createIndex('version', 'version', { unique: false });
                }
            };
        });
    }

    /**
     * Get cached data from IndexedDB
     */
    function getCached(key) {
        if (!db) return Promise.resolve(null);

        return new Promise((resolve) => {
            try {
                const transaction = db.transaction([CONFIG.STORE_NAME], 'readonly');
                const store = transaction.objectStore(CONFIG.STORE_NAME);
                const request = store.get(key);

                request.onsuccess = (event) => {
                    const cached = event.target.result;
                    
                    if (!cached) {
                        resolve(null);
                        return;
                    }

                    // Check version
                    if (cached.version !== CONFIG.DATA_VERSION) {
                        console.log(`Cache invalidated for ${key}: version mismatch`);
                        resolve(null);
                        return;
                    }

                    // Check expiry
                    const age = Date.now() - cached.timestamp;
                    const maxAge = CONFIG.CACHE_EXPIRY_DAYS * 24 * 60 * 60 * 1000;
                    
                    if (age > maxAge) {
                        console.log(`Cache expired for ${key}: ${Math.round(age / 86400000)} days old`);
                        resolve(null);
                        return;
                    }

                    console.log(`✓ Cache hit: ${key}`);
                    resolve(cached.data);
                };

                request.onerror = () => {
                    console.warn(`Cache read error for ${key}`);
                    resolve(null);
                };
            } catch (error) {
                console.warn(`Cache access error: ${error.message}`);
                resolve(null);
            }
        });
    }

    /**
     * Store data in IndexedDB
     */
    function setCached(key, data) {
        if (!db) return Promise.resolve();

        return new Promise((resolve) => {
            try {
                const transaction = db.transaction([CONFIG.STORE_NAME], 'readwrite');
                const store = transaction.objectStore(CONFIG.STORE_NAME);
                
                const cacheEntry = {
                    key: key,
                    data: data,
                    timestamp: Date.now(),
                    version: CONFIG.DATA_VERSION
                };

                const request = store.put(cacheEntry);

                request.onsuccess = () => {
                    console.log(`✓ Cached: ${key}`);
                    resolve();
                };

                request.onerror = () => {
                    console.warn(`Cache write error for ${key}`);
                    resolve(); // Don't fail on cache errors
                };
            } catch (error) {
                console.warn(`Cache storage error: ${error.message}`);
                resolve();
            }
        });
    }

    /**
     * Fetch GeoJSON from network
     */
    async function fetchGeoJSON(url) {
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const geojson = await response.json();
            
            // Validate GeoJSON structure
            if (!geojson.type || geojson.type !== 'FeatureCollection') {
                throw new Error('Invalid GeoJSON: missing FeatureCollection type');
            }

            if (!Array.isArray(geojson.features)) {
                throw new Error('Invalid GeoJSON: missing features array');
            }

            return geojson;
        } catch (error) {
            console.error(`Failed to fetch ${url}:`, error);
            throw error;
        }
    }

    /**
     * Load GeoJSON with caching
     */
    async function loadGeoJSON(key, url) {
        // Try cache first
        const cached = await getCached(key);
        if (cached) {
            return cached;
        }

        // Fetch from network
        console.log(`Fetching ${key} from network...`);
        const data = await fetchGeoJSON(url);

        // Cache for next time
        await setCached(key, data);

        return data;
    }

    /**
     * Load all canonical theme data (supports single file or multiple files per theme)
     */
    async function loadAllThemes(progressCallback) {
        const results = {};
        const themeKeys = Object.keys(THEMES);
        let loaded = 0;

        for (const themeKey of themeKeys) {
            const theme = THEMES[themeKey];
            
            try {
                // Check if theme has single file or multiple files
                const files = theme.files || [theme.file];
                const allFeatures = [];
                
                // Load and merge all files for this theme
                for (const file of files) {
                    const geojson = await loadGeoJSON(`${themeKey}_${file}`, file);
                    allFeatures.push(...geojson.features);
                }
                
                // Create merged GeoJSON
                const mergedGeoJSON = {
                    type: 'FeatureCollection',
                    features: allFeatures
                };
                
                results[themeKey] = {
                    id: theme.id,
                    color: theme.color,
                    data: mergedGeoJSON,
                    features: allFeatures.length
                };

                loaded++;
                if (progressCallback) {
                    progressCallback(loaded, themeKeys.length, themeKey);
                }
            } catch (error) {
                console.error(`Failed to load theme ${themeKey}:`, error);
                throw error;
            }
        }

        return results;
    }

    /**
     * Load static layers (fire, preservations, predictions)
     */
    async function loadStaticLayers() {
        const results = {};

        for (const [key, url] of Object.entries(STATIC_LAYERS)) {
            try {
                const geojson = await loadGeoJSON(`static_${key}`, url);
                results[key] = geojson;
            } catch (error) {
                console.error(`Failed to load static layer ${key}:`, error);
                // Static layers are optional, continue on error
            }
        }

        return results;
    }

    /**
     * Clear all cached data
     */
    function clearCache() {
        if (!db) {
            console.warn('No database connection to clear');
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([CONFIG.STORE_NAME], 'readwrite');
            const store = transaction.objectStore(CONFIG.STORE_NAME);
            const request = store.clear();

            request.onsuccess = () => {
                console.log('✓ Cache cleared');
                resolve();
            };

            request.onerror = () => {
                console.error('Failed to clear cache');
                reject();
            };
        });
    }

    /**
     * Get cache statistics
     */
    async function getCacheStats() {
        if (!db) return { enabled: false };

        return new Promise((resolve) => {
            const transaction = db.transaction([CONFIG.STORE_NAME], 'readonly');
            const store = transaction.objectStore(CONFIG.STORE_NAME);
            const request = store.getAll();

            request.onsuccess = (event) => {
                const items = event.target.result;
                const totalSize = JSON.stringify(items).length;
                
                resolve({
                    enabled: true,
                    itemCount: items.length,
                    totalSizeKB: Math.round(totalSize / 1024),
                    version: CONFIG.DATA_VERSION,
                    items: items.map(item => ({
                        key: item.key,
                        timestamp: new Date(item.timestamp).toISOString(),
                        age: Math.round((Date.now() - item.timestamp) / 86400000) + ' days'
                    }))
                });
            };

            request.onerror = () => {
                resolve({ enabled: false, error: 'Failed to read cache' });
            };
        });
    }

    // Public API
    return {
        init: initDB,
        loadAllThemes,
        loadStaticLayers,
        loadGeoJSON,
        clearCache,
        getCacheStats,
        THEMES,
        STATIC_LAYERS
    };
})();

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.DataLoader = DataLoader;
}
