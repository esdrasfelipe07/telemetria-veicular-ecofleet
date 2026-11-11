import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "EcoFleet - Telemetria Veicular"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Defaults to SQLite for immediate out-of-the-box local testing,
    # or PostgreSQL when DATABASE_URL is set in Docker / Production.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./telemetry.db"
    )
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-key-ufrn-telemetry-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 horas

    # Limites para disparo de alertas na telemetria
    SPEED_LIMIT_KMH: float = 80.0
    MAX_ENGINE_TEMP_C: float = 102.0
    MIN_BATTERY_VOLTS: float = 11.5

    class Config:
        case_sensitive = True

settings = Settings()
