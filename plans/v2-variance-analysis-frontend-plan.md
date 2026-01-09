# V2 Production Yield Variance Analysis - Frontend Implementation Plan

**Date:** 2026-01-08  
**Module:** Production Yield V2  
**Component:** VarianceAnalysisTable.tsx  
**Status:** READY FOR IMPLEMENTATION

---

## 1. EXECUTIVE SUMMARY

### Objective
Build a React/TypeScript frontend component to display production yield variance data from the V2 API endpoint (`GET /api/v2/yield/variance`), following existing dashboard patterns in the Alkana codebase.

### Current State
- ✅ Backend V2 API complete and tested
- ✅ 606 production performance records available
- ✅ API supports date filtering and loss threshold filtering
- ✅ Response structure includes records, summary stats, date_range

### Deliverable
A professional data table component with:
- Default 30-day date range (matching API default)
- Date range picker for custom filtering
- Loss threshold slider/input
- Summary KPI cards
- Sortable data table
- Responsive design matching existing dashboards

---

## 2. API SPECIFICATION

### Endpoint
```
GET /api/v2/yield/variance
```

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | string | No | last 30 days | ISO format: YYYY-MM-DD |
| `end_date` | string | No | today | ISO format: YYYY-MM-DD |
| `loss_threshold` | number | No | 0 | Show only records with loss_pct > threshold |

### Response Structure
```typescript
interface VarianceAnalysisResponse {
  records: VarianceRecord[];
  summary: {
    total_records: number;
    avg_loss_pct: number;
    high_loss_count: number;
  };
  date_range: {
    start: string;
    end: string;
  };
}

interface VarianceRecord {
  process_order_id: string;
  batch_id: string;
  material_code: string;
  material_description: string;
  product_group_1: string | null;
  output_actual_kg: number;
  input_actual_kg: number;
  loss_kg: number;
  loss_pct: number;
  variant_fg_pct: number | null;
  posting_date: string; // ISO date
}
```

### Sample Response
```json
{
  "records": [
    {
      "process_order_id": "10000107994",
      "batch_id": "25L2485610",
      "material_code": "100000512.0",
      "material_description": "PUL-53306 AC EX CLEAR 10 VN-20LP",
      "product_group_1": null,
      "output_actual_kg": 820.0,
      "input_actual_kg": 820.0,
      "loss_kg": 820.0,
      "loss_pct": 100.0,
      "variant_fg_pct": null,
      "posting_date": "2026-01-08"
    }
  ],
  "summary": {
    "total_records": 606,
    "avg_loss_pct": 13.16,
    "high_loss_count": 11
  },
  "date_range": {
    "start": "2025-12-09",
    "end": "2026-01-08"
  }
}
```

---

## 3. COMPONENT ARCHITECTURE

### File Location
```
web/src/pages/VarianceAnalysisTable.tsx
```

### Component Structure
```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, AlertTriangle, Target, Factory } from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import api from '../services/api';
import { getToday } from '../utils/dateHelpers';

// TypeScript Interfaces (as defined above)

const VarianceAnalysisTable = () => {
  // State management
  // API integration
  // UI rendering
}

export default VarianceAnalysisTable;
```

---

## 4. STATE MANAGEMENT

### Local State (React useState)
```typescript
// Date range state (default: last 30 days)
const [startDate, setStartDate] = useState<string>(() => {
  const date = new Date();
  date.setDate(date.getDate() - 30);
  return date.toISOString().split('T')[0];
});
const [endDate, setEndDate] = useState<string>(getToday());

// Loss threshold filter (default: 0 = show all)
const [lossThreshold, setLossThreshold] = useState<number>(0);
```

### Data Fetching (React Query)
```typescript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['variance-analysis', startDate, endDate, lossThreshold],
  queryFn: async () => {
    const response = await api.get<VarianceAnalysisResponse>(
      '/api/v2/yield/variance',
      {
        params: {
          start_date: startDate,
          end_date: endDate,
          loss_threshold: lossThreshold
        }
      }
    );
    return response.data;
  },
  // Auto-refresh every 5 minutes (optional)
  refetchInterval: 300000,
  // Keep previous data while fetching new data
  keepPreviousData: true
});
```

