'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { user } = useAuth();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith('.csv') || selectedFile.name.endsWith('.xlsx') || selectedFile.name.endsWith('.xls')) {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please select a CSV or XLSX file');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiClient.uploadFile(file);
      setJobId(response.job_id);
      setSuccess(response.message);
      
      // Poll for job status
      pollJobStatus(response.job_id);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await apiClient.getBatchJob(jobId);
        setJobStatus(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          if (status.status === 'completed') {
            setTimeout(() => {
              router.push('/');
            }, 2000);
          }
        }
      } catch (err) {
        console.error('Error polling job status:', err);
        clearInterval(interval);
      }
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Upload Activity Data</h1>
          <p className="text-muted-foreground">
            Upload a CSV or XLSX file with your organization's activity data. The system will automatically classify and calculate carbon emissions.
          </p>
        </div>

        <div className="bg-card border rounded-lg p-6 space-y-6">
          {error && (
            <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-500/10 text-green-600 dark:text-green-400 px-4 py-3 rounded-md text-sm">
              {success}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-2">
              Select File (CSV or XLSX)
            </label>
            <div className="flex items-center space-x-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileChange}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 border border-input bg-background rounded-md hover:bg-accent"
              >
                Choose File
              </button>
              {file && (
                <span className="text-sm text-muted-foreground">
                  {file.name} ({(file.size / 1024).toFixed(2)} KB)
                </span>
              )}
            </div>
          </div>

          {file && (
            <div className="bg-muted p-4 rounded-md">
              <h3 className="font-medium mb-2">Expected CSV format:</h3>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                <li><strong>description</strong> (required): Activity description</li>
                <li><strong>category</strong> (optional): Activity category</li>
                <li><strong>supplier_name</strong> (optional): Supplier name</li>
                <li><strong>amount</strong> (required): Numeric amount</li>
                <li><strong>unit</strong> (required): Unit (kWh, kg, EUR, USD, etc.)</li>
                <li><strong>region</strong> (optional): Region code (2-letter ISO)</li>
                <li><strong>year</strong> (optional): Year for the activity</li>
                <li><strong>activity_date</strong> (optional): Date (YYYY-MM-DD)</li>
              </ul>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? 'Uploading and processing...' : 'Upload and Process'}
          </button>

          {jobStatus && (
            <div className="mt-6 space-y-4">
              <div>
                <h3 className="font-medium mb-2">Processing Status</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Status:</span>
                    <span className={`font-medium ${
                      jobStatus.status === 'completed' ? 'text-green-600' :
                      jobStatus.status === 'failed' ? 'text-red-600' :
                      'text-yellow-600'
                    }`}>
                      {jobStatus.status}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Progress:</span>
                    <span>{jobStatus.processed_records} / {jobStatus.total_records}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Successful:</span>
                    <span className="text-green-600">{jobStatus.successful_records}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Failed:</span>
                    <span className="text-red-600">{jobStatus.failed_records}</span>
                  </div>
                  {jobStatus.status === 'processing' && (
                    <div className="w-full bg-muted rounded-full h-2 mt-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{
                          width: `${(jobStatus.processed_records / jobStatus.total_records) * 100}%`,
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

