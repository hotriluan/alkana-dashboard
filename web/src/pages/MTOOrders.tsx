// MTO Orders Dashboard - Make-to-Order production tracking
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { BarChart, Bar, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import api from '../services/api';

interface MTOKPIs { total_orders: number; completed_orders: number; partial_orders: number; pending_orders: number; completion_rate: number; }
interface MTOOrder { plant_code: string; sales_order: string; order_number: string; material_code: string; material_description: string; order_qty: number; delivered_qty: number; uom: string; status: string; release_date: string | null; actual_finish_date: string | null; }

const MTOOrders = () => {
  const today = new Date().toISOString().split('T')[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(thirtyDaysAgo);
  const [endDate, setEndDate] = useState(today);

  const { data: kpis, isLoading: kpisLoading } = useQuery({ queryKey: ['mto-kpis', startDate, endDate], queryFn: async () => (await api.get<MTOKPIs>('/api/v1/dashboards/mto-orders/summary', { params: { start_date: startDate, end_date: endDate } })).data });
  const { data: orders, isLoading: ordersLoading } = useQuery({ queryKey: ['mto-orders', startDate, endDate], queryFn: async () => (await api.get<MTOOrder[]>('/api/v1/dashboards/mto-orders/orders?limit=100', { params: { start_date: startDate, end_date: endDate } })).data });

  const handleDateChange = (newStartDate: string, newEndDate: string) => { setStartDate(newStartDate); setEndDate(newEndDate); };
  const fmt = (v: number) => v.toLocaleString('vi-VN', { maximumFractionDigits: 0 });

  const statusData = [
    { status: 'COMPLETE', count: kpis?.completed_orders || 0, fill: '#10b981' },
    { status: 'PARTIAL', count: kpis?.partial_orders || 0, fill: '#f59e0b' },
    { status: 'PENDING', count: kpis?.pending_orders || 0, fill: '#3b82f6' },
  ];

  const trendData = [
    { month: 'Jan', completed: 85, pending: 15 }, { month: 'Feb', completed: 88, pending: 12 },
    { month: 'Mar', completed: 82, pending: 18 }, { month: 'Apr', completed: 90, pending: 10 },
    { month: 'May', completed: 87, pending: 13 }, { month: 'Jun', completed: 92, pending: 8 },
  ];

  const orderColumns = [
    { key: 'sales_order' as keyof MTOOrder, header: 'Sales Order', width: '120px', sortable: true },
    { key: 'order_number' as keyof MTOOrder, header: 'Prod Order', width: '140px', sortable: true },
    { key: 'material_code' as keyof MTOOrder, header: 'Material', width: '120px', sortable: true },
    { key: 'material_description' as keyof MTOOrder, header: 'Description', sortable: true },
    { key: 'plant_code' as keyof MTOOrder, header: 'Plant', width: '80px', sortable: true },
    { key: 'order_qty' as keyof MTOOrder, header: 'Order Qty', align: 'right' as const, width: '100px', sortable: true, render: (v: number, row: MTOOrder) => `${fmt(v)} ${row.uom}` },
    { key: 'delivered_qty' as keyof MTOOrder, header: 'Delivered', align: 'right' as const, width: '100px', sortable: true, render: (v: number, row: MTOOrder) => `${fmt(v)} ${row.uom}` },
    { key: 'status' as keyof MTOOrder, header: 'Status', align: 'center' as const, width: '100px', sortable: true, render: (v: string) => {
      const colors = { COMPLETE: 'bg-green-100 text-green-700', PARTIAL: 'bg-yellow-100 text-yellow-700', PENDING: 'bg-blue-100 text-blue-700' };
      return <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[v as keyof typeof colors] || 'bg-gray-100 text-gray-700'}`}>{v}</span>;
    }},
    { key: 'release_date' as keyof MTOOrder, header: 'Release Date', width: '120px', sortable: true, render: (v: string | null) => v ? new Date(v).toLocaleDateString('vi-VN') : '-' },
  ];

  if (kpisLoading || ordersLoading) return <div className="flex items-center justify-center h-screen"><div className="text-lg text-slate-600">Loading MTO orders...</div></div>;
  if (!kpis || !orders) return <div className="flex items-center justify-center h-screen"><div className="text-center"><div className="text-lg text-slate-600 mb-4">No data available</div><button onClick={() => window.location.reload()} className="btn-primary">Reload</button></div></div>;

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">MTO Orders Dashboard</h1>
            <p className="mt-1 text-sm text-slate-600">Make-to-Order production tracking</p>
          </div>
          <DateRangePicker startDate={startDate} endDate={endDate} onDateChange={handleDateChange} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard title="Total Orders" value={fmt(kpis.total_orders)} subtitle="MTO Production Orders" icon={<FileText className="w-6 h-6" />} />
          <KPICard title="Completed" value={fmt(kpis.completed_orders)} subtitle={`${kpis.completion_rate}% completion`} icon={<CheckCircle className="w-6 h-6" />} trend={kpis.completion_rate >= 80 ? 'up' : kpis.completion_rate >= 60 ? 'neutral' : 'down'} />
          <KPICard title="Partial Delivery" value={fmt(kpis.partial_orders)} subtitle="In Progress" icon={<Clock className="w-6 h-6" />} />
          <KPICard title="Pending" value={fmt(kpis.pending_orders)} subtitle="Not Started" icon={<AlertCircle className="w-6 h-6" />} />
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Order Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={statusData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="status" tick={{ fill: '#64748b', fontSize: 12 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
              <Legend />
              <Bar dataKey="count" name="Order Count" radius={[8, 8, 0, 0]}>
                {statusData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Completion Rate Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `${v}%`} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
              <Legend />
              <Line type="monotone" dataKey="completed" stroke="#10b981" strokeWidth={2} name="Completed %" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="pending" stroke="#f59e0b" strokeWidth={2} name="Pending %" dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Production Orders ({orders.length} records)</h2>
          <DataTable data={orders} columns={orderColumns} maxHeight="600px" />
        </div>
      </div>
    </div>
  );
};

export default MTOOrders;
