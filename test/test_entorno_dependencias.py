"""Guardas de reproducibilidad del entorno de tests.

Un clon limpio debe poder instalar `requirements-dev.txt`, recolectar la suite y
aplicar migraciones sin dependencias implícitas del entorno global.
"""

import tomllib
from importlib import metadata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _leer(nombre: str) -> str:
    return (RAIZ / nombre).read_text(encoding="utf-8").lower()


def test_requirements_declara_alembic() -> None:
    assert "alembic" in _leer("requirements.txt")


def test_requirements_dev_incluye_dependencias_de_runtime() -> None:
    assert "-r requirements.txt" in _leer("requirements-dev.txt")


def test_requirements_dev_declara_pytest_asyncio() -> None:
    assert "pytest-asyncio" in _leer("requirements-dev.txt")


def test_pyproject_configura_asyncio_auto() -> None:
    config = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))

    assert config["tool"]["pytest"]["ini_options"]["asyncio_mode"] == "auto"


def _pins_de_requirements() -> dict[str, str]:
    """Extrae `paquete==version` de requirements.txt (ignora extras y comentarios)."""
    pins: dict[str, str] = {}
    for linea in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "==" not in linea:
            continue
        nombre, version = linea.split("==", 1)
        pins[nombre.split("[", 1)[0].strip().lower()] = version.strip()
    return pins


def test_requirements_pins_coinciden_con_el_entorno_probado() -> None:
    """Un pin que no coincide con lo instalado hace la suite no reproducible."""
    for nombre, esperada in _pins_de_requirements().items():
        assert metadata.version(nombre) == esperada, (
            f"{nombre}: requirements.txt pide {esperada}, instalado {metadata.version(nombre)}"
        )
