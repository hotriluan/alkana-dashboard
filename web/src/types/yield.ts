/**
 * TypeScript types for Yield V3 API
 * Auto-generated from src/api/routers/yield_v3.py
 */

export interface YieldKPI {
  total_orders: number;
  total_output_kg: number;
  total_input_kg: number;
  total_loss_kg: number;
  avg_yield_pct: number;
  avg_loss_pct: number;
  high_loss_count: number;
  period_start: string; // MM/YYYY
  period_end: string;   // MM/YYYY
}

export interface TrendDataPoint {
  period: string; // MM/YYYY
  avg_yield_pct: number;
  avg_loss_pct: number;
  total_output_kg: number;
  order_count: number;
}

export interface DistributionDataPoint {
  product_group: string;
  avg_yield_pct: number;
  avg_loss_pct: number;
  total_output_kg: number;
  order_count: number;
}

export interface CategoryPerformance {
  category: string;
  total_output_kg: number;
  total_loss_kg: number;
  loss_pct_avg: number;  // Weighted: (total_loss / (total_output + total_loss)) * 100
  batch_count: number;
}

export interface ParetoDataPoint {
  material_code: string;
  material_description: string | null;
  total_loss_kg: number;
  avg_loss_pct: number;
  cumulative_pct: number;
}

export interface QualityDataPoint {
  process_order_id: string;
  material_code: string | null;
  sg_theoretical: number | null;
  sg_actual: number | null;
  sg_variance: number;
  loss_pct: number | null;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  records_loaded: number;
  records_updated: number;
  records_skipped: number;
  errors: string[];
  reference_date: string; // YYYY-MM-DD
}

export interface AvailablePeriod {
  period: string; // MM/YYYY
  record_count: number;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  version: string;
  database?: {
    total_records: number;
    periods_count: number;
    earliest_period: string | null;
    latest_period: string | null;
  };
  error?: string;
}
