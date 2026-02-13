from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class Settings(BaseSettings):
    APP_NAME: str = "BE iQuality Test"
    API_V1_PREFIX: str = "/api/v1"
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    DB_HOST: str | None = None
    DB_PORT: int = 5432
    DB_NAME: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None

    OPENROUTER_API_KEY: str | None = None

    @property
    def DATABASE_URL(self) -> str | None:
        if not (self.DB_HOST and self.DB_NAME and self.DB_USER and self.DB_PASSWORD):
            return None
        user = quote_plus(self.DB_USER)
        pwd = quote_plus(self.DB_PASSWORD)
        return f"postgresql+psycopg://{user}:{pwd}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
