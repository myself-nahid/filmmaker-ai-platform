from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GOOGLE_DRIVE_CREDENTIALS_FILE: str
    GOOGLE_CLOUD_PROJECT_ID: str
    GOOGLE_CLOUD_LOCATION: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()