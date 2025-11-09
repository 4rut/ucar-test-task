from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="incidents-api", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/incidents",
        alias="DATABASE_URL"
    )

    model_config = {
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
