/**
 * Upload Status Component
 * Display upload progress and results
 * 
 * Skills: react, typescript, polling
 */
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle, XCircle, Clock, Loader2, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { uploadAPI } from '../../services/api';

interface UploadStatusProps {
  uploadId: number;
  onComplete?: () => void;
}

export const UploadStatusComponent = ({ uploadId, onComplete }: UploadStatusProps) => {
  const { data: status, isLoading, error } = useQuery({
    queryKey: ['upload-status', uploadId],
    queryFn: () => uploadAPI.getStatus(uploadId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Poll every 1 second if pending/processing
      if (status === 'pending' || status === 'processing') {
        return 1000;
      }
      // Stop polling if completed/failed
      return false;
    },
  });

  // Call onComplete callback when upload finishes
  useEffect(() => {
    if (status && (status.status === 'completed' || status.status === 'failed') && onComplete) {
      onComplete();
    }
  }, [status, onComplete]);

  if (isLoading && !status) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-3">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          <span className="text-gray-600">Loading status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-red-900">Error loading status</h4>
            <p className="text-sm text-red-700 mt-1">{(error as Error).message}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!status) return null;

  const getStatusIcon = () => {
    switch (status.status) {
      case 'completed':
        return <CheckCircle className="w-8 h-8 text-green-600" />;
      case 'failed':
        return <XCircle className="w-8 h-8 text-red-600" />;
      case 'processing':
        return <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />;
      case 'pending':
        return <Clock className="w-8 h-8 text-yellow-600" />;
      default:
        return <AlertCircle className="w-8 h-8 text-gray-600" />;
    }
  };

  const getStatusColor = () => {
    switch (status.status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      case 'processing':
        return 'bg-blue-50 border-blue-200';
      case 'pending':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`rounded-lg border p-6 ${getStatusColor()}`}>
      <div className="flex items-start space-x-4">
        {getStatusIcon()}
        
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h4 className="text-lg font-semibold">
              {status.status === 'completed' && 'Upload Complete'}
              {status.status === 'failed' && 'Upload Failed'}
              {status.status === 'processing' && 'Processing...'}
              {status.status === 'pending' && 'Upload Pending'}
            </h4>
            <span className={`
              px-2 py-1 rounded text-xs font-medium
              ${status.status === 'completed' ? 'bg-green-100 text-green-800' : ''}
              ${status.status === 'failed' ? 'bg-red-100 text-red-800' : ''}
              ${status.status === 'processing' ? 'bg-blue-100 text-blue-800' : ''}
              ${status.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : ''}
            `}>
              {status.status.toUpperCase()}
            </span>
          </div>

          <div className="flex items-center space-x-2 text-sm text-gray-600 mb-3">
            <FileSpreadsheet className="w-4 h-4" />
            <span className="font-medium">{status.original_name}</span>
            <span className="text-gray-400">•</span>
            <span>{status.file_type}</span>
            <span className="text-gray-400">•</span>
            <span>{(status.file_size / 1024 / 1024).toFixed(2)} MB</span>
          </div>

          {status.snapshot_date && (
            <div className="mb-3 text-sm">
              <span className="text-gray-600">Snapshot Date: </span>
              <span className="font-medium">{status.snapshot_date}</span>
            </div>
          )}

          {/* Stats Grid */}
          {status.status === 'completed' && (
            <div className="grid grid-cols-4 gap-4 mt-4">
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Loaded</p>
                <p className="text-2xl font-bold text-green-600">{status.rows_loaded.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Updated</p>
                <p className="text-2xl font-bold text-blue-600">{status.rows_updated.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Skipped</p>
                <p className="text-2xl font-bold text-gray-600">{status.rows_skipped.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Failed</p>
                <p className="text-2xl font-bold text-red-600">{status.rows_failed.toLocaleString()}</p>
              </div>
            </div>
          )}

          {/* Error Message */}
          {status.error_message && (
            <div className="mt-4 p-3 bg-red-100 border border-red-200 rounded">
              <p className="text-sm text-red-800">
                <strong>Error:</strong> {status.error_message}
              </p>
            </div>
          )}

          {/* Timestamps */}
          <div className="mt-4 text-xs text-gray-500">
            <p>Uploaded: {new Date(status.uploaded_at).toLocaleString()}</p>
            {status.processed_at && (
              <p>Processed: {new Date(status.processed_at).toLocaleString()}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
