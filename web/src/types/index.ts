// TypeScript types for Alkana Dashboard - AR Aging

export interface ARCollectionTotal {
  division: string;
  dist_channel: string;
  total_target: number;
  total_realization: number;
  collection_rate_pct: number;
  report_date?: string;
}

export interface ARCollectionSummary {
  total_target: number;
  total_realization: number;
  collection_rate_pct: number;
  report_date: string | null;
  divisions: ARCollectionTotal[];
}

export interface ARAgingBucket {
  bucket: string;
  target_amount: number;
  realization_amount: number;
}

export interface ARCustomerDetail {
  division: string;
  salesman_name: string | null;
  customer_name: string;
  total_target: number;
  total_realization: number;
  collection_rate_pct: number;
  not_due: number;
  target_1_30: number;
  target_31_60: number;
  target_61_90: number;
  target_91_120: number;
  target_121_180: number;
  target_over_180: number;
  risk_level: string;
}

export interface User {
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
