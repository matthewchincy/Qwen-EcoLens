import json
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

def analyze_image(image_url: str, language: str = 'en') -> dict:
    """
    Analyzes food image using Qwen-VL via OpenAI compatible API.
    """
    if not settings.DASHSCOPE_API_KEY:
        logger.error("DASHSCOPE_API_KEY is missing.")
        return {"error": "API Key missing"}

    client = OpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )

    lang_instr = f"Respond in {language} language." if language != 'en' else ""

    messages = [
        {
            "role": "system",
            "content": f"You are a Nutrition & ESG Expert. Analyze the food image. Identify the dish. Estimate calories. Calculate Carbon Emission (kg CO2e). Assign an ESG Score (1-10). Determine if it is Eco-Friendly (bool) and Healthy (bool). Return ONLY valid JSON: {{'food_name': str, 'calories': int, 'carbon_emission_kg': float, 'esg_score': int, 'eco_friendly': bool, 'healthy': bool, 'reasoning': str}}. {lang_instr}"
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": "Analyze this food item."}
            ]
        }
    ]

    try:
        completion = client.chat.completions.create(
            model="qwen-vl-max-latest",
            messages=messages,
            top_p=0.8,
            temperature=0.7
        )

        result_text = completion.choices[0].message.content
        logger.info(f"AI Response: {result_text}")

        # Basic cleanup if code blocks are included
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        return json.loads(result_text)

    except Exception as e:
        logger.error(f"Error calling Qwen AI: {e}")
        return {"error": str(e)}
