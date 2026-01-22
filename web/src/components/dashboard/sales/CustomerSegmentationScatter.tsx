/**
 * Customer Segmentation Scatter Plot
 * X-Axis: Order Frequency (count of sales orders)
 * Y-Axis: Total Revenue (sum of net value)
 * Top-Right = VIP Customers
 */
import React, { useState } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { SEMANTIC_COLORS, TOOLTIP_STYLES } from '../../../constants/chartColors';
import { Spinner } from '../../common/Spinner';
import { formatCurrencyCompact, formatCurrencyFull, formatInteger } from '../../../utils/formatters';

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

type FilterType = 'ALL' | 'VIP' | 'LOYAL' | 'HIGH_VALUE' | 'CASUAL';

const CustomerSegmentationScatter: React.FC<CustomerSegmentationScatterProps> = ({
  data,
  loading = false,
  height = 400,
  onCustomerSelect,
}) => {
  const [hoveredCustomer, setHoveredCustomer] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterType>('ALL');

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

  // Segment color mapping
  const SEGMENT_COLORS = {
    'VIP': '#3B82F6',           // Blue
    'LOYAL': '#F59E0B',         // Amber  
    'HIGH_VALUE': '#10B981',    // Green
    'CASUAL': '#94A3B8'         // Slate
  };

  // Classify each customer by segment and assign color
  type SegmentType = 'VIP' | 'LOYAL' | 'HIGH_VALUE' | 'CASUAL';
  
  interface CustomerWithSegment extends CustomerSegment {
    segment: SegmentType;
    fill: string;
  }

  const dataWithSegments: CustomerWithSegment[] = data.map(customer => {
    let segment: SegmentType;
    if (customer.order_frequency >= medianFreq && customer.total_revenue >= medianRevenue) {
      segment = 'VIP';
    } else if (customer.order_frequency >= medianFreq && customer.total_revenue < medianRevenue) {
      segment = 'LOYAL';
    } else if (customer.order_frequency < medianFreq && customer.total_revenue >= medianRevenue) {
      segment = 'HIGH_VALUE';
    } else {
      segment = 'CASUAL';
    }
    
    return {
      ...customer,
      segment,
      fill: SEGMENT_COLORS[segment]
    };
  });

  // Group data by segment for rendering
  const vipData = dataWithSegments.filter(c => c.segment === 'VIP');
  const loyalData = dataWithSegments.filter(c => c.segment === 'LOYAL');
  const highValueData = dataWithSegments.filter(c => c.segment === 'HIGH_VALUE');
  const casualData = dataWithSegments.filter(c => c.segment === 'CASUAL');

  // Filter data based on selected segment
  const getFilteredData = (segment: FilterType) => {
    if (segment === 'ALL') return { vip: vipData, loyal: loyalData, highValue: highValueData, casual: casualData };
    if (segment === 'VIP') return { vip: vipData, loyal: [], highValue: [], casual: [] };
    if (segment === 'LOYAL') return { vip: [], loyal: loyalData, highValue: [], casual: [] };
    if (segment === 'HIGH_VALUE') return { vip: [], loyal: [], highValue: highValueData, casual: [] };
    return { vip: [], loyal: [], highValue: [], casual: casualData }; // CASUAL
  };

  const filteredDatasets = getFilteredData(filter);

  const CustomTooltip: React.FC<any> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white rounded shadow p-2 border border-slate-200 z-50">
          <p className="text-sm font-semibold">{data.customer_name}</p>
          <p className="text-xs">
            <span className="font-medium">Segment:</span> {data.segment}
          </p>
          <p className="text-xs">
            <span className="font-medium">Frequency:</span> {formatInteger(data.order_frequency)} orders
          </p>
          <p className="text-xs">
            <span className="font-medium">Revenue:</span> {formatCurrencyFull(data.total_revenue)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Customer Segmentation</h3>
      
      {/* Segment Filter Tabs */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <button
          onClick={() => setFilter('ALL')}
          className={`px-3 py-1 rounded text-sm font-medium transition ${
            filter === 'ALL'
              ? 'bg-slate-700 text-white'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          All Customers ({dataWithSegments.length})
        </button>
        <button
          onClick={() => setFilter('VIP')}
          className={`px-3 py-1 rounded text-sm font-medium transition ${
            filter === 'VIP'
              ? 'bg-blue-600 text-white'
              : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
          }`}
        >
          🔵 VIP ({vipData.length})
        </button>
        <button
          onClick={() => setFilter('LOYAL')}
          className={`px-3 py-1 rounded text-sm font-medium transition ${
            filter === 'LOYAL'
              ? 'bg-amber-600 text-white'
              : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
          }`}
        >
          🟡 Loyal ({loyalData.length})
        </button>
        <button
          onClick={() => setFilter('HIGH_VALUE')}
          className={`px-3 py-1 rounded text-sm font-medium transition ${
            filter === 'HIGH_VALUE'
              ? 'bg-green-600 text-white'
              : 'bg-green-50 text-green-700 hover:bg-green-100'
          }`}
        >
          🟢 High-Value ({highValueData.length})
        </button>
        <button
          onClick={() => setFilter('CASUAL')}
          className={`px-3 py-1 rounded text-sm font-medium transition ${
            filter === 'CASUAL'
              ? 'bg-slate-500 text-white'
              : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
          }`}
        >
          ⚪ Casual ({casualData.length})
        </button>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 80 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={SEMANTIC_COLORS.SLATE} />
          <XAxis 
            type="number"
            dataKey="order_frequency" 
            name="Order Frequency"
            unit=" orders"
            tickFormatter={(value: number) => formatInteger(value)}
            label={{ value: 'Order Frequency', position: 'insideBottomRight', offset: -5 }}
            allowDecimals={false}
          />
          <YAxis 
            dataKey="total_revenue" 
            tickFormatter={(value: number) => formatCurrencyCompact(value)}
            label={{ value: 'Total Revenue ($)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} {...TOOLTIP_STYLES} />
          <ReferenceLine x={medianFreq} stroke={SEMANTIC_COLORS.SLATE} strokeDasharray="3 3" />
          <ReferenceLine y={medianRevenue} stroke={SEMANTIC_COLORS.SLATE} strokeDasharray="3 3" />
          
          {/* Render each segment with its own color */}
          {filteredDatasets.vip.length > 0 && (
            <Scatter
              name="VIP"
              data={filteredDatasets.vip}
              fill="#3B82F6"
              onClick={(e: any) => {
                if (onCustomerSelect && e.customer_name) {
                  onCustomerSelect(e.customer_name);
                }
              }}
              onMouseEnter={(e: any) => setHoveredCustomer(e.customer_name)}
              onMouseLeave={() => setHoveredCustomer(null)}
              style={{ cursor: 'pointer' }}
            />
          )}
          
          {filteredDatasets.loyal.length > 0 && (
            <Scatter
              name="Loyal"
              data={filteredDatasets.loyal}
              fill="#F59E0B"
              onClick={(e: any) => {
                if (onCustomerSelect && e.customer_name) {
                  onCustomerSelect(e.customer_name);
                }
              }}
              onMouseEnter={(e: any) => setHoveredCustomer(e.customer_name)}
              onMouseLeave={() => setHoveredCustomer(null)}
              style={{ cursor: 'pointer' }}
            />
          )}
          
          {filteredDatasets.highValue.length > 0 && (
            <Scatter
              name="High-Value"
              data={filteredDatasets.highValue}
              fill="#10B981"
              onClick={(e: any) => {
                if (onCustomerSelect && e.customer_name) {
                  onCustomerSelect(e.customer_name);
                }
              }}
              onMouseEnter={(e: any) => setHoveredCustomer(e.customer_name)}
              onMouseLeave={() => setHoveredCustomer(null)}
              style={{ cursor: 'pointer' }}
            />
          )}
          
          {filteredDatasets.casual.length > 0 && (
            <Scatter
              name="Casual"
              data={filteredDatasets.casual}
              fill="#94A3B8"
              onClick={(e: any) => {
                if (onCustomerSelect && e.customer_name) {
                  onCustomerSelect(e.customer_name);
                }
              }}
              onMouseEnter={(e: any) => setHoveredCustomer(e.customer_name)}
              onMouseLeave={() => setHoveredCustomer(null)}
              style={{ cursor: 'pointer' }}
            />
          )}
        </ScatterChart>
      </ResponsiveContainer>

      {/* Quadrant Info */}
      <div className="grid grid-cols-2 gap-3 mt-4 text-xs border-t pt-3">
        <div className="p-2 bg-blue-50 rounded">
          <p className="font-semibold text-blue-900">VIP Customers</p>
          <p className="text-blue-700">High Frequency + High Revenue</p>
          <p className="text-blue-600 text-xs">Top-Right Quadrant ({filteredDatasets.vip.length})</p>
        </div>
        <div className="p-2 bg-amber-50 rounded">
          <p className="font-semibold text-amber-900">Loyal Customers</p>
          <p className="text-amber-700">High Frequency + Low Revenue</p>
          <p className="text-amber-600 text-xs">Top-Left Quadrant ({filteredDatasets.loyal.length})</p>
        </div>
        <div className="p-2 bg-green-50 rounded">
          <p className="font-semibold text-green-900">High-Value Deals</p>
          <p className="text-green-700">Low Frequency + High Revenue</p>
          <p className="text-green-600 text-xs">Bottom-Right Quadrant ({filteredDatasets.highValue.length})</p>
        </div>
        <div className="p-2 bg-slate-50 rounded">
          <p className="font-semibold text-slate-900">Casual Buyers</p>
          <p className="text-slate-700">Low Frequency + Low Revenue</p>
          <p className="text-slate-600 text-xs">Bottom-Left Quadrant ({filteredDatasets.casual.length})</p>
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
