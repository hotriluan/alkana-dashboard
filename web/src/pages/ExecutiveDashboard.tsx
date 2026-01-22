// Executive Dashboard - High-level KPIs and business overview
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Users, Package, DollarSign, ShoppingCart, Factory, AlertCircle } from 'lucide-react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import api from '../services/api';
import { getFirstDayOfMonth, getToday } from '../utils/dateHelpers';
import { formatCurrencyCompact, formatCurrencyFull } from '../utils/formatters';
import { getDivisionName } from '../constants/chartColors';

interface ExecutiveKPIs {
  total_revenue: number;
  revenue_growth_pct: number;
  total_customers: number;
  active_customers: number;
  total_orders: number;
  completed_orders: number;
  completion_rate: number;
  total_inventory_value: number;
  inventory_items: number;
  total_ar: number;
  overdue_ar: number;
  overdue_pct: number;
}

interface RevenueByDivision extends Record<string, any> {
  division_code: string;
  revenue: number;
  customer_count: number;
  order_count: number;
}

interface TopCustomer {
  customer_name: string;
  revenue: number;
  order_count: number;
}

const ExecutiveDashboard = () => {
  const today = getToday();
  const firstDayOfMonth = getFirstDayOfMonth();
  const [startDate, setStartDate] = useState(firstDayOfMonth);
  const [endDate, setEndDate] = useState(today);

  const handleDateChange = (newStartDate: string, newEndDate: string) => {
    setStartDate(newStartDate);
    setEndDate(newEndDate);
  };

  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['executive-kpis', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<ExecutiveKPIs>(`/api/v1/dashboards/executive/summary?start_date=${startDate}&end_date=${endDate}`);
      return response.data;
    },
  });

  const { data: revenueByDivision, isLoading: divisionLoading } = useQuery({
    queryKey: ['executive-revenue-by-division', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<RevenueByDivision[]>(`/api/v1/dashboards/executive/revenue-by-division?start_date=${startDate}&end_date=${endDate}`);
      return response.data;
    },
  });

  const { data: topCustomers, isLoading: customersLoading } = useQuery({
    queryKey: ['executive-top-customers', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<TopCustomer[]>(`/api/v1/dashboards/executive/top-customers?limit=10&start_date=${startDate}&end_date=${endDate}`);
      return response.data;
    },
  });

  const formatNumber = (value: number) => {
    return value.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
  };

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  const customerColumns = [
    {
      key: 'customer_name' as keyof TopCustomer,
      header: 'Customer Name',
      sortable: true,
    },
    {
      key: 'revenue' as keyof TopCustomer,
      header: 'Revenue',
      align: 'right' as const,
      sortable: true,
      render: (value: number) => formatCurrencyFull(value),
    },
    {
      key: 'order_count' as keyof TopCustomer,
      header: 'Orders',
      align: 'right' as const,
      width: '100px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Executive Dashboard</h1>
          <div className="text-sm text-gray-500 mt-1">
            Last updated: {new Date().toLocaleString('vi-VN')}
          </div>
        </div>
        <DateRangePicker startDate={startDate} endDate={endDate} onDateChange={handleDateChange} />
      </div>

      {/* KPI Cards - Row 1: Revenue & Customers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Revenue"
          value={kpis ? formatCurrencyFull(kpis.total_revenue) : '0'}
          icon={<DollarSign className="h-6 w-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total Customers"
          value={kpis ? formatNumber(kpis.total_customers) : '0'}
          icon={<Users className="h-6 w-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total Orders"
          value={kpis ? formatNumber(kpis.total_orders) : '0'}
          icon={<ShoppingCart className="h-6 w-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Production Completion"
          value={kpis ? `${kpis.completion_rate}%` : '0%'}
          subtitle="Percentage of production orders marked as Delivered (DLV) or Technically Completed (TECO)."
          icon={<Factory className="h-6 w-6" />}
          loading={kpisLoading}
        />
      </div>

      {/* KPI Cards - Row 2: Inventory & AR */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Inventory Items"
          value={kpis ? formatNumber(kpis.inventory_items) : '0'}
          icon={<Package className="h-6 w-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total AR"
          value={kpis ? formatCurrencyFull(kpis.total_ar) : '0'}
          icon={<DollarSign className="h-6 w-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Overdue AR"
          value={kpis ? formatCurrencyFull(kpis.overdue_ar) : '0'}
          icon={<AlertCircle className="h-6 w-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Overdue %"
          value={kpis ? `${kpis.overdue_pct}%` : '0%'}
          icon={<TrendingUp className="h-6 w-6" />}
          loading={kpisLoading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue by Division - Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Division</h2>
          {divisionLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={revenueByDivision || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="division_code" 
                  tickFormatter={(code: string) => getDivisionName(code)} 
                  style={{ fontSize: '12px' }} 
                />
                <YAxis 
                  tickFormatter={(value: number) => formatCurrencyCompact(value)}
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  formatter={(value) => formatCurrencyFull(Number(value))}
                  labelFormatter={(label: string) => getDivisionName(label)}
                  contentStyle={{ fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="revenue" fill="#3b82f6" name="Revenue" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Revenue Distribution - Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue Distribution</h2>
          {divisionLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={revenueByDivision || []}
                  dataKey="revenue"
                  nameKey="division_code"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry: any) => {
                    return `${getDivisionName(entry.division_code)}: ${formatCurrencyCompact(entry.revenue)}`;
                  }}
                  labelLine={{ stroke: '#666', strokeWidth: 1 }}
                >
                  {(revenueByDivision || []).map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => formatCurrencyFull(Number(value))}
                  labelFormatter={(label: string) => getDivisionName(label)}
                  contentStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Top Customers Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Top 10 Customers by Revenue</h2>
        </div>
        <div className="p-6">
          <DataTable
            columns={customerColumns}
            data={topCustomers || []}
            loading={customersLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default ExecutiveDashboard;
