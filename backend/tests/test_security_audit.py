import os
import time
import pytest
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import SessionLocal
from app.models import User, Vehicle
from app.rate_limiter import auth_rate_limiter

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reseta o limitador de taxa antes de cada teste para evitar interferências."""
    auth_rate_limiter.reset()

# ==============================================================================
# 1. TESTE ITEM 1 - Variáveis de Ambiente e .gitignore
# ==============================================================================
def test_item_01_env_and_secrets_not_tracked():
    """Garante que .env não está exposto nem rastreado no git."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    gitignore_path = os.path.join(root_dir, ".gitignore")
    
    assert os.path.exists(gitignore_path), "Arquivo .gitignore deve existir"
    with open(gitignore_path, "r") as f:
        content = f.read()
        assert ".env" in content, ".gitignore deve ignorar .env"

    # Garante que nenhum arquivo .env real foi commitado
    assert not os.path.exists(os.path.join(root_dir, ".env")), ".env não deve existir no root"
    assert not os.path.exists(os.path.join(root_dir, "backend/.env")), "backend/.env não deve existir no repo"

# ==============================================================================
# 2. TESTE ITEM 3 - Validação Estrita no Backend (Pydantic / Whitelist)
# ==============================================================================
def test_item_03_backend_input_validation_strict():
    """Valida que entradas fora dos limites seguros ou malformadas são rejeitadas com 422."""
    
    # 1. Latitude absurda (> 90)
    bad_payload_lat = {
        "vehicle_id": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "latitude": 999.0, # Inválido!
        "longitude": -35.20,
        "speed": 50.0
    }
    res = client.post("/api/v1/telemetry", json=bad_payload_lat)
    assert res.status_code == 422, "Latitude > 90 deve retornar 422 Unprocessable Entity"

    # 2. Velocidade negativa
    bad_payload_speed = {
        "vehicle_id": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "latitude": -5.84,
        "longitude": -35.20,
        "speed": -10.0 # Inválido!
    }
    res = client.post("/api/v1/telemetry", json=bad_payload_speed)
    assert res.status_code == 422, "Velocidade negativa deve retornar 422"

    # 3. Propriedade não esperada (Extra field forbidden - Whitelist)
    bad_payload_extra = {
        "vehicle_id": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "latitude": -5.84,
        "longitude": -35.20,
        "speed": 50.0,
        "malicious_injected_field": "exploit" # Campo não permitido
    }
    res = client.post("/api/v1/telemetry", json=bad_payload_extra)
    assert res.status_code == 422, "Propriedades desconhecidas (extra fields) devem ser bloqueadas com 422"

# ==============================================================================
# 3. TESTE ITEM 4 - Injeção de SQL (SQL Injection)
# ==============================================================================
def test_item_04_sql_injection_defense():
    """Testa tentativas clássicas de SQL Injection em endpoints de busca e autenticação."""
    sql_payloads = [
        "' OR '1'='1",
        "admin' --",
        "1; DROP TABLE vehicles; --",
        "' UNION SELECT null, null, null --"
    ]

    for payload in sql_payloads:
        # Tentativa no login
        res = client.post("/api/v1/auth/login-json", json={
            "email": "gestor@ufrn.br",
            "password": payload
        })
        assert res.status_code in (401, 422), f"SQL Injection no login deve falhar de forma segura. Código: {res.status_code}"
        assert "syntax error" not in res.text.lower(), "Não deve haver vazamento de erro de SQL"

    # Tentativa em parâmetro numérico de rota
    res = client.get("/api/v1/vehicles/' OR 1=1 --")
    assert res.status_code == 422, "ID malformado deve ser rejeitado pela validação de rota"

# ==============================================================================
# 4. TESTE ITEM 5 - Autenticação Fraca (Políticas de Senha)
# ==============================================================================
def test_item_05_weak_password_prevention():
    """Garante que senhas curtas (< 8 chars) ou sem letras/números são rejeitadas."""
    # Senha curta
    res_short = client.post("/api/v1/auth/register", json={
        "email": "curta@ufrn.br",
        "full_name": "Usuario Curto",
        "password": "123", # Muito curta
        "role": "driver"
    })
    assert res_short.status_code == 422
    assert "8" in res_short.text or "min_length" in res_short.text

    # Senha sem números
    res_no_num = client.post("/api/v1/auth/register", json={
        "email": "semnum@ufrn.br",
        "full_name": "Usuario Sem Num",
        "password": "apenasletras",
        "role": "driver"
    })
    assert res_no_num.status_code == 422
    assert "número" in res_no_num.text

    # Senha forte aceita
    valid_email = f"valido_{int(time.time())}@ufrn.br"
    res_valid = client.post("/api/v1/auth/register", json={
        "email": valid_email,
        "full_name": "Usuario Valido",
        "password": "SenhaForte123!",
        "role": "driver"
    })
    assert res_valid.status_code == 201

