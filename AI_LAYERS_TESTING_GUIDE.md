# AI Layers Testing Guide

## Quick Start Testing

### 1. Start Local Server
```bash
cd d:\Programing\ResolveMaping_final2
python -m http.server 8000
```

Open browser: `http://localhost:8000/`

### 2. Enable AI Layers

**In Sidebar:**
1. Scroll to "AI Analysis Layers" section
2. Check one or more:
   - ☑ Regenerative Adoption
   - ☑ Water Risk
   - ☑ Economic Resilience
   - ☑ Climate Vulnerability

**Expected Result:**
- Colored circles appear on map (204 points)
- Legend appears in bottom-right corner
- Farmers boundary line appears (dashed outline)

---

## Detailed Testing Checklist

### ✅ Visual Display Tests

#### Test 1: Layer Rendering
```
Steps:
1. Enable "Regenerative Adoption" layer
2. Zoom to Shouf region (around zoom 11)

Expected:
- Green and red circles visible
- Size: ~10px at zoom 11
- White stroke around each circle
- No blur (sharp edges)
- Opacity: 70% (can see base map through markers)

Pass Criteria:
✓ All 204 markers render
✓ Colors are distinct (red vs green)
✓ Base map visible underneath
✓ No console errors
```

#### Test 2: Transparency Check
```
Steps:
1. Enable AI layer
2. Switch base map to "Satellite (Esri)"
3. Compare with old water/energy layers

Expected:
- Satellite imagery clearly visible through markers
- AI markers: 70% opacity
- Old layers (water/energy): More opaque circles
- White stroke provides definition

Pass Criteria:
✓ Can identify roads/buildings through AI markers
✓ Noticeably more transparent than other layers
✓ Still clearly visible and clickable
```

#### Test 3: Zoom Behavior
```
Steps:
1. Enable AI layer
2. Zoom from level 8 → 16
3. Observe marker size changes

Expected Sizes:
- Zoom 8: 6px (very small)
- Zoom 10: 8px
- Zoom 12: 10px
- Zoom 14: 12px
- Zoom 16: 14px

Pass Criteria:
✓ Markers grow smoothly with zoom
✓ Never too large (max 14px)
✓ Always visible (min 6px)
✓ No overlap at low zoom
```

### ✅ Color Accuracy Tests

#### Test 4: Regenerative Adoption Colors
```
Steps:
1. Enable "Regenerative Adoption" layer
2. Click on various markers
3. Check color matches prediction

Expected Colors:
- Pred_Regen_Adoption: "0" → Red circle (#e74c3c)
- Pred_Regen_Adoption: "1" → Green circle (#27ae60)

Test Cases:
- Village "الباروك" with "لا" (No) practices → Red
- Village "الباروك" with "نعم" (Yes) practices → Green

Pass Criteria:
✓ All "0" predictions are red
✓ All "1" predictions are green
✓ No gray markers (unless data error)
```

#### Test 5: Water Risk Colors (Inverted Logic)
```
Steps:
1. Enable "Water Risk" layer
2. Verify color inversion (0=green, 1=red)

Expected Colors:
- Pred_Water_Risk: "0" → Green (#27ae60) = LOW RISK
- Pred_Water_Risk: "1" → Red (#e74c3c) = HIGH RISK

Test Case:
- Village with "دائماً كافية" (always sufficient) water → Green (low risk)
- Village with "نادراً" (rarely) sufficient water → Red (high risk)

Pass Criteria:
✓ Logic is inverted correctly
✓ Green = safe/low risk
✓ Red = danger/high risk
```

#### Test 6: Production Level Colors (3 Categories)
```
Steps:
1. Enable "Economic Resilience" layer
2. Verify 3-tier color system

Expected Colors:
- Pred_Production_Level: "0" → Red (#e74c3c)
- Pred_Production_Level: "1" → Yellow (#f39c12)
- Pred_Production_Level: "2" → Green (#27ae60)

Pass Criteria:
✓ Red = low production
✓ Yellow = medium production
✓ Green = high production
✓ All three colors visible on map
```

### ✅ Interaction Tests

#### Test 7: Hover Behavior
```
Steps:
1. Enable any AI layer
2. Hover mouse over markers
3. Observe visual changes

Expected:
- Opacity increases: 70% → 95%
- Stroke thickens: 1px → 2px
- Marker stays same color
- Cursor changes to pointer

Pass Criteria:
✓ Hover feedback immediate
✓ Smooth opacity transition
✓ No flickering
✓ Returns to normal on mouse leave
```

#### Test 8: Click Details Panel
```
Steps:
1. Enable "Regenerative Adoption"
2. Click on marker in village "علمان" (Alman)
3. Details panel opens on right

Expected Content:
┌─────────────────────────────────┐
│ Model Predictions               │
├─────────────────────────────────┤
│ Village: علمان                  │
│ Current Practices: [Arabic text]│
│ Water Availability: [text]      │
│ Production Level: [text]        │
│ ─────────────────────────────── │
│ Predictions:                    │
│ • Regen Adoption: Likely/Unlikely│
│ • Water Risk: High/Low          │
│ • Production: Low/Med/High      │
└─────────────────────────────────┘

Pass Criteria:
✓ Panel opens immediately
✓ Shows village name
✓ Shows all scenario inputs
✓ Shows all predictions with labels
✓ Values formatted (not raw "0"/"1")
```

