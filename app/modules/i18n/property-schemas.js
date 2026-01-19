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
            '4.القرية': { en: 'Village', ar: 'القرية' },
            '4.القرية:': { en: 'Village', ar: 'القرية' },
            '4. Village': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            'المحصول': { en: 'Crops', ar: 'المحصول' },
            '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟': { en: 'Crops', ar: 'المحصول' },
            '10. Main Crops': { en: 'Crops', ar: 'المحصول' },
            '_4': { en: 'Cultivation Months', ar: 'اشهر الزراعة' },
            '_5': { en: 'Crop Irrigation', ar: 'ريّ المحصول' },
            '_6': { en: 'Main Water Source', ar: 'مصدر مياه الريّ الرئيسي' },
            '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟': { en: 'Main irrigation source', ar: 'مصدر مياه الريّ الرئيسي' },
            '13. Water Source': { en: 'Main irrigation source', ar: 'مصدر مياه الريّ الرئيسي' },
            '_7': { en: 'Water Availability', ar: 'توفر المياه' },
            '16.كيف تقيّم توفر المياه خلال موسم الزراعة؟': { en: 'Water sufficiency', ar: 'توفر المياه' },
            '16. Water Availability': { en: 'Water sufficiency', ar: 'توفر المياه' },
            '_8': { en: 'Water Shortage Months', ar: 'أشهر شح المياه' },
            '17.هل هناك أشهر خلال السنة تعاني فيها من شح المياه؟': { en: 'Water scarcity months', ar: 'أشهر شح المياه' },
            '17. Are there months during the year when you suffer from water scarcity?': { en: 'Water scarcity months', ar: 'أشهر شح المياه' },
            'ما أشهر  الذي  تعاني فيها من شح المياه؟': { en: 'Scarcity months', ar: 'أشهر الشح' },
            '17. Water Scarcity Months': { en: 'Scarcity months', ar: 'أشهر الشح' },
            '18.هل لاحظت أي تغيير في احتياجات الري خلال السنوات العشر الماضية؟': { en: 'Irrigation needs change', ar: 'تغير احتياجات الري' },
            '18. Change in Irrigation Needs': { en: 'Irrigation needs change', ar: 'تغير احتياجات الري' }
        },

        // Energy theme - 13 properties
        energy: {
            'القرية': { en: 'Village', ar: 'القرية' },
            '4.القرية': { en: 'Village', ar: 'القرية' },
            '4.القرية:': { en: 'Village', ar: 'القرية' },
            '4. Village': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            '_3': { en: 'Energy Source', ar: 'مصدر الطاقة' },
            '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟': { en: 'Main Energy Source', ar: 'مصدر الطاقة الرئيسي' },
            '14. Energy Source': { en: 'Main Energy Source', ar: 'مصدر الطاقة الرئيسي' },
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
            '4.القرية': { en: 'Village', ar: 'القرية' },
            '4.القرية:': { en: 'Village', ar: 'القرية' },
            '4. Village': { en: 'Village', ar: 'القرية' },
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
            '4.القرية': { en: 'Village', ar: 'القرية' },
            '4.القرية:': { en: 'Village', ar: 'القرية' },
            '4. Village': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            '2.الفئة العمرية:': { en: 'Age Group', ar: 'الفئة العمرية' },
            '2. Age Group': { en: 'Age Group', ar: 'الفئة العمرية' },
            '3.الجنس:': { en: 'Gender', ar: 'الجنس' },
            '3. Gender': { en: 'Gender', ar: 'الجنس' },
            '_3': { en: 'Farm Size', ar: 'حجم الزراعة' },
            '8.ما هو حجم الحيازة الزراعية الخاصة بك؟': { en: 'Farm Size', ar: 'حجم الزراعة' },
            '8. Farm Size': { en: 'Farm Size', ar: 'حجم الزراعة' },
            '_4': { en: 'Soil Type', ar: 'نوع التربة' },
            '9.ما هو نوع التربة في أرضك؟': { en: 'Soil Type', ar: 'نوع التربة' },
            '9. Soil Type': { en: 'Soil Type', ar: 'نوع التربة' },
            '_5': { en: 'Climate Changes', ar: 'التغيرات المناخية' },
            '_6': { en: 'Climate Change Impact', ar: 'تأثير الغيرات المناخية' }
        },

        // Regenerative Agriculture theme - 7 properties (note: CSV only has 7 columns, not 8)
        regen: {
            'القرية': { en: 'Village', ar: 'القرية' },
            '4.القرية': { en: 'Village', ar: 'القرية' },
            '4.القرية:': { en: 'Village', ar: 'القرية' },
            '4. Village': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            '_3': { en: 'Regenerative Techniques', ar: 'تقنيات الزراعة التجديدية' },
            '_4': { en: 'Soil Amendment Types', ar: 'أنواع محسنات التربة' },
            '_5': { en: 'Chemical Fertilizers', ar: 'الاسمدة الكيميائية' },
            '_6': { en: 'Pest Control', ar: 'مكافحة الآفات' }
        },

        // Model Predictions theme - 7 properties
        modelpredictions: {
            'Village_Name': { en: 'Village', ar: 'القرية' },
            'Y': { en: 'Latitude', ar: 'خط العرض' },
            'X': { en: 'Longitude', ar: 'خط الطول' },
            'Practices_Regen': { en: 'Current Agricultural Practices', ar: 'الممارسات الزراعية الحالية' },
            'Water_Availability': { en: 'Water Availability', ar: 'توفر المياه' },
            'Production_Level': { en: 'Current Production Level', ar: 'مستوى الإنتاج الحالي' },
            'Pred_Regen_Adoption': { en: 'Regenerative Adoption Prediction', ar: 'توقع اعتماد الزراعة التجديدية' },
            'Pred_Water_Risk': { en: 'Water Risk Prediction', ar: 'توقع خطر شح المياه' },
            'Pred_Production_Level': { en: 'Production Capacity Prediction', ar: 'توقع القدرة الإنتاجية' }
        }
    };

    /**
     * Format prediction values for display
     * Converts discrete prediction codes to human-readable labels
     */
    const PREDICTION_VALUE_FORMATTERS = {
        'Pred_Regen_Adoption': {
            '0': { en: 'Unlikely to Adopt', ar: 'غير محتمل الاعتماد' },
            '1': { en: 'Likely to Adopt', ar: 'محتمل الاعتماد' }
        },
        'Pred_Water_Risk': {
            '0': { en: 'Low Risk', ar: 'خطر منخفض' },
            '1': { en: 'High Risk', ar: 'خطر عالي' }
        },
        'Pred_Production_Level': {
            '0': { en: 'Low', ar: 'منخفض' },
            '1': { en: 'Medium', ar: 'متوسط' },
            '2': { en: 'High', ar: 'عالي' }
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
     * Clean property label by removing question numbers
     * @param {string} label - Raw label with potential numbering
     * @returns {string} Cleaned label
     */
    function cleanLabel(label) {
        if (!label) return label;
        // Remove question numbering like "13." or "4." from the start
        return label.replace(/^\d+\.\s*/, '');
    }

    /**
     * Format property value for display
     * @param {any} value - Raw value
     * @param {string} propertyKey - Property key (for context)
     * @param {string} lang - Language ('en' or 'ar')
     * @returns {string} Formatted value
     */
    function formatValue(value, propertyKey, lang = 'en') {
        if (value === null || value === undefined) return '-';
        if (value === '') return '-';
        
        // Handle prediction values with human-readable labels
        if (PREDICTION_VALUE_FORMATTERS[propertyKey]) {
            const formatter = PREDICTION_VALUE_FORMATTERS[propertyKey][String(value)];
            if (formatter) {
                return formatter[lang] || String(value);
            }
        }
        
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
     * Build display properties for details panel
     * @param {Object} feature - GeoJSON feature
     * @param {string} theme - Theme key
     * @param {string} lang - Language ('en' or 'ar')
     * @returns {Object} Object with {villageName, themeLabel, details} for display
     */
    function buildDetailsPanel(feature, theme, lang = 'en') {
        const schema = SCHEMAS[theme];
        const values = feature.properties?.values?.[lang];
        if (!values) return { villageName: null, themeLabel: null, details: [] };

        // Extract village name for header (priority order)
        const villageKeys = ['القرية', '4.القرية', '4.القرية:', 'Village', '4. Village'];
        let villageName = null;
        let villageKey = null;
        
        for (const key of villageKeys) {
            if (values[key]) {
                villageName = values[key];
                villageKey = key;
                break;
            }
        }

        // Get theme label
        const themeLabels = {
            water: { en: 'Water', ar: 'المياه' },
            energy: { en: 'Energy', ar: 'الطاقة' },
            food: { en: 'Food', ar: 'الغذاء' },
            general: { en: 'General Info', ar: 'معلومات عامة' },
            generalinfo: { en: 'General Info', ar: 'معلومات عامة' },
            regen: { en: 'Regenerative Agriculture', ar: 'الزراعة التجديدية' },
            regenerativeagriculture: { en: 'Regenerative Agriculture', ar: 'الزراعة التجديدية' }
        };
        
        const themeLabel = themeLabels[theme]?.[lang] || theme;

        const details = [];
        const processedKeys = new Set();
        
        // Mark village as processed
        if (villageKey) processedKeys.add(villageKey);
        
        // Skip coordinates from display (they're in the map)
        processedKeys.add('X');
        processedKeys.add('Y');
        processedKeys.add('x');
        processedKeys.add('y');
        processedKeys.add('Latitude');
        processedKeys.add('Longitude');

        // Define core fields to display (matching old data structure)
        // Only show the underscore-numbered fields that old data has
        const coreFieldsByTheme = {
            water: ['_4', '_5', '_6', '_7', '_8'],
            energy: ['_3', '_4', '_5', '_6', '_7', '_8', '_9', '_10', '_11', '_12'],
            food: ['_3', '_4', '_5', '_6', '_7', '_8', '_9', '_10'],
            general: ['_3', '_4', '_5', '_6'],
            generalinfo: ['_3', '_4', '_5', '_6'],
            regen: ['_3', '_4', '_5', '_6'],
            regenerativeagriculture: ['_3', '_4', '_5', '_6']
        };

        const coreFields = coreFieldsByTheme[theme] || [];

        // PRIORITY 1: Show core fields that match old data structure
        if (schema && coreFields.length > 0) {
            for (const coreKey of coreFields) {
                // Find if this core field exists in current data
                let foundKey = null;
                let foundValue = null;

                // Check if underscore key exists directly
                if (values[coreKey] && values[coreKey] !== '' && values[coreKey] !== null) {
                    foundKey = coreKey;
                    foundValue = values[coreKey];
                } else {
                    // Check if any canonical key maps to this underscore key
                    for (const [key, value] of Object.entries(values)) {
                        if (processedKeys.has(key)) continue;
                        if (value === null || value === undefined || value === '') continue;
                        
                        // Check if this key maps to the core field in schema
                        if (schema[key] && schema[coreKey] && 
                            schema[key][lang] === schema[coreKey][lang]) {
                            foundKey = key;
                            foundValue = value;
                            break;
                        }
                    }
                }

                if (foundKey && foundValue) {
                    details.push({
                        label: schema[coreKey][lang],
                        value: formatValue(foundValue, foundKey, lang),
                        key: foundKey
                    });
                    processedKeys.add(foundKey);
                }
            }
        }

        // PRIORITY 2: Only if no core fields were found, show all schema-mapped fields
        if (details.length === 0 && schema) {
            for (const [key, value] of Object.entries(values)) {
                if (processedKeys.has(key)) continue;
                if (value === null || value === undefined || value === '') continue;
                
                if (schema[key]) {
                    details.push({
                        label: schema[key][lang],
                        value: formatValue(value, key, lang),
                        key: key
                    });
                    processedKeys.add(key);
                }
            }
        }

        return {
            villageName: villageName,
            themeLabel: themeLabel,
            details: details
        };
    }

    // Public API
    return {
        getPropertyLabel,
        getPropertyValue,
        getFeatureProperties,
        getThemeSchema,
        getThemePropertyKeys,
        formatValue,
        cleanLabel,
        buildDetailsPanel,
        SCHEMAS
    };
})();

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.PropertySchemas = PropertySchemas;
}
