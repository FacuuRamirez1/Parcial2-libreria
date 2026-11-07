"""Primitivas de seguridad.

C-08 deja solo el hash ficticio del login, calculado una única vez en el
`lifespan` y fuera del bucle de eventos. C-11 amplía este módulo con el hash y
la verificación de contraseñas, el semáforo de bcrypt y los tokens JWT.
"""

import asyncio

import bcrypt

PASSWORD_FICTICIA = b"ficticio-no-usada-para-login"


async def calcular_hash_ficticio(costo: int) -> bytes:
    """Calcula un hash bcrypt ficticio fuera del bucle de eventos.

    Se usa cuando el correo del login no existe para que el tiempo de respuesta
    no delate si la cuenta existe (RN-08). El costo sale de `BCRYPT_COST`.
    """
    return await asyncio.to_thread(
        bcrypt.hashpw, PASSWORD_FICTICIA, bcrypt.gensalt(rounds=costo)
    )
