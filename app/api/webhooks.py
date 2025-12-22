from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.services.telegram_service import proccess_telegram_message
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook to receive updates from Telegram.
    Returns 200 OK immediately and processes in background.
    """
    try:
        data = await request.json()
        # Basic validation (optional)
        if not data:
             raise HTTPException(status_code=400, detail="No data received")
             
        background_tasks.add_task(proccess_telegram_message, data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        # Always return 200 to Telegram to stop retries, unless critical
        return {"status": "error", "message": str(e)}
