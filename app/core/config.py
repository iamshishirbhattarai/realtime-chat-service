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

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool = False

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    cors_origins: list[str] = []

    class Config:
        env_file = ".env"


settings = Settings()
