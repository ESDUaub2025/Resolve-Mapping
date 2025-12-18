# Details Panel Schema Update - Complete

## Summary
Updated `property-schemas.js` to include complete and accurate property mappings for ALL 5 data themes. The details panel will now display correct bilingual labels for every layer.

## Changes Made

### Updated File
- **File**: `app/modules/i18n/property-schemas.js`
- **Change**: Replaced incomplete SCHEMAS object with complete mappings based on actual CSV column structure

### Property Schemas by Theme

#### 1. Water Theme (9 properties)
```javascript
'القرية' → Village / القرية
'Y' → Latitude / خط العرض
'X' → Longitude / خط الطول
'المحصول' → Crops / المحصول
'اشهر الزراعة' → Cultivation Months / اشهر الزراعة
'ريّ المحصول' → Crop Irrigation / ريّ المحصول
'مصدر مياه الريّ الرئيسي' → Main Water Source / مصدر مياه الريّ الرئيسي
'توفر المياه' → Water Availability / توفر المياه
'أشهر شح المياه' → Water Shortage Months / أشهر شح المياه
```

#### 2. Energy Theme (13 properties)
```javascript
'القرية' → Village / القرية
'Y' → Latitude / خط العرض
'X' → Longitude / خط الطول
'مصدر الطاقة' → Energy Source / مصدر الطاقة
'كمية الطاقة المستخدمة خلال موسم الذروة' → Peak Season Energy Use / كمية الطاقة المستخدمة خلال موسم الذروة
'يدويا%' → Manual % / يدويا%
'ديزل%' → Diesel % / ديزل%
'شبكة%' → Grid % / شبكة%
'بنزين%' → Gasoline % / بنزين%
'شمسية%' → Solar % / شمسية%
'Diesel L/Week (Avg)' → Diesel L/Week (Avg) / ديزل لتر/أسبوع (متوسط)
'Benzine L/Week (Avg)' → Gasoline L/Week (Avg) / بنزين لتر/أسبوع (متوسط)
'kW/Week (Avg)' → kW/Week (Avg) / كيلوواط/أسبوع (متوسط)
```

#### 3. Food Theme (11 properties)
```javascript
'القرية' → Village / القرية
'Y' → Latitude / خط العرض
'X' → Longitude / خط الطول
'المحاصيل الرئيسية' → Main Crops / المحاصيل الرئيسية
'توقيت المحاصيل' → Crop Timing / توقيت المحاصيل
'مستوى الانتاج' → Production Level / مستوى الانتاج
'المنتجات التقليدية الرئيسية' → Main Traditional Products / المنتجات التقليدية الرئيسية
'نسبة المشاركين في تحضير المؤونة' → Food Preservation Participation / نسبة المشاركين في تحضير المؤونة
'انواع الحيوانات' → Animal Types / انواع الحيوانات
'عدد الطيور' → Number of Birds / عدد الطيور
'نوع العلف' → Feed Type / نوع العلف
```

#### 4. General Info Theme (7 properties)
```javascript
'القرية' → Village / القرية
'Y' → Latitude / خط العرض
'X' → Longitude / خط الطول
'حجم الزراعة' → Farm Size / حجم الزراعة
'نوع التربة' → Soil Type / نوع التربة
'التغيرات المناخية' → Climate Changes / التغيرات المناخية
'تأثير الغيرات المناخية' → Climate Change Impact / تأثير الغيرات المناخية
```

#### 5. Regenerative Agriculture Theme (8 properties)
```javascript
'القرية' → Village / القرية
'Y' → Latitude / خط العرض
'X' → Longitude / خط الطول
'تقنيات الزراعة التجديدية' → Regenerative Techniques / تقنيات الزراعة التجديدية
'أنواع محسنات التربة' → Soil Amendment Types / أنواع محسنات التربة
'الاسمدة الكيميائية' → Chemical Fertilizers / الاسمدة الكيميائية
'مكافحة الآفات' → Pest Control / مكافحة الآفات
'المبيدات الكيميائية' → Chemical Pesticides / المبيدات الكيميائية
```

## How It Works

### Architecture
1. **Canonical GeoJSON Structure**: Each feature has nested bilingual properties:
   ```json
   {
     "properties": {
       "values": {
         "en": { "القرية": "Mrosti", "المحصول": "Apples" },
         "ar": { "القرية": "مرستي", "المحصول": "تفاح" }
       }
     }
   }
   ```

2. **Property Schemas**: Maps Arabic property keys to human-readable labels:
   ```javascript
   'المحصول': { en: 'Crops', ar: 'المحصول' }
   ```

3. **Details Panel**: Uses `buildDetailsPanel(feature, theme, lang)` to:
   - Extract feature properties for current language
   - Map property keys to localized labels
   - Format and display in details panel

### Display Priority
Common fields shown first:
1. Village (القرية)
2. Latitude (Y)
3. Longitude (X)

Then theme-specific properties in schema order.

## Testing Checklist

Test the details panel for each layer:

### Water Layer
- [x] Click water point → Details panel appears
- [ ] Village name shows correct transliteration (e.g., "Mrosti")
- [ ] All 9 properties display with correct labels
- [ ] Switch to Arabic → Labels change to Arabic
- [ ] Values remain correct in both languages

### Energy Layer
- [ ] Click energy point → Details panel shows 13 properties
- [ ] Village name correct (e.g., "Barja")
- [ ] Energy source, percentages, and averages display
- [ ] Arabic labels work correctly

### Food Layer
- [ ] Click food point → Details panel shows 11 properties
- [ ] Main crops, timing, production level visible
- [ ] Animal types and feed type display
- [ ] Bilingual labels work

### General Layer
- [ ] Click general point → Details panel shows 7 properties
- [ ] Farm size, soil type, climate info visible
- [ ] Bilingual labels work

### Regenerative Layer
- [ ] Click regen point → Details panel shows 8 properties
- [ ] Regenerative techniques, soil amendments visible
- [ ] Pest control and fertilizer info display
- [ ] Bilingual labels work

## Files Changed
1. `app/modules/i18n/property-schemas.js` - Complete schema definitions added

## Files Created (for documentation)
1. `scripts/list_csv_columns.py` - List all CSV columns by theme
2. `scripts/map_column_translations.py` - Map Arabic keys to English values

## Result
✅ All 5 themes now have complete property schemas
✅ Details panel will work for water, energy, food, general, and regen layers
✅ Bilingual labels (English/Arabic) fully supported
✅ All CSV columns mapped to human-readable labels
