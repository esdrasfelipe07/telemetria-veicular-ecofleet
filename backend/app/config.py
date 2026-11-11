import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "EcoFleet - Telemetria Veicular"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Defaults to SQLite for local development or PostgreSQL in Docker/Production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./telemetry.db"
    )
    
    # Chave secreta de 64 caracteres criptograficamente robusta (RFC 7518)
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "b3a886dfc798a729e2f495831cf04c4059292c2db814238e8ec4eef443213197"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 horas

    # Origens explícitas permitidas pelo CORS (prevenção de CORS mal configurado)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Limites para disparo de alertas na telemetria
    SPEED_LIMIT_KMH: float = 80.0
    MAX_ENGINE_TEMP_C: float = 102.0
    MIN_BATTERY_VOLTS: float = 11.5

settings = Settings()
