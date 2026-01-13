/**
 * VarianceAnalysisTable - Production Variance Analysis Component (V2)
 * 
 * Displays top materials with highest production loss.
 * Features:
 * - Top 20 materials by loss (KG)
 * - Highlights Loss% > 2.0 in red
 * - Sortable columns
 * - Product group filtering
 * 
 * Reference: ARCHITECTURAL DIRECTIVE Production Yield V2.1, Task 3.1, Deep Clean 2026-01-12
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, TrendingDown, Package, Activity } from 'lucide-react';
import { KPICard } from '../../common/KPICard';
import { DataTable } from '../../common/DataTable';
import api from '../../../services/api';

// ============================================================================
// Types (matching API response)
// ============================================================================

interface MaterialVariance {
  material_code: string;
  material_description: string | null;
  total_output_kg: number;
  total_input_kg: number;
  total_loss_kg: number;
  avg_loss_pct: number;
  order_count: number;
}

interface VarianceSummary {
  total_orders: number;
  total_output_kg: number;
  total_input_kg: number;
  total_loss_kg: number;
  avg_loss_pct: number;
  materials_with_high_loss: number;
}

interface OrderVarianceDetail {
  process_order_id: string;
  batch_id: string | null;
  material_code: string | null;
  material_description: string | null;
  parent_order_id: string | null;
  output_actual_kg: number | null;
  input_actual_kg: number | null;
  loss_kg: number | null;
  loss_pct: number | null;
  sg_theoretical: number | null;
  sg_actual: number | null;
}

// ============================================================================
// API Functions
// ============================================================================

const fetchVarianceSummary = async (): Promise<VarianceSummary> => {
  const response = await api.get<VarianceSummary>('/api/v2/yield/variance/summary');
  return response.data;
};

const fetchOrderDetails = async (materialCode?: string): Promise<OrderVarianceDetail[]> => {
  const params: Record<string, unknown> = { limit: 50 };
  if (materialCode) {
    params.material_code = materialCode;
  }
  const response = await api.get<OrderVarianceDetail[]>('/api/v2/yield/variance/details', { params });
  return response.data;
};

// ============================================================================
// Helper Functions
// ============================================================================

const formatNumber = (value: number | null | undefined, decimals: number = 1): string => {
  if (value === null || value === undefined) return '-';
  return value.toLocaleString('vi-VN', { 
    minimumFractionDigits: decimals, 
    maximumFractionDigits: decimals 
  });
};

const formatKg = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  if (Math.abs(value) >= 1000) {
    return `${(value / 1000).toFixed(1)}T`;
  }
  return `${value.toFixed(1)} kg`;
};

const formatPercent = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  return `${value.toFixed(2)}%`;
};

// ============================================================================
// Component
// ============================================================================

const VarianceAnalysisTable = () => {
  const [selectedMaterial, setSelectedMaterial] = useState<string | null>(null);
  const [showHighLossOnly, setShowHighLossOnly] = useState(false);

  // Fetch summary KPIs
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['variance-summary'],
    queryFn: fetchVarianceSummary,
    staleTime: 30000, // 30 seconds
  });

  // Fetch material variance data
  const { data: materials, isLoading: materialsLoading } = useQuery({
    queryKey: ['material-variance', showHighLossOnly],
    queryFn: async () => {
      const response = await api.get<MaterialVariance[]>('/api/v2/yield/variance', {
        params: { 
          limit: 20,
          min_loss_pct: showHighLossOnly ? 2.0 : undefined
        }
      });
      return response.data;
    },
    staleTime: 30000,
  });

  // Fetch order details when material is selected
  const { data: orderDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['order-variance-details', selectedMaterial],
    queryFn: () => fetchOrderDetails(selectedMaterial || undefined),
    enabled: !!selectedMaterial,
    staleTime: 30000,
  });

  // Material table columns
  const materialColumns = [
    {
      key: 'material_code' as keyof MaterialVariance,
      header: 'Material Code',
      sortable: true,
      render: (value: string, _row: MaterialVariance) => (
        <button 
          onClick={() => setSelectedMaterial(value)}
          className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
        >
          {value}
        </button>
      ),
    },
    {
      key: 'material_description' as keyof MaterialVariance,
      header: 'Description',
      sortable: true,
      render: (value: string | null) => (
        <span className="text-gray-600 truncate max-w-xs block" title={value || ''}>
          {value || '-'}
        </span>
      ),
    },
    {
      key: 'total_output_kg' as keyof MaterialVariance,
      header: 'Output (KG)',
      sortable: true,
      align: 'right' as const,
      render: (value: number) => formatKg(value),
    },
    {
      key: 'total_loss_kg' as keyof MaterialVariance,
      header: 'Loss (KG)',
      sortable: true,
      align: 'right' as const,
      render: (value: number) => (
        <span className={value > 0 ? 'text-red-600 font-medium' : ''}>
          {formatKg(value)}
        </span>
      ),
    },
    {
      key: 'avg_loss_pct' as keyof MaterialVariance,
      header: 'Avg Loss %',
      sortable: true,
      align: 'right' as const,
      render: (value: number) => {
        const isHighLoss = value > 2.0;
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            isHighLoss 
              ? 'bg-red-100 text-red-800' 
              : value > 1.0 
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-green-100 text-green-800'
          }`}>
            {formatPercent(value)}
          </span>
        );
      },
    },
    {
      key: 'order_count' as keyof MaterialVariance,
      header: 'Orders',
      sortable: true,
      align: 'right' as const,
      render: (value: number) => value.toLocaleString(),
    },
  ];

  // Order detail columns
  const orderColumns = [
    {
      key: 'process_order_id' as keyof OrderVarianceDetail,
      header: 'Process Order',
      sortable: true,
    },
    {
      key: 'batch_id' as keyof OrderVarianceDetail,
      header: 'Batch',
      sortable: true,
      render: (value: string | null) => value || '-',
    },
    {
      key: 'output_actual_kg' as keyof OrderVarianceDetail,
      header: 'Output (KG)',
      sortable: true,
      align: 'right' as const,
      render: (value: number | null) => formatNumber(value, 2),
    },
    {
      key: 'input_actual_kg' as keyof OrderVarianceDetail,
      header: 'Input (KG)',
      sortable: true,
      align: 'right' as const,
      render: (value: number | null) => formatNumber(value, 2),
    },
    {
      key: 'loss_kg' as keyof OrderVarianceDetail,
      header: 'Loss (KG)',
      sortable: true,
      align: 'right' as const,
      render: (value: number | null) => (
        <span className={value && value > 0 ? 'text-red-600 font-medium' : ''}>
          {formatNumber(value, 2)}
        </span>
      ),
    },
    {
      key: 'loss_pct' as keyof OrderVarianceDetail,
      header: 'Loss %',
      sortable: true,
      align: 'right' as const,
      render: (value: number | null) => {
        if (value === null) return '-';
        const isHighLoss = value > 2.0;
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            isHighLoss 
              ? 'bg-red-100 text-red-800' 
              : value > 1.0 
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-green-100 text-green-800'
          }`}>
            {formatPercent(value)}
          </span>
        );
      },
    },
    {
      key: 'sg_actual' as keyof OrderVarianceDetail,
      header: 'SG Actual',
      sortable: true,
      align: 'right' as const,
      render: (value: number | null) => value?.toFixed(4) || '-',
    },
  ];

  const isLoading = summaryLoading || materialsLoading;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Production Variance Analysis</h1>
          <p className="text-gray-500 mt-1">V2 - Isolated Analysis from ZRPP062</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showHighLossOnly}
              onChange={(e) => setShowHighLossOnly(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Show High Loss Only (&gt; 2%)</span>
          </label>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Orders"
          value={summary?.total_orders.toLocaleString() || '0'}
          icon={<Package className="w-6 h-6" />}
          loading={summaryLoading}
        />
        <KPICard
          title="Total Output"
          value={formatKg(summary?.total_output_kg)}
          icon={<Activity className="w-6 h-6" />}
          loading={summaryLoading}
        />
        <KPICard
          title="Total Loss"
          value={formatKg(summary?.total_loss_kg)}
          icon={<TrendingDown className="w-6 h-6" />}
          loading={summaryLoading}
          className={summary && summary.total_loss_kg > 0 ? 'border-red-200' : ''}
        />
        <KPICard
          title="High Loss Materials"
          value={summary?.materials_with_high_loss.toString() || '0'}
          subtitle="Loss % > 2.0"
          icon={<AlertTriangle className="w-6 h-6" />}
          loading={summaryLoading}
          className={summary && summary.materials_with_high_loss > 0 ? 'border-yellow-200' : ''}
        />
      </div>

      {/* Materials Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Top 20 Materials by Loss
          </h2>
          <p className="text-sm text-gray-500">
            Click material code to view order details
          </p>
        </div>
        {isLoading ? (
          <div className="p-6 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <DataTable
            data={materials || []}
            columns={materialColumns}
            maxHeight="400px"
          />
        )}
      </div>

      {/* Order Details (when material selected) */}
      {selectedMaterial && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Order Details: {selectedMaterial}
              </h2>
              <p className="text-sm text-gray-500">
                Showing individual orders for selected material
              </p>
            </div>
            <button
              onClick={() => setSelectedMaterial(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕ Close
            </button>
          </div>
          {detailsLoading ? (
            <div className="p-6 flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <DataTable
              data={orderDetails || []}
              columns={orderColumns}
              maxHeight="300px"
            />
          )}
        </div>
      )}
    </div>
  );
};

export default VarianceAnalysisTable;
