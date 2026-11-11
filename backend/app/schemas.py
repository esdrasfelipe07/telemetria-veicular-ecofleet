from datetime import datetime
from typing import List, Optional
import re
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    role: str = Field("manager", pattern="^(admin|manager|driver)$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Senha com no mínimo 8 caracteres")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("A senha deve conter ao menos uma letra.")
        if not re.search(r"\d", v):
            raise ValueError("A senha deve conter ao menos um número.")
        return v

class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

# --- Telemetry Schemas ---
class TelemetryItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_id: int = Field(..., gt=0)
    recorded_at: datetime = Field(..., description="Timestamp da coleta no veículo (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed: float = Field(..., ge=0.0, le=300.0, description="Velocidade em km/h")
    rpm: Optional[int] = Field(0, ge=0, le=15000)
    fuel_level: Optional[float] = Field(100.0, ge=0.0, le=100.0)
    engine_temp: Optional[float] = Field(90.0, ge=-40.0, le=200.0)
    battery_voltage: Optional[float] = Field(12.6, ge=0.0, le=35.0)
    odometer: Optional[float] = Field(0.0, ge=0.0, le=2000000.0)
    is_offline_sync: Optional[bool] = Field(False, description="Flag indicando se veio de buffer/cache offline")

class TelemetryBatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[TelemetryItemCreate] = Field(
        ..., 
        min_length=1,
        max_length=500,
        description="Lista de medições agregadas durante período com conectividade reduzida (máx. 500)"
    )

class TelemetryResponse(TelemetryItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ingested_at: datetime

# --- Alert Schemas ---
class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_id: int
    alert_type: str
    message: str
    severity: str
    triggered_at: datetime
    resolved: bool

# --- Vehicle Schemas ---
class VehicleBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plate: str = Field(..., min_length=5, max_length=10, pattern=r"^[A-Z0-9-]+$")
    model: str = Field(..., min_length=2, max_length=100)
    brand: str = Field(..., min_length=2, max_length=100)
    year: int = Field(..., ge=1980, le=datetime.now().year + 1)
    status: str = Field("active", pattern="^(active|maintenance|inactive)$")
    driver_name: Optional[str] = Field(None, max_length=150)

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: Optional[str] = Field(None, min_length=2, max_length=100)
    brand: Optional[str] = Field(None, min_length=2, max_length=100)
    year: Optional[int] = Field(None, ge=1980, le=datetime.now().year + 1)
    status: Optional[str] = Field(None, pattern="^(active|maintenance|inactive)$")
    driver_name: Optional[str] = Field(None, max_length=150)

class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class VehicleWithLatestTelemetry(VehicleResponse):
    latest_telemetry: Optional[TelemetryResponse] = None
    active_alerts_count: int = 0