#### Test 9: Multiple Scenarios Per Village
```
Steps:
1. Navigate to village "علمان" (Alman)
2. Count visible markers at this location
3. Click each marker separately

Expected:
- Multiple markers at same coordinates (18 for Alman)
- Each marker represents different scenario
- Clicking shows different input combinations
- Same village, different predictions

Pass Criteria:
✓ Multiple markers visible
✓ Each clickable independently
✓ Details panel updates per scenario
✓ Can distinguish scenarios
```

### ✅ Legend Tests

#### Test 10: Legend Display
```
Steps:
1. No AI layers enabled → Legend hidden
2. Enable "Regenerative Adoption" → Legend appears
3. Enable "Water Risk" → Legend updates
4. Disable all → Legend disappears

Expected Legend (Regen):
┌───────────────────────────┐
│ Regenerative Adoption     │
│ 🔴 Unlikely to Adopt      │
│ 🟢 Likely to Adopt        │
└───────────────────────────┘

Pass Criteria:
✓ Legend appears only when layer active
✓ Shows correct categories
✓ Colors match map markers
✓ Text clear and readable
✓ Updates dynamically
```

#### Test 11: Multiple Layers Legend
```
Steps:
1. Enable "Regenerative Adoption"
2. Enable "Water Risk"
3. Enable "Economic Resilience"

Expected:
- All three legends stack vertically
- Each has title + category rows
- Distinct colors for each
- No overlap or cut-off

Pass Criteria:
✓ All legends visible
✓ Properly formatted
✓ Readable on all backgrounds
✓ Positioned correctly (bottom-right)
```

### ✅ Language Switching Tests

#### Test 12: Bilingual Labels
```
Steps:
1. Enable AI layer (English mode)
2. Click marker → Note prediction labels
3. Click language toggle (EN → AR)
4. Click same marker → Note labels

Expected:
English: "Regenerative Adoption Prediction"
Arabic: "توقع اعتماد الزراعة التجديدية"

English: "Likely to Adopt"
Arabic: "محتمل الاعتماد"

Pass Criteria:
✓ Property labels switch language
✓ Prediction values switch language
✓ Legend switches language
✓ Village names remain Arabic
✓ Input features remain Arabic
```

#### Test 13: RTL Layout
```
Steps:
1. Switch to Arabic language
2. Check details panel layout
3. Check legend alignment

Expected:
- Details panel: Right-to-left text flow
- Legend: Text aligned right
- No text overflow or cutoff

Pass Criteria:
✓ RTL rendering correct
✓ No layout breaks
✓ All text visible
```

### ✅ Performance Tests

#### Test 14: Initial Load Time
```
Steps:
1. Clear browser cache
2. Refresh page
3. Measure time to first AI marker render

Target:
- < 2 seconds on fast connection
- < 5 seconds on slow connection

Pass Criteria:
✓ Load completes without errors
✓ No browser freezing
✓ Console shows: "✓ Loaded 5/5: regen" etc.
```

#### Test 15: Layer Toggle Performance
```
Steps:
1. Toggle AI layer on/off rapidly (5 times)
2. Observe smoothness

Expected:
- Instant on/off
- No lag or stutter
- No memory leaks
- Smooth animation

Pass Criteria:
✓ Toggle response < 100ms
✓ No console errors
✓ Memory usage stable
```

#### Test 16: Concurrent Layer Performance
```
Steps:
1. Enable all 4 AI layers simultaneously
2. Zoom in/out rapidly
3. Pan around map
4. Check frame rate

Expected:
- All 204 × 4 = 816 markers render
- No lag during zoom/pan
- Smooth interactions
- FPS > 30

Pass Criteria:
✓ No visible lag
✓ Interactions smooth
✓ No console warnings
✓ CPU usage reasonable
```

### ✅ Edge Case Tests

#### Test 17: Missing/Invalid Data
```
Steps:
1. Check rows 173, 202 (known bad data)
2. These have "Option 5" for Water_Availability

Expected:
- Markers display with gray color (fallback)
- No console errors
- Details panel shows raw value

Pass Criteria:
✓ Graceful degradation
✓ No crashes
✓ Gray color indicates error
```

#### Test 18: Boundary Visibility
```
Steps:
1. No AI layers → Boundary hidden
2. Enable any AI layer → Boundary appears
3. Disable all AI layers → Boundary hides

Expected:
- Dashed line around farmers region
- Light gray/black color
- Low opacity
- Updates automatically

Pass Criteria:
✓ Boundary syncs with AI layers
✓ Visible when needed
✓ Hidden when not needed
```

### ✅ Cross-Browser Tests

