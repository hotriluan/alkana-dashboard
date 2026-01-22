// Inventory Dashboard - Current stock levels and movements
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Package, Factory, Layers, Weight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import InventoryTopMovers from '../components/dashboard/inventory/InventoryTopMovers';
import api from '../services/api';
import { getFirstDayOfMonth, getToday } from '../utils/dateHelpers';

interface InventoryKPI { total_items: number; total_materials: number; total_plants: number; total_qty_kg: number; }
interface InventoryItem { plant_code: string; material_code: string; material_description: string; current_qty: number; current_qty_kg: number; uom: string; last_movement: string; }
interface PlantInventory { plant_code: string; item_count: number; total_kg: number; }

const Inventory = () => {
  const today = getToday();
  const firstDayOfMonth = getFirstDayOfMonth();
  const [startDate, setStartDate] = useState(firstDayOfMonth);
  const [endDate, setEndDate] = useState(today);
  const [category, setCategory] = useState<string>('ALL_CORE');

  const { data: kpis, isLoading: kpisLoading } = useQuery({ queryKey: ['inventory-kpis', startDate, endDate], queryFn: async () => (await api.get<InventoryKPI>('/api/v1/dashboards/inventory/summary', { params: { start_date: startDate, end_date: endDate } })).data });
  const { data: items, isLoading: itemsLoading } = useQuery({ queryKey: ['inventory-items', startDate, endDate], queryFn: async () => (await api.get<InventoryItem[]>('/api/v1/dashboards/inventory/items?limit=100', { params: { start_date: startDate, end_date: endDate } })).data });
  const { data: byPlant, isLoading: plantsLoading } = useQuery({ queryKey: ['inventory-by-plant', startDate, endDate], queryFn: async () => (await api.get<PlantInventory[]>('/api/v1/dashboards/inventory/by-plant', { params: { start_date: startDate, end_date: endDate } })).data });

  // Flow trends from backend API
  const { data: flowTrends, isLoading: flowTrendsLoading } = useQuery({
    queryKey: ['inventory-flow-trends', startDate, endDate],
    queryFn: async () => (await api.get('/api/v1/dashboards/inventory/flow-trends', {
      params: { start_date: startDate, end_date: endDate }
    })).data
  });

  // NEW: Top Movers and Dead Stock Analysis
  const { data: topMoversData, isLoading: topMoversLoading } = useQuery({
    queryKey: ['inventory-top-movers', startDate, endDate, category],
    queryFn: async () => (await api.get('/api/v1/dashboards/inventory/top-movers-and-dead-stock', {
      params: { start_date: startDate, end_date: endDate, limit: 10, category }
    })).data
  });

  const handleDateChange = (newStartDate: string, newEndDate: string) => { setStartDate(newStartDate); setEndDate(newEndDate); };
  const fmt = (v: number) => {
    const thousands = v / 1000;
    if (thousands >= 1) return `${thousands.toFixed(1)}K`;
    return v.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
  };
  const fmtKg = (v: number) => {
    const thousands = v / 1000;
    if (thousands >= 1) return `${thousands.toFixed(1)}K kg`;
    return `${v.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} kg`;
  };

  // Use real API data or fallback to empty array
  const flowTrendData = flowTrends || [];

  const itemColumns = [
    { key: 'material_code' as keyof InventoryItem, header: 'Material', width: '120px', sortable: true },
    { key: 'material_description' as keyof InventoryItem, header: 'Description', sortable: true },
    { key: 'plant_code' as keyof InventoryItem, header: 'Plant', width: '80px', sortable: true },
    { key: 'current_qty_kg' as keyof InventoryItem, header: 'Net Change (kg)', align: 'right' as const, width: '140px', sortable: true, render: (v: number) => {
      const sign = v >= 0 ? '+' : '';
      return `${sign}${fmtKg(v)}`;
    }},
    { key: 'current_qty' as keyof InventoryItem, header: 'Transactions', align: 'right' as const, width: '100px', sortable: true, render: (v: number) => fmt(Math.abs(v)) },
    { key: 'last_movement' as keyof InventoryItem, header: 'Last Active', width: '120px', sortable: true, render: (v: string) => new Date(v).toLocaleDateString('vi-VN') },
  ];

  const plantColumns = [
    { key: 'plant_code' as keyof PlantInventory, header: 'Plant', sortable: true },
    { key: 'item_count' as keyof PlantInventory, header: 'Items', align: 'right' as const, sortable: true, render: fmt },
    { key: 'total_kg' as keyof PlantInventory, header: 'Total Weight', align: 'right' as const, sortable: true, render: fmtKg },
  ];

  if (kpisLoading || itemsLoading || plantsLoading || flowTrendsLoading) return <div className="flex items-center justify-center h-screen"><div className="text-lg text-slate-600">Loading inventory...</div></div>;
  if (!kpis || !items || !byPlant) return <div className="flex items-center justify-center h-screen"><div className="text-center"><div className="text-lg text-slate-600 mb-4">No data available</div><button onClick={() => window.location.reload()} className="btn-primary">Reload</button></div></div>;

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Inventory Movement Dashboard</h1>
            <p className="mt-1 text-sm text-slate-600">Transaction flow analysis - Data from MB51 movements. Net changes within selected period.</p>
          </div>
          <DateRangePicker startDate={startDate} endDate={endDate} onDateChange={handleDateChange} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard title="Total Throughput" value={fmtKg(kpis.total_qty_kg)} subtitle="Weight Handled (In + Out)" icon={<Weight className="w-6 h-6" />} />
          <KPICard title="Active Items" value={fmt(kpis.total_materials)} subtitle="Materials with Transactions" icon={<Layers className="w-6 h-6" />} />
          <KPICard title="Plants" value={fmt(kpis.total_plants)} subtitle="Locations" icon={<Factory className="w-6 h-6" />} />
          <KPICard title="Transaction Count" value={fmt(kpis.total_items)} subtitle="Total Movements" icon={<Package className="w-6 h-6" />} />
        </div>

        {/* ========== ZONE 1: NEW VISUAL INTELLIGENCE ========== */}
        <div className="mb-8">
          <InventoryTopMovers 
            topMovers={topMoversData?.top_movers || []} 
            deadStock={topMoversData?.dead_stock || []} 
            loading={topMoversLoading} 
            dateRange={{ from: new Date(startDate), to: new Date(endDate) }}
            selectedCategory={category}
            onCategoryChange={setCategory}
          />
        </div>

        {/* ========== ZONE 2: FLOW ANALYSIS CHARTS & TABLES ========== */}
        <div className="card">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Inbound vs Outbound Flow Trends</h2>
          <p className="text-sm text-slate-600 mb-4">Movement activity over time - Green: receipts, Red: issues</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={flowTrendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="period" tick={{ fill: '#64748b', fontSize: 12 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
              <Legend />
              <Bar dataKey="inbound" fill="#10b981" name="Inbound (kg)" radius={[8, 8, 0, 0]} />
              <Bar dataKey="outbound" fill="#ef4444" name="Outbound (kg)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Activity Intensity by Plant</h2>
          <p className="text-sm text-slate-600 mb-4">Transaction volume showing warehouse workload</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={byPlant} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="plant_code" tick={{ fill: '#64748b', fontSize: 12 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
              <Legend />
              <Bar dataKey="item_count" fill="#3b82f6" name="Transaction Count" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Activity by Plant</h2>
          <DataTable data={byPlant} columns={plantColumns} maxHeight="300px" />
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Material Movement Analysis ({items.length} materials)</h2>
          <p className="text-sm text-slate-600 mb-4">Net change = Sum of all movements (positive = more in than out)</p>
          <DataTable data={items} columns={itemColumns} maxHeight="600px" />
        </div>
      </div>
    </div>
  );
};

export default Inventory;
