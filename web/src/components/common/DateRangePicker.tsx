// Shared DateRangePicker component for filtering dashboards
import { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onDateChange: (startDate: string, endDate: string) => void;
  label?: string;
}

export const DateRangePicker = ({ 
  startDate, 
  endDate, 
  onDateChange
}: DateRangePickerProps) => {
  const [localStartDate, setLocalStartDate] = useState(startDate);
  const [localEndDate, setLocalEndDate] = useState(endDate);

  // Sync local state with props when they change
  useEffect(() => {
    setLocalStartDate(startDate);
    setLocalEndDate(endDate);
  }, [startDate, endDate]);

  const handleApply = () => {
    onDateChange(localStartDate, localEndDate);
  };

  const handleReset = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const today = `${year}-${month}-${day}`;
    const firstDayOfMonth = `${year}-${month}-01`;
    setLocalStartDate(firstDayOfMonth);
    setLocalEndDate(today);
    onDateChange(firstDayOfMonth, today);
  };

  return (
    <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-sm border border-gray-200">
      <Calendar className="w-5 h-5 text-gray-500" />
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <label className="text-xs text-gray-500 mb-1">From</label>
          <input
            type="date"
            value={localStartDate}
            onChange={(e) => setLocalStartDate(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>
        <span className="text-gray-400 mt-5">-</span>
        <div className="flex flex-col">
          <label className="text-xs text-gray-500 mb-1">To</label>
          <input
            type="date"
            value={localEndDate}
            onChange={(e) => setLocalEndDate(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>
      </div>
      <div className="flex gap-2 ml-2">
        <button
          onClick={handleApply}
          className="px-4 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          Apply
        </button>
        <button
          onClick={handleReset}
          className="px-4 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors text-sm font-medium"
        >
          Reset
        </button>
      </div>
    </div>
  );
};
