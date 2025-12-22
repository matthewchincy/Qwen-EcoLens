from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DASHSCOPE_API_KEY: str
    TELEGRAM_BOT_TOKEN: str
    DATABASE_URL: str
    WEBHOOK_URL: str = "http://localhost:8000/webhook/telegram"

    # OSS Settings
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_ENDPOINT: str = ""
    OSS_BUCKET_NAME: str = ""
    
    # Admin
    ADMIN_IDS: list[str] = ["382366398"]

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

settings = Settings()
