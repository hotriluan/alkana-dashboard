/**
 * Period Range Selector for Yield V3
 * Allows selecting start/end periods in MM/YYYY format
 */
import { Calendar } from 'lucide-react';
import { useAvailablePeriods } from '@/hooks/useYieldV3';
import type { AvailablePeriod } from '@/types/yield';

interface PeriodRangeSelectorProps {
  periodStart: string;
  periodEnd: string;
  onPeriodStartChange: (period: string) => void;
  onPeriodEndChange: (period: string) => void;
}

export default function PeriodRangeSelector({
  periodStart,
  periodEnd,
  onPeriodStartChange,
  onPeriodEndChange,
}: PeriodRangeSelectorProps) {
  const { data: availablePeriods, isLoading } = useAvailablePeriods();

  // If no available periods, show loading or empty state
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600" />
        Loading periods...
      </div>
    );
  }

  if (!availablePeriods || availablePeriods.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic">
        No data available. Please upload data first.
      </div>
    );
  }

  // Build period options from available periods
  const periodOptions = availablePeriods.map((p: AvailablePeriod) => p.period);

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <Calendar className="w-4 h-4 text-gray-400" />
        <span className="text-sm font-medium text-gray-700">Period:</span>
      </div>

      {/* Start Period */}
      <select
        value={periodStart}
        onChange={(e) => onPeriodStartChange(e.target.value)}
        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="" disabled>
          Select start
        </option>
        {periodOptions.map((period) => (
          <option key={period} value={period}>
            {period}
          </option>
        ))}
      </select>

      <span className="text-gray-400">→</span>

      {/* End Period */}
      <select
        value={periodEnd}
        onChange={(e) => onPeriodEndChange(e.target.value)}
        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="" disabled>
          Select end
        </option>
        {periodOptions.map((period) => (
          <option key={period} value={period}>
            {period}
          </option>
        ))}
      </select>

      {/* Quick Filters */}
      <div className="flex gap-2 ml-4">
        <button
          onClick={() => {
            if (periodOptions.length > 0) {
              const latest = periodOptions[0];
              onPeriodStartChange(latest);
              onPeriodEndChange(latest);
            }
          }}
          className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
        >
          Latest Month
        </button>
        <button
          onClick={() => {
            if (periodOptions.length >= 3) {
              onPeriodStartChange(periodOptions[2]);
              onPeriodEndChange(periodOptions[0]);
            }
          }}
          className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
        >
          Last 3 Months
        </button>
        <button
          onClick={() => {
            if (periodOptions.length > 0) {
              onPeriodStartChange(periodOptions[periodOptions.length - 1]);
              onPeriodEndChange(periodOptions[0]);
            }
          }}
          className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
        >
          All Time
        </button>
      </div>
    </div>
  );
}
