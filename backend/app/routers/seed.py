from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Vehicle, TelemetryLog, Alert
from app.auth import get_password_hash

router = APIRouter(prefix="/seed", tags=["População de Dados (Seed)"])

# Trajetória real traçada estritamente ao longo do asfalto do Anel Viário da UFRN (Campus Central)
# Contorno: Reitoria -> CCHLA -> Centro de Biociências -> Setor IV -> ECT -> Ginásio/Atletismo -> IMD -> Reitoria
UFRN_ANEL_VIARIO_WAYPOINTS = [
    (-5.8378, -35.2053, 30.0, 1400, 90.0), # Rotatória Reitoria / Praça Cívica
    (-5.8390, -35.2050, 38.0, 1600, 90.5), # Anel Viário descendo em frente ao CCHLA
    (-5.8405, -35.2043, 42.0, 1750, 91.0), # Setor de Aulas II
    (-5.8420, -35.2034, 46.0, 1900, 91.5), # Acesso Biblioteca Central / RU
    (-5.8429, -35.2028, 40.0, 1650, 91.2), # Rotatória Sul / Centro de Biociências
    (-5.8433, -35.2015, 45.0, 1800, 91.8), # Anel Viário Sul (Setor de Aulas IV)
    (-5.8437, -35.1995, 48.0, 1900, 92.0), # Anel Sul (Área Tecnológica / ECT)
    (-5.8441, -35.1970, 50.0, 2000, 92.2), # Curva Sudeste do Anel Viário
    (-5.8425, -35.1953, 52.0, 2050, 92.5), # Anel Viário Leste (Reta)
    (-5.8405, -35.1951, 84.0, 2900, 98.0), # Reta Anel Leste (Alerta de Velocidade 84 km/h)
    (-5.8385, -35.1962, 50.0, 2000, 92.0), # Anel Leste aproximando do Ginásio Poliesportivo
    (-5.8368, -35.1975, 42.0, 1750, 91.5), # Curva da Pista de Atletismo
    (-5.8350, -35.1998, 38.0, 1600, 91.0), # Anel Viário Norte (Parque Tecnológico / Bosque)
    (-5.8335, -35.2020, 35.0, 1500, 90.8), # Proximidades do IMD
    (-5.8325, -35.2036, 32.0, 1450, 90.5), # Curva Norte (Acesso Solon de Miranda Galvão)
    (-5.8340, -35.2052, 35.0, 1500, 90.8), # Sentido Reitoria
    (-5.8360, -35.2057, 32.0, 1450, 90.5), # Chegada à Praça Cívica
    (-5.8378, -35.2053, 30.0, 1400, 90.0), # Retorno à Rotatória da Reitoria (Loop Fechado)
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
        is_offline = (i >= 6 and i <= 10)

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
                message=f"Velocidade excedida no Anel Viário Leste: {speed:.1f} km/h (Limite: 80 km/h)",
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
