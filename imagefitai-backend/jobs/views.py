from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import shutil

from .models import Job
from .services.s3_service import S3Service
from .services.ffmpeg_service import FFmpegService
from .services.llm_service import LLMService


class PresignedUploadView(APIView):
    """Generate presigned URL for S3 upload."""

    def post(self, request):
        file_name = request.data.get('fileName')
        content_type = request.data.get('contentType', 'image/jpeg')

        if not file_name:
            return Response(
                {'error': 'fileName is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            s3_service = S3Service()
            result = s3_service.generate_presigned_upload_url(file_name, content_type)
            return Response({
                'uploadUrl': result['upload_url'],
                's3Key': result['s3_key']
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobCreateView(APIView):
    """Create a new job and process the image."""

    def post(self, request):
        s3_key = request.data.get('s3Key')
        rules_text = request.data.get('rulesText')

        if not s3_key or not rules_text:
            return Response(
                {'error': 's3Key and rulesText are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create job in database
        job = Job.objects.create(
            s3_key=s3_key,
            rules_text=rules_text,
            status='pending'
        )

        # Process the job synchronously (MVP approach)
        try:
            self._process_job(job)
        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            job.save()

        return Response({
            'jobId': str(job.id),
            'status': job.status
        }, status=status.HTTP_201_CREATED)

    def _process_job(self, job):
        """Process the image transformation job."""
        s3_service = S3Service()
        ffmpeg_service = FFmpegService()
        llm_service = LLMService()

        job.status = 'processing'
        job.save()

        job_dir = None

        try:
            # Step 1: Create temp directory
            job_dir = ffmpeg_service.create_job_directory(str(job.id))

            # Step 2: Download image from S3
            file_extension = os.path.splitext(job.s3_key)[1].lower()
            input_filename = f"input{file_extension}"
            input_path = os.path.join(job_dir, input_filename)
            s3_service.download_file(job.s3_key, input_path)

            # Step 3: Get image metadata
            metadata = ffmpeg_service.get_image_metadata(input_path)
            job.original_metadata = metadata
            job.save()

            # Step 4: Call LLM to get ffmpeg commands
            # CHANGED: Pass input_filename to LLM service
            llm_result = llm_service.generate_ffmpeg_commands(job.rules_text, metadata, input_filename)
            job.constraints = llm_result.get('constraints')
            job.commands = llm_result.get('commands')
            job.summary = llm_result.get('summary')
            job.save()

            # Step 5: Execute ffmpeg commands
            for command in llm_result['commands']:
                ffmpeg_service.execute_command(command, job_dir)

            # Step 6: Upload output to S3
            output_filename = llm_result.get('final_output', 'output.png')
            output_path = os.path.join(job_dir, output_filename)

            # Check if output exists, if not try common output names
            if not os.path.exists(output_path):
                for try_name in ['output.png', 'output.jpg', 'output.jpeg']:
                    try_path = os.path.join(job_dir, try_name)
                    if os.path.exists(try_path):
                        output_path = try_path
                        output_filename = try_name
                        break

            if not os.path.exists(output_path):
                raise Exception(f"Output file not found: {output_filename}")

            output_s3_key = f"outputs/{job.id}/{output_filename}"
            s3_service.upload_file(output_path, output_s3_key)
            job.output_s3_key = output_s3_key

            # Step 7: Mark as completed
            job.status = 'completed'
            job.save()

        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            job.save()
            raise

        finally:
            # Always cleanup temp directory
            if job_dir:
                ffmpeg_service.cleanup_job_directory(str(job.id))


class JobStatusView(APIView):
    """Get job status and results."""

    def get(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        s3_service = S3Service()

        response_data = {
            'jobId': str(job.id),
            'status': job.status,
            'summary': job.summary,
            'error': job.error,
        }

        # Generate presigned URLs for images
        if job.s3_key:
            response_data['originalImageUrl'] = s3_service.generate_presigned_download_url(job.s3_key)

        if job.output_s3_key:
            response_data['outputImageUrl'] = s3_service.generate_presigned_download_url(job.output_s3_key)

        return Response(response_data)