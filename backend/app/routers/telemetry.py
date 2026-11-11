from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import Vehicle, TelemetryLog, Alert
from app.schemas import (
    TelemetryItemCreate, TelemetryBatchCreate, TelemetryResponse, AlertResponse
)

router = APIRouter(prefix="/telemetry", tags=["Telemetria e Ingestão de Dados"])

def evaluate_telemetry_alerts(item: TelemetryItemCreate, db: Session) -> Optional[Alert]:
    """
    Avalia os parâmetros da telemetria contra limites seguros de operação veicular.
    Gera alertas automáticos caso anomalias sejam detectadas.
    """
    alert = None
    if item.speed > settings.SPEED_LIMIT_KMH:
        alert = Alert(
            vehicle_id=item.vehicle_id,
            alert_type="SPEED_EXCEEDED",
            message=f"Velocidade excedida: {item.speed:.1f} km/h (Limite: {settings.SPEED_LIMIT_KMH} km/h)",
            severity="HIGH" if item.speed > (settings.SPEED_LIMIT_KMH + 20) else "MEDIUM",
            triggered_at=item.recorded_at
        )
    elif item.engine_temp > settings.MAX_ENGINE_TEMP_C:
        alert = Alert(
            vehicle_id=item.vehicle_id,
            alert_type="HIGH_ENGINE_TEMP",
            message=f"Superaquecimento do motor detectado: {item.engine_temp:.1f}°C (Máx: {settings.MAX_ENGINE_TEMP_C}°C)",
            severity="CRITICAL",
            triggered_at=item.recorded_at
        )
    elif item.battery_voltage < settings.MIN_BATTERY_VOLTS:
        alert = Alert(
            vehicle_id=item.vehicle_id,
            alert_type="LOW_BATTERY",
            message=f"Tensão baixa na bateria veicular: {item.battery_voltage:.1f}V (Mín: {settings.MIN_BATTERY_VOLTS}V)",
            severity="LOW",
            triggered_at=item.recorded_at
        )

    if alert:
        db.add(alert)
    return alert

@router.post("", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
def ingest_single_telemetry(payload: TelemetryItemCreate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo especificado não existe")

    log_entry = TelemetryLog(
        vehicle_id=payload.vehicle_id,
        recorded_at=payload.recorded_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        rpm=payload.rpm,
        fuel_level=payload.fuel_level,
        engine_temp=payload.engine_temp,
        battery_voltage=payload.battery_voltage,
        odometer=payload.odometer,
        is_offline_sync=payload.is_offline_sync or False
    )
    db.add(log_entry)
    evaluate_telemetry_alerts(payload, db)
    db.commit()
    db.refresh(log_entry)
    return log_entry

@router.post("/batch", status_code=status.HTTP_201_CREATED)
def ingest_telemetry_batch(batch: TelemetryBatchCreate, db: Session = Depends(get_db)):
    """
    ENDPOINT CHAVE PARA SUPORTE A CONECTIVIDADE REDUZIDA (OFFLINE-FIRST):
    Recebe um pacote acumulado de telemetria que foi guardado no cache local do
    veículo quando o sinal de rede (3G/4G) estava indisponível.
    """
    if not batch.items:
        raise HTTPException(status_code=400, detail="Lote de telemetria vazio")

    # Verifica se os veículos existem
    vehicle_ids = {item.vehicle_id for item in batch.items}
    existing_vehicles = {
        v.id for v in db.query(Vehicle.id).filter(Vehicle.id.in_(vehicle_ids)).all()
    }
    
    missing = vehicle_ids - existing_vehicles
    if missing:
        raise HTTPException(
            status_code=400, 
            detail=f"Veículos com IDs inexistentes no lote: {list(missing)}"
        )

    alerts_count = 0
    records_to_insert = []
    
    for item in batch.items:
        records_to_insert.append(
            TelemetryLog(
                vehicle_id=item.vehicle_id,
                recorded_at=item.recorded_at,
                latitude=item.latitude,
                longitude=item.longitude,
                speed=item.speed,
                rpm=item.rpm,
                fuel_level=item.fuel_level,
                engine_temp=item.engine_temp,
                battery_voltage=item.battery_voltage,
                odometer=item.odometer,
                is_offline_sync=True # Identifica que veio de buffer offline
            )
        )
        if evaluate_telemetry_alerts(item, db):
            alerts_count += 1

    db.bulk_save_objects(records_to_insert)
    db.commit()

    return {
        "status": "success",
        "message": f"Sincronização em lote concluída com sucesso.",
        "received_count": len(batch.items),
        "persisted_count": len(records_to_insert),
        "alerts_triggered": alerts_count
    }

@router.get("/vehicles/{vehicle_id}/trajectory", response_model=List[TelemetryResponse])
def get_vehicle_trajectory(
    vehicle_id: int,
    limit: int = Query(100, ge=1, le=1000),
    hours: Optional[int] = Query(None, description="Filtrar pelas últimas N horas"),
    db: Session = Depends(get_db)
):
    query = db.query(TelemetryLog).filter(TelemetryLog.vehicle_id == vehicle_id)
    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = query.filter(TelemetryLog.recorded_at >= since)
    
    # Ordenado do mais recente para o mais antigo ou vice-versa para traçado da rota
    trajectory = query.order_by(TelemetryLog.recorded_at.asc()).limit(limit).all()
    return trajectory

@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    vehicle_id: Optional[int] = None,
    unresolved_only: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if vehicle_id:
        query = query.filter(Alert.vehicle_id == vehicle_id)
    if unresolved_only:
        query = query.filter(Alert.resolved == False)
    return query.order_by(Alert.triggered_at.desc()).limit(100).all()

@router.patch("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    alert.resolved = True
    db.commit()
    return {"status": "success", "message": "Alerta resolvido"}
