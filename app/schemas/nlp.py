from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class MessageRequest(BaseModel):
    message: str

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    intent: str
    sentimiento: str
    servicio: Optional[str] = None
    fecha_hora: Optional[str] = None
    nombre_cliente: Optional[str] = None
    telefono: Optional[str] = None
    faq_key: Optional[str] = None
    error: Optional[str] = None
    response: str
    analysis: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)