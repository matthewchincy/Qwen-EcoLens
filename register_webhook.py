import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Content-Type": "application/json"
}

def set_webhook():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")

    if not token or not webhook_url:
        print("Error: Please make sure TELEGRAM_BOT_TOKEN and WEBHOOK_URL are set in .env")
        return

    print(f"Setting webhook to: {webhook_url}")
    url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
    
    try:
        response = requests.get(url)
        print(f"Webhook Response: {response.json()}")

        # Set My Commands (Persistent Menu)
        commands = [
            {"command": "start", "description": "Start & Guide 📸"},
            {"command": "stats", "description": "Daily Consumption 📅"},
            {"command": "language", "description": "Change Language 🌐"},
            {"command": "policy", "description": "Terms & Privacy 📜"}
        ]
        cmd_url = f"https://api.telegram.org/bot{token}/setMyCommands"
        cmd_response = requests.post(cmd_url, json={"commands": commands})
        print(f"Set Commands Response: {cmd_response.json()}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    set_webhook()
