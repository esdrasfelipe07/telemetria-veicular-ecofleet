from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db, Base, engine
from app.models import User, Vehicle, TelemetryLog, Alert
from app.auth import get_password_hash

router = APIRouter(prefix="/seed", tags=["População de Dados (Seed)"])

@router.post("")
def populate_sample_data(db: Session = Depends(get_db)):
    """
    Popula o banco de dados com dados de teste realistas:
    - Veículos da frota do Campus Central da UFRN (Circular, Van IMD, etc.)
    - Usuário gestor da frota
    - Trajetórias GPS no anel viário da UFRN
    - Alertas de telemetria
    """
    # 1. Cria usuário padrão
    admin = db.query(User).filter(User.email == "gestor@ufrn.br").first()
    if not admin:
        admin = User(
            email="gestor@ufrn.br",
            full_name="Gestor de Frota UFRN",
            hashed_password=get_password_hash("senha123"),
            role="manager"
        )
        db.add(admin)

    # 2. Veículos
    v1 = db.query(Vehicle).filter(Vehicle.plate == "RN-UFRN01").first()
    if not v1:
        v1 = Vehicle(
            plate="RN-UFRN01",
            model="Ônibus Circular Direto",
            brand="Mercedes-Benz OF-1721",
            year=2023,
            status="active",
            driver_name="Seu Francisco"
        )
        db.add(v1)

    v2 = db.query(Vehicle).filter(Vehicle.plate == "RN-IMD002").first()
    if not v2:
        v2 = Vehicle(
            plate="RN-IMD002",
            model="Van Laboratório Móvel",
            brand="Renault Master L3H2",
            year=2022,
            status="active",
            driver_name="Mariana Lima"
        )
        db.add(v2)

    v3 = db.query(Vehicle).filter(Vehicle.plate == "RN-LAB003").first()
    if not v3:
        v3 = Vehicle(
            plate="RN-LAB003",
            model="Caminhonete de Campo",
            brand="Toyota Hilux 4x4",
            year=2024,
            status="maintenance",
            driver_name="Carlos Eduardo"
        )
        db.add(v3)

    db.commit()
    db.refresh(v1)
    db.refresh(v2)

    # 3. Telemetria Simulada no Anel Viário da UFRN (Coordenadas reais do Campus Central de Natal)
    # Rota ao redor do campus central da UFRN: Reitoria -> CCET -> IMD -> CCHLA -> Reitoria
    ufrn_route_points = [
        (-5.8365, -35.2052, 38.0, 1600, 91.0),
        (-5.8380, -35.2040, 42.5, 1750, 91.2),
        (-5.8402, -35.2031, 48.0, 1900, 92.0),
        (-5.8430, -35.2025, 52.0, 2100, 92.5),
        (-5.8465, -35.2030, 45.0, 1800, 92.0),
        (-5.8480, -35.2060, 35.0, 1500, 91.5),
        (-5.8460, -35.2090, 40.0, 1650, 91.8),
        (-5.8420, -35.2105, 55.0, 2200, 93.0),
        (-5.8385, -35.2095, 83.5, 2900, 98.0), # Trecho com excesso de velocidade para gerar alerta!
        (-5.8360, -35.2075, 40.0, 1700, 92.0),
        (-5.8350, -35.2058, 30.0, 1400, 91.0),
    ]

    # Só adiciona histórico se ainda não tiver registros para v1
    existing_logs = db.query(TelemetryLog).filter(TelemetryLog.vehicle_id == v1.id).count()
    if existing_logs == 0:
        base_time = datetime.now(timezone.utc) - timedelta(minutes=len(ufrn_route_points) * 2)
        battery = 12.6
        fuel = 78.5
        odometer = 14230.0

        for i, (lat, lon, speed, rpm, temp) in enumerate(ufrn_route_points):
            pt_time = base_time + timedelta(minutes=i * 2)
            fuel -= 0.15
            odometer += (speed * (2 / 60))
            is_offline = (i >= 5 and i <= 8) # Simula que os pontos 5 a 8 foram acumulados offline
            
            log = TelemetryLog(
                vehicle_id=v1.id,
                recorded_at=pt_time,
                ingested_at=pt_time if not is_offline else pt_time + timedelta(minutes=10),
                latitude=lat,
                longitude=lon,
                speed=speed,
                rpm=rpm,
                fuel_level=round(fuel, 1),
                engine_temp=temp,
                battery_voltage=battery,
                odometer=round(odometer, 2),
                is_offline_sync=is_offline
            )
            db.add(log)

            # Se excedeu 80 km/h, gera alerta
            if speed > 80.0:
                alert = Alert(
                    vehicle_id=v1.id,
                    alert_type="SPEED_EXCEEDED",
                    message=f"Velocidade excedida próximo ao anel viário: {speed:.1f} km/h (Limite: 80 km/h)",
                    severity="HIGH",
                    triggered_at=pt_time,
                    resolved=False
                )
                db.add(alert)

        db.commit()

    return {
        "status": "success",
        "message": "Dados de demonstração (UFRN) gerados com sucesso!",
        "credentials": {
            "email": "gestor@ufrn.br",
            "password": "senha123"
        }
    }
