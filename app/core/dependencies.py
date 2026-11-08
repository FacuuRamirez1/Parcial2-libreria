"""Dependencias compartidas de autenticación y autorización.

- `get_usuario_actual` (C-11): identifica al usuario por la cookie; toda falla es 401.
- `requiere_rol(*roles)` (C-12): permiso por los roles VIGENTES leídos de la base en cada
  petición (nunca los del token); sin rol permitido es 403. Corre después de la 401.
- `exigir_password_al_dia` (C-12): 403 mientras `debe_cambiar_password`; se monta UNA sola vez
  sobre el grupo protegido en `app/main.py` (las rutas `/auth/*` quedan en el grupo abierto).

Todas comparten la misma `SessionDep` que el Unit of Work de la ruta (una conexión por petición).
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.core.database import SessionDep
from app.core.security import decodificar_token
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import AsignacionRolRepository

COOKIE_TOKEN = "access_token"
_SIN_SESION = "No hay una sesión válida"
_SIN_PERMISO = "No tenés permiso para esta operación"
_CAMBIO_PENDIENTE = "Tenés que cambiar la contraseña antes de seguir"

ADMIN = "ADMIN"
VENDEDOR = "VENDEDOR"
CLIENTE = "CLIENTE"
ROLES_VALIDOS = frozenset({ADMIN, VENDEDOR, CLIENTE})
PERSONAL = (VENDEDOR, ADMIN)


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


def requiere_rol(*roles: str) -> Callable[..., Awaitable[UsuarioActual]]:
    """Fábrica de dependencia: deja pasar solo si el usuario tiene algún rol de `roles` VIGENTE.

    - Los roles se consultan en la base en cada petición (`roles_vigentes`: sin `revocada_en` y
      sin vencer); los del token no deciden nada.
    - Depende de `UsuarioActualDep` (401 si no hay sesión) y de `SessionDep`: FastAPI cachea
      ambas por petición, así que es la misma sesión/conexión que usa el Unit of Work.
    - Devuelve el `UsuarioActual` para que la ruta que necesite al actor lo reciba sin otra consulta.
    - Un rol desconocido es un error de programación: falla al construir (al importar), no en runtime.
    """
    desconocidos = set(roles) - ROLES_VALIDOS
    if not roles or desconocidos:
        raise ValueError(f"Roles inválidos para requiere_rol: {sorted(desconocidos) or 'ninguno indicado'}")
    permitidos = frozenset(roles)

    async def _requiere_rol(actual: UsuarioActualDep, session: SessionDep) -> UsuarioActual:
        vigentes = await AsignacionRolRepository(session).roles_vigentes(actual.usuario.id, datetime.now(UTC))
        if permitidos.isdisjoint(vigentes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_PERMISO)
        return actual

    return _requiere_rol


async def exigir_password_al_dia(actual: UsuarioActualDep) -> UsuarioActual:
    """403 mientras el usuario deba cambiar su contraseña (RN-06).

    `debe_cambiar_password` sale del `Usuario` que `get_usuario_actual` acaba de leer de la base
    en ESTA petición: tras `POST /auth/cambiar-password` la misma cookie ya pasa. Se declara una
    sola vez, sobre el grupo protegido de `app/main.py`.
    """
    if actual.usuario.debe_cambiar_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_CAMBIO_PENDIENTE)
    return actual
