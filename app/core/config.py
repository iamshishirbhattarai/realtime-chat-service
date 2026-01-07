from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    redis_url: str
    redis_host: str
    redis_port: int

    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int

    postgres_url: str

    class Config:
        env_file = ".env"


settings = Settings()
