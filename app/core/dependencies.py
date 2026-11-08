"""Dependencias compartidas de autenticación (usuario actual).

C-11 trae solo la parte 401; C-12 suma aquí `requiere_rol` y el control del cambio
obligatorio de contraseña sin tocar `get_usuario_actual`.
"""

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.core.database import SessionDep
from app.core.security import decodificar_token
from app.modules.usuarios.models import Usuario

COOKIE_TOKEN = "access_token"
_SIN_SESION = "No hay una sesión válida"


@dataclass(frozen=True)
class UsuarioActual:
    """Usuario autenticado y los roles que traía el token (solo informativos)."""

    usuario: Usuario
    roles_token: list[str]


def _sin_sesion() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_SIN_SESION)


async def get_usuario_actual(request: Request, session: SessionDep) -> UsuarioActual:
    """Identifica al usuario por la cookie `access_token`; cualquier falla es 401.

    - El token se lee SOLO de la cookie (nunca de `Authorization`).
    - `session` es la misma `SessionDep` que usa el Unit of Work de la ruta: FastAPI
      cachea la dependencia por petición, así que hay una sola conexión.
    - Los roles del token no deciden permisos; se devuelven como informativos.
    """
    token = request.cookies.get(COOKIE_TOKEN)
    if not token:
        raise _sin_sesion()
    try:
        carga = decodificar_token(token, request.app.state.settings)
        usuario_id = int(carga["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise _sin_sesion() from None

    usuario = await session.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise _sin_sesion()

    roles = carga.get("roles")
    return UsuarioActual(usuario=usuario, roles_token=list(roles) if isinstance(roles, list) else [])


UsuarioActualDep = Annotated[UsuarioActual, Depends(get_usuario_actual)]
