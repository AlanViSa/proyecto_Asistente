"""
Configuración del sistema de monitoreo y métricas.

Este módulo configura:
- Métricas de Prometheus
- Instrumentación de OpenTelemetry
- Logging estructurado
"""
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.prometheus import PrometheusExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentation
from structlog import get_logger
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
import time

# Configuración de métricas de Prometheus
# Contadores
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total de solicitudes HTTP',
    ['method', 'endpoint', 'status']
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total de errores HTTP',
    ['method', 'endpoint', 'error_type']
)

# Histogramas
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'Duración de las solicitudes HTTP',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Gauges
ACTIVE_USERS = Gauge(
    'active_users',
    'Número de usuarios activos'
)

DB_CONNECTIONS = Gauge(
    'db_connections',
    'Número de conexiones activas a la base de datos'
)

# Métricas de negocio
APPOINTMENTS_COUNT = Counter(
    "appointments_total",
    "Total de citas",
    ["status"]
)

SERVICES_COUNT = Gauge(
    "services_total",
    "Total de servicios activos"
)

CLIENTS_COUNT = Gauge(
    "clients_total",
    "Total de clientes registrados"
)

# Configuración de OpenTelemetry
def setup_tracing(app):
    """Configura el sistema de trazabilidad con OpenTelemetry."""
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)
    
    # Configurar el exportador de Prometheus
    prometheus_exporter = PrometheusExporter()
    span_processor = BatchSpanProcessor(prometheus_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Instrumentar FastAPI
    FastAPIInstrumentation.instrument(app, tracer_provider=tracer_provider)

# Configuración de logging estructurado
logger = get_logger()

def setup_logging():
    """Configura el sistema de logging estructurado."""
    # La configuración se realiza a través de structlog
    # Los logs se enviarán a stdout en formato JSON
    pass

def get_logger(name: Optional[str] = None):
    """Obtiene un logger estructurado con el nombre especificado."""
    return get_logger(name or __name__)

def setup_monitoring(app: FastAPI):
    """
    Configura el monitoreo de la aplicación
    """
    try:
        Instrumentator().instrument(app).expose(app)
        logger.info("Monitoreo Prometheus configurado correctamente")
    except Exception as e:
        logger.error(f"Error al configurar monitoreo: {e}")
        raise

    @app.middleware("http")
    async def monitor_requests(request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Registrar métricas
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)
            
            return response
        except Exception as e:
            ERROR_COUNT.labels(type="http").inc()
            logger.error(f"Error en request: {e}")
            raise

    @app.on_event("startup")
    async def startup_event():
        """
        Evento de inicio de la aplicación
        """
        try:
            ACTIVE_USERS.set(0)
            DB_CONNECTIONS.set(0)
            ERROR_COUNT.labels(type="app").inc(0)
            ERROR_COUNT.labels(type="db").inc(0)
            logger.info("Métricas inicializadas correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar métricas: {e}")
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Evento de cierre de la aplicación
        """
        try:
            ACTIVE_USERS.set(0)
            DB_CONNECTIONS.set(0)
            logger.info("Métricas limpiadas correctamente")
        except Exception as e:
            logger.error(f"Error al limpiar métricas: {e}")
            raise 