# Testing Instructions - Details Panel for All Layers

## What Was Fixed
The PropertySchemas module (`app/modules/i18n/property-schemas.js`) now has complete property definitions for all 5 data themes:
- ✅ Water (9 properties)
- ✅ Energy (13 properties)
- ✅ Food (11 properties)
- ✅ General Info (7 properties)
- ✅ Regenerative Agriculture (8 properties)

## How to Test

### 1. Start the Development Server
```bash
python -m http.server 8000
```

Open browser: `http://localhost:8000/`

### 2. Test Each Layer

#### Water Layer
1. Check the "Water" checkbox in the sidebar
2. Click any water point on the map
3. **Expected**: Details panel opens on the right side
4. **Verify**:
   - Village name shows (e.g., "Mrosti", "Barja")
   - All 9 properties display:
     * Village
     * Latitude, Longitude
     * Crops
     * Cultivation Months
     * Crop Irrigation
     * Main Water Source
     * Water Availability
     * Water Shortage Months
5. Switch language to Arabic (AR button)
6. **Verify**: Labels change to Arabic but values remain correct

#### Energy Layer
1. Uncheck Water, check "Energy"
2. Click any energy point
3. **Expected**: Details panel shows 13 properties:
   - Village, Lat/Lon
   - Energy Source
   - Peak Season Energy Use
   - Manual %, Diesel %, Grid %, Gasoline %, Solar %
   - Diesel L/Week, Gasoline L/Week, kW/Week averages
4. Test language switch

#### Food Layer
1. Check "Food" layer
2. Click any food point
3. **Expected**: 11 properties display:
   - Village, Lat/Lon
   - Main Crops
   - Crop Timing
   - Production Level
   - Main Traditional Products
   - Food Preservation Participation
   - Animal Types
   - Number of Birds
   - Feed Type
4. Test language switch

#### General Info Layer
1. Check "General Info" layer
2. Click any general point
3. **Expected**: 7 properties:
   - Village, Lat/Lon
   - Farm Size
   - Soil Type
   - Climate Changes
   - Climate Change Impact
4. Test language switch

#### Regenerative Agriculture Layer
1. Check "Regenerative Agriculture" layer
2. Click any regen point
3. **Expected**: 8 properties:
   - Village, Lat/Lon
   - Regenerative Techniques
   - Soil Amendment Types
   - Chemical Fertilizers
   - Pest Control
   - Chemical Pesticides
4. Test language switch

### 3. Test Village Names
**Critical verification** - Village names must show phonetic transliterations, NOT literal translations:

✅ **Correct Examples**:
- Mrosti (NOT "My lady")
- Barja (NOT "towers")
- Al-Barouk (NOT "The Barack")
- Al-Matla (NOT "The view")

❌ **Wrong** (old data):
- "My lady" instead of Mrosti
- "towers" instead of Barja

### 4. Common Issues to Check

#### Issue: Details panel is empty or shows "No data here"
**Cause**: Feature doesn't have featureId or canonical structure
**Check**: 
1. Open browser console (F12)
2. Look for errors about missing featureId
3. Verify canonical GeoJSON files exist in `data/geojson/canonical/`

#### Issue: Properties show Arabic keys instead of English labels
**Cause**: PropertySchemas missing definition for that property key
**Solution**: Already fixed - all properties now mapped

#### Issue: Only some properties show, not all
**Cause**: Empty or null values in data
**Note**: This is normal - only non-empty properties are displayed

#### Issue: Language switch doesn't work
**Cause**: Missing Arabic translations in schema
**Solution**: Already fixed - all properties have both en/ar labels

### 5. Browser Console Verification

Open browser console (F12) and check:
1. No errors about "PropertySchemas is not defined"
2. No warnings about "Feature XXX not found"
3. When clicking features, you should see feature properties logged

### 6. Multi-Language Testing Flow

**English Mode**:
1. Click a water point → See "Village", "Crops", "Water Availability"
2. Click an energy point → See "Energy Source", "Diesel %"
3. All labels in English

**Switch to Arabic (click AR button)**:
1. Click same water point → See "القرية", "المحصول", "توفر المياه"
2. Click same energy point → See "مصدر الطاقة", "ديزل%"
3. All labels in Arabic

**Switch back to English**:
1. Everything returns to English labels
2. Village names remain in phonetic English (Mrosti, not مرستي)

## Expected Behavior Summary

| Layer | Properties | Common Fields | Theme-Specific |
|-------|-----------|---------------|----------------|
| Water | 9 | Village, Lat, Lon | 6 water-related |
| Energy | 13 | Village, Lat, Lon | 10 energy-related |
| Food | 11 | Village, Lat, Lon | 8 food-related |
| General | 7 | Village, Lat, Lon | 4 general info |
| Regen | 8 | Village, Lat, Lon | 5 regen practices |

## Success Criteria
✅ Details panel opens for ALL 5 layers
✅ All properties display with correct labels
✅ Village names show phonetic transliteration
✅ Language switch works (EN ↔ AR)
✅ No console errors
✅ Empty/null values are hidden (not shown as "null" or "undefined")
