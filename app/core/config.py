from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GOOGLE_DRIVE_CREDENTIALS_FILE: str
    GOOGLE_CLOUD_PROJECT_ID: str
    GOOGLE_CLOUD_LOCATION: str
    DATABASE_URL: str
    KIE_API_KEY: str
    PUBLIC_SERVER_URL: str
    MAIN_BACKEND_SAVE_URL: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()