// Production Yield Dashboard - Manufacturing efficiency tracking
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Factory, AlertTriangle, Target } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/common/KPICard';
import { DataTable } from '../components/common/DataTable';
import { DateRangePicker } from '../components/common/DateRangePicker';
import api from '../services/api';

interface YieldKPIs {
  avg_yield_rate: number;
  total_input: number;
  total_output: number;
  total_scrap: number;
}

interface YieldRecord {
  plant_code: string;
  material_code: string;
  material_description: string;
  total_input_qty: number;
  total_output_qty: number;
  yield_percentage: number;
  scrap_qty: number;
  uom: string;
}

interface PlantYield {
  plant_code: string;
  material_count: number;
  avg_yield: number;
  total_input: number;
  total_output: number;
  total_scrap: number;
}

import { getFirstDayOfMonth, getToday } from '../utils/dateHelpers';

const ProductionYield = () => {
  const today = getToday();
  const firstDayOfMonth = getFirstDayOfMonth();
  const [startDate, setStartDate] = useState(firstDayOfMonth);
  const [endDate, setEndDate] = useState(today);

  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['yield-kpis', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<YieldKPIs>('/api/v1/dashboards/yield/summary', {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    },
  });

  const { data: records, isLoading: recordsLoading } = useQuery({
    queryKey: ['yield-records', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<YieldRecord[]>('/api/v1/dashboards/yield/records?limit=100', {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    },
  });

  const { data: byPlant, isLoading: plantLoading } = useQuery({
    queryKey: ['yield-by-plant', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<PlantYield[]>('/api/v1/dashboards/yield/by-plant', {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    },
  });

  const handleDateChange = (newStartDate: string, newEndDate: string) => {
    setStartDate(newStartDate);
    setEndDate(newEndDate);
  };

  const formatNumber = (value: number) => {
    const thousands = value / 1000;
    if (thousands >= 1) return `${thousands.toFixed(1)}K`;
    return value.toLocaleString('vi-VN', { maximumFractionDigits: 0 });
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const yieldColumns = [
    {
      key: 'material_code' as keyof YieldRecord,
      header: 'Material',
      width: '120px',
      sortable: true,
    },
    {
      key: 'material_description' as keyof YieldRecord,
      header: 'Description',
      sortable: true,
    },
    {
      key: 'plant_code' as keyof YieldRecord,
      header: 'Plant',
      width: '80px',
      sortable: true,
    },
    {
      key: 'total_input_qty' as keyof YieldRecord,
      header: 'Input Qty',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number, row: YieldRecord) => `${formatNumber(value)} ${row.uom}`,
    },
    {
      key: 'total_output_qty' as keyof YieldRecord,
      header: 'Output Qty',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number, row: YieldRecord) => `${formatNumber(value)} ${row.uom}`,
    },
    {
      key: 'scrap_qty' as keyof YieldRecord,
      header: 'Scrap',
      align: 'right' as const,
      width: '100px',
      sortable: true,
      render: (value: number, row: YieldRecord) => `${formatNumber(value)} ${row.uom}`,
    },
    {
      key: 'yield_percentage' as keyof YieldRecord,
      header: 'Yield %',
      align: 'right' as const,
      width: '100px',
      sortable: true,
      render: (value: number) => {
        const color = value >= 95 ? 'text-green-600 font-semibold' : 
                     value >= 85 ? 'text-yellow-600 font-semibold' : 
                     'text-red-600 font-semibold';
        return <span className={color}>{formatPercent(value)}</span>;
      },
    },
  ];

  const plantColumns = [
    {
      key: 'plant_code' as keyof PlantYield,
      header: 'Plant',
      width: '100px',
      sortable: true,
    },
    {
      key: 'material_count' as keyof PlantYield,
      header: 'Materials',
      align: 'right' as const,
      width: '100px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'total_input' as keyof PlantYield,
      header: 'Total Input',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'total_output' as keyof PlantYield,
      header: 'Total Output',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'total_scrap' as keyof PlantYield,
      header: 'Total Scrap',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number) => formatNumber(value),
    },
    {
      key: 'avg_yield' as keyof PlantYield,
      header: 'Avg Yield %',
      align: 'right' as const,
      width: '120px',
      sortable: true,
      render: (value: number) => {
        const color = value >= 95 ? 'text-green-600 font-semibold' : 
                     value >= 85 ? 'text-yellow-600 font-semibold' : 
                     'text-red-600 font-semibold';
        return <span className={color}>{formatPercent(value)}</span>;
      },
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Production Yield Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">Manufacturing efficiency and material yield tracking</p>
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
          title="Avg Yield Rate"
          value={kpis ? formatPercent(kpis.avg_yield_rate) : '0%'}
          icon={<Target className="w-6 h-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total Input"
          value={kpis ? formatNumber(kpis.total_input) : '0'}
          icon={<Factory className="w-6 h-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total Output"
          value={kpis ? formatNumber(kpis.total_output) : '0'}
          icon={<TrendingUp className="w-6 h-6" />}
          loading={kpisLoading}
        />
        <KPICard
          title="Total Scrap"
          value={kpis ? formatNumber(kpis.total_scrap) : '0'}
          icon={<AlertTriangle className="w-6 h-6" />}
          loading={kpisLoading}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Yield by Plant Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Yield Rate by Plant</h2>
          {plantLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byPlant || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="plant_code" style={{ fontSize: '12px' }} />
                <YAxis 
                  tickFormatter={(value) => `${value.toFixed(0)}%`}
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  formatter={(value) => `${Number(value).toFixed(1)}%`}
                  contentStyle={{ fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="avg_yield" fill="#10b981" name="Avg Yield %" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Input vs Output Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Input vs Output by Plant</h2>
          {plantLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byPlant || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="plant_code" style={{ fontSize: '12px' }} />
                <YAxis 
                  tickFormatter={(value) => {
                    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
                    return value.toString();
                  }}
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  formatter={(value) => formatNumber(Number(value))}
                  contentStyle={{ fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="total_input" fill="#3b82f6" name="Input" radius={[4, 4, 0, 0]} />
                <Bar dataKey="total_output" fill="#10b981" name="Output" radius={[4, 4, 0, 0]} />
                <Bar dataKey="total_scrap" fill="#ef4444" name="Scrap" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Plant Performance Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Yield by Plant ({(byPlant || []).length} plants)
          </h2>
        </div>
        <div className="p-6">
          <DataTable data={byPlant || []} columns={plantColumns} loading={plantLoading} />
        </div>
      </div>

      {/* Material Yield Details Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Material Yield Details ({(records || []).length} materials)
          </h2>
        </div>
        <div className="p-6">
          <DataTable data={records || []} columns={yieldColumns} loading={recordsLoading} />
        </div>
      </div>
    </div>
  );
};

export default ProductionYield;
