"""Rutas HTTP de /auth."""

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.database import SessionDep
from app.core.dependencies import UsuarioActualDep
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
from app.modules.usuarios.service import cambiar_password, login, obtener_yo, registrar
from app.modules.usuarios.unit_of_work import UsuariosUnitOfWork

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NOMBRE = "access_token"
IP_MAX = 45  # largo de intento_acceso.ip


async def get_usuarios_uow(session: SessionDep) -> UsuariosUnitOfWork:
    """El router construye el UoW (sin abrir) y se lo pasa al servicio."""
    return UsuariosUnitOfWork(session)


@router.post("/registro", response_model=RegistroOut, status_code=status.HTTP_201_CREATED)
async def registro_endpoint(
    datos: RegistroIn,
    request: Request,
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> RegistroOut:
    return await registrar(
        uow,
        datos,
        request.app.state.semaforo_bcrypt,
        request.app.state.settings.BCRYPT_COST,
    )


def get_registro_intentos(request: Request) -> RegistroIntentosPropio:
    """Registro de intentos con sesión propia, tomada de la fábrica de la aplicación."""
    return RegistroIntentosPropio(request.app.state.session_factory)


def _ip_cliente(request: Request) -> str:
    # Dirección de la conexión; X-Forwarded-For es falsificable sin un proxy de confianza (D-12).
    host = request.client.host if request.client else "desconocida"
    return host[:IP_MAX]


@router.post("/login", response_model=LoginOut)
async def login_endpoint(
    datos: LoginIn,
    request: Request,
    response: Response,
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
    registro_intentos: RegistroIntentosPropio = Depends(get_registro_intentos),
) -> LoginOut:
    estado = request.app.state
    cuerpo, token = await login(
        uow,
        registro_intentos,
        datos,
        _ip_cliente(request),
        estado.settings,
        estado.semaforo_bcrypt,
        estado.hash_ficticio,
    )
    response.set_cookie(
        COOKIE_NOMBRE,
        token,
        max_age=cuerpo.expira_en_segundos,
        httponly=True,
        samesite="lax",
        secure=estado.settings.COOKIE_SECURE,
        path="/",
    )
    return cuerpo


@router.get("/yo", response_model=YoOut)
async def yo_endpoint(
    actual: UsuarioActualDep,
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> YoOut:
    return await obtener_yo(uow, actual)


@router.post("/logout", response_model=MensajeOut)
async def logout_endpoint(request: Request, response: Response) -> MensajeOut:
    """Cierra la sesión sin exigirla: borra la cookie con los mismos atributos con que se puso."""
    response.delete_cookie(
        COOKIE_NOMBRE,
        httponly=True,
        samesite="lax",
        secure=request.app.state.settings.COOKIE_SECURE,
        path="/",
    )
    return MensajeOut(mensaje="Sesión cerrada")


@router.post("/cambiar-password", response_model=MensajeOut)
async def cambiar_password_endpoint(
    datos: CambioPasswordIn,
    request: Request,
    actual: UsuarioActualDep,
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> MensajeOut:
    estado = request.app.state
    return await cambiar_password(uow, actual, datos, estado.settings, estado.semaforo_bcrypt)
