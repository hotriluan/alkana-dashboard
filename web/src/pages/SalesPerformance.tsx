// Sales Performance Dashboard - Customer and division sales tracking
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DollarSign, Users, ShoppingCart, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import api from '../services/api';

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

const SalesPerformance = () => {
  const today = new Date().toISOString().split('T')[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(thirtyDaysAgo);
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

  const handleDateChange = (newStartDate: string, newEndDate: string) => {
    setStartDate(newStartDate);
    setEndDate(newEndDate);
  };

  const formatCurrency = (value: number) => {
    const billions = value / 1_000_000_000;
    if (billions >= 1) return `${billions.toFixed(1)}B`;
    const millions = value / 1_000_000;
    if (millions >= 1) return `${millions.toFixed(0)}M`;
    const thousands = value / 1_000;
    if (thousands >= 1) return `${thousands.toFixed(0)}K`;
    return value.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
  };

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
      width: '100px',
      sortable: true,
    },
    {
      key: 'sales_amount' as keyof SalesRecord,
      header: 'Sales Amount',
      align: 'right' as const,
      width: '140px',
      sortable: true,
      render: (value: number) => formatCurrency(value),
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
      render: (value: number) => formatCurrency(value),
    },
  ];

  const divisionColumns = [
    {
      key: 'division_code' as keyof DivisionSales,
      header: 'Division',
      width: '120px',
      sortable: true,
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
      render: (value: number) => formatCurrency(value),
    },
    {
      key: 'avg_order_value' as keyof DivisionSales,
      header: 'Avg Order Value',
      align: 'right' as const,
      width: '140px',
      sortable: true,
      render: (value: number) => formatCurrency(value),
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
          value={kpis ? formatCurrency(kpis.total_sales) : '0'}
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
          value={kpis ? formatCurrency(kpis.avg_order_value) : '0'}
          icon={<TrendingUp className="w-6 h-6" />}
          loading={kpisLoading}
        />
      </div>

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
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  tickFormatter={(value) => {
                    const billions = value / 1_000_000_000;
                    return billions >= 1 ? `${billions.toFixed(1)}B` : `${(value / 1_000_000).toFixed(0)}M`;
                  }}
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  formatter={(value) => formatCurrency(Number(value))}
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
                  tickFormatter={(value) => {
                    const billions = value / 1_000_000_000;
                    return billions >= 1 ? `${billions.toFixed(1)}B` : `${(value / 1_000_000).toFixed(0)}M`;
                  }}
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
                  formatter={(value) => formatCurrency(Number(value))}
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
