// API Service - Axios client for Alkana Dashboard
import axios from 'axios';
import type { ARCollectionSummary, ARAgingBucket, ARCustomerDetail, User, LoginRequest, LoginResponse } from '../types';
import type { UploadResponse, UploadStatus, UploadHistoryItem } from '../types/upload';

export const API_BASE_URL = 'http://localhost:8000';

// Axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await api.post<LoginResponse>('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/api/v1/auth/me');
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/api/v1/auth/logout');
    localStorage.removeItem('access_token');
  },
};

// AR Aging API
export const arAgingAPI = {
  getSnapshots: async (): Promise<{ snapshot_date: string; row_count: number }[]> => {
    const response = await api.get<{ snapshot_date: string; row_count: number }[]>('/api/v1/dashboards/ar-aging/snapshots');
    return response.data;
  },

  getSummary: async (snapshotDate?: string): Promise<ARCollectionSummary> => {
    const params = snapshotDate ? { snapshot_date: snapshotDate } : {};
    const response = await api.get<ARCollectionSummary>('/api/v1/dashboards/ar-aging/summary', { params });
    return response.data;
  },

  getByBucket: async (snapshotDate?: string): Promise<ARAgingBucket[]> => {
    const params = snapshotDate ? { snapshot_date: snapshotDate } : {};
    const response = await api.get<ARAgingBucket[]>('/api/v1/dashboards/ar-aging/by-bucket', { params });
    return response.data;
  },

  getCustomers: async (snapshotDate?: string, riskLevel?: string, limit: number = 50): Promise<ARCustomerDetail[]> => {
    const params = { snapshot_date: snapshotDate, risk_level: riskLevel, limit };
    const response = await api.get<ARCustomerDetail[]>('/api/v1/dashboards/ar-aging/customers', { params });
    return response.data;
  },
};

// Upload API
export const uploadAPI = {
  /**
   * Upload file with optional snapshot_date for AR data
   */
  uploadFile: async (file: File, snapshotDate?: string): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (snapshotDate) {
      formData.append('snapshot_date', snapshotDate);
    }

    const response = await api.post<UploadResponse>('/api/v1/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Get upload status by ID
   */
  getStatus: async (uploadId: number): Promise<UploadStatus> => {
    const response = await api.get<UploadStatus>(`/api/v1/upload/${uploadId}/status`);
    return response.data;
  },

  /**
   * Get upload history
   */
  getHistory: async (limit: number = 20): Promise<UploadHistoryItem[]> => {
    const response = await api.get<UploadHistoryItem[]>('/api/v1/upload/history', {
      params: { limit },
    });
    return response.data;
  },
};

export default api;
