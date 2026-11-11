import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Vehicle
from app.routers import auth, vehicles, telemetry, seed

logger = logging.getLogger("ecofleet.security")

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

# Configuração Segura de CORS: Origens explícitas e controladas (Prevenção Item 19)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,
)

# Tratamento Global de Exceções Não Capturadas (Prevenção Item 12 - Vazamento de Informações Sensíveis)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado na rota {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Ocorreu um erro interno no servidor. Os detalhes foram registrados de forma segura.",
            "path": request.url.path
        }
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
