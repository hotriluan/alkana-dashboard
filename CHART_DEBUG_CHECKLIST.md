# Chart Bars Not Visible - Debug Checklist

## Current Status
- ✅ Build successful
- ✅ Frontend deployed  
- ✅ API returns 200 OK (2.8 kB data)
- ✅ Y-axis labels render (material names visible)
- ✅ XAxis configured with domain
- ✅ Bar components have fill colors
- ❌ Bars NOT visible

## Critical Data Needed

### 1. Get Actual API Response
```bash
# On Ubuntu server
curl -H "Authorization: Bearer $(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)" \
  "http://localhost:8000/api/v1/dashboards/inventory/top-movers-and-dead-stock?limit=10" | \
  python3 -m json.tool
```

### 2. Browser Network Tab Method
1. Open F12 DevTools
2. Network tab
3. Find request: `top-movers-and-dead-stock`
4. Click on it
5. Click "Response" sub-tab
6. Copy entire JSON
7. Check velocity_score values

## Known Issues to Check

### Issue 1: Date Range Too Narrow
- Screenshot shows date "01/02" (Feb 1st)
- If range is 1 day, velocity_score will be tiny
- Solution: Expand date range to 90 days

### Issue 2: Small Values
- Previous test showed velocity_score: 12 (vs expected 2494)
- With domain `[0, 'dataMax + 5']`, range is [0, 17]
- Small values might render but be visually imperceptible

### Issue 3: Bars Rendering Behind Elements
- Check z-index of chart container
- Check if parent has `overflow: hidden`

## Quick Fixes to Try

### Fix 1: Force Larger Domain
```tsx
<XAxis 
  type="number" 
  domain={[0, 100]}  // Force minimum scale
  ...
/>
```

### Fix 2: Add Min Bar Size
```tsx
<Bar 
  dataKey="velocity_score"
  minPointSize={5}  // Minimum 5px bar
  ...
/>
```

### Fix 3: Check Data Transform
Look for any `.filter()` or `.map()` that might remove/alter values

## Next Steps
1. Get actual API response JSON
2. Verify velocity_score values
3. Check date range in UI
4. Try expanding date range to see if bars appear
5. If values < 20, apply Fix 1 or Fix 2

## Code Files to Check
- `/web/src/pages/Inventory.tsx` - Date range defaults
- `/web/src/components/dashboard/inventory/InventoryTopMovers.tsx` - Chart rendering
- `/src/core/inventory_analytics.py` - Backend velocity calculation
