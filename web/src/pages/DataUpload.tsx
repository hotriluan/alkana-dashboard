/**
 * Data Upload Page
 * Main page for uploading SAP Excel files
 * 
 * Skills: react, typescript, state-management
 */
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload as UploadIcon, AlertCircle } from 'lucide-react';
import { uploadAPI } from '../services/api';
import { FileUpload } from '../components/upload/FileUpload';
import { UploadStatusComponent } from '../components/upload/UploadStatus';
import { UploadHistory } from '../components/upload/UploadHistory';

const DataUpload = () => {
  const [currentUploadId, setCurrentUploadId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: ({ file, snapshotDate }: { file: File; snapshotDate?: string }) =>
      uploadAPI.uploadFile(file, snapshotDate),
    onSuccess: (data) => {
      setCurrentUploadId(data.upload_id);
      setError(null);
      // Invalidate history to refresh
      queryClient.invalidateQueries({ queryKey: ['upload-history'] });
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  const handleFileSelect = (file: File, snapshotDate?: string) => {
    setError(null);
    uploadMutation.mutate({ file, snapshotDate });
  };

  const handleUploadComplete = () => {
    // Refresh history when upload completes
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
          Upload SAP Excel files to update dashboard data. Files are automatically validated and processed.
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
            isUploading={uploadMutation.isPending}
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

          {!currentUploadId && (
            <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8">
              <div className="text-center text-gray-500">
                <UploadIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No active upload</p>
                <p className="text-sm mt-1">Select a file to begin</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upload History */}
      <div className="mt-8">
        <UploadHistory />
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">📘 Upload Guidelines</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>File Format:</strong> Excel files (.xlsx, .xls, .xlsm)</li>
          <li>• <strong>File Size:</strong> Maximum 50MB</li>
          <li>• <strong>Auto-Detection:</strong> File type is automatically detected from headers</li>
          <li>• <strong>AR Data (ZRFI005):</strong> Requires snapshot date. Day 1 deletes previous month's data</li>
          <li>• <strong>Upsert Mode:</strong> Updates existing records, inserts new ones, skips unchanged</li>
          <li>• <strong>Processing Time:</strong> Large files may take 1-2 minutes to process</li>
        </ul>
      </div>
    </div>
  );
};

export default DataUpload;
