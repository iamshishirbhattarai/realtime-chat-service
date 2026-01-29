from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    redis_url: str
    redis_host: str
    redis_port: int

    jwt_secret_key: str
    jwt_refresh_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    jwt_refresh_token_expire_minutes: int

    postgres_url: str

    cors_origins: list[str] = []

    class Config:
        env_file = ".env"


settings = Settings()
