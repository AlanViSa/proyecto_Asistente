from fastapi import APIRouter
from app.api.endpoints import clientes, citas, whatsapp, nlp

api_router = APIRouter()

api_router.include_router(clientes.router, prefix="/clientes", tags=["clientes"])
api_router.include_router(citas.router, prefix="/citas", tags=["citas"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(nlp.router, prefix="/nlp", tags=["nlp"]) 