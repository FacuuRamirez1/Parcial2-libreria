"""Primitivas de seguridad.

C-08 deja solo el hash ficticio del login, calculado una única vez en el
`lifespan` y fuera del bucle de eventos. C-11 amplía este módulo con el hash y
la verificación de contraseñas (bcrypt bajo semáforo) y la emisión y
decodificación de tokens JWT.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import Settings

PASSWORD_FICTICIA = b"ficticio-no-usada-para-login"


async def hashear_password(password: str, costo: int, semaforo: asyncio.Semaphore) -> str:
    """Calcula el hash bcrypt de `password` fuera del bucle y bajo el semáforo.

    Se llama ANTES de abrir la transacción que guarda el hash: no debe haber una
    conexión tomada mientras bcrypt calcula. El contrato de entrada ya limitó la
    contraseña a 72 bytes. Devuelve el hash como `str` (se guarda en `password_hash`).
    """
    async with semaforo:
        hash_bytes = await asyncio.to_thread(
            bcrypt.hashpw, password.encode("utf-8"), bcrypt.gensalt(rounds=costo)
        )
    return hash_bytes.decode("ascii")


async def verificar_password(
    password: str, hash_guardado: str | bytes, semaforo: asyncio.Semaphore
) -> bool:
    """Verifica `password` contra un hash bcrypt (`str` o `bytes`) fuera del bucle y bajo el semáforo."""
    hash_bytes = hash_guardado.encode("ascii") if isinstance(hash_guardado, str) else hash_guardado
    async with semaforo:
        return await asyncio.to_thread(bcrypt.checkpw, password.encode("utf-8"), hash_bytes)


async def calcular_hash_ficticio(costo: int) -> bytes:
    """Calcula un hash bcrypt ficticio fuera del bucle de eventos.

    Se usa cuando el correo del login no existe para que el tiempo de respuesta
    no delate si la cuenta existe (RN-08). El costo sale de `BCRYPT_COST`.
    """
    return await asyncio.to_thread(
        bcrypt.hashpw, PASSWORD_FICTICIA, bcrypt.gensalt(rounds=costo)
    )


def crear_token(usuario_id: int, roles: list[str], settings: Settings) -> tuple[str, int]:
    """Emite el JWT de acceso. Devuelve `(token, segundos de vida)`.

    `sub` es string (PyJWT lo exige); los `roles` del token son informativos: los
    permisos se deciden con los roles vigentes en la base (D-10).
    """
    segundos = settings.ACCESS_TOKEN_MINUTES * 60
    ahora = datetime.now(timezone.utc)
    carga = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(seconds=segundos),
        "roles": sorted(roles),
    }
    token = jwt.encode(carga, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITMO)
    return token, segundos


def decodificar_token(token: str, settings: Settings) -> dict:
    """Valida firma, vencimiento y claims obligatorios; devuelve la carga.

    Lanza `jwt.InvalidTokenError` (o una subclase) si algo falla. La lista de
    algoritmos es fija: nunca se acepta el `alg` que trae el token.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITMO],
        options={"require": ["sub", "exp", "iat"]},
    )
