from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Vehicle
from app.routers import auth, vehicles, telemetry, seed

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria todas as tabelas no banco de dados na inicialização
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed se o banco estiver vazio
    db = SessionLocal()
    try:
        if db.query(Vehicle).count() == 0:
            seed.populate_sample_data(db)
    finally:
        db.close()
    
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API RESTful para Ingestão e Processamento de Telemetria Veicular com Suporte a "
        "Conectividade Reduzida (Offline-First), Gestão de Frotas e Alertas em Tempo Real."
    ),
    lifespan=lifespan
)

# Configuração de CORS para permitir acesso a partir do frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos roteadores da API v1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(vehicles.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix=settings.API_V1_STR)
app.include_router(seed.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Healthcheck"])
def root():
    return {
        "sistema": settings.PROJECT_NAME,
        "versao": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "edital": "Vaga 5 - Desenvolvedor Full-stack Júnior (UFRN)"
    }