**Benefits of React Query:**
- Automatic caching
- Background refetching
- Loading and error states
- Request deduplication
- Follows existing dashboard pattern (ProductionYield.tsx, Inventory.tsx)

---

## 5. UI COMPONENT LAYOUT

### Layout Structure
```
┌──────────────────────────────────────────────────────────────┐
│ Header                                                        │
│   Title: "Production Yield Variance Analysis"                │
│   DateRangePicker (right-aligned)                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Filter Controls                                               │
│   Loss Threshold Slider: [0]──●────[100%]                    │
│   Current: Show losses > 0%                                   │
└──────────────────────────────────────────────────────────────┘

┌────────────┬────────────┬────────────┬────────────────────────┐
│ KPI Cards (4 columns)                                         │
├────────────┼────────────┼────────────┼────────────────────────┤
│ Total      │ Avg Loss   │ High Loss  │ Date Range            │
│ Records    │ 13.16%     │ 11 Orders  │ 2025-12-09            │
│ 606        │            │ (>50%)     │ to 2026-01-08         │
└────────────┴────────────┴────────────┴────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Data Table (Sortable, Scrollable)                            │
├──────────┬──────────┬──────────┬─────────┬─────────┬─────────┤
│ Process  │ Batch    │ Material │ Output  │ Input   │ Loss %  │
│ Order    │ ID       │          │ (kg)    │ (kg)    │         │
├──────────┼──────────┼──────────┼─────────┼─────────┼─────────┤
│ 1000...  │ 25L...   │ 100...   │ 820.0   │ 820.0   │ 100.0%  │
│          │          │ PUL-53...│         │         │ 🔴      │
└──────────┴──────────┴──────────┴─────────┴─────────┴─────────┘
```

---

## 6. DETAILED IMPLEMENTATION SPECS

### 6.1 KPI Cards

**Card 1: Total Records**
```typescript
<KPICard
  title="Total Records"
  value={data?.summary.total_records.toLocaleString() ?? '0'}
  subtitle={`${data?.date_range.start} to ${data?.date_range.end}`}
  icon={<Factory className="w-6 h-6" />}
  trend="neutral"
/>
```

**Card 2: Average Loss**
```typescript
<KPICard
  title="Average Loss"
  value={`${data?.summary.avg_loss_pct.toFixed(2)}%`}
  subtitle="Production Variance"
  icon={<TrendingUp className="w-6 h-6" />}
  trend={data?.summary.avg_loss_pct > 10 ? "down" : "up"}
/>
```

**Card 3: High Loss Count**
```typescript
<KPICard
  title="High Loss Orders"
  value={data?.summary.high_loss_count.toString() ?? '0'}
  subtitle="Loss > 50%"
  icon={<AlertTriangle className="w-6 h-6" />}
  trend={data?.summary.high_loss_count > 5 ? "down" : "neutral"}
/>
```

**Card 4: Date Range Display**
```typescript
<KPICard
  title="Analysis Period"
  value={`${calculateDaysDifference(data?.date_range.start, data?.date_range.end)} days`}
  subtitle={`${data?.date_range.start} to ${data?.date_range.end}`}
  icon={<Target className="w-6 h-6" />}
/>
```

---

### 6.2 Loss Threshold Filter

