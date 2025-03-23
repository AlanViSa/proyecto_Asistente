import pytest
from datetime import datetime, time
from app.services.faq_service import FAQService

@pytest.fixture
def faq_service():
    return FAQService()

def test_horario_inicializacion(faq_service):
    """Prueba la inicialización correcta de los horarios"""
    assert faq_service.horario_apertura == time(9, 0)
    assert faq_service.horario_cierre == time(20, 0)

def test_servicios_disponibles(faq_service):
    """Prueba que los servicios estén correctamente configurados"""
    assert "corte_dama" in faq_service.servicios
    assert "corte_caballero" in faq_service.servicios
    assert "tinte" in faq_service.servicios
    
    servicio = faq_service.servicios["corte_dama"]
    assert "nombre" in servicio
    assert "duracion" in servicio
    assert "descripcion" in servicio

def test_get_servicio_info(faq_service):
    """Prueba la obtención de información de servicios"""
    servicio = faq_service.get_servicio_info("corte_dama")
    assert servicio is not None
    assert servicio["nombre"] == "Corte de Dama"
    assert servicio["duracion"] == 60
    
    # Prueba servicio inexistente
    servicio_invalido = faq_service.get_servicio_info("servicio_inexistente")
    assert servicio_invalido is None

def test_get_duracion_servicio(faq_service):
    """Prueba la obtención de duración de servicios"""
    duracion = faq_service.get_duracion_servicio("corte_dama")
    assert duracion == 60
    
    # Prueba servicio inexistente (debe devolver el valor por defecto)
    duracion_default = faq_service.get_duracion_servicio("servicio_inexistente")
    assert duracion_default == 60

def test_get_faq_response(faq_service):
    """Prueba la obtención de respuestas a preguntas frecuentes"""
    respuesta = faq_service.get_faq_response("horario")
    assert respuesta is not None
    assert "horario de atención" in respuesta.lower()
    
    # Prueba pregunta inexistente
    respuesta_invalida = faq_service.get_faq_response("pregunta_inexistente")
    assert respuesta_invalida is None

def test_es_horario_disponible(faq_service):
    """Prueba la validación de horarios disponibles"""
    # Horario dentro del rango
    fecha_valida = datetime(2024, 3, 21, 14, 30)  # 2:30 PM
    assert faq_service.es_horario_disponible(fecha_valida) is True
    
    # Horario fuera del rango
    fecha_invalida = datetime(2024, 3, 21, 22, 0)  # 10:00 PM
    assert faq_service.es_horario_disponible(fecha_invalida) is False

def test_get_siguiente_horario_disponible(faq_service):
    """Prueba la obtención del siguiente horario disponible"""
    # Hora antes de apertura
    fecha_temprana = datetime(2024, 3, 21, 7, 0)  # 7:00 AM
    siguiente = faq_service.get_siguiente_horario_disponible(fecha_temprana)
    assert siguiente.hour == 9
    assert siguiente.minute == 0
    
    # Hora después del cierre
    fecha_tarde = datetime(2024, 3, 21, 21, 0)  # 9:00 PM
    siguiente = faq_service.get_siguiente_horario_disponible(fecha_tarde)
    assert siguiente.day == fecha_tarde.day + 1
    assert siguiente.hour == 9
    assert siguiente.minute == 0

def test_validar_servicio(faq_service):
    """Prueba la validación de servicios"""
    assert faq_service.validar_servicio("corte_dama") is True
    assert faq_service.validar_servicio("CORTE_DAMA") is True  # Prueba case-insensitive
    assert faq_service.validar_servicio("servicio_inexistente") is False

def test_generar_lista_servicios(faq_service):
    """Prueba la generación de la lista de servicios"""
    lista = faq_service._generar_lista_servicios()
    assert isinstance(lista, str)
    assert "Corte de Dama" in lista
    assert "min" in lista
    assert "📌" in lista  # Verifica que incluye emojis 