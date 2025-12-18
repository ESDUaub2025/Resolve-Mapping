/**
 * Filter Engine with Two-Stage Normalization
 * ===========================================
 * Professional filter architecture with code-based filtering.
 * 
 * Two-Stage Approach:
 * 1. Normalize: Convert display values to stable codes
 * 2. Apply: Filter features using codes (language-independent)
 * 
 * Benefits:
 * - Language-independent filtering
 * - Stable filter state across language switches
 * - Efficient feature matching
 */

const FilterEngine = (function() {
    'use strict';

    /**
     * Value normalization maps (display value → stable code)
     * These are language-independent codes for filter values
     */
    const NORMALIZATION_MAPS = {
        // Village names (both AR and EN map to same code)
        village: {
            // Arabic names
            'الباروك': 'barouk',
            'عين وزين': 'ain_wazin',
            'عماطور': 'amatur',
            'بيت الدين': 'beit_eddine',
            'بتلون': 'batloun',
            'المختارة': 'mukhtara',
            'دير القمر': 'deir_el_qamar',
            'برجا': 'barja',
            'كفرحيم': 'kafarheim',
            'عين قني': 'ain_kani',
            'القبيات': 'qobaiyat',
            
            // English names (same codes)
            'Barouk': 'barouk',
            'Baroque': 'barouk',
            'Ain Wazin': 'ain_wazin',
            'Amatur': 'amatur',
            'Beit Eddine': 'beit_eddine',
            'Batloun': 'batloun',
            'Mukhtara': 'mukhtara',
            'Deir el Qamar': 'deir_el_qamar',
            'Barja': 'barja',
            'Kafarheim': 'kafarheim',
            'Ain Kani': 'ain_kani',
            'Qobaiyat': 'qobaiyat'
        },

        // Energy sources
        energySource: {
            // Arabic
            'طاقة شمسية': 'solar',
            'مولد كهربائي': 'generator',
            'كهرباء عامة': 'public_grid',
            'بطارية': 'battery',
            
            // English
            'Solar Energy': 'solar',
            'Solar': 'solar',
            'Generator': 'generator',
            'Public Grid': 'public_grid',
            'Battery': 'battery'
        },

        // Water sources
        waterSource: {
            // Arabic
            'بئر جوفي': 'well',
            'نهر': 'river',
            'قنوات ري': 'irrigation',
            'صهريج': 'tank',
            'نبع': 'spring',
            
            // English
            'Well': 'well',
            'Underground Well': 'well',
            'River': 'river',
            'Irrigation Channels': 'irrigation',
            'Tank': 'tank',
            'Water Tank': 'tank',
            'Spring': 'spring'
        },

        // Crop types
        cropType: {
            // Arabic
            'تفاح': 'apple',
            'بندورة': 'tomato',
            'خيار': 'cucumber',
            'زيتون': 'olive',
            'عنب': 'grape',
            'حمضيات': 'citrus',
            'دراق': 'peach',
            
            // English
            'Apple': 'apple',
            'Apples': 'apple',
            'Tomato': 'tomato',
            'Tomatoes': 'tomato',
            'Cucumber': 'cucumber',
            'Olive': 'olive',
            'Olives': 'olive',
            'Grape': 'grape',
            'Grapes': 'grape',
            'Citrus': 'citrus',
            'Peach': 'peach',
            'Peaches': 'peach'
        },

        // Regenerative practices
        regenPractice: {
            // Arabic
            'سماد عضوي': 'organic_fertilizer',
            'تناوب محاصيل': 'crop_rotation',
            'حفظ تربة': 'soil_conservation',
            'ري بالتنقيط': 'drip_irrigation',
            
            // English
            'Organic Fertilizer': 'organic_fertilizer',
            'Crop Rotation': 'crop_rotation',
            'Soil Conservation': 'soil_conservation',
            'Drip Irrigation': 'drip_irrigation'
        }
    };

    /**
     * Normalize a display value to stable code
     * @param {string} category - Filter category (village, energySource, etc.)
     * @param {string} value - Display value (in any language)
     * @returns {string|null} Normalized code or null if not found
     */
    function normalizeValue(category, value) {
        if (!value) return null;
        
        const map = NORMALIZATION_MAPS[category];
        if (!map) {
            console.warn(`No normalization map for category: ${category}`);
            return value.toLowerCase().trim();
        }

        // Direct lookup
        if (map[value]) {
            return map[value];
        }

        // Case-insensitive lookup
        const lowerValue = value.toLowerCase().trim();
        for (const [key, code] of Object.entries(map)) {
            if (key.toLowerCase() === lowerValue) {
                return code;
            }
        }

        // Partial match (for composite values like "apples, tomatoes")
        for (const [key, code] of Object.entries(map)) {
            if (value.includes(key) || key.includes(value)) {
                return code;
            }
        }

        // Fallback: use sanitized value as code
        return lowerValue.replace(/[^a-z0-9]/g, '_');
    }

    /**
     * Check if a feature matches a normalized code
     * @param {Object} feature - GeoJSON feature with canonical structure
     * @param {string} propertyKey - Property key to check (in both languages)
     * @param {string} normalizedCode - Stable code to match
     * @param {string} currentLang - Current language ('en' or 'ar')
     * @returns {boolean} True if feature matches
     */
    function featureMatchesCode(feature, propertyKey, normalizedCode, currentLang = 'en') {
        const values = feature.properties?.values;
        if (!values) return false;

        // Check both languages (filter should work regardless of language)
        const arValue = values.ar?.[propertyKey];
        const enValue = values.en?.[propertyKey];

        // Normalize feature values and compare
        const category = getCategoryForProperty(propertyKey);
        
        if (arValue) {
            const arCode = normalizeValue(category, String(arValue));
            if (arCode === normalizedCode) return true;
            
            // For composite values (e.g., "apples, tomatoes")
            if (String(arValue).includes(',')) {
                const parts = String(arValue).split(',');
                for (const part of parts) {
                    const partCode = normalizeValue(category, part.trim());
                    if (partCode === normalizedCode) return true;
                }
            }
        }

        if (enValue) {
            const enCode = normalizeValue(category, String(enValue));
            if (enCode === normalizedCode) return true;
            
            // For composite values
            if (String(enValue).includes(',')) {
                const parts = String(enValue).split(',');
                for (const part of parts) {
                    const partCode = normalizeValue(category, part.trim());
                    if (partCode === normalizedCode) return true;
                }
            }
        }

        return false;
    }

    /**
     * Map property keys to normalization categories
     */
    function getCategoryForProperty(propertyKey) {
        const mapping = {
            'القرية': 'village',
            'Village': 'village',
            'مصدر الطاقة': 'energySource',
            'Energy Source': 'energySource',
            'المحصول': 'cropType',
            'Crop': 'cropType',
            'Main_Crops': 'cropType',
            '_6': 'waterSource', // Water source column
            'Water Source': 'waterSource',
            'الممارسات': 'regenPractice',
            'Practices': 'regenPractice'
        };

        return mapping[propertyKey] || 'generic';
    }

    /**
     * Apply filters to features
     * @param {Array} features - Array of GeoJSON features
     * @param {Object} filters - Filter object {propertyKey: displayValue}
     * @param {string} currentLang - Current language
     * @returns {Array} Filtered features
     */
    function applyFilters(features, filters, currentLang = 'en') {
        if (!filters || Object.keys(filters).length === 0) {
            return features; // No filters, return all
        }

        // Normalize all filter values to codes
        const normalizedFilters = {};
        for (const [key, value] of Object.entries(filters)) {
            if (!value) continue;
            const category = getCategoryForProperty(key);
            normalizedFilters[key] = normalizeValue(category, value);
        }

        // Filter features
        return features.filter(feature => {
            // Feature must match ALL active filters (AND logic)
            for (const [propertyKey, normalizedCode] of Object.entries(normalizedFilters)) {
                if (!featureMatchesCode(feature, propertyKey, normalizedCode, currentLang)) {
                    return false;
                }
            }
            return true;
        });
    }

    /**
     * Get unique values for a property (for building filter dropdowns)
     * @param {Array} features - Array of GeoJSON features
     * @param {string} propertyKey - Property key to extract values from
     * @param {string} lang - Language to extract ('en' or 'ar')
     * @returns {Array} Sorted unique values
     */
    function getUniqueValues(features, propertyKey, lang = 'en') {
        const values = new Set();

        features.forEach(feature => {
            const propValues = feature.properties?.values?.[lang];
            if (propValues && propValues[propertyKey]) {
                const value = String(propValues[propertyKey]).trim();
                
                // Handle composite values (comma-separated)
                if (value.includes(',')) {
                    value.split(',').forEach(part => {
                        const trimmed = part.trim();
                        if (trimmed) values.add(trimmed);
                    });
                } else if (value) {
                    values.add(value);
                }
            }
        });

        return Array.from(values).sort();
    }

    /**
     * Build filter options for a property
     * @param {Array} features - Array of GeoJSON features
     * @param {string} propertyKey - Property key
     * @param {string} lang - Current language
     * @returns {Array} Array of {label, value, code} objects
     */
    function buildFilterOptions(features, propertyKey, lang = 'en') {
        const uniqueValues = getUniqueValues(features, propertyKey, lang);
        const category = getCategoryForProperty(propertyKey);

        return uniqueValues.map(value => ({
            label: value,
            value: value,
            code: normalizeValue(category, value)
        }));
    }

    /**
     * Export normalization maps for debugging
     */
    function getNormalizationMaps() {
        return { ...NORMALIZATION_MAPS };
    }

    // Public API
    return {
        normalizeValue,
        applyFilters,
        featureMatchesCode,
        getUniqueValues,
        buildFilterOptions,
        getCategoryForProperty,
        getNormalizationMaps
    };
})();

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.FilterEngine = FilterEngine;
}
