from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SIFSentinel API"
    environment: str = "development"

    database_url: str = (
        "postgresql+psycopg://"
        "sifsentinel:sifsentinel@localhost:5432/sifsentinel"
    )

    class Config:
        env_file = ".env"


settings = Settings()