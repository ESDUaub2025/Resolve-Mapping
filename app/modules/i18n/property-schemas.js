/**
 * Property Schema Mapping & I18N
 * ===============================
 * Maps property keys between Arabic and English for display.
 * Language affects presentation only, NOT data sources.
 * 
 * Architecture:
 * - Single canonical data with bilingual properties
 * - Schema defines how to display properties in each language
 * - No data reloading on language switch
 */

const PropertySchemas = (function() {
    'use strict';

    /**
     * Property display schemas by theme
     * Maps property keys to human-readable labels in both languages
     * Property keys match what's actually in the canonical GeoJSON files
     * (The canonical generation script creates numbered keys like _3, _4, etc.)
     */
    const SCHEMAS = {
        // Water theme - 9 properties
        water: {
            'القرية': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            'المحصول': { en: 'Crops', ar: 'المحصول' },
            '_4': { en: 'Cultivation Months', ar: 'اشهر الزراعة' },
            '_5': { en: 'Crop Irrigation', ar: 'ريّ المحصول' },
            '_6': { en: 'Main Water Source', ar: 'مصدر مياه الريّ الرئيسي' },
            '_7': { en: 'Water Availability', ar: 'توفر المياه' },
            '_8': { en: 'Water Shortage Months', ar: 'أشهر شح المياه' }
        },

        // Energy theme - 13 properties
        energy: {
            'القرية': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            '_3': { en: 'Energy Source', ar: 'مصدر الطاقة' },
            '_4': { en: 'Peak Season Energy Use', ar: 'كمية الطاقة المستخدمة خلال موسم الذروة' },
            '_5': { en: 'Manual %', ar: 'يدويا%' },
            '_6': { en: 'Diesel %', ar: 'ديزل%' },
            '_7': { en: 'Grid %', ar: 'شبكة%' },
            '_8': { en: 'Gasoline %', ar: 'بنزين%' },
            '_9': { en: 'Solar %', ar: 'شمسية%' },
            '_10': { en: 'Diesel L/Week (Avg)', ar: 'ديزل لتر/أسبوع (متوسط)' },
            '_11': { en: 'Gasoline L/Week (Avg)', ar: 'بنزين لتر/أسبوع (متوسط)' },
            '_12': { en: 'kW/Week (Avg)', ar: 'كيلوواط/أسبوع (متوسط)' }
        },

        // Food theme - 11 properties
        food: {
            'القرية': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            '_3': { en: 'Main Crops', ar: 'المحاصيل الرئيسية' },
            '_4': { en: 'Crop Timing', ar: 'توقيت المحاصيل' },
            '_5': { en: 'Production Level', ar: 'مستوى الانتاج' },
            '_6': { en: 'Main Traditional Products', ar: 'المنتجات التقليدية الرئيسية' },
            '_7': { en: 'Food Preservation Participation', ar: 'نسبة المشاركين في تحضير المؤونة' },
            '_8': { en: 'Animal Types', ar: 'انواع الحيوانات' },
            '_9': { en: 'Number of Birds', ar: 'عدد الطيور' },
            '_10': { en: 'Feed Type', ar: 'نوع العلف' }
        },

        // General Info theme - 7 properties
        general: {
            'القرية': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            '_3': { en: 'Farm Size', ar: 'حجم الزراعة' },
            '_4': { en: 'Soil Type', ar: 'نوع التربة' },
            '_5': { en: 'Climate Changes', ar: 'التغيرات المناخية' },
            '_6': { en: 'Climate Change Impact', ar: 'تأثير الغيرات المناخية' }
        },

        // Regenerative Agriculture theme - 7 properties (note: CSV only has 7 columns, not 8)
        regen: {
            'القرية': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            '_3': { en: 'Regenerative Techniques', ar: 'تقنيات الزراعة التجديدية' },
            '_4': { en: 'Soil Amendment Types', ar: 'أنواع محسنات التربة' },
            '_5': { en: 'Chemical Fertilizers', ar: 'الاسمدة الكيميائية' },
            '_6': { en: 'Pest Control', ar: 'مكافحة الآفات' }
        }
    };

    /**
     * Get property label in specified language
     * @param {string} theme - Theme key (water, energy, food, general, regen)
     * @param {string} propertyKey - Property key from GeoJSON
     * @param {string} lang - Language ('en' or 'ar')
     * @returns {string} Localized label or property key if not found
     */
    function getPropertyLabel(theme, propertyKey, lang = 'en') {
        const schema = SCHEMAS[theme];
        if (!schema || !schema[propertyKey]) {
            return propertyKey; // Fallback to key itself
        }
        return schema[propertyKey][lang] || propertyKey;
    }

    /**
     * Get property value from canonical feature
     * @param {Object} feature - GeoJSON feature with canonical structure
     * @param {string} propertyKey - Property key
     * @param {string} lang - Language ('en' or 'ar')
     * @returns {any} Property value in specified language
     */
    function getPropertyValue(feature, propertyKey, lang = 'en') {
        const values = feature.properties?.values;
        if (!values) return null;
        
        return values[lang]?.[propertyKey] || null;
    }

    /**
     * Get all properties for a feature in specified language
     * @param {Object} feature - GeoJSON feature
     * @param {string} theme - Theme key
     * @param {string} lang - Language ('en' or 'ar')
     * @returns {Object} Object with {label: value} pairs
     */
    function getFeatureProperties(feature, theme, lang = 'en') {
        const values = feature.properties?.values;
        if (!values || !values[lang]) return {};

        const schema = SCHEMAS[theme] || {};
        const result = {};

        for (const [key, value] of Object.entries(values[lang])) {
            const label = getPropertyLabel(theme, key, lang);
            if (value !== null && value !== undefined && value !== '') {
                result[label] = value;
            }
        }

        return result;
    }

    /**
     * Get schema for a theme
     * @param {string} theme - Theme key
     * @returns {Object} Schema object or null
     */
    function getThemeSchema(theme) {
        return SCHEMAS[theme] || null;
    }

    /**
     * Get all property keys for a theme
     * @param {string} theme - Theme key
     * @returns {Array} Array of property keys
     */
    function getThemePropertyKeys(theme) {
        const schema = SCHEMAS[theme];
        return schema ? Object.keys(schema) : [];
    }

    /**
     * Format property value for display
     * @param {any} value - Raw value
     * @param {string} propertyKey - Property key (for context)
     * @returns {string} Formatted value
     */
    function formatValue(value, propertyKey) {
        if (value === null || value === undefined) return '-';
        if (value === '') return '-';
        
        // Handle numeric values
        if (typeof value === 'number') {
            return value.toLocaleString();
        }

        // Handle boolean values
        if (typeof value === 'boolean') {
            return value ? '✓' : '✗';
        }

        return String(value);
    }

    /**
     * Priority order for common fields (shown first across all themes)
     */
    const COMMON_FIELD_PRIORITY = ['القرية', 'Y', 'X'];

    /**
     * Build display properties for details panel
     * @param {Object} feature - GeoJSON feature
     * @param {string} theme - Theme key
     * @param {string} lang - Language ('en' or 'ar')
     * @returns {Array} Array of {label, value} objects for display
     */
    function buildDetailsPanel(feature, theme, lang = 'en') {
        const schema = SCHEMAS[theme];
        if (!schema) return [];

        const values = feature.properties?.values?.[lang];
        if (!values) return [];

        const commonDetails = [];
        const specificDetails = [];

        // First, add common fields in priority order
        COMMON_FIELD_PRIORITY.forEach(key => {
            const value = values[key];
            if (value !== null && value !== undefined && value !== '') {
                const label = schema[key] ? schema[key][lang] : key;
                commonDetails.push({
                    label: label,
                    value: formatValue(value, key),
                    key: key,
                    isCommon: true
                });
            }
        });

        // Then, add theme-specific fields in schema order
        for (const [key, labels] of Object.entries(schema)) {
            // Skip common fields (already added)
            if (COMMON_FIELD_PRIORITY.includes(key)) continue;

            const value = values[key];
            if (value !== null && value !== undefined && value !== '') {
                specificDetails.push({
                    label: labels[lang],
                    value: formatValue(value, key),
                    key: key,
                    isCommon: false
                });
            }
        }

        // Return common fields first, then specific fields
        return [...commonDetails, ...specificDetails];
    }

    // Public API
    return {
        getPropertyLabel,
        getPropertyValue,
        getFeatureProperties,
        getThemeSchema,
        getThemePropertyKeys,
        formatValue,
        buildDetailsPanel,
        SCHEMAS
    };
})();

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.PropertySchemas = PropertySchemas;
}
