import axios from 'axios';
import type {
  PresignedUrlResponse,
  JobCreateRequest,
  JobCreateResponse,
  JobStatusResponse,
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Get presigned URL for S3 upload
  getPresignedUrl: async (fileName: string, contentType: string): Promise<PresignedUrlResponse> => {
    const response = await api.post('/uploads/presign', { fileName, contentType });
    return response.data;
  },

  // Upload file directly to S3
  uploadToS3: async (presignedUrl: string, file: File): Promise<void> => {
    await axios.put(presignedUrl, file, {
      headers: {
        'Content-Type': file.type,
      },
    });
  },

  // Create a job
  createJob: async (data: JobCreateRequest): Promise<JobCreateResponse> => {
    const response = await api.post('/jobs', data);
    return response.data;
  },

  // Get job status
  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },
};