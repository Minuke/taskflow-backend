"""Limitación de peticiones (rate limiting) en memoria, con ventana deslizante."""

import math
import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import settings

SWEEP_EVERY = 1000  # cada cuántas comprobaciones se limpian las claves antiguas


class SlidingWindowRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._checks = 0

    def check(self, key: str) -> int | None:
        """Registra un intento. Devuelve None si se permite, o los segundos de espera si no."""
        now = time.monotonic()
        with self._lock:
            self._checks += 1
            if self._checks % SWEEP_EVERY == 0:
                self._sweep(now)

            hits = self._hits[key]
            while hits and hits[0] <= now - self.window_seconds:
                hits.popleft()

            if len(hits) >= self.max_attempts:
                return max(1, math.ceil(hits[0] + self.window_seconds - now))

            hits.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._checks = 0

    def _sweep(self, now: float) -> None:
        # Evita que crezca la memoria con IPs que ya no vuelven.
        expired = [
            key
            for key, hits in self._hits.items()
            if not hits or hits[-1] <= now - self.window_seconds
        ]
        for key in expired:
            del self._hits[key]


def _too_many_attempts_message(seconds: int) -> str:
    unit = "segundo" if seconds == 1 else "segundos"
    return f"Demasiados intentos. Inténtalo de nuevo en {seconds} {unit}."


def create_rate_limit_dependency(
    limiter: SlidingWindowRateLimiter, scope: str, is_enabled: Callable[[], bool]
) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        if not is_enabled():
            return

        client_ip = request.client.host if request.client else "unknown"
        retry_after = limiter.check(f"{scope}:{client_ip}")
        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=_too_many_attempts_message(retry_after),
                headers={"Retry-After": str(retry_after)},
            )

    return dependency


def _rate_limit_enabled() -> bool:
    return settings.rate_limit_enabled


login_limiter = SlidingWindowRateLimiter(
    settings.rate_limit_attempts, settings.rate_limit_window_seconds
)
register_limiter = SlidingWindowRateLimiter(
    settings.rate_limit_attempts, settings.rate_limit_window_seconds
)

limit_login = create_rate_limit_dependency(login_limiter, "login", _rate_limit_enabled)
limit_register = create_rate_limit_dependency(register_limiter, "register", _rate_limit_enabled)
