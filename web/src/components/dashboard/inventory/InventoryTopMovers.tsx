/**
 * Inventory Top Movers vs Dead Stock Chart
 * Split-view displaying:
 * - Left: Top 10 High Velocity Items (actively moving)
 * - Right: Top 10 Dead Stock Risks (high stock, no movement)
 * Features: Material type filtering and semantic coloring
 */
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { SEMANTIC_COLORS, TOOLTIP_STYLES } from '../../../constants/chartColors';
import { Spinner } from '../../common/Spinner';

interface TopMover {
  material_code: string;
  material_description: string;
  velocity_score: number;
  material_type: string;
}

interface DeadStock {
  material_code: string;
  material_description: string;
  stock_kg: number;
  velocity_score: number;
  material_type: string;
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
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
}

// Material type semantic colors
const MATERIAL_TYPE_COLORS = {
  FG: SEMANTIC_COLORS.GREEN,    // Finish Goods - Green/Teal (value/money)
  SFG: SEMANTIC_COLORS.BLUE,    // Semi-Finish - Blue (Work In Progress)
  RM: SEMANTIC_COLORS.AMBER,    // Raw Materials - Amber/Orange (input/stockpile)
  OTHER: SEMANTIC_COLORS.SLATE, // Other materials - Slate (secondary)
};

const CATEGORY_OPTIONS = [
  { id: 'ALL_CORE', label: 'All Core', emoji: '📊' },
  { id: 'FG', label: 'Finish Goods (10)', emoji: '🟢' },
  { id: 'SFG', label: 'Semi-Finish (12)', emoji: '🔵' },
  { id: 'RM', label: 'Raw Material (15)', emoji: '🟤' },
];

const InventoryTopMovers: React.FC<InventoryTopMoversProps> = ({
  topMovers = [],
  deadStock = [],
  loading = false,
  dateRange,
  selectedCategory,
  onCategoryChange,
}) => {

  // Calculate number of days in date range
  const getDayCount = () => {
    if (!dateRange) return 90; // Fallback to 90 if not provided
    const diffTime = Math.abs(dateRange.to.getTime() - dateRange.from.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1 to include both start and end dates
  };
  const dayCount = getDayCount();

  // Handle category filter change

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

  // Get color based on material type
  const getMaterialColor = (materialType: string) => {
    return MATERIAL_TYPE_COLORS[materialType as keyof typeof MATERIAL_TYPE_COLORS] || MATERIAL_TYPE_COLORS.OTHER;
  };

  // Tooltip for Top Movers
  const TopMoverTooltip: React.FC<any> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white rounded shadow-lg p-3 border border-slate-200 max-w-xs">
          <p className="text-sm font-bold text-slate-900">[{data.material_type}] {data.material_code}</p>
          <p className="text-xs text-slate-600 mb-2">{data.material_description}</p>
          <p className="text-sm">
            <span className="font-semibold text-slate-700">Movements:</span>{' '}
            <span className="font-bold" style={{ color: getMaterialColor(data.material_type) }}>
              {data.velocity_score}/{dayCount}d
            </span>
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
          <p className="text-sm font-bold text-slate-900">[{data.material_type}] {data.material_code}</p>
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
          Identify fast-moving materials and high-risk slow-moving inventory by material segment
        </p>
      </div>

      {/* Segment Control: Filter Tabs */}
      <div className="mb-6 flex gap-2 flex-wrap">
        {CATEGORY_OPTIONS.map((option) => (
          <button
            key={option.id}
            onClick={() => onCategoryChange(option.id)}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
              selectedCategory === option.id
                ? 'bg-slate-900 text-white shadow-md'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            {option.emoji} {option.label}
          </button>
        ))}
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
                <Bar 
                  dataKey="velocity_score" 
                  radius={[0, 8, 8, 0]} 
                  name={`Movements/${dayCount}d`}
                >
                  {topMovers.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getMaterialColor(entry.material_type)} />
                  ))}
                </Bar>
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
                <Bar 
                  dataKey="stock_kg" 
                  radius={[0, 8, 8, 0]} 
                  name="Stock (kg)"
                >
                  {deadStock.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getMaterialColor(entry.material_type)} />
                  ))}
                </Bar>
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

      {/* Material Type Legend */}
      <div className="mt-6 pt-4 border-t border-slate-200">
        <p className="text-xs font-semibold text-slate-700 mb-3">Material Type Color Legend:</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(MATERIAL_TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></div>
              <span className="text-xs text-slate-600">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InventoryTopMovers;
