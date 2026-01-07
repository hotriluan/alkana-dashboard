/**
 * File Upload Component
 * Drag-and-drop or click to upload Excel files
 * 
 * Skills: react, typescript, file-handling
 */
import { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, X } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File, snapshotDate?: string) => void;
  isUploading: boolean;
  allowedTypes?: string[];
}

export const FileUpload = ({ 
  onFileSelect, 
  isUploading,
  allowedTypes = ['.xlsx', '.xls', '.xlsm']
}: FileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  // Default to today's date in YYYY-MM-DD format
  const [snapshotDate, setSnapshotDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileSelection = (file: File) => {
    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(extension)) {
      alert(`Invalid file type. Allowed: ${allowedTypes.join(', ')}`);
      return;
    }

    // Check file size (50MB limit)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('File too large. Maximum size: 50MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = () => {
    if (selectedFile) {
      // Auto-detect if AR file by name
      const isARFile = selectedFile.name.toLowerCase().includes('zrfi005');
      
      // For AR file: use provided snapshot_date or default to today
      const finalSnapshotDate = isARFile && !snapshotDate
        ? new Date().toISOString().split('T')[0] // Today in YYYY-MM-DD format
        : snapshotDate || undefined;

      onFileSelect(selectedFile, finalSnapshotDate);
      
      // Reset after upload
      setSelectedFile(null);
      setSnapshotDate('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setSnapshotDate('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Upload SAP Excel File</h3>

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={allowedTypes.join(',')}
          onChange={handleFileChange}
          disabled={isUploading}
          className="hidden"
        />

        <div className="flex flex-col items-center space-y-3">
          <Upload className="w-12 h-12 text-gray-400" />
          <div>
            <p className="text-lg font-medium text-gray-700">
              Drag & drop file here or click to browse
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Supported: {allowedTypes.join(', ')} (Max 50MB)
            </p>
          </div>
        </div>
      </div>

      {/* Selected File Info */}
      {selectedFile && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <FileSpreadsheet className="w-8 h-8 text-green-600" />
              <div>
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={handleCancel}
              disabled={isUploading}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Snapshot Date (for AR files) */}
          {selectedFile.name.toLowerCase().includes('zrfi005') && (
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Snapshot Date (for AR data)
              </label>
              <input
                type="date"
                value={snapshotDate}
                onChange={(e) => setSnapshotDate(e.target.value)}
                max={new Date().toISOString().split('T')[0]}
                placeholder={new Date().toISOString().split('T')[0]}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                disabled={isUploading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Default: Today ({new Date().toISOString().split('T')[0]}). New month will auto-delete previous month's data.
              </p>
            </div>
          )}

          {/* Upload Button */}
          <div className="mt-4 flex space-x-2">
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className={`
                flex-1 px-4 py-2 rounded-md font-medium text-white
                ${isUploading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700'
                }
              `}
            >
              {isUploading ? 'Uploading...' : 'Upload File'}
            </button>
            <button
              onClick={handleCancel}
              disabled={isUploading}
              className="px-4 py-2 border border-gray-300 rounded-md font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Supported File Types */}
      <div className="mt-4 text-sm text-gray-600">
        <p className="font-medium mb-1">Supported SAP Reports:</p>
        <ul className="list-disc list-inside space-y-1 text-xs">
          <li>COOISPI - Production Orders</li>
          <li>MB51 - Material Movements</li>
          <li>ZRMM024 - MRP Controller</li>
          <li>ZRSD002 - Sales Orders</li>
          <li>ZRSD004 - Delivery</li>
          <li>ZRSD006 - Distribution Channel</li>
          <li>ZRFI005 - AR Aging (requires snapshot date)</li>
          <li>TARGET - Sales Targets</li>
        </ul>
      </div>
    </div>
  );
};