# ==============================================================================
# 5. TESTE ITEM 6 - IDOR e Controle de Acesso Seguro
# ==============================================================================
def test_item_06_access_control_and_protected_routes():
    """Verifica se rotas sensíveis exigem autenticação obrigatória via Bearer Token."""
    # Criação de veículo sem token
    res = client.post("/api/v1/vehicles", json={
        "plate": "ABC-1234",
        "model": "Carro Teste",
        "brand": "Fiat",
        "year": 2024
    })
    assert res.status_code == 401, "Criar veículo sem token deve retornar 401 Unauthorized"

    # Perfil /me sem token
    res_me = client.get("/api/v1/auth/me")
    assert res_me.status_code == 401, "Acessar /me sem token deve retornar 401"

# ==============================================================================
# 6. TESTE ITEM 7 - Senhas Armazenadas com Hash Seguro (Bcrypt com Salt)
# ==============================================================================
def test_item_07_passwords_hashed_with_bcrypt():
    """Garante que senhas nunca são salvas em texto puro no banco e usam Bcrypt ($2b$)."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "gestor@ufrn.br").first()
        assert user is not None, "Usuário gestor deve existir no banco"
        assert user.hashed_password != "senha123", "Senha NUNCA deve ser texto plano"
        assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$"), \
            "Hash deve usar o padrão seguro do Bcrypt"
        assert len(user.hashed_password) >= 60, "Comprimento do hash bcrypt deve ser >= 60 caracteres"
    finally:
        db.close()

# ==============================================================================
# 7. TESTE ITENS 8 & 15 - Força Bruta e Rate Limiting (Controle de Taxa)
# ==============================================================================
def test_items_08_and_15_rate_limiting_brute_force_prevention():
    """Garante que requisições repetidas acionam 429 Too Many Requests."""
    auth_rate_limiter.reset()

    # Dispara 5 tentativas de login com erro (limite configurado: 5 por minuto)
    for _ in range(5):
        res = client.post("/api/v1/auth/login-json", json={
            "email": "gestor@ufrn.br",
            "password": "senha_incorreta"
        })
        assert res.status_code == 401, "Tentativas normais devem retornar 401"

    # A 6ª tentativa consecutiva deve ser bloqueada pelo Rate Limiter
    blocked_res = client.post("/api/v1/auth/login-json", json={
        "email": "gestor@ufrn.br",
        "password": "senha_incorreta"
    })
    assert blocked_res.status_code == 429, "6ª tentativa deve ser bloqueada com 429 Too Many Requests"
    assert "Retry-After" in blocked_res.headers, "Resposta 429 deve incluir cabeçalho Retry-After"

# ==============================================================================
# 8. TESTE ITEM 9 - Falta de Bloqueio Durante Envio (Double Submit / Duplicidade)
# ==============================================================================
def test_item_09_duplicate_prevention_and_uniqueness():
    """Garante que registros duplicados são rejeitados pelo banco/backend."""
    # Login para obter token de autorização
    login_res = client.post("/api/v1/auth/login-json", json={
        "email": "gestor@ufrn.br",
        "password": "senha123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    plate = f"DUP-{int(time.time()) % 10000}"
    vehicle_payload = {
        "plate": plate,
        "model": "Van Teste",
        "brand": "Renault",
        "year": 2023,
        "status": "active"
    }

    # 1ª criação -> Sucesso
    res1 = client.post("/api/v1/vehicles", json=vehicle_payload, headers=headers)
    assert res1.status_code == 201

    # 2ª criação imediata da mesma placa -> Bloqueada
    res2 = client.post("/api/v1/vehicles", json=vehicle_payload, headers=headers)
    assert res2.status_code == 400
    assert "já está cadastrado" in res2.text

# ==============================================================================
# 9. TESTE ITEM 12 - Mensagens de Erro Revelando Informações Sensíveis
# ==============================================================================
def test_item_12_no_sensitive_info_in_error_responses():
    """Garante que exceções não revelam stack traces de Python ou detalhes internos."""
    # Rota que não existe
    res_404 = client.get("/api/v1/rota_inexistente_12345")
    assert res_404.status_code == 404
    assert "traceback" not in res_404.text.lower()
    assert "/home/" not in res_404.text

    # Erro de método não permitido
    res_405 = client.delete("/api/v1/auth/login")
    assert res_405.status_code == 405
    assert "traceback" not in res_405.text.lower()

# ==============================================================================
# 10. TESTE ITEM 14 - Tokens JWT Inseguros (alg: none, assinatura inválida, expiração)
# ==============================================================================
def test_item_14_jwt_security_verification():
    """Testa rejeição de tokens forjados com 'alg: none', assinatura inválida ou expirados."""
    
    # 1. Ataque de 'alg: none'
    forged_none_token = jwt.encode({"sub": "gestor@ufrn.br", "role": "admin"}, key="", algorithm="none")
    res_none = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged_none_token}"})
    assert res_none.status_code == 401, "Token com alg:none deve ser rejeitado"

    # 2. Token assinado com chave secreta errada
    wrong_key_token = jwt.encode(
        {"sub": "gestor@ufrn.br", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, 
        key="chave-falsa-do-atacante-com-pelo-menos-32-bytes!", 
        algorithm="HS256"
    )
    res_wrong = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {wrong_key_token}"})
    assert res_wrong.status_code == 401, "Token com assinatura inválida deve ser rejeitado"

    # 3. Token expirado
    expired_token = jwt.encode(
        {"sub": "gestor@ufrn.br", "exp": datetime.now(timezone.utc) - timedelta(hours=2)},
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    res_exp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_exp.status_code == 401, "Token expirado deve ser rejeitado"

# ==============================================================================
# 11. TESTE ITEM 16 - Nginx bloqueia arquivos ocultos e sensíveis
# ==============================================================================
def test_item_16_nginx_sensitive_files_blocked():
    """Garante que a configuração do Nginx bloqueia arquivos ocultos e sensíveis."""
    nginx_conf_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../frontend/nginx.conf")
    )
    assert os.path.exists(nginx_conf_path), "nginx.conf deve existir"
    with open(nginx_conf_path, "r") as f:
        conf = f.read()
        assert "location ~ /\\." in conf, "Nginx deve bloquear arquivos ocultos (.git, .env)"
        assert "deny all" in conf

# ==============================================================================
# 12. TESTE ITEM 19 - CORS Configurado com Origens Explícitas
# ==============================================================================
def test_item_19_cors_explicit_origins():
    """Verifica que o CORS não utiliza wildcard '*' indiscriminadamente com credenciais."""
    assert "*" not in settings.ALLOWED_ORIGINS, "ALLOWED_ORIGINS não deve ser '*' quando allow_credentials é True"
    assert "http://localhost:5173" in settings.ALLOWED_ORIGINS
    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS

# ==============================================================================
# 13. TESTE ITEM 2 - Ausência de Validação no Frontend / Tipagem
# ==============================================================================
def test_item_02_frontend_validation_and_types_exist():
    """Verifica se o frontend possui tipos e validações TypeScript para os payloads."""
    frontend_types_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../frontend/src/types.ts")
    )
    assert os.path.exists(frontend_types_path)
    with open(frontend_types_path, "r") as f:
        types_content = f.read()
        assert "export interface TelemetryLog" in types_content
        assert "latitude: number;" in types_content
        assert "longitude: number;" in types_content
        assert "speed: number;" in types_content

# ==============================================================================
# 14. TESTE ITEM 10 - CSRF (Cross-Site Request Forgery)
# ==============================================================================
def test_item_10_csrf_protection_bearer_tokens():
    """Garante que a API utiliza cabeçalhos 'Authorization: Bearer' em vez de cookies de sessão vulneráveis."""
    # Requisição simulando ataque CSRF de navegador (sem cabeçalho Authorization)
    res = client.post("/api/v1/vehicles", json={
        "plate": "CSRF-001",
        "model": "Carro",
        "brand": "Ford",
        "year": 2024
    })
    # Como não usa cookie ambiente e sim Bearer Token, o navegador não envia autenticação automaticamente
    assert res.status_code == 401, "Ataque CSRF sem Bearer token deve ser bloqueado com 401"

# ==============================================================================
# 15. TESTE ITEM 11 - Upload de Arquivos sem Validação
# ==============================================================================
def test_item_11_no_unrestricted_file_upload_endpoints():
    """Garante que a aplicação não expõe endpoints arbitrários de upload de arquivos sem validação."""
    paths = []
    for route in app.routes:
        if hasattr(route, "path"):
            paths.append(route.path)
        elif hasattr(route, "routes"):
            for sub in route.routes:
                if hasattr(sub, "path"):
                    paths.append(sub.path)
    for p in paths:
        assert "upload" not in p.lower(), f"Rota de upload encontrada sem sandboxing: {p}"

# ==============================================================================
# 16. TESTE ITEM 17 - SSRF (Server-Side Request Forgery)
# ==============================================================================
def test_item_17_ssrf_protection_no_arbitrary_url_fetching():
    """Audita os schemas para garantir que nenhuma URL externa fornecida por usuário é consumida pelo servidor."""
    from app.schemas import TelemetryItemCreate, VehicleCreate, UserCreate
    for schema_cls in [TelemetryItemCreate, VehicleCreate, UserCreate]:
        fields = schema_cls.model_fields.keys()
        for field in fields:
            assert "url" not in field.lower() or field == "token_url", \
                f"Campo de URL suspeito de SSRF detectado no schema {schema_cls.__name__}: {field}"

# ==============================================================================
# 17. TESTE ITEM 18 - Cookies Inseguros
# ==============================================================================
def test_item_18_no_insecure_cookies_set():
    """Verifica que as respostas do sistema não emitem cookies sem flags HttpOnly, Secure ou SameSite."""
    res = client.post("/api/v1/auth/login-json", json={
        "email": "gestor@ufrn.br",
        "password": "senha123"
    })
    # O sistema usa Bearer Tokens (JWT no body da resposta), logo não deve setar cookies inseguros
    assert "set-cookie" not in res.headers or "httponly" in res.headers["set-cookie"].lower()

