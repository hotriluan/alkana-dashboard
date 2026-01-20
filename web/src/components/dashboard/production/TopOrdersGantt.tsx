/**
 * Top Orders Gantt-Style Chart
 * Lightweight HTML/Tailwind implementation (no Recharts)
 * Shows top 10 orders with timeline from release to finish
 */
import React from 'react';
import { Spinner } from '../../common/Spinner';

interface OrderGantt {
  order_number: string;
  material_code: string;
  order_qty_kg: number;
  release_date: string;
  actual_finish: string;
  is_delayed: boolean;
}

interface TopOrdersGanttProps {
  data: OrderGantt[];
  loading?: boolean;
}

const TopOrdersGantt: React.FC<TopOrdersGanttProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-80">
        <Spinner />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center bg-slate-50 rounded h-80">
        <p className="text-slate-500">No orders data available</p>
      </div>
    );
  }

  // Parse dates and calculate position
  const calculatePosition = (date: string): number => {
    const d = new Date(date);
    return d.getTime();
  };

  const dates = data.flatMap((o) => [
    calculatePosition(o.release_date),
    calculatePosition(o.actual_finish || o.release_date),
  ]);
  const minDate = Math.min(...dates);
  const maxDate = Math.max(...dates);
  const dateRange = maxDate - minDate || 86400000; // 1 day fallback

  const getProgressWidth = (order: OrderGantt): number => {
    const start = calculatePosition(order.release_date);
    const end = calculatePosition(order.actual_finish || order.release_date);
    const progress = ((end - start) / dateRange) * 100;
    return Math.max(5, Math.min(100, progress)); // Min 5%, Max 100%
  };

  const getLeftOffset = (order: OrderGantt): number => {
    const start = calculatePosition(order.release_date);
    const offset = ((start - minDate) / dateRange) * 100;
    return offset;
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Top 10 Orders Timeline</h3>
      
      <div className="space-y-3">
        {data.map((order) => (
          <div key={order.order_number}>
            {/* Label with order info */}
            <div className="flex justify-between items-start mb-1">
              <div>
                <p className="text-sm font-semibold">{order.order_number}</p>
                <p className="text-xs text-slate-600">{order.material_code} • {order.order_qty_kg.toFixed(0)} kg</p>
              </div>
              <span className={`text-xs font-semibold px-2 py-1 rounded ${
                order.is_delayed ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
              }`}>
                {order.is_delayed ? 'DELAYED' : 'ON TRACK'}
              </span>
            </div>

            {/* Gantt bar */}
            <div className="relative h-6 bg-slate-100 rounded overflow-hidden">
              <div
                className={`h-full rounded transition-all ${
                  order.is_delayed ? 'bg-red-500' : 'bg-blue-500'
                }`}
                style={{
                  width: `${getProgressWidth(order)}%`,
                  marginLeft: `${getLeftOffset(order)}%`,
                }}
                title={`From ${order.release_date} to ${order.actual_finish}`}
              />
            </div>

            {/* Date labels */}
            <div className="flex justify-between text-xs text-slate-500 mt-0.5">
              <span>{new Date(order.release_date).toLocaleDateString()}</span>
              <span>{new Date(order.actual_finish || order.release_date).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-6 text-xs border-t pt-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500 rounded" />
          <span>On Track</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded" />
          <span>Delayed</span>
        </div>
      </div>
    </div>
  );
};

export default TopOrdersGantt;
