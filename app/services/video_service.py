import logging
import asyncio
import json
from dashscope import VideoSynthesis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Set International Endpoint for DashScope SDK
import dashscope
# Set International Endpoint for DashScope SDK
import dashscope
dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"
dashscope.api_key = settings.DASHSCOPE_API_KEY

import sys
import requests # Ensure requests is imported

async def generate_video(prompt: str, image_url: str = None, progress_callback=None) -> str:
    """
    Generates a video using Alibaba Cloud Wan2.x model via DashScope.
    Returns the URL of the generated video.
    """
    # Use subprocess to run isolated script
    try:
        logger.info(f"Starting video generation subprocess with prompt: {prompt[:30]}...")
        
        # Path to runner
        runner_path = "app/services/video_runner.py" 
        python_exe = sys.executable

        # Start subprocess
        process = await asyncio.create_subprocess_exec(
            python_exe, runner_path, prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        video_url = None
        
        # Read stdout line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            line_str = line.decode().strip()
            if not line_str: 
                continue
            
            # Parse output
            if line_str.startswith("PROGRESS:"):
                # Format: PROGRESS: RUNNING (1/120)
                status_part = line_str.replace("PROGRESS:", "").strip()
                if progress_callback:
                    await progress_callback(f"Generating... {status_part}")
            
            elif line_str.startswith("RESULT_URL:"):
                video_url = line_str.replace("RESULT_URL:", "").strip()
            
            elif line_str.startswith("ERROR:"):
                logger.error(f"Video Runner Error: {line_str}")
        
        # Wait for finish
        await process.wait()
        
        if process.returncode == 0 and video_url:
            logger.info(f"Video generation succeeded: {video_url}")
            return video_url
        else:
             logger.error("Video subprocess failed or no URL returned.")
             return None

    except Exception as e:
        logger.error(f"Exception in video subprocess: {e}")
        print(f"DEBUG: Subprocess Exception: {e}", flush=True)
        return None
