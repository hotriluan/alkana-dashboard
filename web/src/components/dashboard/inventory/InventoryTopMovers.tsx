/**
 * Inventory Top Movers vs Dead Stock Chart
 * Split-view displaying:
 * - Left: Top 10 High Velocity Items (actively moving)
 * - Right: Top 10 Dead Stock Risks (high stock, no movement)
 */
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { SEMANTIC_COLORS, RECHARTS_DEFAULTS, TOOLTIP_STYLES } from '../../../constants/chartColors';
import { Spinner } from '../../common/Spinner';

interface TopMover {
  material_code: string;
  material_description: string;
  velocity_score: number;
}

interface DeadStock {
  material_code: string;
  material_description: string;
  stock_kg: number;
  velocity_score: number;
}

interface DateRange {
  from: Date;
  to: Date;
}

interface InventoryTopMoversProps {
  topMovers: TopMover[];
  deadStock: DeadStock[];
  loading?: boolean;
  dateRange?: DateRange;
}

const InventoryTopMovers: React.FC<InventoryTopMoversProps> = ({
  topMovers = [],
  deadStock = [],
  loading = false,
  dateRange,
}) => {
  // Calculate number of days in date range
  const getDayCount = () => {
    if (!dateRange) return 90; // Fallback to 90 if not provided
    const diffTime = Math.abs(dateRange.to.getTime() - dateRange.from.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1 to include both start and end dates
  };
  const dayCount = getDayCount();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  if ((!topMovers || topMovers.length === 0) && (!deadStock || deadStock.length === 0)) {
    return (
      <div className="flex items-center justify-center bg-slate-50 rounded h-96">
        <p className="text-slate-500">No inventory data available</p>
      </div>
    );
  }

  // Format material name: show description if available, fallback to code
  const formatMaterial = (item: TopMover | DeadStock) => {
    if (item.material_description && item.material_description.length > 30) {
      return item.material_description.substring(0, 30) + '...';
    }
    return item.material_description || item.material_code;
  };

  // Tooltip for Top Movers
  const TopMoverTooltip: React.FC<any> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white rounded shadow-lg p-3 border border-slate-200 max-w-xs">
          <p className="text-sm font-bold text-slate-900">{data.material_code}</p>
          <p className="text-xs text-slate-600 mb-2">{data.material_description}</p>
          <p className="text-sm">
            <span className="font-semibold text-slate-700">Movements:</span>{' '}
            <span className="text-green-600 font-bold">{data.velocity_score}/{dayCount}d</span>
          </p>
        </div>
      );
    }
    return null;
  };

  // Tooltip for Dead Stock
  const DeadStockTooltip: React.FC<any> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white rounded shadow-lg p-3 border border-red-200 max-w-xs">
          <p className="text-sm font-bold text-slate-900">{data.material_code}</p>
          <p className="text-xs text-slate-600 mb-2">{data.material_description}</p>
          <p className="text-sm">
            <span className="font-semibold text-slate-700">Stock:</span>{' '}
            <span className="text-red-600 font-bold">{data.stock_kg.toLocaleString('en-US', { maximumFractionDigits: 0 })} kg</span>
          </p>
          <p className="text-xs text-slate-600 mt-1">
            <span className="font-semibold">Velocity:</span> {data.velocity_score} movements
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900">Inventory Analysis: Movers vs Dead Stock</h2>
        <p className="text-sm text-slate-600 mt-1">
          Identify fast-moving materials and high-risk slow-moving inventory
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Top Movers */}
        <div className="border border-slate-200 rounded-lg p-4 bg-gradient-to-br from-green-50 to-slate-50">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-green-900">🟢 Top 10 High Velocity Items</h3>
            <p className="text-xs text-slate-600 mt-1">Most actively moving materials</p>
          </div>
          
          {topMovers && topMovers.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                data={topMovers}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={SEMANTIC_COLORS.SLATE} vertical={false} />
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis 
                  dataKey={(item) => formatMaterial(item)} 
                  type="category" 
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  width={195}
                />
                <Tooltip content={<TopMoverTooltip />} {...TOOLTIP_STYLES} />
                <Bar dataKey="velocity_score" fill="#10b981" radius={[0, 8, 8, 0]} name={`Movements/${dayCount}d`} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-96 bg-slate-50 rounded text-slate-400">
              No high velocity items
            </div>
          )}
        </div>

        {/* Right: Dead Stock */}
        <div className="border border-slate-200 rounded-lg p-4 bg-gradient-to-br from-red-50 to-slate-50">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-red-900">🔴 Top 10 Dead Stock Risks</h3>
            <p className="text-xs text-slate-600 mt-1">High stock, zero movement (inventory waste)</p>
          </div>

          {deadStock && deadStock.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                data={deadStock}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={SEMANTIC_COLORS.SLATE} vertical={false} />
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis 
                  dataKey={(item) => formatMaterial(item)} 
                  type="category" 
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  width={195}
                />
                <Tooltip content={<DeadStockTooltip />} {...TOOLTIP_STYLES} />
                <Bar dataKey="stock_kg" fill="#ef4444" radius={[0, 8, 8, 0]} name="Stock (kg)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-96 bg-slate-50 rounded text-slate-400">
              No dead stock items
            </div>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-slate-200">
        <div className="bg-green-50 rounded p-3 text-center">
          <p className="text-2xl font-bold text-green-600">{topMovers?.length || 0}</p>
          <p className="text-xs text-slate-600">High Velocity Items</p>
        </div>
        <div className="bg-red-50 rounded p-3 text-center">
          <p className="text-2xl font-bold text-red-600">{deadStock?.length || 0}</p>
          <p className="text-xs text-slate-600">Dead Stock Items</p>
        </div>
      </div>
    </div>
  );
};

export default InventoryTopMovers;
