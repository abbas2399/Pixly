# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pixly is an AI-powered image transformation service that automatically processes images to meet specific compliance requirements. The system accepts user-provided image requirements in natural language (e.g., "Image must be JPEG, max 200KB, minimum resolution 600x600") and uses Claude AI (via AWS Bedrock) to generate and execute FFmpeg commands for image transformation.

## Architecture

### Monorepo Structure

This is a monorepo with two main components:

- `imagefit-ai/` - React + TypeScript + Vite frontend
- `imagefitai-backend/` - Django REST API backend

### Technology Stack

**Frontend:**
- React 19 with TypeScript
- Vite as build tool
- Axios for HTTP requests
- Direct S3 presigned URL uploads

**Backend:**
- Django 4.2 with Django REST Framework
- PostgreSQL (production) / SQLite (local development)
- AWS S3 for image storage
- AWS Bedrock (Claude 3.5 Haiku) for LLM-based FFmpeg command generation
- FFmpeg for image processing
- WhiteNoise for static file serving
- Gunicorn for production server

### Request Flow

1. **Upload**: Frontend requests presigned S3 URL from backend → uploads image directly to S3
2. **Job Creation**: Frontend creates job with S3 key and requirements text
3. **Processing Pipeline** (synchronous in backend):
   - Download image from S3 to temporary directory (`/tmp/imagefitai/job-{id}/`)
   - Extract metadata using FFprobe
   - Send metadata + requirements to Claude (Bedrock) to generate FFmpeg commands
   - Execute FFmpeg commands in isolated temp directory
   - Upload processed image to S3 (`outputs/{job_id}/`)
   - Cleanup temp directory
4. **Results**: Frontend polls job status endpoint to get presigned download URLs for before/after images

### Key Backend Services

Located in `imagefitai-backend/jobs/services/`:

- **s3_service.py**: Manages S3 operations (presigned URLs, upload/download)
- **llm_service.py**: Interfaces with AWS Bedrock Claude to generate FFmpeg commands from natural language requirements
- **ffmpeg_service.py**: Executes image transformations, validates commands for security, manages temp directories

### Database Model

Single `Job` model (`imagefitai-backend/jobs/models.py`) tracks:
- Status: pending → processing → completed/failed
- Input: `s3_key`, `rules_text`
- Processing: `original_metadata`, `constraints`, `commands` (JSON fields)
- Output: `output_s3_key`, `summary`, `error`

## Development Commands

### Backend (Django)

Navigate to `imagefitai-backend/` directory for all Django commands:

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python manage.py runserver

# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser for admin panel
python manage.py createsuperuser

# Access admin panel
# http://localhost:8000/admin

# Collect static files (production)
python manage.py collectstatic --noinput
```

### Frontend (React)

Navigate to `imagefit-ai/` directory for all frontend commands:

```bash
# Install dependencies
npm install

# Run development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Environment Configuration

### Backend Environment Variables

Create `imagefitai-backend/.env` (see `.env.example`):

```
# Required for AWS Bedrock (Claude AI)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket_name
AWS_REGION=us-east-1

# Optional - Django settings
SECRET_KEY=your_secret_key
DEBUG=True  # False in production
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend API Configuration

The frontend API base URL is hardcoded in `imagefit-ai/src/services/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8000/api';
```

Update this for production deployments.

## API Endpoints

Base URL: `/api/`

- `POST /api/uploads/presign` - Generate S3 presigned upload URL
  - Body: `{ fileName: string, contentType: string }`
  - Returns: `{ uploadUrl: string, s3Key: string }`

- `POST /api/jobs` - Create and process image transformation job
  - Body: `{ s3Key: string, rulesText: string }`
  - Returns: `{ jobId: string, status: string }`
  - Note: Processing happens synchronously

- `GET /api/jobs/<job_id>` - Get job status and results
  - Returns: `{ jobId, status, summary, error, originalImageUrl, outputImageUrl }`

## Deployment

### Render Deployment

The repository includes `render.yaml` for deployment with:
- PostgreSQL database (`pixly-db`)
- Web service running Gunicorn (`pixly-backend`)
- Build command in `imagefitai-backend/build.sh`

Build process:
1. Install Python dependencies
2. Run `collectstatic`
3. Run database migrations

### Critical Production Settings

- `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` with actual domain
- Set `CSRF_TRUSTED_ORIGINS` and `CORS_ALLOWED_ORIGINS`
- Use PostgreSQL (configured via `DATABASE_URL` environment variable)
- Ensure FFmpeg is installed on production server

## Important Notes

### FFmpeg Command Security

The `ffmpeg_service.py` includes command validation to prevent shell injection:
- Commands must start with `ffmpeg`
- Rejects dangerous characters: `;`, `&&`, `||`, `|`, `>`, `<`, backticks, `$`
- Rejects absolute paths (except for `-i` input)
- Commands execute in isolated temp directories with 30-second timeout

### LLM Service Details

- Uses AWS Bedrock with Claude 3.5 Haiku (`us.anthropic.claude-3-5-haiku-20241022-v1:0`)
- Prompt in `llm_service.py` includes FFmpeg examples and safety rules
- Returns JSON with: `constraints`, `commands`, `final_output`, `summary`
- Handles markdown code block cleanup and JSON extraction

### Job Processing

- Currently synchronous (MVP approach) - jobs process during the POST request
- Frontend polls status endpoint every 1 second for up to 60 seconds
- Each job gets isolated temp directory that's cleaned up in `finally` block
- Failed jobs store error message in database

### Frontend Polling

The frontend polls job status after creation, expecting the backend to eventually complete. In the current implementation, the backend processes synchronously, so the first poll typically returns completed/failed status.
