/**
 * Production Funnel Chart
 * Visualizes order progression through production stages
 */
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { COLOR_ARRAYS, SEMANTIC_COLORS, RECHARTS_DEFAULTS, TOOLTIP_STYLES } from '../../../constants/chartColors';
import { Spinner } from '../../common/Spinner';

interface FunnelData {
  stage_name: string;
  status_code: string;
  order_count: number;
}

interface DateRange {
  from: Date;
  to: Date;
}

interface ProductionFunnelProps {
  data: FunnelData[];
  loading?: boolean;
  height?: number;
  dateRange?: DateRange;
}

const ProductionFunnel: React.FC<ProductionFunnelProps> = ({
  data,
  loading = false,
  height = 350,
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <Spinner />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center bg-slate-50 rounded" style={{ height }}>
        <p className="text-slate-500">No production data available</p>
      </div>
    );
  }

  // Map stages to colors (progression from left to right)
  const chartData = data.map((item, idx) => ({
    ...item,
    fill: COLOR_ARRAYS.FUNNEL[idx % COLOR_ARRAYS.FUNNEL.length],
  }));

  const CustomTooltip: React.FC<any> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white rounded shadow p-2 border border-slate-200">
          <p className="text-sm font-semibold">{data.stage_name}</p>
          <p className="text-sm">
            <span className="font-medium">Orders:</span> {data.order_count}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Production Order Funnel</h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          margin={RECHARTS_DEFAULTS.margin}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={SEMANTIC_COLORS.SLATE} />
          <XAxis dataKey="stage_name" />
          <YAxis label={{ value: 'Order Count', angle: -90, position: 'insideLeft' }} />
          <Tooltip content={<CustomTooltip />} {...TOOLTIP_STYLES} />
          <Bar dataKey="order_count" fill={SEMANTIC_COLORS.BLUE} radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-slate-500 mt-2">
        Stages: Created → Released → In Progress → Completed
      </p>
    </div>
  );
};

export default ProductionFunnel;
