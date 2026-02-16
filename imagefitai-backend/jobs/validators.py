import os

ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff']
MAX_FILE_SIZE_MB = 5  # 5MB max

def validate_uploaded_image(file):
    """Validate uploaded file is a safe image."""
    errors = []

    # Check file size
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        errors.append(f'File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.')

    # Check extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        errors.append(f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}')

    # Check content type
    allowed_content_types = [
        'image/png', 'image/jpeg', 'image/webp',
        'image/gif', 'image/bmp', 'image/tiff'
    ]
    if file.content_type not in allowed_content_types:
        errors.append('Invalid content type. Must be an image file.')

    return errors