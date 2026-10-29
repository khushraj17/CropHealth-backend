from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name : str = "Crop Health API"
    app_env: str = "development"
    debug: bool = False
    api_v2_prefix: str = "/api/v2"
    database_url : str
    upload_dir: str = "uploads"
    max_upload_size_bytes: int = 5 * 1024 * 1024

    imagekit_private_key: str
    imagekit_url_endpoint: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()