#### Test 19: Browser Compatibility
```
Test in:
- Chrome (latest)
- Firefox (latest)
- Edge (latest)
- Safari (if available)

Pass Criteria:
✓ Identical rendering
✓ Same colors
✓ Same interactions
✓ No browser-specific errors
```

### ✅ Regression Tests

#### Test 20: Old Layers Still Work
```
Steps:
1. Enable water-points layer
2. Enable energy-points layer
3. Verify no interference with AI layers

Expected:
- Old layers render normally
- Different visual style (larger, more opaque)
- Can enable old + AI simultaneously
- No conflicts

Pass Criteria:
✓ Old layers unchanged
✓ Old layer count badges work
✓ Old layer filtering works
✓ No console errors
```

---

## Common Issues & Solutions

### Issue 1: Gray Markers
**Symptom:** Some markers appear gray instead of red/green/yellow

**Diagnosis:**
```javascript
// Check browser console for:
console.log(feature.properties.Pred_Regen_Adoption);
// If undefined or wrong value → data issue
```

**Solution:** 
- Check source data for these features
- Verify property name spelling
- Check for null/missing values

### Issue 2: Legend Not Appearing
**Symptom:** AI layer enabled but no legend

**Diagnosis:**
```javascript
// Check layer visibility:
map.getLayoutProperty('ai-regen', 'visibility')
// Should return 'visible'
```

**Solution:**
- Verify updateAiBoundaryVisibility() is called
- Check updateLegend() function execution
- Inspect for CSS z-index conflicts

### Issue 3: Markers Too Small/Large
**Symptom:** Markers not visible or too big

**Diagnosis:**
- Check current zoom level
- Verify circle-radius expression

**Solution:**
- Adjust zoom-based radius stops in addAiHeatmapLayer
- Test at zoom levels 8-16

### Issue 4: Click Not Working
**Symptom:** Clicking marker doesn't open details

**Diagnosis:**
```javascript
// Check if click handler registered:
map.listens('click')
```

**Solution:**
- Verify bindPopup() called for AI layers
- Check feature.properties.featureId exists
- Inspect StateStore.getState()

---

## Performance Benchmarks

### Target Metrics
```
Load Time:        < 2s (204 features)
Render FPS:       > 30fps
Memory Usage:     < 100MB increase
Interaction Lag:  < 100ms
Layer Toggle:     < 50ms
```

### Measuring Performance
```javascript
// In browser console:

// 1. Measure load time
performance.mark('ai-start');
// Enable AI layer
performance.mark('ai-end');
performance.measure('ai-load', 'ai-start', 'ai-end');
console.log(performance.getEntriesByName('ai-load')[0].duration);

// 2. Check memory
console.memory.usedJSHeapSize / 1048576; // MB

// 3. Check feature count
map.getSource('ai-predictions')._data.features.length;
// Should be 204
```

---

## Success Criteria Summary

✅ **Visual:** Clear categorical colors, transparent markers, visible base map
✅ **Functional:** All 204 points clickable, details panel works
✅ **Performance:** Smooth interactions, fast loading
✅ **Bilingual:** Labels work in EN/AR, RTL correct
✅ **Production:** No errors, graceful degradation, proper error handling
✅ **UX:** Hover feedback, clear legend, intuitive categories

---

## Test Report Template

```markdown
# AI Layers Test Report

**Date:** [Date]
**Tester:** [Name]
**Browser:** [Chrome/Firefox/Edge] [Version]

## Test Results

### Visual Display
- [ ] Test 1: Layer Rendering
- [ ] Test 2: Transparency Check
- [ ] Test 3: Zoom Behavior

### Color Accuracy
- [ ] Test 4: Regenerative Colors
- [ ] Test 5: Water Risk Colors
- [ ] Test 6: Production Colors

### Interactions
- [ ] Test 7: Hover Behavior
- [ ] Test 8: Click Details
- [ ] Test 9: Multiple Scenarios

### Legend
- [ ] Test 10: Legend Display
- [ ] Test 11: Multiple Layers

### Language
- [ ] Test 12: Bilingual Labels
- [ ] Test 13: RTL Layout

### Performance
- [ ] Test 14: Initial Load
- [ ] Test 15: Toggle Speed
- [ ] Test 16: Concurrent Layers

### Edge Cases
- [ ] Test 17: Invalid Data
- [ ] Test 18: Boundary Sync

### Cross-Browser
- [ ] Test 19: Chrome
- [ ] Test 19: Firefox
- [ ] Test 19: Edge

### Regression
- [ ] Test 20: Old Layers Work

## Issues Found

[List any issues discovered]

## Overall Status

[ ] ✅ PASS - Production ready
[ ] ⚠️ MINOR ISSUES - Acceptable with notes
[ ] ❌ FAIL - Requires fixes

**Notes:**
[Additional comments]
```

---

**Testing Priority:** HIGH - This is production-grade code
**Estimated Testing Time:** 2-3 hours for complete validation
**Required:** Test on at least 2 browsers before deployment
