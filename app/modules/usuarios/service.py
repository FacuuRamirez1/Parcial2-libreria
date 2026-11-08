"""Servicio del módulo usuarios: registro, login (y más adelante sesión y cambio de contraseña).

El servicio recibe el Unit of Work SIN abrir y lo abre con `async with`. El hash de
bcrypt se calcula SIEMPRE fuera de la transacción.
"""

import asyncio
import math
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.dependencies import UsuarioActual
from app.core.security import crear_token, hashear_password, verificar_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.usuarios.repository import RegistroIntentosPropio
from app.modules.usuarios.schemas import (
    CambioPasswordIn,
    LoginIn,
    LoginOut,
    MensajeOut,
    RegistroIn,
    RegistroOut,
    YoOut,
)
from app.modules.usuarios.unit_of_work import UsuariosUnitOfWork

UNIQUE_VIOLATION = "23505"
MAX_FALLOS = 5
VENTANA_SEGUNDOS = 60
MSG_LOGIN_INVALIDO = "Correo o contraseña incorrectos"
MSG_SIN_SESION = "No hay una sesión válida"
MSG_PASSWORD_ACTUAL = "La contraseña actual no es correcta"
MSG_DEMASIADOS_INTENTOS = "Demasiados intentos fallidos; probá de nuevo más tarde"


def _es_unicidad(exc: IntegrityError) -> bool:
    codigo = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    return codigo == UNIQUE_VIOLATION


async def registrar(
    uow: UsuariosUnitOfWork,
    datos: RegistroIn,
    semaforo: asyncio.Semaphore,
    costo: int,
) -> RegistroOut:
    """Crea usuario + rol CLIENTE + ficha de cliente en UN solo bloque (RN-02).

    Sin pre-consulta del correo: la unicidad la garantiza la base (uq_usuario_email y
    uq_cliente_email) y el 23505 se traduce a 409 con un mensaje propio.
    """
    password_hash = await hashear_password(datos.password, costo, semaforo)  # antes de la transacción
    try:
        async with uow:
            usuario = Usuario(email=datos.email, nombre=datos.nombre, password_hash=password_hash)
            await uow.usuarios.add(usuario)
            await uow.asignaciones.add(AsignacionRol(usuario_id=usuario.id, rol="CLIENTE"))
            cliente = Cliente(nombre=datos.nombre, email=datos.email, usuario_id=usuario.id)
            await uow.clientes.add(cliente)
    except IntegrityError as exc:  # el UoW ya revirtió las tres escrituras
        if _es_unicidad(exc):
            raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado") from exc
        raise
    return RegistroOut(
        id=usuario.id, email=usuario.email, nombre=usuario.nombre, cliente_id=cliente.id
    )


async def login(
    uow: UsuariosUnitOfWork,
    registro_intentos: RegistroIntentosPropio,
    datos: LoginIn,
    ip: str,
    settings: Settings,
    semaforo: asyncio.Semaphore,
    hash_ficticio: bytes,
) -> tuple[LoginOut, str]:
    """Login en el orden de D-06. Devuelve `(cuerpo, token)`; el router pone el token en la cookie.

    1. Bloque de lectura: límite de intentos (429 sin bcrypt) y usuario + roles vigentes.
       Al salir del bloque la conexión vuelve al pool, ANTES de calcular bcrypt.
    2. Fuera de transacción: verificación contra el hash del usuario o el ficticio
       (mismo mensaje y tiempo parecido exista o no el correo).
    3. Se anota el intento en su propia transacción y recién entonces se responde.
    """
    ahora = datetime.now(UTC)
    async with uow:
        cantidad, mas_antiguo = await uow.intentos.contar_fallos_recientes(
            datos.email, ip, ahora - timedelta(seconds=VENTANA_SEGUNDOS)
        )
        if cantidad >= MAX_FALLOS:
            espera = VENTANA_SEGUNDOS - (ahora - mas_antiguo).total_seconds()
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                MSG_DEMASIADOS_INTENTOS,
                headers={"Retry-After": str(max(1, math.ceil(espera)))},
            )
        usuario = await uow.usuarios.get_by_email(datos.email)
        roles: list[str] = []
        if usuario is not None:
            roles = await uow.asignaciones.roles_vigentes(usuario.id, ahora)

    hash_a_verificar = usuario.password_hash if usuario is not None else hash_ficticio
    coincide = await verificar_password(datos.password, hash_a_verificar, semaforo)
    exito = usuario is not None and usuario.activo and coincide

    await registro_intentos.anotar(datos.email, ip, exito)

    if not exito:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, MSG_LOGIN_INVALIDO)
    token, segundos = crear_token(usuario.id, roles, settings)
    cuerpo = LoginOut(
        mensaje="Sesión iniciada",
        debe_cambiar_password=usuario.debe_cambiar_password,
        expira_en_segundos=segundos,
    )
    return cuerpo, token


async def obtener_yo(uow: UsuariosUnitOfWork, actual: UsuarioActual) -> YoOut:
    """Datos del usuario autenticado. Los roles vigentes se leen de la base en esta
    petición (D-10); los del token se devuelven solo como informativos."""
    usuario = actual.usuario
    async with uow:
        roles = await uow.asignaciones.roles_vigentes(usuario.id, datetime.now(UTC))
    return YoOut(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        debe_cambiar_password=usuario.debe_cambiar_password,
        roles_vigentes=roles,
        roles_token=actual.roles_token,
    )


async def cambiar_password(
    uow: UsuariosUnitOfWork,
    actual: UsuarioActual,
    datos: CambioPasswordIn,
    settings: Settings,
    semaforo: asyncio.Semaphore,
) -> MensajeOut:
    """Cambia la contraseña del usuario autenticado en el orden de D-11.

    1. Bloque de relectura: cierra la transacción implícita que abrió `get_usuario_actual`
       y devuelve la conexión al pool ANTES de bcrypt.
    2. Fuera de transacción: se verifica la actual (422 si no coincide) y se calcula el hash nuevo.
    3. UN solo bloque: nuevo hash + `debe_cambiar_password = false` + evento de seguridad (RN-16).
    No se emite token nuevo ni se invalidan las sesiones abiertas (DD-11).
    """
    async with uow:
        usuario = await uow.usuarios.get_by_id(actual.usuario.id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, MSG_SIN_SESION)

    if not await verificar_password(datos.password_actual, usuario.password_hash, semaforo):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, MSG_PASSWORD_ACTUAL)
    nuevo_hash = await hashear_password(datos.password_nueva, settings.BCRYPT_COST, semaforo)

    async with uow:
        usuario.password_hash = nuevo_hash
        usuario.debe_cambiar_password = False
        await uow.usuarios.update(usuario)
        await uow.eventos.add(EventoSeguridad(actor=usuario.email, accion="Cambio de contraseña"))
    return MensajeOut(mensaje="Contraseña actualizada")
