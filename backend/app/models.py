from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="manager") # admin, manager, driver
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(20), unique=True, index=True, nullable=False)
    model = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(50), default="active") # active, maintenance, inactive
    driver_name = Column(String(150), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    telemetry_logs = relationship(
        "TelemetryLog", 
        back_populates="vehicle", 
        cascade="all, delete-orphan",
        order_by="TelemetryLog.recorded_at.desc()"
    )
    alerts = relationship(
        "Alert", 
        back_populates="vehicle", 
        cascade="all, delete-orphan",
        order_by="Alert.triggered_at.desc()"
    )

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # recorded_at: Momento exato em que a telemetria foi aferida pelos sensores do veículo
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    # ingested_at: Momento em que o servidor recebeu a informação (essencial para medir latência de conectividade)
    ingested_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Dados de Posicionamento e Deslocamento
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=False) # km/h
    odometer = Column(Float, default=0.0) # km acumulado
    
    # Telemetria de Motores & Sensores
    rpm = Column(Integer, default=0) # Rotações por minuto
    fuel_level = Column(Float, default=100.0) # 0 a 100%
    engine_temp = Column(Float, default=90.0) # Graus Celsius
    battery_voltage = Column(Float, default=12.6) # Volts
    
    # Metadados de Conectividade
    is_offline_sync = Column(Boolean, default=False) # Indica se o dado foi acumulado no cache local offline

    vehicle = relationship("Vehicle", back_populates="telemetry_logs")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False) # SPEED_EXCEEDED, HIGH_ENGINE_TEMP, LOW_BATTERY
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    triggered_at = Column(DateTime(timezone=True), default=utc_now)
    resolved = Column(Boolean, default=False)

    vehicle = relationship("Vehicle", back_populates="alerts")
