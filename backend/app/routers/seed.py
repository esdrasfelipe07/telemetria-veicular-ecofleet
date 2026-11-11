from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Vehicle, TelemetryLog, Alert
from app.auth import get_password_hash

router = APIRouter(prefix="/seed", tags=["População de Dados (Seed)"])

# Trajetória com coordenadas de alta fidelidade desenhadas estritamente sobre as curvas
# do Anel Viário do Campus Central da UFRN (Natal/RN)
UFRN_ANEL_VIARIO_WAYPOINTS = [
    (-5.8360, -35.2055, 30.0, 1400, 90.0), # Reitoria / Praça Cívica
    (-5.8364, -35.2046, 35.0, 1500, 90.5), # Acesso Norte
    (-5.8368, -35.2038, 38.0, 1600, 91.0), # Curva do Ginásio Poliesportivo
    (-5.8375, -35.2032, 40.0, 1650, 91.0), # Pista de Atletismo
    (-5.8385, -35.2028, 42.0, 1700, 91.2), # Anel Leste Norte
    (-5.8400, -35.2024, 45.0, 1800, 91.5), # CCET / ECT
    (-5.8418, -35.2023, 48.0, 1900, 92.0), # DECOM / DCA
    (-5.8438, -35.2025, 50.0, 2000, 92.2), # Setor de Aulas IV
    (-5.8455, -35.2030, 48.0, 1950, 92.0), # Anel Leste Sul
    (-5.8468, -35.2040, 44.0, 1800, 91.8), # Curva Sul (Próximo ao IMD)
    (-5.8475, -35.2052, 40.0, 1700, 91.5), # Rotatória Sul
    (-5.8476, -35.2063, 38.0, 1600, 91.5), # Acesso RU / Centro de Biociências
    (-5.8470, -35.2072, 40.0, 1650, 91.8), # Curva Sudoeste
    (-5.8458, -35.2077, 45.0, 1800, 92.0), # Anel Oeste Sul
    (-5.8440, -35.2078, 52.0, 2100, 92.5), # CCHLA
    (-5.8420, -35.2077, 84.0, 2900, 98.0), # Reta CCHLA/BCZM (Gera Alerta de Velocidade)
    (-5.8402, -35.2073, 50.0, 2050, 92.5), # Setor de Aulas II
    (-5.8388, -35.2066, 42.0, 1750, 91.5), # Setor de Aulas I
    (-5.8376, -35.2060, 36.0, 1550, 91.0), # Aproximação da Reitoria
    (-5.8360, -35.2055, 30.0, 1400, 90.0)  # Fechamento do Anel Viário
]

@router.post("")
def populate_sample_data(db: Session = Depends(get_db)):
    """
    Popula ou reinicializa o banco de dados com veículos da frota UFRN
    e trajetória georreferenciada de alta precisão sobre o Anel Viário.
    """
    # 1. Usuário Gestor da Frota
    admin = db.query(User).filter(User.email == "gestor@ufrn.br").first()
    if not admin:
        admin = User(
            email="gestor@ufrn.br",
            full_name="Gestor de Frota UFRN",
            hashed_password=get_password_hash("senha123"),
            role="manager"
        )
        db.add(admin)

    # 2. Veículos da Frota UFRN
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

    # 3. Limpa telemetria e alertas anteriores de v1 para resetar a rota com as vias corretas
    db.query(TelemetryLog).filter(TelemetryLog.vehicle_id == v1.id).delete()
    db.query(Alert).filter(Alert.vehicle_id == v1.id).delete()
    db.commit()

    # 4. Popula os pontos com as coordenadas reais do Anel Viário da UFRN
    base_time = datetime.now(timezone.utc) - timedelta(minutes=len(UFRN_ANEL_VIARIO_WAYPOINTS) * 2)
    battery = 12.6
    fuel = 78.5
    odometer = 14230.0

    for i, (lat, lon, speed, rpm, temp) in enumerate(UFRN_ANEL_VIARIO_WAYPOINTS):
        pt_time = base_time + timedelta(minutes=i * 2)
        fuel -= 0.12
        odometer += (speed * (2 / 60))
        # Simula período com conectividade reduzida (trecho sul/oeste do campus)
        is_offline = (i >= 9 and i <= 14)

        log = TelemetryLog(
            vehicle_id=v1.id,
            recorded_at=pt_time,
            ingested_at=pt_time if not is_offline else pt_time + timedelta(minutes=15),
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

        if speed > 80.0:
            alert = Alert(
                vehicle_id=v1.id,
                alert_type="SPEED_EXCEEDED",
                message=f"Velocidade excedida no Anel Viário Oeste: {speed:.1f} km/h (Limite: 80 km/h)",
                severity="HIGH",
                triggered_at=pt_time,
                resolved=False
            )
            db.add(alert)

    db.commit()

    return {
        "status": "success",
        "message": f"Demonstração UFRN atualizada com {len(UFRN_ANEL_VIARIO_WAYPOINTS)} pontos georreferenciados no Anel Viário!",
        "waypoints_count": len(UFRN_ANEL_VIARIO_WAYPOINTS)
    }
