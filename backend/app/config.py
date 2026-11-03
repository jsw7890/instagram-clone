from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-instagram-clone-change-me"
    access_token_expire_minutes: int = 10080
    database_url: str = "sqlite:///./instagram.db"
    upload_dir: str = "uploads"
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 10

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
