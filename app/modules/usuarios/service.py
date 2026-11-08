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
from app.core.paginacion import PaginatedResponse, Paginacion, calcular_paginas, verificar_pagina
from app.core.security import crear_token, hashear_password, verificar_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.usuarios.repository import RegistroIntentosPropio
from app.modules.usuarios.schemas import (
    AsignacionRolIn,
    AsignacionRolOut,
    CambioPasswordIn,
    EventoOut,
    LoginIn,
    LoginOut,
    MensajeOut,
    PersonalIn,
    PersonalOut,
    RegistroIn,
    RegistroOut,
    YoOut,
)
from app.modules.usuarios.unit_of_work import UsuariosUnitOfWork

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
MAX_FALLOS = 5
VENTANA_SEGUNDOS = 60
MSG_LOGIN_INVALIDO = "Correo o contraseña incorrectos"
MSG_SIN_SESION = "No hay una sesión válida"
MSG_PASSWORD_ACTUAL = "La contraseña actual no es correcta"
MSG_USUARIO_NO_ENCONTRADO = "Usuario no encontrado"
MSG_ROL_VIGENTE = "El usuario ya tiene ese rol vigente"
MSG_ROL_NO_ASIGNADO = "El usuario no tiene ese rol asignado"
MSG_AUTOREVOCACION_ADMIN = "Un administrador no puede revocarse su propio rol ADMIN"
MSG_SIN_ADMINISTRADORES = "El sistema no puede quedarse sin administradores"
MSG_DEMASIADOS_INTENTOS = "Demasiados intentos fallidos; probá de nuevo más tarde"


def _es_unicidad(exc: IntegrityError) -> bool:
    codigo = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    return codigo == UNIQUE_VIOLATION


def _es_fk(exc: IntegrityError) -> bool:
    codigo = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    return codigo == FOREIGN_KEY_VIOLATION


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


async def alta_personal(
    uow: UsuariosUnitOfWork,
    actor: UsuarioActual,
    datos: PersonalIn,
    settings: Settings,
    semaforo: asyncio.Semaphore,
) -> PersonalOut:
    """Alta de un miembro del personal por un administrador, en el orden de D-05.

    1. Bloque vacío: cierra la transacción implícita que abrieron `get_usuario_actual` y
       `requiere_rol` y devuelve la conexión al pool ANTES de bcrypt (sin esto quedaría tomada
       ~300 ms sin usar la base). Con `expire_on_commit=False` el correo del actor sigue disponible.
    2. Fuera de transacción: hash de la contraseña provisoria.
    3. UN solo bloque: usuario (debe cambiar la contraseña) + asignación abierta + evento (RN-16).
       Si cualquiera falla se revierten las tres. El correo repetido lo rechaza UNIQUE (23505 → 409),
       sin pre-consulta; la ficha de `cliente` no se toca (el personal no es cliente).
    """
    async with uow:
        pass
    password_hash = await hashear_password(datos.password, settings.BCRYPT_COST, semaforo)
    try:
        async with uow:
            usuario = Usuario(
                email=datos.email,
                nombre=datos.nombre,
                password_hash=password_hash,
                debe_cambiar_password=True,
            )
            await uow.usuarios.add(usuario)
            await uow.asignaciones.add(
                AsignacionRol(usuario_id=usuario.id, rol=datos.rol, otorgada_por=actor.usuario.id)
            )
            await uow.eventos.add(
                EventoSeguridad(
                    actor=actor.usuario.email,
                    accion=f"Alta de personal {datos.email} con rol {datos.rol}",
                )
            )
    except IntegrityError as exc:  # el UoW ya revirtió las tres escrituras
        if _es_unicidad(exc):
            raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado") from exc
        raise
    return PersonalOut(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        debe_cambiar_password=True,
        roles_vigentes=[datos.rol],
    )


async def listar_roles(uow: UsuariosUnitOfWork, usuario_id: int) -> list[AsignacionRolOut]:
    """Historial completo de roles del usuario (S-09), 404 si no existe (D-08)."""
    ahora = datetime.now(UTC)
    async with uow:
        if await uow.usuarios.get_by_id(usuario_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_USUARIO_NO_ENCONTRADO)
        asignaciones = await uow.asignaciones.listar_de_usuario(usuario_id)
    return [AsignacionRolOut.desde_modelo(a, ahora) for a in asignaciones]


