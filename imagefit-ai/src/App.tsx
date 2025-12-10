import { useState } from 'react';
import { apiService } from './services/api';
import type { JobStatusResponse } from './types';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [requirements, setRequirements] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }
      // Validate file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        setError('File size must be less than 50MB');
        return;
      }
      setSelectedFile(file);
      setError('');
      setJobStatus(null);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await apiService.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          setIsProcessing(false);
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000); // Poll every 2 seconds
        } else {
          setError('Job timed out. Please try again.');
          setIsProcessing(false);
        }
      } catch (err) {
        setError('Failed to get job status');
        setIsProcessing(false);
      }
    };

    poll();
  };

  const handleSubmit = async () => {
    if (!selectedFile || !requirements.trim()) {
      setError('Please select a file and enter requirements');
      return;
    }

    setIsProcessing(true);
    setError('');
    setJobStatus(null);

    try {
      // Step 1: Get presigned URL
      const presignedData = await apiService.getPresignedUrl(
        selectedFile.name,
        selectedFile.type
      );

      // Step 2: Upload to S3
      await apiService.uploadToS3(presignedData.uploadUrl, selectedFile);

      // Step 3: Create job
      const jobData = await apiService.createJob({
        s3Key: presignedData.s3Key,
        rulesText: requirements,
      });

      // Step 4: Poll for status
      pollJobStatus(jobData.jobId);

    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setRequirements('');
    setJobStatus(null);
    setError('');
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Pixly</h1>
        <p>Transform your images to meet strict compliance requirements.</p>
      </header>

      <main className="main">
        <div className="card">
          {/* Step 1: File Upload */}
          <div className="section">
            <h3>Step 1: Upload Your Image</h3>
          <label className="file-upload-btn">
  <input
    type="file"
    accept="image/*"
    onChange={handleFileChange}
    disabled={isProcessing}
    style={{ display: 'none' }}
  />
  <svg
    aria-hidden="true"
    stroke="currentColor"
    strokeWidth="2"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      strokeWidth="2"
      stroke="#ffffff"
      d="M13.5 3H12H8C6.34315 3 5 4.34315 5 6V18C5 19.6569 6.34315 21 8 21H11M13.5 3L19 8.625M13.5 3V7.625C13.5 8.17728 13.9477 8.625 14.5 8.625H19M19 8.625V11.8125"
      strokeLinejoin="round"
      strokeLinecap="round"
    ></path>
    <path
      strokeLinejoin="round"
      strokeLinecap="round"
      strokeWidth="2"
      stroke="#ffffff"
      d="M17 15V18M17 21V18M17 18H14M17 18H20"
    ></path>
  </svg>
  Upload Image
</label>
            {selectedFile && (
              <p className="success">
                ✓ Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>

          {/* Step 2: Requirements */}
          <div className="section">
            <h3>Step 2: Enter Image Requirements</h3>
            <textarea
              placeholder="Example: Image must be JPEG, max 200KB, minimum resolution 600x600, aspect ratio 1:1"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              disabled={isProcessing}
              rows={4}
            />
            {requirements && (
              <p className="success">✓ Requirements entered ({requirements.length} characters)</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={!selectedFile || !requirements.trim() || isProcessing}
            className="submit-btn"
          >
            {isProcessing ? 'Processing...' : 'Process Image'}
          </button>

          {/* Error Display */}
          {error && <p className="error">{error}</p>}

          {/* Job Status */}
          {jobStatus && (
            <div className="section">
              <h3>Job Status</h3>
              <div className={`status-box status-${jobStatus.status}`}>
                <p>
                  {jobStatus.status === 'completed' && '✓ '}
                  {jobStatus.status === 'failed' && '✗ '}
                  {jobStatus.status === 'processing' && '⏳ '}
                  {jobStatus.status === 'pending' && '⏳ '}
                  <strong>Status: {jobStatus.status.toUpperCase()}</strong>
                </p>
                <p className="job-id">Job ID: {jobStatus.jobId}</p>
              </div>
            </div>
          )}

          {/* Results */}
          {jobStatus?.status === 'completed' && (
            <div className="section">
              <h3>✓ Image Processing Complete!</h3>

              {jobStatus.summary && (
                <div className="summary-box">
                  <strong>Summary:</strong>
                  <p>{jobStatus.summary}</p>
                </div>
              )}

              <div className="images-container">
                <div className="image-box">
                  <h4>Original Image</h4>
                  {jobStatus.originalImageUrl && (
                    <img src={jobStatus.originalImageUrl} alt="Original" />
                  )}
                </div>

                <div className="image-box">
                  <h4>Compliant Image</h4>
                  {jobStatus.outputImageUrl && (
                    <>
                      <img src={jobStatus.outputImageUrl} alt="Processed" />
                      <a
                        href={jobStatus.outputImageUrl}
                        download
                        className="download-btn"
                      >
                        Download Compliant Image
                      </a>
                    </>
                  )}
                </div>
              </div>

              <button onClick={handleReset} className="reset-btn">
                Process Another Image
              </button>
            </div>
          )}

          {/* Error Result */}
          {jobStatus?.status === 'failed' && (
            <div className="section">
              <div className="error-box">
                <strong>Error:</strong>
                <p>{jobStatus.error}</p>
              </div>
              <button onClick={handleReset} className="reset-btn">
                Try Again
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;