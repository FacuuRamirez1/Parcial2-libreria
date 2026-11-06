"""Guardas de reproducibilidad del entorno de tests.

Un clon limpio debe poder instalar `requirements-dev.txt`, recolectar la suite y
aplicar migraciones sin dependencias implícitas del entorno global.
"""

import tomllib
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
