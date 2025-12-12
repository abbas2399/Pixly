import boto3
import json
from django.conf import settings


class LLMService:
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'

    def generate_ffmpeg_commands(self, rules_text: str, image_metadata: dict, input_filename: str = "input.jpg") -> dict:
        """Send rules and metadata to Bedrock Claude, get back ffmpeg commands."""

        prompt = f"""You are an image processing expert. Given the user's requirements and the current image metadata, generate ffmpeg commands to transform the image.

USER REQUIREMENTS:
{rules_text}

CURRENT IMAGE METADATA:
- Width: {image_metadata.get('width')} pixels
- Height: {image_metadata.get('height')} pixels
- Format: {image_metadata.get('format')}
- File size: {image_metadata.get('size_kb')} KB

INPUT FILENAME: {input_filename}

# NEW: Added this entire section with ffmpeg examples
FFMPEG EXAMPLES FOR COMMON OPERATIONS:
- Convert to PNG: ffmpeg -i {input_filename} output.png
- Convert to JPG: ffmpeg -i {input_filename} output.jpg
- Resize to specific dimensions: ffmpeg -i {input_filename} -vf "scale=800:600" output.jpg
- Resize maintaining aspect ratio (width 800): ffmpeg -i {input_filename} -vf "scale=800:-1" output.jpg
- Resize maintaining aspect ratio (height 600): ffmpeg -i {input_filename} -vf "scale=-1:600" output.jpg
- Convert and resize: ffmpeg -i {input_filename} -vf "scale=400:400" output.png
- Compress JPEG (quality 1-31, lower=better): ffmpeg -i {input_filename} -q:v 5 output.jpg

# NEW: Added these important rules to prevent bad commands
IMPORTANT RULES:
- Use EXACTLY "{input_filename}" as input
- Output filename should be "output.png" or "output.jpg" based on target format
- Do NOT use -pix_fmt for simple format conversions
- Do NOT use -c:v for simple image conversions
- Keep commands simple - ffmpeg handles format conversion automatically based on output extension
- Each command should be a single, complete ffmpeg command

Respond ONLY with valid JSON in this exact format:
{{
    "constraints": {{
        "format": "target format or null",
        "width": target_width_or_null,
        "height": target_height_or_null,
        "max_size_kb": max_size_or_null,
        "aspect_ratio": "ratio or null"
    }},
    "commands": [
        "ffmpeg -i {input_filename} output.png"
    ],
    "final_output": "output.png",
    "summary": "Brief description of what transformations were applied"
}}"""

        try:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )

            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text'].strip()

            # Clean up response - remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Find JSON object in response (in case there's extra text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise Exception("No JSON object found in LLM response")

            json_text = response_text[start_idx:end_idx]

            # Parse JSON
            result = json.loads(json_text)

            # Validate required fields
            required_fields = ['constraints', 'commands', 'final_output', 'summary']
            for field in required_fields:
                if field not in result:
                    raise Exception(f"Missing required field: {field}")

            if not isinstance(result['commands'], list) or len(result['commands']) == 0:
                raise Exception("Commands must be a non-empty list")

            return result

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM service error: {str(e)}")