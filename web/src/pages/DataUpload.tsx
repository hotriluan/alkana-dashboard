/**
 * Data Upload Page - V4 Centralized Smart Ingestion
 * Main page for uploading ALL SAP Excel files
 * 
 * Features:
 * - Auto-detection of file types
 * - Period selector modal for ZRPP062 (Production Yield)
 * - Automatic routing to correct endpoints
 * - Unified upload experience
 */
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload as UploadIcon, AlertCircle, Calendar, X } from 'lucide-react';
import { uploadAPI } from '../services/api';
import { FileUpload } from '../components/upload/FileUpload';
import { UploadStatusComponent } from '../components/upload/UploadStatus';
import { UploadHistory } from '../components/upload/UploadHistory';
import { detectFileType, guessFromFilename, DETECTION_RULES, type DetectionRule } from '../utils/fileDetection';

const DataUpload = () => {
  const [currentUploadId, setCurrentUploadId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detectedFile, setDetectedFile] = useState<{ file: File; rule: DetectionRule } | null>(null);
  const [showPeriodModal, setShowPeriodModal] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: ({ file, snapshotDate }: { file: File; snapshotDate?: string }) =>
      uploadAPI.uploadFile(file, snapshotDate),
    onSuccess: (data) => {
      setCurrentUploadId(data.upload_id);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['upload-history'] });
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  // Smart upload mutation for detected files
  const smartUploadMutation = useMutation({
    mutationFn: async ({ file, endpoint, month, year }: { 
      file: File; 
      endpoint: string;
      month?: number; 
      year?: number;
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      
      if (month && year) {
        formData.append('month', month.toString());
        formData.append('year', year.toString());
      }
      
      // Use relative URL so it works in both dev and production
      const baseUrl = window.location.origin;
      const fullEndpoint = `${baseUrl}${endpoint}`;
      console.log('🚀 Uploading to:', fullEndpoint, { month, year });
      
      const response = await fetch(fullEndpoint, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        } else {
          throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
        }
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      setError(null);
      setShowPeriodModal(false);
      setDetectedFile(null);
      
      // Set upload ID for tracking
      if (data.upload_id) {
        setCurrentUploadId(data.upload_id);
      }
      
      // Show success message with details
      const message = `✅ Upload successful!\n\n` +
        `File: ${data.file_name || 'Unknown'}\n` +
        `Loaded: ${data.records_loaded || 0} records\n` +
        `Updated: ${data.records_updated || 0} records`;
      
      alert(message);
      
      // Refresh all relevant queries
      queryClient.invalidateQueries({ queryKey: ['yield', 'v3'] });
      queryClient.invalidateQueries({ queryKey: ['upload-history'] });
      queryClient.invalidateQueries({ queryKey: ['yield'] });
    },
    onError: (error: Error) => {
      setError(error.message);
      setShowPeriodModal(false);
    },
  });

  const handleFileDropped = async (file: File) => {
    console.log('📁 File dropped:', file.name);
    
    // Try to detect file type
    let detectedRule = await detectFileType(file);
    
    // Fallback: guess from filename
    if (!detectedRule) {
      const guessedType = guessFromFilename(file.name);
      if (guessedType) {
        console.log('🔍 File type guessed from filename:', guessedType);
        // Find rule by type
        detectedRule = DETECTION_RULES.find(r => r.type === guessedType) || null;
      }
    }
    
    if (detectedRule) {
      console.log('✅ File detected:', detectedRule.type, '| Requires period:', detectedRule.requiresPeriod);
      
      // If file requires period (ZRPP062), show modal immediately
      if (detectedRule.requiresPeriod) {
        setDetectedFile({ file, rule: detectedRule });
        setShowPeriodModal(true);
      }
    } else {
      console.warn('⚠️ File type not detected');
    }
  };

  const handleFileSelect = async (file: File, snapshotDate?: string) => {
    setError(null);
    
    // Check if file was already detected
    if (detectedFile && detectedFile.file === file) {
      // File already detected, just proceed with upload
      if (detectedFile.rule.requiresPeriod) {
        // Period modal should already be showing
        return;
      }
      
      // Auto-upload for other files
      smartUploadMutation.mutate({ 
        file, 
        endpoint: detectedFile.rule.endpoint 
      });
      return;
    }
    
    // Try to detect file type
    const detectedRule = await detectFileType(file);
    
    if (detectedRule) {
      console.log('✅ File detected:', detectedRule.type, '| Requires period:', detectedRule.requiresPeriod);
      
      // If file requires period (ZRPP062), show modal
      if (detectedRule.requiresPeriod) {
        setDetectedFile({ file, rule: detectedRule });
        setShowPeriodModal(true);
        return;
      }
      
      // Auto-upload for other detected files
      setDetectedFile({ file, rule: detectedRule });
      smartUploadMutation.mutate({ 
        file, 
        endpoint: detectedRule.endpoint 
      });
    } else {
      console.warn('⚠️ File type not detected, using fallback upload');
      // Fallback to standard upload (legacy V1 endpoint)
      uploadMutation.mutate({ file, snapshotDate });
    }
  };

  const handlePeriodConfirm = () => {
    if (detectedFile) {
      smartUploadMutation.mutate({
        file: detectedFile.file,
        endpoint: detectedFile.rule.endpoint,
        month: selectedMonth,
        year: selectedYear,
      });
    }
  };

  const handleUploadComplete = () => {
    queryClient.invalidateQueries({ queryKey: ['upload-history'] });
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <UploadIcon className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Data Upload</h1>
        </div>
        <p className="text-gray-600">
          Upload SAP Excel files to update dashboard data. Files are automatically detected and routed.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-900">Upload Failed</h4>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Upload Section */}
        <div>
          <FileUpload
            onFileSelect={handleFileSelect}
            onFileDropped={handleFileDropped}
            isUploading={uploadMutation.isPending || smartUploadMutation.isPending}
          />
        </div>

        {/* Current Upload Status */}
        <div>
          {currentUploadId && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Current Upload</h3>
              <UploadStatusComponent
                uploadId={currentUploadId}
                onComplete={handleUploadComplete}
              />
            </div>
          )}

          {!currentUploadId && !smartUploadMutation.isPending && (
            <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8">
              <div className="text-center text-gray-500">
                <UploadIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No active upload</p>
                <p className="text-sm mt-1">Select a file to begin</p>
              </div>
            </div>
          )}

          {smartUploadMutation.isPending && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mx-auto mb-3" />
                <p className="font-medium text-blue-900">Uploading...</p>
                <p className="text-sm text-blue-700 mt-1">Processing {detectedFile?.file.name}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Period Selector Modal */}
      {showPeriodModal && detectedFile && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Calendar className="w-6 h-6 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-900">Select Reporting Period</h2>
              </div>
              <button
                onClick={() => setShowPeriodModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-4">
                Detected: <strong>{detectedFile.rule.label}</strong>
              </p>
              <p className="text-sm text-gray-600 mb-4">
                This file contains production yield data. Please select the reporting period.
              </p>

              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Month</label>
                  <select
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                      <option key={m} value={m}>
                        {new Date(2020, m - 1).toLocaleString('en', { month: 'long' })}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="w-28">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Year</label>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - 2 + i).map(
                      (y) => (
                        <option key={y} value={y}>
                          {y}
                        </option>
                      )
                    )}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowPeriodModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handlePeriodConfirm}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Upload
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload History */}
      <div className="mt-8">
        <UploadHistory />
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">📘 Smart Upload Guidelines</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>Auto-Detection:</strong> File type is detected from column headers</li>
          <li>• <strong>ZRPP062 (Yield):</strong> Requires reporting period (month/year)</li>
          <li>• <strong>ZRSD006 (Master):</strong> Uploads immediately, updates product hierarchy</li>
          <li>• <strong>File Format:</strong> Excel files (.xlsx, .xls)</li>
          <li>• <strong>File Size:</strong> Maximum 50MB</li>
          <li>• <strong>Upsert Mode:</strong> Updates existing, inserts new, skips unchanged</li>
        </ul>
      </div>
    </div>
  );
};

export default DataUpload;
