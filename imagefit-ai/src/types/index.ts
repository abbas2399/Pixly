export interface PresignedUrlResponse {
  uploadUrl: string;
  s3Key: string;
}

export interface JobCreateRequest {
  s3Key: string;
  rulesText: string;
}

export interface JobCreateResponse {
  jobId: string;
  status: string;
}

export interface JobStatusResponse {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  currentStep?: string;
  originalImageUrl?: string;
  outputImageUrl?: string;
  summary?: string;
  error?: string;
  
}