async def asignar_rol(
    uow: UsuariosUnitOfWork,
    actor: UsuarioActual,
    usuario_id: int,
    datos: AsignacionRolIn,
) -> AsignacionRolOut:
    """Asigna un rol (opcionalmente con vencimiento) en UN solo bloque (D-06).

    EXCEPCION declarada a la regla "no pre-consultar unicidad" (CLAUDE.md, RN-03/RN-05): se lee la
    asignación abierta del rol porque hace falta distinguir "vigente -> 409" de "vencida -> cerrarla
    y abrir otra". El índice único parcial ix_asignacion_rol_abierta sigue siendo el garante: si dos
    asignaciones se cruzan, el 23505 también responde 409. El usuario NO se consulta antes: la clave
    foránea lo rechaza (23503 -> 404).

    Cerrar la vencida = escribir su `revocada_en` (S-08); la fila no se borra. El evento de seguridad
    va en el mismo bloque: si algo falla se revierte todo.
    """
    ahora = datetime.now(UTC)
    try:
        async with uow:
            abierta = await uow.asignaciones.get_abierta(usuario_id, datos.rol)
            if abierta is not None:
                if abierta.vence_en is None or abierta.vence_en > ahora:
                    raise HTTPException(status.HTTP_409_CONFLICT, MSG_ROL_VIGENTE)
                abierta.revocada_en = ahora
                await uow.asignaciones.update(abierta)
            nueva = AsignacionRol(
                usuario_id=usuario_id,
                rol=datos.rol,
                vence_en=datos.vence_en,
                otorgada_por=actor.usuario.id,
            )
            await uow.asignaciones.add(nueva)
            accion = f"Asignación de rol {datos.rol} al usuario {usuario_id}"
            if datos.vence_en is not None:
                accion += f" hasta {datos.vence_en.astimezone(UTC).isoformat(timespec='seconds')}"
            await uow.eventos.add(EventoSeguridad(actor=actor.usuario.email, accion=accion))
    except IntegrityError as exc:  # el UoW ya revirtió todo el bloque
        if _es_fk(exc):
            raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_USUARIO_NO_ENCONTRADO) from exc
        if _es_unicidad(exc):
            raise HTTPException(status.HTTP_409_CONFLICT, MSG_ROL_VIGENTE) from exc
        raise
    return AsignacionRolOut.desde_modelo(nueva, ahora)


async def revocar_rol(
    uow: UsuariosUnitOfWork,
    actor: UsuarioActual,
    usuario_id: int,
    rol: str,
) -> AsignacionRolOut:
    """Revoca la asignación abierta de un rol escribiendo `revocada_en` (la fila NO se borra), D-07.

    Orden, todo en UN bloque: (1) autoprotección: nadie se revoca su propio ADMIN (409, antes de leer
    nada); (2) 404 si no hay asignación abierta (cubre al usuario inexistente); (3) si es un ADMIN
    vigente, el sistema no puede quedarse sin administradores activos (409); (4) `revocada_en` +
    evento de seguridad en el mismo bloque: si el evento falla se revierte la revocación.
    Revocar una abierta ya vencida también la cierra (no cambia permisos y deja el historial prolijo).
    El conteo del paso 3 no toma bloqueos: la carrera entre dos revocaciones simultáneas es del cap. 7.
    """
    if rol == "ADMIN" and usuario_id == actor.usuario.id:
        raise HTTPException(status.HTTP_409_CONFLICT, MSG_AUTOREVOCACION_ADMIN)
    ahora = datetime.now(UTC)
    async with uow:
        abierta = await uow.asignaciones.get_abierta(usuario_id, rol)
        if abierta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_ROL_NO_ASIGNADO)
        vigente = abierta.vence_en is None or abierta.vence_en > ahora
        if rol == "ADMIN" and vigente and await uow.asignaciones.contar_admins_vigentes(ahora) <= 1:
            raise HTTPException(status.HTTP_409_CONFLICT, MSG_SIN_ADMINISTRADORES)
        abierta.revocada_en = ahora
        await uow.asignaciones.update(abierta)
        await uow.eventos.add(
            EventoSeguridad(
                actor=actor.usuario.email,
                accion=f"Revocación de rol {rol} al usuario {usuario_id}",
            )
        )
    return AsignacionRolOut.desde_modelo(abierta, ahora)


async def listar_eventos(uow: UsuariosUnitOfWork, pag: Paginacion) -> PaginatedResponse[EventoOut]:
    """Historial de seguridad paginado, del más reciente al más antiguo (D-08).

    Mismo patrón que los listados de C-09: `total` primero, 422 si la página no existe
    (con cero eventos hay una sola página vacía)."""
    async with uow:
        total = await uow.eventos.count()
        verificar_pagina(pag.page, pag.size, total)
        eventos = await uow.eventos.listar_recientes(pag.offset, pag.limit)
        return PaginatedResponse(
            items=[EventoOut.model_validate(e) for e in eventos],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )
