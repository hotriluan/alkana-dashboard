/**
 * React Query hooks for Yield V3 API
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { API_BASE_URL } from '@/services/api';
import type {
  YieldKPI,
  TrendDataPoint,
  DistributionDataPoint,
  CategoryPerformance,
  ParetoDataPoint,
  QualityDataPoint,
  UploadResponse,
  AvailablePeriod,
  HealthResponse
} from '@/types/yield';

const BASE_PATH = `${API_BASE_URL}/api/v3/yield`;

// ============================================================================
// Query Hooks
// ============================================================================

export function useYieldHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['yield', 'v3', 'health'],
    queryFn: async () => {
      const res = await fetch(`${BASE_PATH}/health`);
      if (!res.ok) throw new Error('Failed to fetch health status');
      return res.json();
    },
    staleTime: 60000, // 1 minute
  });
}

export function useAvailablePeriods() {
  return useQuery<AvailablePeriod[]>({
    queryKey: ['yield', 'v3', 'periods'],
    queryFn: async () => {
      const res = await fetch(`${BASE_PATH}/periods`);
      if (!res.ok) throw new Error('Failed to fetch available periods');
      return res.json();
    },
    staleTime: 300000, // 5 minutes
  });
}

export function useYieldKPI(periodStart: string, periodEnd: string) {
  return useQuery<YieldKPI>({
    queryKey: ['yield', 'v3', 'kpi', periodStart, periodEnd],
    queryFn: async () => {
      const params = new URLSearchParams({ period_start: periodStart, period_end: periodEnd });
      const res = await fetch(`${BASE_PATH}/kpi?${params}`);
      if (!res.ok) throw new Error('Failed to fetch KPIs');
      return res.json();
    },
    enabled: !!periodStart && !!periodEnd,
    staleTime: 60000,
  });
}

export function useYieldTrend(periodStart: string, periodEnd: string) {
  return useQuery<TrendDataPoint[]>({
    queryKey: ['yield', 'v3', 'trend', periodStart, periodEnd],
    queryFn: async () => {
      const params = new URLSearchParams({ period_start: periodStart, period_end: periodEnd });
      const res = await fetch(`${BASE_PATH}/trend?${params}`);
      if (!res.ok) throw new Error('Failed to fetch trend data');
      return res.json();
    },
    enabled: !!periodStart && !!periodEnd,
    staleTime: 60000,
  });
}

export function useYieldDistribution(
  periodStart: string,
  periodEnd: string,
  groupBy: 'ph_level_1' | 'ph_level_2' | 'ph_level_3' | 'product_group_1' | 'product_group_2' | 'mrp_controller' = 'ph_level_3'
) {
  return useQuery<DistributionDataPoint[]>({
    queryKey: ['yield', 'v3', 'distribution', periodStart, periodEnd, groupBy],
    queryFn: async () => {
      const params = new URLSearchParams({
        period_start: periodStart,
        period_end: periodEnd,
        group_by: groupBy,
      });
      const res = await fetch(`${BASE_PATH}/distribution?${params}`);
      if (!res.ok) throw new Error('Failed to fetch distribution data');
      return res.json();
    },
    enabled: !!periodStart && !!periodEnd,
    staleTime: 60000,
  });
}

export interface DrillDownMaterial {
  material_code: string;
  material_description: string | null;
  total_loss_kg: number;
  avg_loss_pct: number;
  order_count: number;
}

export function useDistributionDetails(
  periodStart: string,
  periodEnd: string,
  category: string,
  level: 'ph_level_1' | 'ph_level_2' | 'ph_level_3' = 'ph_level_3'
) {
  return useQuery<DrillDownMaterial[]>({
    queryKey: ['yield', 'v3', 'distribution', 'details', periodStart, periodEnd, category, level],
    queryFn: async () => {
      const params = new URLSearchParams({
        period_start: periodStart,
        period_end: periodEnd,
        category,
        level,
      });
      const res = await fetch(`${BASE_PATH}/distribution/details?${params}`);
      if (!res.ok) throw new Error('Failed to fetch drill-down details');
      return res.json();
    },
    enabled: !!periodStart && !!periodEnd && !!category,
    staleTime: 60000,
  });
}

export function useYieldPareto(periodStart: string, periodEnd: string, limit: number = 10) {
  return useQuery<ParetoDataPoint[]>({
    queryKey: ['yield', 'v3', 'pareto', periodStart, periodEnd, limit],
    queryFn: async () => {
      const params = new URLSearchParams({
        period_start: periodStart,
        period_end: periodEnd,
        limit: limit.toString(),
      });
      const res = await fetch(`${BASE_PATH}/pareto?${params}`);
      if (!res.ok) throw new Error('Failed to fetch Pareto data');
      return res.json();
    },
    enabled: !!periodStart && !!periodEnd,
    staleTime: 60000,
  });
}

export function useYieldQuality(periodStart: string, periodEnd: string, limit: number = 100) {
  return useQuery<QualityDataPoint[]>({
    queryKey: ['yield', 'v3', 'quality', periodStart, periodEnd, limit],
    queryFn: async () => {
      const params = new URLSearchParams({
        period_start: periodStart,
        period_end: periodEnd,
        limit: limit.toString(),
      });
      const res = await fetch(`${BASE_PATH}/quality?${params}`);
      if (!res.ok) throw new Error('Failed to fetch quality data');
      return res.json();
    },
    enabled: !!periodStart && !!periodEnd,
    staleTime: 60000,
  });
}

export function useCategoryPerformance(periodStart: string, periodEnd: string) {
  return useQuery<CategoryPerformance[]>({
    queryKey: ['yield', 'v3', 'category-performance', periodStart, periodEnd],
    queryFn: async () => {
      const params = new URLSearchParams({
        period_start: periodStart,
        period_end: periodEnd,
      });
      const res = await fetch(`${BASE_PATH}/category-performance?${params}`);
      if (!res.ok) throw new Error('Failed to fetch category performance data');
      return res.json();
    },
    enabled: !!periodStart && !!periodEnd,
    staleTime: 60000,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

interface UploadParams {
  file: File;
  month: number;
  year: number;
}

interface MasterDataUploadParams {
  file: File;
}

export function useYieldUpload() {
  const queryClient = useQueryClient();

  return useMutation<UploadResponse, Error, UploadParams>({
    mutationFn: async ({ file, month, year }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('month', month.toString());
      formData.append('year', year.toString());

      const res = await fetch(`${BASE_PATH}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Upload failed');
      }

      return res.json();
    },
    onSuccess: () => {
      // Invalidate all yield queries to refetch data
      queryClient.invalidateQueries({ queryKey: ['yield', 'v3'] });
    },
  });
}

export function useMasterDataUpload() {
  const queryClient = useQueryClient();

  return useMutation<UploadResponse, Error, MasterDataUploadParams>({
    mutationFn: async ({ file }) => {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${BASE_PATH}/upload-master-data`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Master data upload failed');
      }

      return res.json();
    },
    onSuccess: () => {
      // Invalidate distribution queries to refetch with new categories
      queryClient.invalidateQueries({ queryKey: ['yield', 'v3', 'distribution'] });
    },
  });
}
