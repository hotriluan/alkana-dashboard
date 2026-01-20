/**
 * Inventory ABC Analysis Treemap Chart
 * Visualizes material stock quantities and velocity classification
 * 
 * Size: stock_kg (Physical volume)
 * Color: ABC class (Red=A, Blue=B, Gray=C)
 */
import React from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { COLORS_ABC, SEMANTIC_COLORS } from '../../../constants/chartColors';
import { Spinner } from '../../common/Spinner';

interface TreemapItem {
  material_code: string;
  material_description: string;
  stock_kg: number;
  velocity_score: number;
  abc_class: 'A' | 'B' | 'C';
}

interface DateRange {
  from: Date;
  to: Date;
}

interface InventoryTreemapProps {
  data: TreemapItem[];
  loading?: boolean;
  height?: number;
  dateRange?: DateRange;
}

const InventoryTreemap: React.FC<InventoryTreemapProps> = ({
  data,
  loading = false,
  height = 400,
}) => {
  // Transform data for Recharts Treemap (requires nested structure)
  const getColor = (abcClass: string): string => {
    switch (abcClass) {
      case 'A':
        return COLORS_ABC.A;
      case 'B':
        return COLORS_ABC.B;
      case 'C':
        return COLORS_ABC.C;
      default:
        return SEMANTIC_COLORS.SLATE;
    }
  };

  const transformedData = data.map((item) => ({
    name: `${item.material_code}`,
    size: item.stock_kg,
    description: item.material_description,
    velocity: item.velocity_score,
    class: item.abc_class,
    fill: getColor(item.abc_class),
    children: [],
  }));

  const CustomTooltip: React.FC<any> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      // Format stock with thousands separator
      const formatStock = (kg: number) => {
        return kg.toLocaleString('en-US', { maximumFractionDigits: 0 });
      };
      
      // Get class explanation
      const getClassLabel = (abcClass: string) => {
        switch (abcClass) {
          case 'A':
            return 'A (Fast Moving - High Velocity)';
          case 'B':
            return 'B (Medium Movement - Standard)';
          case 'C':
            return 'C (Slow Moving - Low Activity)';
          default:
            return abcClass;
        }
      };
      
      return (
        <div className="bg-white rounded shadow-lg p-3 border border-slate-200 max-w-xs">
          <p className="text-sm font-bold text-slate-900">{data.name}</p>
          <p className="text-xs text-slate-600 mb-2">{data.description}</p>
          <div className="space-y-1">
            <p className="text-xs">
              <span className="font-semibold text-slate-700">Stock:</span>{' '}
              <span className="text-slate-900">{formatStock(data.size)} kg</span>
            </p>
            <p className="text-xs">
              <span className="font-semibold text-slate-700">Velocity:</span>{' '}
              <span className="text-slate-900">{data.velocity} movements/90d</span>
            </p>
            <p className="text-xs">
              <span className="font-semibold text-slate-700">Class:</span>{' '}
              <span className="text-slate-900">{getClassLabel(data.class)}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

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
        <p className="text-slate-500">No inventory data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Inventory Stock Distribution (ABC Analysis)</h3>
      <ResponsiveContainer width="100%" height={height}>
        <Treemap
          data={transformedData}
          dataKey="size"
          stroke={SEMANTIC_COLORS.SLATE}
          fill-opacity={0.8}
          isAnimationActive={true}
        >
          <Tooltip content={<CustomTooltip />} />
        </Treemap>
      </ResponsiveContainer>
      <div className="flex gap-6 mt-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: COLORS_ABC.A }} />
          <span>Class A (Fast, Top 20%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: COLORS_ABC.B }} />
          <span>Class B (Medium, 30%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: COLORS_ABC.C }} />
          <span>Class C (Slow, 50%)</span>
        </div>
      </div>
    </div>
  );
};

export default InventoryTreemap;
