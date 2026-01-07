/**
 * Upload API Types
 * 
 * Skills: typescript, type-safety
 */

export interface UploadResponse {
  upload_id: number;
  status: string;
  message: string;
}

export interface UploadStatus {
  upload_id: number;
  file_name: string;
  original_name: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  processed_at: string | null;
  rows_loaded: number;
  rows_updated: number;
  rows_skipped: number;
  rows_failed: number;
  error_message: string | null;
  snapshot_date: string | null;
}

export interface UploadHistoryItem {
  upload_id: number;
  original_name: string;
  file_type: string;
  status: string;
  uploaded_at: string;
  rows_loaded: number;
  rows_failed: number;
}
