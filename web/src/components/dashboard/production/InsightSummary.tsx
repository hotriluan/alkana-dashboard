/**
 * Insight Summary - Natural Language Analysis
 * 
 * Provides human-readable summaries of top production issues:
 * 1. Biggest Volume Loss - High absolute impact
 * 2. Worst Efficiency - Process quality issues
 */
import { AlertTriangle, TrendingDown, Target } from 'lucide-react';
import type { CategoryPerformance } from '@/types/yield';

interface InsightSummaryProps {
  data: CategoryPerformance[];
}

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US').format(Math.round(num));
};

export default function InsightSummary({ data }: InsightSummaryProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
        <p className="text-gray-500 text-center">No data available for analysis</p>
      </div>
    );
  }

  // 1. Biggest Volume Loss (sort by total_loss_kg DESC)
  const biggestLoss = [...data].sort((a, b) => b.total_loss_kg - a.total_loss_kg)[0];

  // 2. Worst Efficiency (sort by loss_pct_avg DESC, filter volume >= 1000kg)
  const significantCategories = data.filter(d => d.total_output_kg >= 1000);
  const worstEfficiency = significantCategories.length > 0
    ? [...significantCategories].sort((a, b) => b.loss_pct_avg - a.loss_pct_avg)[0]
    : null;

  // 3. Best Performer (sort by loss_pct_avg ASC, filter volume >= 1000kg)
  const bestPerformer = significantCategories.length > 0
    ? [...significantCategories].sort((a, b) => a.loss_pct_avg - b.loss_pct_avg)[0]
    : null;

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border-2 border-blue-200 shadow-sm">
      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-blue-600" />
        Performance Insights
      </h3>

      <div className="space-y-4">
        {/* Biggest Volume Loss */}
        {biggestLoss && (
          <div className="bg-white rounded-lg p-4 border-l-4 border-red-500">
            <div className="flex items-start gap-3">
              <TrendingDown className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-red-600 mb-1">🔴 BIGGEST VOLUME LOSS</p>
                <p className="text-gray-800 leading-relaxed">
                  <span className="font-bold">{biggestLoss.category}</span> lost{' '}
                  <span className="font-bold text-red-600">{formatNumber(biggestLoss.total_loss_kg)} kg</span>{' '}
                  ({biggestLoss.loss_pct_avg.toFixed(2)}% loss rate) due to high production volume.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Worst Efficiency */}
        {worstEfficiency && worstEfficiency !== biggestLoss && (
          <div className="bg-white rounded-lg p-4 border-l-4 border-orange-500">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-orange-600 mb-1">⚠️ WORST EFFICIENCY</p>
                <p className="text-gray-800 leading-relaxed">
                  <span className="font-bold">{worstEfficiency.category}</span> has a{' '}
                  <span className="font-bold text-orange-600">{worstEfficiency.loss_pct_avg.toFixed(2)}% loss rate</span>{' '}
                  (process quality issue detected).
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Best Performer */}
        {bestPerformer && (
          <div className="bg-white rounded-lg p-4 border-l-4 border-green-500">
            <div className="flex items-start gap-3">
              <Target className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-green-600 mb-1">✅ BEST PERFORMER</p>
                <p className="text-gray-800 leading-relaxed">
                  <span className="font-bold">{bestPerformer.category}</span> achieved{' '}
                  <span className="font-bold text-green-600">{bestPerformer.loss_pct_avg.toFixed(2)}% loss rate</span>{' '}
                  with {formatNumber(bestPerformer.total_output_kg)} kg produced.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-blue-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-gray-900">{data.length}</p>
            <p className="text-xs text-gray-600">Categories</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-600">
              {formatNumber(data.reduce((sum, d) => sum + d.total_loss_kg, 0))}
            </p>
            <p className="text-xs text-gray-600">Total Loss (kg)</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-blue-600">
              {data.reduce((sum, d) => sum + d.batch_count, 0)}
            </p>
            <p className="text-xs text-gray-600">Total Batches</p>
          </div>
        </div>
      </div>
    </div>
  );
}
