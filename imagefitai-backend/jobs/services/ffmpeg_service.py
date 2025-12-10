import subprocess
import os
import shutil
import uuid
import json


class FFmpegService:
    def __init__(self):
        self.base_temp_dir = '/tmp/imagefitai'

    def create_job_directory(self, job_id: str) -> str:
        """Create a temporary directory for a job."""
        job_dir = os.path.join(self.base_temp_dir, f"job-{job_id}")
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    def cleanup_job_directory(self, job_id: str) -> None:
        """Remove the temporary directory for a job."""
        job_dir = os.path.join(self.base_temp_dir, f"job-{job_id}")
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir)

    def get_image_metadata(self, image_path: str) -> dict:
        """Extract metadata from an image using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                image_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise Exception(f"ffprobe failed: {result.stderr}")

            data = json.loads(result.stdout)
            stream = data.get('streams', [{}])[0]
            format_info = data.get('format', {})

            return {
                'width': stream.get('width'),
                'height': stream.get('height'),
                'format': format_info.get('format_name'),
                'size_bytes': int(format_info.get('size', 0)),
                'size_kb': round(int(format_info.get('size', 0)) / 1024, 2)
            }
        except subprocess.TimeoutExpired:
            raise Exception("ffprobe timed out")
        except json.JSONDecodeError:
            raise Exception("Failed to parse ffprobe output")

    def validate_command(self, command: str) -> bool:
        """Validate that a command is safe to execute."""
        # Must start with ffmpeg
        if not command.strip().startswith('ffmpeg'):
            return False

        # Reject dangerous characters
        dangerous_patterns = [';', '&&', '||', '|', '>', '<', '`', '$', '\n']
        for pattern in dangerous_patterns:
            if pattern in command:
                return False

        # Reject absolute paths (except for -i input which we control)
        parts = command.split()
        for i, part in enumerate(parts):
            if part.startswith('/') and parts[i-1] != '-i':
                return False

        return True

    def execute_command(self, command: str, job_dir: str, timeout: int = 30) -> bool:
        """Execute an ffmpeg command in the job directory."""
        if not self.validate_command(command):
            raise Exception(f"Invalid or unsafe command: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=job_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                raise Exception(f"Command failed: {result.stderr}")

            return True
        except subprocess.TimeoutExpired:
            raise Exception(f"Command timed out after {timeout} seconds")