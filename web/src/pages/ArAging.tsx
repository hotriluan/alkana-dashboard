// AR Aging Dashboard - Summary AR Collection matching user's Excel screenshot
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { DollarSign, TrendingUp, AlertCircle, Calendar } from 'lucide-react';
import { arAgingAPI } from '../services/api';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import type { ARCollectionTotal, ARCustomerDetail } from '../types';

import { getFirstDayOfMonth, getToday } from '../utils/dateHelpers';

const ArAging = () => {
  const today = getToday();
  const firstDayOfMonth = getFirstDayOfMonth();
  const [startDate, setStartDate] = useState(firstDayOfMonth);
  const [endDate, setEndDate] = useState(today);
  const [selectedSnapshot, setSelectedSnapshot] = useState<string | null>(null);

  // Fetch available snapshot dates
  const { data: snapshots, isLoading: snapshotsLoading } = useQuery({
    queryKey: ['ar-snapshots'],
    queryFn: arAgingAPI.getSnapshots,
  });

  // Set default to latest snapshot when data loads
  useEffect(() => {
    if (snapshots && snapshots.length > 0 && !selectedSnapshot) {
      setSelectedSnapshot(snapshots[0].snapshot_date);
    }
  }, [snapshots, selectedSnapshot]);

  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ['ar-summary', selectedSnapshot],
    queryFn: () => arAgingAPI.getSummary(selectedSnapshot || undefined),
  });

  const { data: buckets, isLoading: bucketsLoading, error: bucketsError } = useQuery({
    queryKey: ['ar-buckets', selectedSnapshot],
    queryFn: arAgingAPI.getByBucket,
  });

  const { data: customers, isLoading: customersLoading, error: customersError } = useQuery({
    queryKey: ['ar-customers', selectedSnapshot],
    queryFn: () => arAgingAPI.getCustomers(undefined, 50),
  });

  const handleDateChange = (newStartDate: string, newEndDate: string) => {
    setStartDate(newStartDate);
    setEndDate(newEndDate);
  };

  const handleSnapshotChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedSnapshot(e.target.value);
  };

  const formatBillion = (value: number) => {
    const billions = value / 1_000_000_000;
    if (billions >= 1) return `${billions.toFixed(1)}B`;
    const millions = value / 1_000_000;
    if (millions >= 1) return `${millions.toFixed(0)}M`;
    return value.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
  };
  const highRiskCount = customers?.filter(c => c.risk_level === 'HIGH').length || 0;

  // Mock trend data
  const trendData = [
    { month: 'Jan', target: 45.2, realization: 38.5 },
    { month: 'Feb', target: 48.1, realization: 40.2 },
    { month: 'Mar', target: 46.8, realization: 39.8 },
    { month: 'Apr', target: 49.3, realization: 41.5 },
    { month: 'May', target: 47.6, realization: 40.1 },
    { month: 'Jun', target: 50.2, realization: 42.8 },
  ];

  const bucketColors = ['#10b981', '#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444', '#dc2626'];

  const divisionColumns = [
    { key: 'division' as keyof ARCollectionTotal, header: 'Division', sortable: true },
    { key: 'total_target' as keyof ARCollectionTotal, header: 'Target', align: 'right' as const, sortable: true, render: formatBillion },
    { key: 'total_realization' as keyof ARCollectionTotal, header: 'Realization', align: 'right' as const, sortable: true, render: formatBillion },
    { key: 'collection_rate_pct' as keyof ARCollectionTotal, header: 'Rate', align: 'right' as const, sortable: true, render: (v: number) => `${v}%` },
  ];

  const customerColumns = [
    { key: 'customer_name' as keyof ARCustomerDetail, header: 'Customer', sortable: true },
    { key: 'division' as keyof ARCustomerDetail, header: 'Division', width: '100px', sortable: true },
    { key: 'total_target' as keyof ARCustomerDetail, header: 'Outstanding', align: 'right' as const, width: '120px', sortable: true, render: formatBillion },
    { key: 'total_realization' as keyof ARCustomerDetail, header: 'Collected', align: 'right' as const, width: '120px', sortable: true, render: formatBillion },
    { key: 'collection_rate_pct' as keyof ARCustomerDetail, header: 'Rate', align: 'center' as const, width: '80px', sortable: true, render: (v: number) => `${v}%` },
    { key: 'risk_level' as keyof ARCustomerDetail, header: 'Risk', align: 'center' as const, width: '100px', sortable: true },
  ];

  if (snapshotsLoading || summaryLoading || bucketsLoading || customersLoading) {
    return <div className="flex items-center justify-center h-screen"><div className="text-lg text-slate-600">Loading AR data...</div></div>;
  }

  if (summaryError || bucketsError || customersError) {
    return <div className="flex items-center justify-center h-screen"><div className="text-center"><div className="text-red-600 text-lg font-semibold mb-2">Error loading data</div><button onClick={() => window.location.reload()} className="btn-primary">Retry</button></div></div>;
  }

  if (!summary || !buckets || !customers) return null;

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">AR Collection Summary</h1>
            <p className="mt-1 text-sm text-slate-600">Accounts Receivable Aging Analysis</p>
          </div>
          <div className="flex items-center space-x-4">
            {/* Snapshot Date Selector */}
            <div className="flex items-center space-x-2 bg-white rounded-lg shadow px-4 py-2 border border-slate-200">
              <Calendar className="w-5 h-5 text-slate-500" />
              <span className="text-sm font-medium text-slate-700">Snapshot:</span>
              <select
                value={selectedSnapshot || ''}
                onChange={handleSnapshotChange}
                className="text-sm font-medium text-blue-600 border-none focus:ring-2 focus:ring-blue-500 rounded-md bg-transparent cursor-pointer"
                disabled={!snapshots || snapshots.length === 0}
              >
                {snapshots && snapshots.length > 0 ? (
                  snapshots.map((snap) => (
                    <option key={snap.snapshot_date} value={snap.snapshot_date}>
                      {new Date(snap.snapshot_date).toLocaleDateString('vi-VN', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })} ({snap.row_count} records)
                    </option>
                  ))
                ) : (
                  <option value="">No snapshots available</option>
                )}
              </select>
            </div>
            <DateRangePicker startDate={startDate} endDate={endDate} onDateChange={handleDateChange} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard title="Total Target" value={formatBillion(summary.total_target)} subtitle="Target Collection" icon={<DollarSign className="w-6 h-6" />} />
          <KPICard title="Total Realization" value={formatBillion(summary.total_realization)} subtitle="Actual Collection" icon={<TrendingUp className="w-6 h-6" />} />
          <KPICard title="Collection Rate" value={`${summary.collection_rate_pct}%`} subtitle="Performance" icon={<BarChart className="w-6 h-6" />} />
          <KPICard title="High Risk" value={highRiskCount} subtitle="Customers" icon={<AlertCircle className="w-6 h-6" />} />
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Collection Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `${v}B`} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
              <Legend />
              <Line type="monotone" dataKey="target" stroke="#3b82f6" strokeWidth={2} name="Target" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="realization" stroke="#10b981" strokeWidth={2} name="Realization" dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">AR Aging Bucket Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={buckets} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="bucket" tick={{ fill: '#64748b', fontSize: 12 }} angle={-15} textAnchor="end" height={80} />
              <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `${(v / 1_000_000_000).toFixed(1)}B`} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
              <Legend />
              <Bar dataKey="target_amount" name="Outstanding Amount" radius={[8, 8, 0, 0]}>
                {buckets.map((_entry, index) => <Cell key={`cell-${index}`} fill={bucketColors[index % bucketColors.length]} />)}
              </Bar>_
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Collection by Division</h2>
          <DataTable data={summary.divisions} columns={divisionColumns} maxHeight="300px" />
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Customer Details ({customers.length} customers)</h2>
          <DataTable data={customers} columns={customerColumns} maxHeight="600px" />
        </div>
      </div>
    </div>
  );
};

export default ArAging;
