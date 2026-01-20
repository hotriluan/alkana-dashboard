/**
 * Production Yield V3 Dashboard - Operational Efficiency Hub
 * 
 * Features:
 * - Historical trend analysis across months
 * - Pareto chart for top loss contributors
 * - Distribution by product groups
 * - SG variance quality scatter plot
 * - Upload modal for monthly data
 */
import { useState } from 'react';
import { TrendingUp, AlertTriangle, Package, Target, Database } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

import PeriodRangeSelector from './PeriodRangeSelector';
import PerformanceMatrix from './PerformanceMatrix';
import InsightSummary from './InsightSummary';
import {
  useYieldKPI,
  useYieldTrend,
  // useYieldDistribution, // Unused for now
  useYieldPareto,
  useAvailablePeriods,
  useCategoryPerformance,
} from '@/hooks/useYieldV3';

// Color palette
const COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#8b5cf6',
  teal: '#14b8a6',
};

const BAR_COLORS = [
  '#3b82f6',
  '#8b5cf6',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#14b8a6',
  '#f97316',
  '#06b6d4',
];

export default function YieldV3Dashboard() {
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');

  const { data: periods } = useAvailablePeriods();
  const { data: kpi, isLoading: kpiLoading } = useYieldKPI(periodStart, periodEnd);
  const { data: trend, isLoading: trendLoading } = useYieldTrend(periodStart, periodEnd);
  // const { data: distribution } = useYieldDistribution(periodStart, periodEnd); // Unused for now
  const { data: categoryPerf, isLoading: categoryPerfLoading } = useCategoryPerformance(
    periodStart,
    periodEnd
  );
  const { data: pareto, isLoading: paretoLoading } = useYieldPareto(periodStart, periodEnd);

  // Auto-select latest period when data loads
  useState(() => {
    if (periods && periods.length > 0 && !periodStart) {
      const latest = periods[0].period;
      const oldest = periods[Math.min(2, periods.length - 1)].period;
      setPeriodStart(oldest);
      setPeriodEnd(latest);
    }
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Production Yield - Operational Efficiency Hub
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Historical trend analysis and efficiency insights
          </p>
        </div>
        <a
          href="/upload"
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Database className="w-4 h-4" />
          Manage Data Source
        </a>
      </div>

      {/* Period Selector */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <PeriodRangeSelector
          periodStart={periodStart}
          periodEnd={periodEnd}
          onPeriodStartChange={setPeriodStart}
          onPeriodEndChange={setPeriodEnd}
        />
      </div>

      {/* KPI Cards */}
      {periodStart && periodEnd && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            title="Avg Yield"
            value={kpi?.avg_yield_pct.toFixed(2) + '%' || '—'}
            icon={<TrendingUp className="w-6 h-6" />}
            color="blue"
            loading={kpiLoading}
          />
          <KPICard
            title="Total Output"
            value={kpi ? `${(kpi.total_output_kg / 1000).toFixed(1)}t` : '—'}
            icon={<Package className="w-6 h-6" />}
            color="green"
            loading={kpiLoading}
          />
          <KPICard
            title="Total Loss"
            value={kpi ? `${(kpi.total_loss_kg / 1000).toFixed(1)}t` : '—'}
            icon={<AlertTriangle className="w-6 h-6" />}
            color="orange"
            loading={kpiLoading}
          />
          <KPICard
            title="Total Orders"
            value={kpi?.total_orders.toLocaleString() || '—'}
            icon={<Target className="w-6 h-6" />}
            color="purple"
            loading={kpiLoading}
          />
        </div>
      )}

      {/* Charts Grid */}
      {periodStart && periodEnd && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Trend Chart */}
          <ChartCard title="Yield Trend Over Time" loading={trendLoading}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg_yield_pct"
                  stroke={COLORS.primary}
                  strokeWidth={2}
                  name="Avg Yield %"
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="avg_loss_pct"
                  stroke={COLORS.danger}
                  strokeWidth={2}
                  name="Avg Loss %"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Pareto Chart */}
          <ChartCard title="Top 10 Loss Contributors (Pareto)" loading={paretoLoading}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pareto || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="material_description" 
                  tick={{ fontSize: 9 }} 
                  angle={-45} 
                  textAnchor="end" 
                  height={100}
                  interval={0}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
                          <p className="font-semibold text-gray-900">{data.material_description}</p>
                          <p className="text-xs text-gray-600">Code: {data.material_code}</p>
                          <p className="text-sm text-red-600 mt-1">Loss: {data.total_loss_kg.toFixed(1)} kg</p>
                          <p className="text-sm text-gray-700">Avg Loss: {data.avg_loss_pct}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
                <Bar dataKey="total_loss_kg" name="Total Loss (kg)" fill={COLORS.danger}>
                  {(pareto || []).map((_entry, index: number) => (
                    <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Distribution Chart */}
          <ChartCard title="Performance Matrix - Volume vs Efficiency" loading={categoryPerfLoading}>
            <PerformanceMatrix data={categoryPerf || []} />
          </ChartCard>

          {/* Insight Summary */}
          <ChartCard title="AI-Powered Insights" loading={categoryPerfLoading}>
            <InsightSummary data={categoryPerf || []} />
          </ChartCard>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

interface KPICardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'orange' | 'purple';
  loading?: boolean;
}

function KPICard({ title, value, icon, color, loading }: KPICardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{title}</span>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
      </div>
      {loading ? (
        <div className="h-8 bg-gray-100 rounded animate-pulse" />
      ) : (
        <div className="text-2xl font-bold text-gray-900">{value}</div>
      )}
    </div>
  );
}

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
  loading?: boolean;
}

function ChartCard({ title, children, loading }: ChartCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      {loading ? (
        <div className="h-[300px] bg-gray-100 rounded animate-pulse" />
      ) : (
        children
      )}
    </div>
  );
}