```typescript
<div className="card">
  <div className="flex items-center justify-between mb-4">
    <h3 className="text-lg font-semibold text-slate-900">Filter by Loss Threshold</h3>
    <span className="text-sm text-slate-600">
      Showing: Loss &gt; {lossThreshold}%
    </span>
  </div>
  
  <div className="flex items-center gap-4">
    <input
      type="range"
      min="0"
      max="100"
      step="5"
      value={lossThreshold}
      onChange={(e) => setLossThreshold(Number(e.target.value))}
      className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
    />
    <input
      type="number"
      min="0"
      max="100"
      value={lossThreshold}
      onChange={(e) => setLossThreshold(Number(e.target.value))}
      className="w-20 px-3 py-2 border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
    <button
      onClick={() => setLossThreshold(0)}
      className="px-4 py-2 bg-slate-100 text-slate-700 rounded hover:bg-slate-200"
    >
      Reset
    </button>
  </div>
  
  {/* Quick preset buttons */}
  <div className="flex gap-2 mt-4">
    <button
      onClick={() => setLossThreshold(10)}
      className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
    >
      &gt; 10%
    </button>
    <button
      onClick={() => setLossThreshold(25)}
      className="px-3 py-1 text-sm bg-yellow-50 text-yellow-700 rounded hover:bg-yellow-100"
    >
      &gt; 25%
    </button>
    <button
      onClick={() => setLossThreshold(50)}
      className="px-3 py-1 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100"
    >
      &gt; 50%
    </button>
  </div>
</div>
```

---

### 6.3 Data Table Configuration

```typescript
const columns = [
  {
    key: 'process_order_id' as keyof VarianceRecord,
    header: 'Process Order',
    width: '130px',
    sortable: true,
  },
  {
    key: 'batch_id' as keyof VarianceRecord,
    header: 'Batch ID',
    width: '120px',
    sortable: true,
  },
  {
    key: 'material_code' as keyof VarianceRecord,
    header: 'Material',
    width: '120px',
    sortable: true,
  },
  {
    key: 'material_description' as keyof VarianceRecord,
    header: 'Description',
    sortable: true,
    render: (value: string) => (
      <div className="max-w-xs truncate" title={value}>
        {value}
      </div>
    ),
  },
  {
    key: 'product_group_1' as keyof VarianceRecord,
    header: 'Product Group',
    width: '120px',
    sortable: true,
    render: (value: string | null) => value ?? '-',
  },
  {
    key: 'output_actual_kg' as keyof VarianceRecord,
    header: 'Output (kg)',
    align: 'right' as const,
    width: '110px',
    sortable: true,
    render: (value: number) => value.toLocaleString('en-US', { maximumFractionDigits: 1 }),
  },
  {
    key: 'input_actual_kg' as keyof VarianceRecord,
    header: 'Input (kg)',
    align: 'right' as const,
    width: '110px',
    sortable: true,
    render: (value: number) => value.toLocaleString('en-US', { maximumFractionDigits: 1 }),
  },
  {
    key: 'loss_kg' as keyof VarianceRecord,
    header: 'Loss (kg)',
    align: 'right' as const,
    width: '110px',
    sortable: true,
    render: (value: number) => (
      <span className={value > 100 ? 'text-red-600 font-semibold' : ''}>
        {value.toLocaleString('en-US', { maximumFractionDigits: 1 })}
      </span>
    ),
  },
  {
    key: 'loss_pct' as keyof VarianceRecord,
    header: 'Loss %',
    align: 'right' as const,
    width: '100px',
    sortable: true,
    render: (value: number) => {
      const color = 
        value >= 50 ? 'text-red-600 font-bold' :
        value >= 25 ? 'text-orange-600 font-semibold' :
        value >= 10 ? 'text-yellow-600' :
        'text-green-600';
      
      return (
        <span className={color}>
          {value.toFixed(2)}%
        </span>
      );
    },
  },
  {
    key: 'posting_date' as keyof VarianceRecord,
    header: 'Posting Date',
    width: '120px',
    sortable: true,
    render: (value: string) => {
      const date = new Date(value);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },
  },
];
```

**Color Coding Logic:**
- 🟢 Green (0-10%): Normal/acceptable loss
- 🟡 Yellow (10-25%): Moderate loss - review
- 🟠 Orange (25-50%): High loss - investigate
- 🔴 Red (>50%): Critical loss - immediate action

---

### 6.4 Date Range Handler

