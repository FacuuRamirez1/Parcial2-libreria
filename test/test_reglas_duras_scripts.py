"""Guardas de reglas duras sobre scripts auxiliares.

`AGENTS.md` prohíbe `create_all` y credenciales/URLs hardcodeadas en el repo.
Los scripts de apoyo deben delegar el esquema a Alembic y leer la URL del entorno.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "scripts"


def test_scripts_no_usan_create_all() -> None:
    infracciones = [
        str(script.relative_to(RAIZ))
        for script in SCRIPTS.glob("*.py")
        if "create_all" in script.read_text(encoding="utf-8")
    ]

    assert infracciones == [], (
        "Los scripts no pueden crear el esquema con create_all; usá Alembic: "
        + ", ".join(infracciones)
    )


def test_scripts_no_hardcodean_urls_de_base() -> None:
    infracciones = [
        str(script.relative_to(RAIZ))
        for script in SCRIPTS.glob("*.py")
        if "postgresql+asyncpg://" in script.read_text(encoding="utf-8")
    ]

    assert infracciones == [], (
        "Los scripts deben leer DATABASE_URL del entorno, no hardcodearla: "
        + ", ".join(infracciones)
    )
