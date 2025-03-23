# Etapa de construcción
FROM python:3.11-slim as builder

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libpq-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar dependencias
RUN poetry install --no-dev --no-root

# Etapa final
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    APP_HOME="/app" \
    APP_USER="appuser"

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root
RUN groupadd -r $APP_USER && useradd -r -g $APP_USER $APP_USER \
    && mkdir -p $APP_HOME \
    && chown -R $APP_USER:$APP_USER $APP_HOME

# Copiar dependencias instaladas desde la etapa de builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Establecer el directorio de trabajo
WORKDIR $APP_HOME

# Copiar el código de la aplicación
COPY --chown=$APP_USER:$APP_USER . .

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/secrets /app/backups \
    && chown -R $APP_USER:$APP_USER /app/logs /app/secrets /app/backups

# Cambiar al usuario no root
USER $APP_USER

# Exponer el puerto
EXPOSE 8000

# Usar tini como entrypoint
ENTRYPOINT ["/usr/bin/tini", "--"]

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 