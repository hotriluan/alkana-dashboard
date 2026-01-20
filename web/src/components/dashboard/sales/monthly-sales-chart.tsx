/**
 * Monthly Sales Trend Chart Component
 * 
 * Displays bar chart with monthly revenue aggregation
 * Features: responsive layout, custom tooltip, year filtering
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatLargeNumber, formatCurrency } from '../../../utils/numberFormatter';
import api from '../../../services/api';

interface MonthlySalesData {
  month_num: number;
  month_name: string;
  revenue: number;
  orders: number;
}

interface MonthlySalesChartProps {
  initialYear?: number;
}

const MonthlySalesChart = ({ initialYear = 2026 }: MonthlySalesChartProps) => {
  const [selectedYear, setSelectedYear] = useState(initialYear);

  const { data: trendData, isLoading } = useQuery({
    queryKey: ['monthly-sales-trend', selectedYear],
    queryFn: async () => {
      const response = await api.get<MonthlySalesData[]>('/api/v1/dashboards/sales/trend', {
        params: { year: selectedYear }
      });
      return response.data;
    },
  });

  // Custom tooltip with full currency formatting
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold text-gray-800">{data.month_name}</p>
          <p className="text-blue-600 font-bold">
            Revenue: {formatCurrency(data.revenue)}
          </p>
          <p className="text-gray-600">Orders: {data.orders}</p>
        </div>
      );
    }
    return null;
  };

  // Format Y-Axis labels
  const formatYAxisLabel = (value: number) => {
    return formatLargeNumber(value);
  };

  return (
    <div className="w-full bg-white rounded-lg shadow p-6 mb-6">
      {/* Header with title and year filter */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-800">Monthly Sales Trend</h2>
        
        {/* Year dropdown */}
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(parseInt(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value={2024}>Year: 2024</option>
          <option value={2025}>Year: 2025</option>
          <option value={2026}>Year: 2026</option>
        </select>
      </div>

      {/* Chart loading state */}
      {isLoading ? (
        <div className="h-96 flex items-center justify-center">
          <div className="text-gray-500">Loading trend data...</div>
        </div>
      ) : trendData && trendData.length > 0 ? (
        /* Chart container */
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={trendData}
            margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="month_name"
              tick={{ fontSize: 12 }}
              tickFormatter={(value: string) => value.substring(0, 3)}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={formatYAxisLabel}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="revenue"
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
              isAnimationActive={true}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        /* Empty state */
        <div className="h-96 flex items-center justify-center">
          <div className="text-gray-500">No sales data available for {selectedYear}</div>
        </div>
      )}

      {/* Summary info */}
      {trendData && trendData.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Total Revenue ({selectedYear}):</span>
              <p className="font-bold text-blue-600">
                {formatCurrency(trendData.reduce((sum: number, m: MonthlySalesData) => sum + m.revenue, 0))}
              </p>
            </div>
            <div>
              <span className="text-gray-600">Total Orders ({selectedYear}):</span>
              <p className="font-bold text-green-600">
                {trendData.reduce((sum: number, m: MonthlySalesData) => sum + m.orders, 0)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MonthlySalesChart;
