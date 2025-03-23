"""
Módulo de modelos de la aplicación.
"""

from typing import List, Optional

from app.models.cliente import Cliente
from app.models.cita import Cita, EstadoCita

# Exportar los modelos
__all__ = [
    "Cliente",
    "Cita",
    "EstadoCita"
] 