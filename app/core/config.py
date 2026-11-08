"""Configuración de la aplicación con pydantic-settings.

Lee las variables de entorno (el entorno del proceso prevalece sobre el .env).
JWT_SECRET_KEY y POSTGRES_PASSWORD no tienen valor por defecto: si faltan, la
aplicación no arranca. La URL de la base se arma con @computed_field usando el
driver postgresql+asyncpg.
"""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Conexión a la base de datos (POSTGRES_PASSWORD sin valor por defecto).
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = Field(default=5432)

    # Seguridad y token.
    JWT_SECRET_KEY: str  # sin valor por defecto
    BCRYPT_COST: int = Field(default=12)
    DB_POOL_SIZE: int = Field(default=5)
    COOKIE_SECURE: bool = Field(default=False)
    ACCESS_TOKEN_MINUTES: int = Field(default=30)
    BCRYPT_CONCURRENCIA: int = Field(default=4)  # cálculos bcrypt simultáneos (semáforo)
    JWT_ALGORITMO: str = Field(default="HS256")

    # SQL en consola.
    SQL_ECHO: bool = Field(default=False)

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """Dirección de conexión con el driver asincrónico postgresql+asyncpg.

        La contraseña se codifica para que caracteres como @, : o / no rompan la URL.
        """
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)
