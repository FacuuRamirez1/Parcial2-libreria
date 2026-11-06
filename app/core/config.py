"""Configuración de la aplicación leída del entorno (y de un .env local no versionado)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent.parent
PREFIJO_DRIVER = "postgresql+asyncpg://"
VALORES_VERDADEROS = {"true", "1", "yes", "on"}


class ErrorDeConfiguracion(RuntimeError):
    """Configuración inválida. El mensaje nombra la variable, nunca su valor."""


@dataclass(frozen=True)
class Configuracion:
    database_url: str
    sql_echo: bool


def leer_configuracion(entorno: Mapping[str, str]) -> Configuracion:
    """Valida y construye la configuración a partir de un mapeo (función pura)."""
    url = entorno.get("DATABASE_URL", "").strip()
    if not url:
        raise ErrorDeConfiguracion(
            "Falta la variable DATABASE_URL (defínela en el entorno o en el archivo .env)."
        )
    if not url.startswith(PREFIJO_DRIVER):
        raise ErrorDeConfiguracion(
            "DATABASE_URL debe usar el driver asincrónico postgresql+asyncpg."
        )
    sql_echo = entorno.get("SQL_ECHO", "").strip().lower() in VALORES_VERDADEROS
    return Configuracion(database_url=url, sql_echo=sql_echo)


def get_settings() -> Configuracion:
    """Carga el .env de la raíz (el entorno del proceso prevalece) y valida."""
    load_dotenv(RAIZ / ".env", override=False)
    return leer_configuracion(os.environ)
