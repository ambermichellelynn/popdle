from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://popdle:popdle@localhost:5432/popdle"
    redis_url: str = "redis://localhost:6379/0"
    tmdb_api_key: str = ""
    secret_key: str = "dev-secret-change-me"
    stripe_secret_key: str = ""
    frontend_base_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
