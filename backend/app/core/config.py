from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "adm4pp3r2025"
    SECRET_KEY: str = "changeme"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]
    REPORTS_DIR: str = "/app/reports"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    class Config:
        env_file = ".env"


settings = Settings()
