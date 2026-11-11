from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "manager"

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

# --- Telemetry Schemas ---
class TelemetryItemCreate(BaseModel):
    vehicle_id: int
    recorded_at: datetime = Field(..., description="Timestamp da coleta no veículo (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed: float = Field(..., ge=0.0, description="Velocidade em km/h")
    rpm: Optional[int] = Field(0, ge=0)
    fuel_level: Optional[float] = Field(100.0, ge=0.0, le=100.0)
    engine_temp: Optional[float] = Field(90.0, ge=-20.0, le=200.0)
    battery_voltage: Optional[float] = Field(12.6, ge=0.0, le=30.0)
    odometer: Optional[float] = Field(0.0, ge=0.0)
    is_offline_sync: Optional[bool] = Field(False, description="Flag indicando se veio de buffer/cache offline")

class TelemetryBatchCreate(BaseModel):
    items: List[TelemetryItemCreate] = Field(
        ..., 
        description="Lista de medições agregadas durante período com conectividade reduzida"
    )

class TelemetryResponse(TelemetryItemCreate):
    id: int
    ingested_at: datetime

    class Config:
        from_attributes = True

# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: int
    vehicle_id: int
    alert_type: str
    message: str
    severity: str
    triggered_at: datetime
    resolved: bool

    class Config:
        from_attributes = True

# --- Vehicle Schemas ---
class VehicleBase(BaseModel):
    plate: str
    model: str
    brand: str
    year: int
    status: str = "active"
    driver_name: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    model: Optional[str] = None
    brand: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    driver_name: Optional[str] = None

class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class VehicleWithLatestTelemetry(VehicleResponse):
    latest_telemetry: Optional[TelemetryResponse] = None
    active_alerts_count: int = 0
