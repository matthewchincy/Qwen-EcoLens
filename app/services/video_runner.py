import sys
import os
import time
import argparse
import dashscope
from dashscope import VideoSynthesis
from dotenv import load_dotenv

# Re-load env manually if needed, or rely on caller to pass vars
# But better to load .env just in case
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run Video Generation")
    parser.add_argument("prompt", type=str, help="Video prompt")
    
    args = parser.parse_args()
    prompt = args.prompt
    
    # Configuration
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("ERROR: Missing DASHSCOPE_API_KEY")
        sys.exit(1)
        
    dashscope.api_key = api_key
    dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

    print(f"LOG: Starting generation for prompt: {prompt[:30]}...", flush=True)

    try:
        rsp = VideoSynthesis.call(
            model='wan2.6-t2v',
            prompt=prompt,
            parameters={
                'size': '1280*720',
                'prompt_extend': True,
                'duration': 5,
                'audio': False
            }
        )
        
        if rsp.status_code != 200:
            print(f"ERROR: Start failed: {rsp.message}", flush=True)
            sys.exit(1)

        task_id = rsp.output.task_id
        # print(f"LOG: Task Started: {task_id}", flush=True) 
        
        # We can print specific prefix for progress that the parent process can parse
        # PROGRESS: RUNNING
        
        retry = 0
        while retry < 120:
            time.sleep(5)
            status = VideoSynthesis.fetch(task_id)
            
            if status.status_code == 200:
                task_status = status.output.task_status
                print(f"PROGRESS: {task_status} ({retry+1}/120)", flush=True)
                
                if task_status == 'SUCCEEDED':
                    video_url = status.output.video_url
                    print(f"RESULT_URL: {video_url}", flush=True)
                    sys.exit(0)
                elif task_status in ['FAILED', 'CANCELED']:
                    print(f"ERROR: Generation failed: {status.output.message}", flush=True)
                    sys.exit(1)
            else:
                 print(f"LOG: Fetch error: {status.message}", flush=True)
            
            retry += 1
            
        print("ERROR: Timeout", flush=True)
        sys.exit(1)

    except Exception as e:
        print(f"ERROR: Exception: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
