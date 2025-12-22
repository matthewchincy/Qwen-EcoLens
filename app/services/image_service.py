import requests
from PIL import Image
from io import BytesIO
import oss2
import uuid
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def download_and_process_image(image_url: str) -> bytes:
    """
    Downloads image from URL and resizes it (Max 1024px).
    Returns image bytes (JPEG).
    """
    try:
        print(f"DEBUG: Processing image: {image_url}")
        
        # 1. Download Image
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        print("DEBUG: Image downloaded and opened successfully.")

        # 2. Resize Image (Max 1024px)
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Convert to bytes
        img_byte_arr = BytesIO()
        # Save as JPEG
        img = img.convert("RGB")
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)
        print("DEBUG: Image resized successfully.")
        
        return img_byte_arr.getvalue()

    except Exception as e:
        print(f"DEBUG: Error processing image: {e}")
        raise e

def upload_to_oss(image_bytes: bytes) -> str:
    """
    Uploads image bytes to OSS and returns Signed URL.
    """
    try:
        # 3. Upload to OSS
        if not settings.OSS_ACCESS_KEY_ID or not settings.OSS_BUCKET_NAME:
            print(f"DEBUG: OSS credentials missing! ID_LEN: {len(settings.OSS_ACCESS_KEY_ID)}, BUCKET: {settings.OSS_BUCKET_NAME}")
            # If no OSS, we cannot return a persistent URL. 
            # In a real app we might fallback to local storage, 
            # but here we'll raise an error or return None to indicate failure to store.
            return None

        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)

        # Generate unique filename
        filename = f"food_logs/{uuid.uuid4()}.jpg"
        
        # Upload
        bucket.put_object(filename, image_bytes)

        # Generate Signed URL (valid for 1 hour) ensures access even if bucket is private
        oss_url = bucket.sign_url('GET', filename, 3600)
        
        print(f"DEBUG: Image uploaded to OSS: {oss_url}")
        return oss_url

    except Exception as e:
        print(f"DEBUG: Error uploading to OSS: {e}")
        return None