```typescript
const handleDateChange = (newStartDate: string, newEndDate: string) => {
  setStartDate(newStartDate);
  setEndDate(newEndDate);
  // React Query will automatically refetch due to queryKey dependency
};
```

---

### 6.5 Loading & Error States

```typescript
// Loading state
if (isLoading) {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <div className="text-lg text-slate-600">Loading variance analysis...</div>
      </div>
    </div>
  );
}

// Error state
if (error) {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <div className="text-lg text-slate-900 mb-2">Error loading data</div>
        <div className="text-sm text-slate-600 mb-4">
          {error instanceof Error ? error.message : 'Unknown error occurred'}
        </div>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

// No data state
if (!data || data.records.length === 0) {
  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header with DateRangePicker */}
        <div className="text-center py-12">
          <Factory className="w-16 h-16 text-slate-400 mx-auto mb-4" />
          <div className="text-xl text-slate-600 mb-2">No variance data found</div>
          <div className="text-sm text-slate-500">
            Try adjusting your date range or lowering the loss threshold
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 7. UTILITY FUNCTIONS

### 7.1 Date Helper
```typescript
// Add to web/src/utils/dateHelpers.ts
export const getLast30Days = (): string => {
  const date = new Date();
  date.setDate(date.getDate() - 30);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const calculateDaysDifference = (startDate: string, endDate: string): number => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffTime = Math.abs(end.getTime() - start.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};
```

---

## 8. TYPESCRIPT TYPE DEFINITIONS

### Location: `web/src/types/index.ts`

Add the following interfaces to the existing types file:

```typescript
// V2 Production Yield Variance Analysis
export interface VarianceRecord {
  process_order_id: string;
  batch_id: string;
  material_code: string;
  material_description: string;
  product_group_1: string | null;
  output_actual_kg: number;
  input_actual_kg: number;
  loss_kg: number;
  loss_pct: number;
  variant_fg_pct: number | null;
  posting_date: string;
}

export interface VarianceAnalysisSummary {
  total_records: number;
  avg_loss_pct: number;
  high_loss_count: number;
}

export interface VarianceAnalysisDateRange {
  start: string;
  end: string;
}

export interface VarianceAnalysisResponse {
  records: VarianceRecord[];
  summary: VarianceAnalysisSummary;
  date_range: VarianceAnalysisDateRange;
}
```

---

## 9. ROUTING INTEGRATION

### Update: `web/src/App.tsx`

Add route for the new component:

```typescript
import VarianceAnalysisTable from './pages/VarianceAnalysisTable';

// Inside <Routes>
<Route
  path="/variance-analysis"
  element={
    <ProtectedRoute>
      <VarianceAnalysisTable />
    </ProtectedRoute>
  }
/>
```

### Update: `web/src/components/DashboardLayout.tsx`

Add navigation link:

```typescript
const navItems = [
  // ... existing items
  { name: 'Variance Analysis', path: '/variance-analysis', icon: TrendingUp },
];
```

---

## 10. TESTING STRATEGY

### 10.1 Manual Testing Checklist

**Data Fetching:**
- [ ] Default date range loads correctly (last 30 days)
- [ ] Custom date range filtering works
- [ ] Loss threshold filter correctly filters records
- [ ] API errors display error message
- [ ] Loading state shows spinner

**UI Behavior:**
- [ ] KPI cards display correct summary stats
- [ ] Table sorting works for all columns
- [ ] Table renders all columns correctly
- [ ] Color coding applies correctly to loss_pct column
- [ ] Date range picker updates data on Apply
- [ ] Reset button restores defaults

**Edge Cases:**
- [ ] Empty data state displays message
- [ ] Invalid date range (start > end) handled gracefully
- [ ] Network timeout displays error
- [ ] Very large datasets (>1000 records) perform well

### 10.2 Integration Testing

```bash
# Start backend server
cd alkana-dashboard
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn src.api.main:app --reload

# Start frontend dev server
cd web
npm run dev

# Navigate to: http://localhost:5173/variance-analysis
```

### 10.3 Test Data Scenarios

1. **Default View**: Should show 606 records (based on current data)
2. **High Loss Filter**: Set threshold to 50% → Should show 11 records
3. **Date Filter**: Single day (2026-01-08) → All 606 records
4. **Combined Filters**: Date range + loss threshold → Subset of records

---

## 11. PERFORMANCE CONSIDERATIONS

### 11.1 Optimization Strategies

**React Query Caching:**
- Cache key includes all filter parameters
- `keepPreviousData: true` prevents UI flashing during refetch
- Optional auto-refresh every 5 minutes

**Table Rendering:**
- DataTable component already optimized with virtualization
- Max height prevents excessive DOM nodes
- Sorting done in-memory (fast for <10,000 records)

**API Response Size:**
- Current dataset: 606 records ≈ 50KB JSON
- Consider pagination if dataset grows >5,000 records

### 11.2 Future Enhancements (V3)

- Server-side pagination (limit, offset params)
- Export to Excel/CSV
- Advanced filters (material code, batch ID search)
- Drill-down to batch details page
- Variance trend charts (time series)
- Batch comparison tool

---

## 12. IMPLEMENTATION CHECKLIST

### Phase 1: Setup (15 min)
- [ ] Create `web/src/pages/VarianceAnalysisTable.tsx`
- [ ] Add TypeScript interfaces to `web/src/types/index.ts`
- [ ] Update `web/src/utils/dateHelpers.ts` with new helpers

### Phase 2: Core Component (45 min)
- [ ] Implement state management (useState)
- [ ] Setup React Query data fetching
- [ ] Add loading/error/empty states
- [ ] Build basic layout structure

### Phase 3: UI Components (60 min)
- [ ] Implement 4 KPI cards
- [ ] Build loss threshold filter with slider
- [ ] Configure DataTable with all columns
- [ ] Add DateRangePicker integration
- [ ] Apply color coding to loss_pct column

### Phase 4: Integration (30 min)
- [ ] Add route to App.tsx
- [ ] Add navigation link to DashboardLayout.tsx
- [ ] Test with local backend server
- [ ] Verify all filters work correctly

### Phase 5: Testing & Polish (30 min)
- [ ] Manual testing of all features
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Responsive design check (mobile, tablet, desktop)
- [ ] Error handling verification
- [ ] Code review and cleanup

**Total Estimated Time:** 3 hours

---

## 13. CODE QUALITY STANDARDS

### Follows Existing Patterns
- ✅ Uses React Query (@tanstack/react-query)
- ✅ Uses existing UI components (KPICard, DataTable, DateRangePicker)
- ✅ Uses Axios API client (web/src/services/api.ts)
- ✅ Uses Lucide icons
- ✅ Uses Tailwind CSS for styling
- ✅ TypeScript strict mode compliance
- ✅ Follows component structure from ProductionYield.tsx and Inventory.tsx

### Best Practices
- Single Responsibility: Component focuses on display, React Query handles data
- DRY: Reuses existing components and utilities
- Type Safety: Full TypeScript coverage
- Error Handling: Comprehensive error states
- User Experience: Loading states, empty states, helpful messages
- Performance: Optimized rendering, caching, memoization

---

## 14. DEPENDENCIES (Already Installed)

```json
{
  "@tanstack/react-query": "^5.x",
  "axios": "^1.x",
  "lucide-react": "^0.x",
  "recharts": "^2.x",
  "react": "^18.x",
  "react-router-dom": "^6.x",
  "tailwindcss": "^3.x"
}
```

No new dependencies required! ✅

---

## 15. EXAMPLE: FULL COMPONENT SKELETON

```typescript
// web/src/pages/VarianceAnalysisTable.tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, AlertTriangle, Target, Factory } from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import api from '../services/api';
import { getToday, getLast30Days, calculateDaysDifference } from '../utils/dateHelpers';

// [TypeScript interfaces here]

const VarianceAnalysisTable = () => {
  // [State management]
  const [startDate, setStartDate] = useState(getLast30Days());
  const [endDate, setEndDate] = useState(getToday());
  const [lossThreshold, setLossThreshold] = useState(0);

  // [React Query data fetching]
  const { data, isLoading, error, refetch } = useQuery({...});

  // [Event handlers]
  const handleDateChange = (newStart: string, newEnd: string) => {...};

  // [Loading/Error/Empty states]
  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!data?.records.length) return <EmptyState />;

  // [Main render]
  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header with DateRangePicker */}
        {/* Loss Threshold Filter */}
        {/* KPI Cards Grid */}
        {/* Data Table */}
      </div>
    </div>
  );
};

