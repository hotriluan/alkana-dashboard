/**
 * Lead Time Breakdown Stacked Bar Chart
 * Visualizes prep, production, and delivery time components
 * Colors: Slate (Prep), Blue (Production), Amber (Delivery)
 */
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { COLORS_LEADTIME_STAGES, SEMANTIC_COLORS, RECHARTS_DEFAULTS, TOOLTIP_STYLES } from '../../../constants/chartColors';
import { Spinner } from '../../common/Spinner';

interface StageBreakdown {
  order_number: string;
  material_code: string;
  material_description: string;
  batch: string;
  prep_days: number;
  production_days: number;
  delivery_days: number;
  total_days: number;
}

interface DateRange {
  from: Date;
  to: Date;
}

interface LeadTimeBreakdownChartProps {
  data: StageBreakdown[];
  loading?: boolean;
  height?: number;
  dateRange?: DateRange;
}

const LeadTimeBreakdownChart: React.FC<LeadTimeBreakdownChartProps> = ({
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
        <p className="text-slate-500">No lead time data available</p>
      </div>
    );
  }

  const CustomTooltip: React.FC<any> = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const total = payload.reduce((sum: number, p: any) => sum + (p.value || 0), 0);
      return (
        <div className="bg-white rounded shadow-lg p-3 border border-slate-200 max-w-xs">
          <p className="text-sm font-bold text-slate-900">{data.order_number}</p>
          <p className="text-xs text-slate-600 mb-2">
            <span className="font-semibold">Product:</span> {data.material_description}
          </p>
          <p className="text-xs text-slate-600 mb-2">
            <span className="font-semibold">Batch:</span> {data.batch}
          </p>
          <div className="border-t pt-2 mt-2 space-y-1">
            {payload.map((p: any, idx: number) => (
              <p key={idx} className="text-xs">
                <span className="font-medium">{p.name}:</span>{' '}
                <span className="text-slate-900">{p.value} days</span>
              </p>
            ))}
            <p className="text-xs font-bold border-t mt-1 pt-1">
              <span className="font-semibold">Total Lead Time:</span>{' '}
              <span className="text-slate-900">{total} days</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Lead Time Breakdown (Last 20 Orders)</h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          margin={RECHARTS_DEFAULTS.margin}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={SEMANTIC_COLORS.SLATE} />
          <XAxis dataKey="order_number" angle={-45} textAnchor="end" height={80} />
          <YAxis label={{ value: 'Days', angle: -90, position: 'insideLeft' }} />
          <Tooltip content={<CustomTooltip />} {...TOOLTIP_STYLES} />
          <Legend />
          <Bar dataKey="prep_days" stackId="a" fill={COLORS_LEADTIME_STAGES.PREP} name="Prep" radius={[0, 0, 0, 0]} />
          <Bar dataKey="production_days" stackId="a" fill={COLORS_LEADTIME_STAGES.PRODUCTION} name="Production" />
          <Bar dataKey="delivery_days" stackId="a" fill={COLORS_LEADTIME_STAGES.DELIVERY} name="Delivery" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* Legend with colors */}
      <div className="flex gap-6 mt-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: COLORS_LEADTIME_STAGES.PREP }} />
          <span>Preparation (MTO only)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: COLORS_LEADTIME_STAGES.PRODUCTION }} />
          <span>Production</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: COLORS_LEADTIME_STAGES.DELIVERY }} />
          <span>Delivery/Transit</span>
        </div>
      </div>
    </div>
  );
};

export default LeadTimeBreakdownChart;
