/**
 * Performance Matrix - Bubble Chart Visualization
 * 
 * Visual Clarity Upgrade for Production Yield V3.6
 * 
 * Axes Mapping:
 * - X-Axis: Total Output (KG) - Volume/Scale
 * - Y-Axis: Loss % - Efficiency (Lower is better)
 * - Z-Axis (Bubble Size): Total Loss (KG) - Impact
 * 
 * Reference Line: Y = 1.0% (Acceptable Limit)
 */
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Label, ZAxis } from 'recharts';
import type { CategoryPerformance } from '@/types/yield';

interface PerformanceMatrixProps {
  data: CategoryPerformance[];
}

const COLORS = {
  excellent: '#10b981',  // Green - Low loss
  good: '#3b82f6',       // Blue - Acceptable
  warning: '#f59e0b',    // Orange - Needs attention
  danger: '#ef4444',     // Red - Critical
};

// Determine color based on loss percentage
const getBubbleColor = (lossPct: number): string => {
  if (lossPct <= 1.0) return COLORS.excellent;
  if (lossPct <= 2.0) return COLORS.good;
  if (lossPct <= 3.0) return COLORS.warning;
  return COLORS.danger;
};

// Format number with thousand separators
const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US').format(Math.round(num));
};

// Custom tooltip with meaningful sentences
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || payload.length === 0) return null;
  
  const data = payload[0].payload as CategoryPerformance;
  const outputTons = data.total_output_kg / 1000;
  
  return (
    <div className="bg-white p-4 border-2 border-gray-300 rounded-lg shadow-xl">
      <p className="font-bold text-gray-900 mb-2 text-lg">{data.category}</p>
      <div className="space-y-1 text-sm">
        <p className="text-gray-700">
          <span className="font-medium">Production:</span> {formatNumber(outputTons)} tons ({data.batch_count} batches)
        </p>
        <p className={`font-semibold ${
          data.loss_pct_avg <= 1.0 ? 'text-green-600' :
          data.loss_pct_avg <= 2.0 ? 'text-blue-600' :
          data.loss_pct_avg <= 3.0 ? 'text-orange-600' : 'text-red-600'
        }`}>
          <span className="font-medium text-gray-700">Efficiency:</span> {data.loss_pct_avg.toFixed(2)}% Loss
        </p>
        <p className="text-red-600 font-semibold">
          <span className="font-medium text-gray-700">Impact:</span> Lost {formatNumber(data.total_loss_kg)} kg this month
        </p>
      </div>
    </div>
  );
};

export default function PerformanceMatrix({ data }: PerformanceMatrixProps) {
  // Transform data for bubble chart
  const chartData = data.map(item => ({
    ...item,
    x: item.total_output_kg,
    y: item.loss_pct_avg,
    z: item.total_loss_kg, // Bubble size
    fill: getBubbleColor(item.loss_pct_avg)
  }));

  // Find max values for axis scaling
  const maxOutput = Math.max(...data.map(d => d.total_output_kg), 0);
  const maxLoss = Math.max(...data.map(d => d.loss_pct_avg), 0);

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Total Output (KG)"
            domain={[0, maxOutput * 1.1]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
          >
            <Label 
              value="Production Volume (KG)" 
              position="bottom" 
              offset={40}
              style={{ fontSize: 14, fontWeight: 600 }}
            />
          </XAxis>
          
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Loss %"
            domain={[0, Math.max(maxLoss * 1.2, 5)]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${value.toFixed(1)}%`}
          >
            <Label 
              value="Loss % (Lower is Better)" 
              angle={-90} 
              position="left"
              offset={40}
              style={{ fontSize: 14, fontWeight: 600 }}
            />
          </YAxis>

          <ZAxis 
            type="number" 
            dataKey="z" 
            range={[100, 2000]} 
            name="Total Loss (KG)"
          />
          
          {/* Reference Line: Acceptable Limit */}
          <ReferenceLine 
            y={1.0} 
            stroke="#10b981" 
            strokeWidth={2}
            strokeDasharray="5 5"
          >
            <Label 
              value="✓ Acceptable Limit (1%)" 
              position="right"
              fill="#10b981"
              style={{ fontSize: 12, fontWeight: 600 }}
            />
          </ReferenceLine>

          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          
          <Scatter 
            name="Categories" 
            data={chartData} 
            fill="#8884d8"
          >
            {chartData.map((entry, index) => (
              <circle key={index} fill={entry.fill} opacity={0.7} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center gap-6 mt-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COLORS.excellent }}></div>
          <span>≤ 1% (Excellent)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COLORS.good }}></div>
          <span>1-2% (Good)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COLORS.warning }}></div>
          <span>2-3% (Warning)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COLORS.danger }}></div>
          <span>&gt; 3% (Critical)</span>
        </div>
      </div>
    </div>
  );
}