export default VarianceAnalysisTable;
```

---

## 16. SUCCESS CRITERIA

### Functional Requirements
- ✅ Displays all 606 production variance records by default
- ✅ Filters by date range (start_date, end_date)
- ✅ Filters by loss threshold (loss_pct > threshold)
- ✅ Shows summary KPIs (total, avg loss, high loss count)
- ✅ Sortable table with all required columns
- ✅ Color-coded loss percentages for visual scanning

### Non-Functional Requirements
- ✅ Loads in <2 seconds with backend running
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Accessible (keyboard navigation, screen reader friendly)
- ✅ Consistent with existing dashboard UI/UX
- ✅ Error handling for network failures
- ✅ TypeScript type safety (no `any` types)

### User Experience
- ✅ Intuitive controls (slider + number input for threshold)
- ✅ Clear visual feedback (loading spinner, error messages)
- ✅ Helpful empty states ("No data found - adjust filters")
- ✅ Professional design matching Alkana branding

---

## 17. ROLLOUT PLAN

### Development Environment
1. Implement component in feature branch
2. Test with local backend (`uvicorn src.api.main:app --reload`)
3. Verify all features work correctly
4. Code review and approval

### Staging Environment
1. Deploy backend V2 API to staging
2. Deploy frontend build to staging
3. Integration testing with staging database
4. User acceptance testing (UAT)

### Production Environment
1. Deploy backend API (ensure backwards compatibility)
2. Deploy frontend build
3. Monitor error logs and performance metrics
4. Gather user feedback

---

## 18. DOCUMENTATION UPDATES

After implementation, update:

1. **README.md**: Add Variance Analysis to feature list
2. **docs/api-reference.md**: Document V2 endpoint (if exists)
3. **docs/user-guide.md**: Add usage instructions for Variance Analysis dashboard
4. **CHANGELOG.md**: Record feature addition

---

## 19. SUPPORT & MAINTENANCE

### Known Limitations
- Single date (all records 2026-01-08) - need historical data for trend analysis
- No drill-down to batch details (future enhancement)
- No export functionality (planned for V3)

### Monitoring
- Track API response times in production
- Monitor React Query cache performance
- Watch for user-reported issues

### Future Roadmap (V3)
- Add batch detail modal/page
- Implement server-side pagination
- Add CSV/Excel export
- Create variance trend charts
- Add material-level aggregations
- Implement batch comparison tool

---

## 20. CONTACTS & REFERENCES

### Key Documents
- [v2_api_test_results.md](../v2_api_test_results.md) - API test results and examples
- [docs/codebase-summary.md](../docs/codebase-summary.md) - Architecture overview
- [web/src/pages/ProductionYield.tsx](../web/src/pages/ProductionYield.tsx) - Reference component

### Backend Reference
- API Router: `src/api/routers/yield_dashboard.py` (assumed location)
- Database Table: `fact_production_performance_v2`
- Total Records: 606

---

**Plan Status:** APPROVED ✅  
**Ready for Implementation:** YES  
**Estimated Development Time:** 3 hours  
**Risk Level:** LOW (follows proven patterns, backend tested)  

---

**Prepared by:** PLANNER Agent  
**Date:** 2026-01-08  
**Review Required:** Senior Frontend Developer  
**Next Action:** Assign to Frontend Developer for implementation
