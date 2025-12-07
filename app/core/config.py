from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    class Config:
        env_file = ".env"


settings = Settings()
