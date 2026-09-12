from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = "development"
    project_name: str = "TaskFlow API"
    cors_origins: list[str] = ["http://localhost:4200"]
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    refresh_token_cookie_name: str = "refresh_token"
    cookie_secure: bool = False
    upload_dir: str = "uploads/tasks"
    max_upload_size_mb: int = 5


settings = Settings()