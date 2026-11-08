FROM python:3.12-alpine

WORKDIR /app

# Capa de dependencias ANTES del código: caché de Docker y rebuilds rápidos.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación: snapshot del TP caps 1-4 (commit f1b9b48).
COPY . .

# Usuario sin privilegios (el contenedor NO corre como root).
RUN adduser -D -u 1000 libreria
RUN chown -R libreria:libreria /app
USER libreria

# Variables de entorno se proveen en tiempo de ejecución con --env-file;
# nunca hay secretos en la imagen ni en capas intermedias.
ENV PYTHONDONTWRITEBYTECODE=1

# Healthcheck sobre 127.0.0.1 (Alpine trae wget; "localhost" resuelve a ::1).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1:8000/health/ready || exit 1

# Arranque: migraciones (Alembic) y, solo si éxito, uvicorn en 0.0.0.0:8000.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
