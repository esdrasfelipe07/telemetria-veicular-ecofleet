import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status

class InMemoryRateLimiter:
    """
    Limitador de taxa (Rate Limiter) em memória baseado em janela deslizante.
    Protege endpoints críticos contra ataques de Força Bruta e DoS.
    """
    def __init__(self, requests_limit: int, time_window_seconds: int):
        self.requests_limit = requests_limit
        self.time_window_seconds = time_window_seconds
        self.client_records: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, request: Request, identifier: str = None) -> bool:
        client_ip = identifier or (request.client.host if request.client else "unknown")
        current_time = time.time()
        
        # Filtra timestamps dentro da janela atual
        window_start = current_time - self.time_window_seconds
        valid_requests = [
            ts for ts in self.client_records[client_ip] 
            if ts > window_start
        ]
        
        if len(valid_requests) >= self.requests_limit:
            retry_after = int(self.time_window_seconds - (current_time - valid_requests[0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de requisições excedido. Tente novamente em {max(1, retry_after)} segundos.",
                headers={"Retry-After": str(max(1, retry_after))}
            )
            
        valid_requests.append(current_time)
        self.client_records[client_ip] = valid_requests
        return True

    def reset(self):
        """Limpa registros em memória (útil para testes automatizados)."""
        self.client_records.clear()

# Limitador restrito para autenticação (ex: máx 5 tentativas de login por minuto por IP)
auth_rate_limiter = InMemoryRateLimiter(requests_limit=5, time_window_seconds=60)

# Limitador geral para APIs normais (ex: máx 120 requisições por minuto por IP)
api_rate_limiter = InMemoryRateLimiter(requests_limit=120, time_window_seconds=60)
