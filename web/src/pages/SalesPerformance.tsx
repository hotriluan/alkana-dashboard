// Sales Performance Dashboard - Customer and division sales tracking
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DollarSign, Users, ShoppingCart, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import MonthlySalesChart from '../components/dashboard/sales/monthly-sales-chart';
import CustomerSegmentationScatter from '../components/dashboard/sales/CustomerSegmentationScatter';
import { getDivisionName } from '../constants/chartColors';
import api from '../services/api';
import { formatCurrencyCompact, formatCurrencyFull } from '../utils/formatters';

interface SalesKPIs {
  total_sales: number;
  total_customers: number;
  avg_order_value: number;
  total_orders: number;
}

interface SalesRecord {
  customer_name: string;
  division_code: string;
  sales_amount: number;
  sales_qty: number;
  order_count: number;
  avg_order_value: number;
}

interface DivisionSales {
  division_code: string;
  customer_count: number;
  total_sales: number;
  total_orders: number;
  avg_order_value: number;
}

import { getFirstDayOfMonth, getToday } from '../utils/dateHelpers';

const SalesPerformance = () => {
  const today = getToday();
  const firstDayOfMonth = getFirstDayOfMonth();
  const [startDate, setStartDate] = useState(firstDayOfMonth);
  const [endDate, setEndDate] = useState(today);

  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['sales-kpis', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<SalesKPIs>('/api/v1/dashboards/sales/summary', {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    },
  });

  const { data: customers, isLoading: customersLoading } = useQuery({
    queryKey: ['sales-customers', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<SalesRecord[]>('/api/v1/dashboards/sales/customers?limit=100', {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    },
  });

  const { data: byDivision, isLoading: divisionLoading } = useQuery({
    queryKey: ['sales-by-division', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<DivisionSales[]>('/api/v1/dashboards/sales/by-division', {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    },
  });

  // NEW: Customer Segmentation for Visual Intelligence
  const { data: segmentationData, isLoading: segmentationLoading } = useQuery({
    queryKey: ['customer-segmentation', startDate, endDate],
    queryFn: async () => (await api.get('/api/v1/dashboards/sales/segmentation', {
      params: { start_date: startDate, end_date: endDate }
    })).data
  });

  const handleDateChange = (newStartDate: string, newEndDate: string) => {
    setStartDate(newStartDate);
    setEndDate(newEndDate);
  };

  // Deprecated local formatter replaced by standardized utilities
  const formatCurrency = (value: number) => formatCurrencyFull(value);

  const formatNumber = (value: number) => {
    return value.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
  };

  const customerColumns = [
    {
      key: 'customer_name' as keyof SalesRecord,
      header: 'Customer Name',
      sortable: true,
    },
    {
      key: 'division_code' as keyof SalesRecord,
      header: 'Division',
      width: '140px',
      sortable: true,
      render: (value: string | number) => (
        <span className="font-medium">
          {getDivisionName(value)}
          <span className="text-xs text-gray-400 ml-1">({value})</span>
        </span>
      ),
    },
    {
      key: 'sales_amount' as keyof SalesRecord,
      header: 'Sales Amount',
      align: 'right' as const,
      width: '140px',
      sortable: true,
      render: (value: number) => formatCurrencyFull(value),
    },
    {
      key: 'sales_qty' as keyof SalesRecord,
      header: 'Sales Qty',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'order_count' as keyof SalesRecord,
      header: 'Orders',
      align: 'right' as const,
      width: '80px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'avg_order_value' as keyof SalesRecord,
      header: 'Avg Order Value',
      align: 'right' as const,
      width: '140px',
      sortable: true,
      render: (value: number) => formatCurrencyFull(value),
    },
  ];

  const divisionColumns = [
    {
      key: 'division_code' as keyof DivisionSales,
      header: 'Division',
      width: '140px',
      sortable: true,
      render: (value: string | number) => (
        <span className="font-medium">
          {getDivisionName(value)}
          <span className="text-xs text-gray-400 ml-1">({value})</span>
        </span>
      ),
    },
    {
      key: 'customer_count' as keyof DivisionSales,
      header: 'Customers',
      align: 'right' as const,
      width: '100px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'total_orders' as keyof DivisionSales,
      header: 'Total Orders',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'total_sales' as keyof DivisionSales,
      header: 'Total Sales',
      align: 'right' as const,
      width: '140px',
      sortable: true,
      render: (value: number) => formatCurrencyFull(value),
    },
    {
      key: 'avg_order_value' as keyof DivisionSales,
      header: 'Avg Order Value',
      align: 'right' as const,
      width: '140px',
      sortable: true,
      render: (value: number) => formatCurrencyFull(value),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sales Performance Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">Customer sales analysis and trends</p>
        </div>
        <DateRangePicker 
          startDate={startDate}
          endDate={endDate}
          onDateChange={handleDateChange}
        />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Sales"
          value={kpis ? formatCurrencyFull(kpis.total_sales) : '0'}
          icon={<DollarSign className="w-6 h-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total Customers"
          value={kpis ? formatNumber(kpis.total_customers) : '0'}
          icon={<Users className="w-6 h-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total Orders"
          value={kpis ? formatNumber(kpis.total_orders) : '0'}
          icon={<ShoppingCart className="w-6 h-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Avg Order Value"
          value={kpis ? formatCurrencyFull(kpis.avg_order_value) : '0'}
          icon={<TrendingUp className="w-6 h-6" />}
          loading={kpisLoading}
        />
      </div>

      {/* Zone 1: Monthly Sales Trend Chart */}
      <MonthlySalesChart initialYear={2026} />

      {/* ========== ZONE 1: NEW VISUAL INTELLIGENCE ========== */}
      <div className="mb-8">
        <CustomerSegmentationScatter 
          data={segmentationData || []} 
          loading={segmentationLoading} 
          dateRange={{ from: new Date(startDate), to: new Date(endDate) }}
        />
      </div>

      {/* ========== ZONE 2: EXISTING CHARTS & TABLES ========== */}
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales by Division Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sales by Division</h2>
          {divisionLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byDivision || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="division_code" 
                  tickFormatter={(value) => getDivisionName(value)}
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  tickFormatter={(value: number) => formatCurrencyCompact(value)}
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  formatter={(value) => formatCurrencyFull(Number(value))}
                  labelFormatter={(value) => `Division: ${getDivisionName(value)}`}
                  contentStyle={{ fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="total_sales" fill="#3b82f6" name="Total Sales" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Customers Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Customers by Revenue</h2>
          {customersLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={(customers || []).slice(0, 10)} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  type="number" 
                  tickFormatter={(value: number) => formatCurrencyCompact(value)}
                  style={{ fontSize: '11px' }}
                />
                <YAxis 
                  dataKey="customer_name" 
                  type="category" 
                  width={180} 
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => value.length > 25 ? value.substring(0, 25) + '...' : value}
                />
                <Tooltip 
                  formatter={(value) => formatCurrencyFull(Number(value))}
                  contentStyle={{ fontSize: '11px' }}
                />
                <Bar dataKey="sales_amount" fill="#10b981" name="Revenue" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Division Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Sales by Division ({(byDivision || []).length} divisions)
          </h2>
        </div>
        <div className="p-6">
          <DataTable data={byDivision || []} columns={divisionColumns} loading={divisionLoading} />
        </div>
      </div>

      {/* Customer Details Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Customer Sales Details ({(customers || []).length} customers)
          </h2>
        </div>
        <div className="p-6">
          <DataTable data={customers || []} columns={customerColumns} loading={customersLoading} />
        </div>
      </div>
    </div>
  );
};

export default SalesPerformance;
