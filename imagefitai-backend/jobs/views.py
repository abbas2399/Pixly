from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import threading

from django.utils.decorators import method_decorator
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit

from .models import Job
from .services.s3_service import S3Service
from .services.ffmpeg_service import FFmpegService
from .services.llm_service import LLMService

DAILY_GLOBAL_LIMIT = 50


def check_global_limit():
    """Return True if the daily global job limit has been reached."""
    from django.utils import timezone
    today = timezone.now().date().isoformat()
    count = cache.get(f'global_job_count_{today}', 0)
    return count >= DAILY_GLOBAL_LIMIT


def increment_global_count():
    """Increment the global daily job counter."""
    from django.utils import timezone
    today = timezone.now().date().isoformat()
    cache_key = f'global_job_count_{today}'
    try:
        cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, 86400)


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


@method_decorator(ratelimit(key='ip', rate='5/d', method='POST', block=False), name='post')
class JobCreateView(APIView):
    """Create a new job and process the image."""

    def post(self, request):
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Rate limit exceeded. You can submit up to 5 jobs per day.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if check_global_limit():
            return Response(
                {'error': 'Service temporarily unavailable due to high demand. Please try again tomorrow.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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
            status='pending',
            current_step='Job queued for processing...'
        )
        increment_global_count()

        # Process the job in background thread so frontend can see progress
        thread = threading.Thread(target=self._process_job_wrapper, args=(job.id,))
        thread.daemon = True
        thread.start()

        return Response({
            'jobId': str(job.id),
            'status': job.status
        }, status=status.HTTP_201_CREATED)

    def _process_job_wrapper(self, job_id):
        """Wrapper to load job and handle exceptions in background thread."""
        try:
            job = Job.objects.get(id=job_id)
            self._process_job(job)
        except Job.DoesNotExist:
            pass
        except Exception as e:
            try:
                job = Job.objects.get(id=job_id)
                job.status = 'failed'
                job.error = str(e)
                job.current_step = None
                job.save()
            except Exception:
                pass

    def _process_job(self, job):
        """Process the image transformation job."""
        s3_service = S3Service()
        ffmpeg_service = FFmpegService()
        llm_service = LLMService()

        job.status = 'processing'
        job.current_step = 'Initializing...'
        job.save()

        job_dir = None

        try:
            # Step 1: Create temp directory
            job.current_step = 'Creating temporary workspace...'
            job.save()
            job_dir = ffmpeg_service.create_job_directory(str(job.id))

            # Step 2: Download image from S3
            job.current_step = 'Downloading image from cloud storage...'
            job.save()
            file_extension = os.path.splitext(job.s3_key)[1].lower()
            input_filename = f"input{file_extension}"
            input_path = os.path.join(job_dir, input_filename)
            s3_service.download_file(job.s3_key, input_path)

            # Step 3: Get image metadata
            job.current_step = 'Analyzing image properties...'
            job.save()
            metadata = ffmpeg_service.get_image_metadata(input_path)
            job.original_metadata = metadata
            job.save()

            # Step 4: Call LLM to get ffmpeg commands
            job.current_step = 'Generating transformation plan with AI...'
            job.save()
            llm_result = llm_service.generate_ffmpeg_commands(job.rules_text, metadata, input_filename)
            job.constraints = llm_result.get('constraints')
            job.commands = llm_result.get('commands')
            job.summary = llm_result.get('summary')
            job.save()

            # Step 5: Execute ffmpeg commands
            job.current_step = 'Applying transformations to image...'
            job.save()
            for command in llm_result['commands']:
                ffmpeg_service.execute_command(command, job_dir)

            # Step 6: Upload output to S3
            job.current_step = 'Uploading processed image...'
            job.save()
            output_filename = os.path.basename(llm_result.get('final_output', 'output.png'))
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
            job.current_step = 'Finalizing...'
            job.save()
            job.status = 'completed'
            job.current_step = None  # Clear step when done
            job.save()

        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            job.current_step = None  # Clear step on failure
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
            'currentStep': job.current_step,
            'summary': job.summary,
            'error': job.error,
        }

        # Generate presigned URLs for images
        if job.s3_key:
            response_data['originalImageUrl'] = s3_service.generate_presigned_download_url(job.s3_key)

        if job.output_s3_key:
            response_data['outputImageUrl'] = s3_service.generate_presigned_download_url(job.output_s3_key)

        return Response(response_data)