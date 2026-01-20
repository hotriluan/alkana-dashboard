/**
 * Customer Segmentation Scatter Plot
 * X-Axis: Order Frequency (count of sales orders)
 * Y-Axis: Total Revenue (sum of net value)
 * Top-Right = VIP Customers
 */
import React, { useState } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { SEMANTIC_COLORS, RECHARTS_DEFAULTS, TOOLTIP_STYLES } from '../../../constants/chartColors';
import { Spinner } from '../../common/Spinner';

interface CustomerSegment {
  customer_name: string;
  order_frequency: number;
  total_revenue: number;
}

interface DateRange {
  from: Date;
  to: Date;
}

interface CustomerSegmentationScatterProps {
  data: CustomerSegment[];
  loading?: boolean;
  height?: number;
  onCustomerSelect?: (customer: string) => void;
  dateRange?: DateRange;
}

const CustomerSegmentationScatter: React.FC<CustomerSegmentationScatterProps> = ({
  data,
  loading = false,
  height = 400,
  onCustomerSelect,
}) => {
  const [hoveredCustomer, setHoveredCustomer] = useState<string | null>(null);

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
        <p className="text-slate-500">No customer data available</p>
      </div>
    );
  }

  // Calculate quadrant boundaries (using median)
  const medianFreq = [...data].sort((a, b) => a.order_frequency - b.order_frequency)[Math.floor(data.length / 2)].order_frequency;
  const medianRevenue = [...data].sort((a, b) => a.total_revenue - b.total_revenue)[Math.floor(data.length / 2)].total_revenue;

  const CustomTooltip: React.FC<any> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white rounded shadow p-2 border border-slate-200">
          <p className="text-sm font-semibold">{data.customer_name}</p>
          <p className="text-xs">
            <span className="font-medium">Frequency:</span> {data.order_frequency} orders
          </p>
          <p className="text-xs">
            <span className="font-medium">Revenue:</span> ${data.total_revenue.toFixed(0)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Customer Segmentation</h3>
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={RECHARTS_DEFAULTS.margin}>
          <CartesianGrid strokeDasharray="3 3" stroke={SEMANTIC_COLORS.SLATE} />
          <XAxis 
            dataKey="order_frequency" 
            label={{ value: 'Order Frequency', position: 'insideBottomRight', offset: -5 }}
          />
          <YAxis 
            dataKey="total_revenue" 
            label={{ value: 'Total Revenue ($)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} {...TOOLTIP_STYLES} />
          <ReferenceLine x={medianFreq} stroke={SEMANTIC_COLORS.SLATE} strokeDasharray="3 3" />
          <ReferenceLine y={medianRevenue} stroke={SEMANTIC_COLORS.SLATE} strokeDasharray="3 3" />
          <Scatter
            name="Customers"
            data={data}
            fill={SEMANTIC_COLORS.BLUE}
            onClick={(e: any) => {
              if (onCustomerSelect && e.customer_name) {
                onCustomerSelect(e.customer_name);
              }
            }}
            onMouseEnter={(e: any) => setHoveredCustomer(e.customer_name)}
            onMouseLeave={() => setHoveredCustomer(null)}
            style={{ cursor: 'pointer' }}
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Quadrant Info */}
      <div className="grid grid-cols-2 gap-3 mt-4 text-xs border-t pt-3">
        <div className="p-2 bg-blue-50 rounded">
          <p className="font-semibold text-blue-900">VIP Customers</p>
          <p className="text-blue-700">High Frequency + High Revenue</p>
          <p className="text-blue-600 text-xs">Top-Right Quadrant</p>
        </div>
        <div className="p-2 bg-amber-50 rounded">
          <p className="font-semibold text-amber-900">Loyal Customers</p>
          <p className="text-amber-700">High Frequency + Low Revenue</p>
          <p className="text-amber-600 text-xs">Top-Left Quadrant</p>
        </div>
        <div className="p-2 bg-green-50 rounded">
          <p className="font-semibold text-green-900">High-Value Deals</p>
          <p className="text-green-700">Low Frequency + High Revenue</p>
          <p className="text-green-600 text-xs">Bottom-Right Quadrant</p>
        </div>
        <div className="p-2 bg-slate-50 rounded">
          <p className="font-semibold text-slate-900">Casual Buyers</p>
          <p className="text-slate-700">Low Frequency + Low Revenue</p>
          <p className="text-slate-600 text-xs">Bottom-Left Quadrant</p>
        </div>
      </div>

      {hoveredCustomer && (
        <p className="text-xs text-slate-600 mt-2 italic">
          Hovered: {hoveredCustomer}
        </p>
      )}
    </div>
  );
};

export default CustomerSegmentationScatter;
