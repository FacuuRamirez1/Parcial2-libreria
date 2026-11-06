"""Guarda contra drift entre los modelos SQLModel y las migraciones Alembic."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def test_alembic_check_sin_drift(preparar_base: None) -> None:
    """`alembic check` debe salir 0: el esquema migrado refleja los modelos."""
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        pytest.skip("Definí TEST_DATABASE_URL o DATABASE_URL para verificar el drift.")

    entorno = {**os.environ, "DATABASE_URL": url}
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "check"],
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert resultado.returncode == 0, (
        "Hay drift entre modelos y migraciones.\n"
        f"stdout:\n{resultado.stdout}\nstderr:\n{resultado.stderr}"
    )
