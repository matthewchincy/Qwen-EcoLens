import logging
import base64
from datetime import datetime
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from app.core.config import settings
from app.core.messages import MESSAGES
from app.db.session import AsyncSessionLocal
from app.db.models import User, FoodLog
from app.services.qwen_ai import analyze_image
from app.services.image_service import download_and_process_image, upload_to_oss
from app.services.video_service import generate_video

logger = logging.getLogger(__name__)
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

CREDIT_COST_ANALYSIS = 50
CREDIT_COST_VIDEO = 100

async def get_or_create_user(session, telegram_id, username):
    result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

async def proccess_telegram_message(update_data: dict):
    """
    Process incoming telegram update.
    """
    msg = update_data.get('message', {})
    callback = update_data.get('callback_query', {})
    
    chat_id = None
    telegram_id = None
    username = None
    text_content = ""
    
    if callback:
        msg = callback.get('message', {})
        chat_id = msg.get('chat', {}).get('id')
        user_data = callback.get('from', {})
        telegram_id = str(user_data.get('id'))
        username = user_data.get('username')
        text_content = callback.get('data', "") # Treat callback data as text command
        # Answer callback to stop loading animation
        try:
             await bot.answer_callback_query(callback_query_id=callback.get('id'))
        except Exception as e:
             logger.error(f"Error answering callback: {e}")
    elif msg:
        chat_id = msg.get('chat', {}).get('id')
        user_data = msg.get('from', {})
        telegram_id = str(user_data.get('id'))
        username = user_data.get('username')
        text_content = msg.get('text', "")
    else:
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, telegram_id, username)
        lang = user.language if user.language in MESSAGES else 'en'
        texts = MESSAGES[lang]

        # --- MENU HELPER ---
        def get_main_menu_keyboard():
            keyboard = [
                [InlineKeyboardButton(texts["menu_scan"], callback_data="scan_food")],
                [InlineKeyboardButton(texts["menu_stats"], callback_data="/stats"), InlineKeyboardButton(texts["menu_lang"], callback_data="/language")],
                [InlineKeyboardButton(texts["menu_policy"], callback_data="/policy")]
            ]
            # ADMIN BUTTON
            if telegram_id in settings.ADMIN_IDS:
                 keyboard.append([InlineKeyboardButton("⚡ Admin: Reload 1000", callback_data="admin_reload")])
                 
            return InlineKeyboardMarkup(keyboard)

        # --- COMMANDS & CALLBACKS ---
        
        # Admin Reload Callback
        if text_content == "admin_reload":
             if telegram_id in settings.ADMIN_IDS:
                  user.credits += 1000
                  await session.commit()
                  await bot.send_message(chat_id=chat_id, text=f"✅ **Credits Reloaded!**\nNew Balance: {user.credits}", parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
             return

        # 1. /start OR Menu Logic
        if text_content == "/start" or text_content == "menu":
            await bot.send_message(
                chat_id=chat_id, 
                text=texts["welcome"].format(credits=user.credits), 
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            return

        # 2. /language
        if text_content.startswith("/language"):
            # Check if specific language selected via callback
            if text_content == "/language":
                # Show language options
                kb = [
                    [InlineKeyboardButton("English 🇺🇸", callback_data="lang_set_en")],
                    [InlineKeyboardButton("Bahasa Melayu 🇲🇾", callback_data="lang_set_ms")],
                    [InlineKeyboardButton("中文 🇨🇳", callback_data="lang_set_zh")],
                    [InlineKeyboardButton("🔙 Back", callback_data="menu")]
                ]
                await bot.send_message(chat_id=chat_id, text=texts["lang_select"], reply_markup=InlineKeyboardMarkup(kb))
                return
            
            # Legacy command support (e.g. user types /language en)
            parts = text_content.split()
            if len(parts) == 2 and parts[1] in ['en', 'ms', 'zh']:
                user.language = parts[1]
                await session.commit()
                texts = MESSAGES[user.language] 
                await bot.send_message(chat_id=chat_id, text=texts["lang_set"], parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
            return

        # Language Set Callbacks
        if text_content.startswith("lang_set_"):
            new_lang = text_content.split("_")[-1]
            if new_lang in ['en', 'ms', 'zh']:
                user.language = new_lang
                await session.commit()
                texts = MESSAGES[user.language] 
                await bot.send_message(chat_id=chat_id, text=texts["lang_set"], parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
            return
            
        # Scan Food Callback (Prompt)
        if text_content == "scan_food":
             await bot.send_message(chat_id=chat_id, text="📸 **Please send me a photo of your food!**", parse_mode='Markdown')
             return

        # 3. /stats
        if text_content == "/stats":
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await session.execute(
                select(FoodLog)
                .filter(FoodLog.user_id == user.id)
                .filter(FoodLog.created_at >= today_start)
            )
            logs = result.scalars().all()
            
            if not logs:
                await bot.send_message(chat_id=chat_id, text=texts["no_logs"], reply_markup=get_main_menu_keyboard())
                return

            total_cals = sum(log.calories for log in logs if log.calories)
            total_carbon = sum(log.analysis_json.get('carbon_emission_kg', 0) for log in logs if log.analysis_json)
            meal_list = "\n".join([f"• {log.food_name} ({log.calories} kcal)" for log in logs])
            
            stats_msg = texts["daily_summary"].format(
                date=datetime.utcnow().strftime('%Y-%m-%d'),
                count=len(logs),
                cals=total_cals,
                carbon=f"{total_carbon:.2f}",
                menu=meal_list
            )
            await bot.send_message(chat_id=chat_id, text=stats_msg, parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
            return
            
        # 4. /policy
        if text_content == "/policy":
             policy_msg = """📜 **Privacy Policy & Terms**

**1. Introduction**
By using **Qwen-EcoLens**, you agree to these terms.

**2. Disclaimer**
*   **AI Analysis:** Data (Nutrition, Carbon, ESG) are estimates by AI. **Informational only**. Not medical advice.
*   **Accuracy:** We do not guarantee 100% accuracy.

**3. Data Privacy**
*   **Images:** Uploaded images are processed by Alibaba Cloud. We may store them for history.
*   **Data:** We handle your Telegram ID/Username to provide the service.

**4. Code of Conduct**
*   Upload food images only. No illegal/abusive content.

**5. Contact**
*   Contact repository maintainer for help.
"""
             await bot.send_message(chat_id=chat_id, text=policy_msg, parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
             return

        # 5. ADMIN: /reload and /check
        if text_content.startswith(("/reload", "/check")):
            if telegram_id not in settings.ADMIN_IDS:
                return # Ignore non-admins
            
            parts = text_content.split()
            cmd = parts[0]
            
            if cmd == "/check" and len(parts) == 2:
                target_username = parts[1].replace("@", "")
                res = await session.execute(select(User).filter(User.username == target_username))
                target_user = res.scalars().first()
                if target_user:
                    await bot.send_message(chat_id=chat_id, text=f"👤 **{target_username}**\nCredits: {target_user.credits}\nLang: {target_user.language}")
                else:
                    await bot.send_message(chat_id=chat_id, text="User not found.")
                return

            if cmd == "/reload" and len(parts) == 3:
                target_username = parts[1].replace("@", "")
                try:
                    amount = int(parts[2])
                    res = await session.execute(select(User).filter(User.username == target_username))
                    target_user = res.scalars().first()
                    if target_user:
                        target_user.credits += amount
                        await session.commit()
                        await bot.send_message(chat_id=chat_id, text=f"✅ Added {amount} credits to @{target_username}. New Balance: {target_user.credits}")
                    else:
                        await bot.send_message(chat_id=chat_id, text="User not found.")
                except ValueError:
                    await bot.send_message(chat_id=chat_id, text="Invalid amount.")
                return

        # Video Generation Callback (Context: food_name|carbon|esg)
        # We need to store context or pass it in callback data (limit 64 chars).
        # Since prompt is complex, passing data is hard.
        # Better: Store last analysis in FoodLog and retrieve it? 
        # Or simplistic: Just use "food_name" if we can fit it.
        # Let's try to fetch the last log for the user to generate video for it.
        
        if text_content == "generate_video":
             # 1. Check Credits
             if user.credits < CREDIT_COST_VIDEO:
                  await bot.send_message(chat_id=chat_id, text=texts["insufficient_credits"].format(cost=CREDIT_COST_VIDEO, balance=user.credits))
                  return
             
             # 2. Get Last Log
             res = await session.execute(
                 select(FoodLog).filter(FoodLog.user_id == user.id).order_by(FoodLog.created_at.desc())
             )
             last_log = res.scalars().first()
             
             if not last_log:
                 await bot.send_message(chat_id=chat_id, text="No recent food log found.")
                 return

             # 3. Deduct Credits
             # Deduct Credits
             user.credits -= CREDIT_COST_VIDEO
             await session.commit()
             
             status_msg = await bot.send_message(chat_id=chat_id, text=texts["video_confirm"], parse_mode='Markdown')
             
             # Define Progress Callback
             async def telegram_progress(msg_text):
                 try:
                     await bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"📽 **{msg_text}**", parse_mode='Markdown')
                 except Exception as e:
                     logger.warning(f"Failed to update progress message: {e}")

             # 4. Generate
             video_prompt = (
                f"A cinematic educational video explaining how {last_log.food_name} affects the environment and human health. "
                f"Show visuals of {last_log.food_name}."
             )
             if last_log.analysis_json:
                 c = last_log.analysis_json.get('carbon_emission_kg')
                 e = last_log.analysis_json.get('esg_score')
                 video_prompt += f" It has {c} kg CO2 emissions and an ESG score of {e}/10."

             video_url = await generate_video(prompt=video_prompt, progress_callback=telegram_progress)

             if video_url:
                 caption = texts["video_caption"].format(food_name=last_log.food_name)
                 await bot.send_video(chat_id=chat_id, video=video_url, caption=caption)
             else:
                 # Refund
                 user.credits += CREDIT_COST_VIDEO
                 await session.commit()
                 await bot.send_message(chat_id=chat_id, text=texts["video_fail"])
             return

        # --- PHOTO PROCESSING ---
        photos = msg.get('photo')
        if not photos:
            if not text_content.startswith("/"):
                await bot.send_message(chat_id=chat_id, text=texts["welcome"].format(credits=user.credits), parse_mode='Markdown')
            return

        # CREDIT CHECK: Analysis
        if user.credits < CREDIT_COST_ANALYSIS:
            await bot.send_message(chat_id=chat_id, text=texts["insufficient_credits"].format(cost=CREDIT_COST_ANALYSIS, balance=user.credits), parse_mode='Markdown')
            return
        
        # Get largest photo
        file_id = photos[-1]['file_id']
        file_info = await bot.get_file(file_id)
        if file_info.file_path.startswith(('http:', 'https:')):
            telegram_image_url = file_info.file_path
        else:
            telegram_image_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_info.file_path}"

        await bot.send_message(chat_id=chat_id, text=texts["thinking"], parse_mode='Markdown')

        # 1. Download & Resize
        try:
             image_bytes = download_and_process_image(telegram_image_url)
        except Exception as e:
            logger.error(f"Image download failed: {e}")
            await bot.send_message(chat_id=chat_id, text=texts["error_process"])
            return

        # 2. Base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        base64_url = f"data:image/jpeg;base64,{base64_image}"

        # 3. Analyze (Pass Language)
        ai_result = analyze_image(base64_url, language=user.language)

        if "error" in ai_result:
             await bot.send_message(chat_id=chat_id, text=f"Error: {ai_result['error']}")
             return

        # DEDUCT CREDITS (Analysis)
        user.credits -= CREDIT_COST_ANALYSIS
        await session.commit()

        # 4. Upload OSS
        final_image_url = telegram_image_url
        try:
             oss_url = upload_to_oss(image_bytes)
             if oss_url: final_image_url = oss_url
        except Exception as e:
             logger.error(f"OSS failed: {e}")

        # Map ESG Score
        esg_score = ai_result.get('esg_score', 5)
        carbon_enum = 'Medium'
        if esg_score >= 8: carbon_enum = 'Low'
        elif esg_score <= 3: carbon_enum = 'High'

        # Save Log
        log = FoodLog(
            user_id=user.id,
            food_name=ai_result.get('food_name', 'Unknown'),
            calories=ai_result.get('calories', 0),
            carbon_score=carbon_enum,
            image_url=final_image_url,
            analysis_json=ai_result,
            credits_used=CREDIT_COST_ANALYSIS
        )
        session.add(log)
        await session.commit()

        # Reply
        eco_icon = "✅" if ai_result.get('eco_friendly') else "⚠️"
        health_icon = "❤️" if ai_result.get('healthy') else "🍔"
        
        # Translate dynamic parts? keys are standard. 
        # Using a generic format or custom per language? 
        # For simplicity, using one format but dynamic reasoning.
        
        response_text = (
            f"🍽 **{ai_result.get('food_name')}**\n\n"
            f"🔥 **{ai_result.get('calories')}** kcal\n"
            f"💨 **{ai_result.get('carbon_emission_kg', 'N/A')}** kg CO2e\n"
            f"🌿 ESG: **{esg_score}/10**\n"
            f"{eco_icon} Eco: {'Yes' if ai_result.get('eco_friendly') else 'No'}\n"
            f"{health_icon} Healthy: {'Yes' if ai_result.get('healthy') else 'No'}\n\n"
            f"📝 {ai_result.get('reasoning')}\n\n"
            f"💰 Bal: **{user.credits}**"
        )
        
        # Add Video Button
        kb = [[InlineKeyboardButton(texts["btn_video"], callback_data="generate_video")]]
        
        await bot.send_message(
            chat_id=chat_id, 
            text=response_text, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(kb)
        )
