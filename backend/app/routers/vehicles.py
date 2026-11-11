from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vehicle, TelemetryLog, Alert
from app.schemas import (
    VehicleCreate, VehicleUpdate, VehicleResponse, VehicleWithLatestTelemetry, TelemetryResponse
)
from app.auth import get_current_user

router = APIRouter(prefix="/vehicles", tags=["Veículos da Frota"])

@router.get("", response_model=List[VehicleWithLatestTelemetry])
def list_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    results = []
    for v in vehicles:
        latest = (
            db.query(TelemetryLog)
            .filter(TelemetryLog.vehicle_id == v.id)
            .order_by(TelemetryLog.recorded_at.desc())
            .first()
        )
        alerts_count = (
            db.query(Alert)
            .filter(Alert.vehicle_id == v.id, Alert.resolved == False)
            .count()
        )
        results.append(
            VehicleWithLatestTelemetry(
                id=v.id,
                plate=v.plate,
                model=v.model,
                brand=v.brand,
                year=v.year,
                status=v.status,
                driver_name=v.driver_name,
                created_at=v.created_at,
                latest_telemetry=TelemetryResponse.from_orm(latest) if latest else None,
                active_alerts_count=alerts_count
            )
        )
    return results

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_in: VehicleCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    existing = db.query(Vehicle).filter(Vehicle.plate == vehicle_in.plate.upper().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Veículo com a placa {vehicle_in.plate} já está cadastrado"
        )
    vehicle = Vehicle(
        plate=vehicle_in.plate.upper().strip(),
        model=vehicle_in.model,
        brand=vehicle_in.brand,
        year=vehicle_in.year,
        status=vehicle_in.status,
        driver_name=vehicle_in.driver_name
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

@router.get("/{vehicle_id}", response_model=VehicleWithLatestTelemetry)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    
    latest = (
        db.query(TelemetryLog)
        .filter(TelemetryLog.vehicle_id == v.id)
        .order_by(TelemetryLog.recorded_at.desc())
        .first()
    )
    alerts_count = (
        db.query(Alert)
        .filter(Alert.vehicle_id == v.id, Alert.resolved == False)
        .count()
    )
    return VehicleWithLatestTelemetry(
        id=v.id,
        plate=v.plate,
        model=v.model,
        brand=v.brand,
        year=v.year,
        status=v.status,
        driver_name=v.driver_name,
        created_at=v.created_at,
        latest_telemetry=TelemetryResponse.from_orm(latest) if latest else None,
        active_alerts_count=alerts_count
    )

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    vehicle_in: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    
    update_data = vehicle_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(v, field, val)
    db.commit()
    db.refresh(v)
    return v

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    db.delete(v)
    db.commit()
    return None
