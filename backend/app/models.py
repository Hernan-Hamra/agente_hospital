"""
Modelos Pydantic para request/response
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ConversationMessage(BaseModel):
    """Mensaje en el historial conversacional"""
    role: str = Field(..., description="Rol del mensaje: 'user' o 'assistant'")
    content: str = Field(..., description="Contenido del mensaje")


class QueryRequest(BaseModel):
    """Request para consulta al agente"""
    pregunta: str = Field(..., min_length=1, description="Consulta del administrativo")
    obra_social: Optional[str] = Field(None, description="Obra social específica (opcional, puede ser null o string vacío)")
    historial: Optional[List[ConversationMessage]] = Field(default_factory=list, description="Historial de conversación previo")
    use_agent: Optional[bool] = Field(False, description="Usar modo agente con function calling (qwen2.5)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pregunta": "¿Qué documentos necesito para enrolar un paciente de ENSALUD?",
                    "obra_social": "ENSALUD",
                    "historial": []
                }
            ]
        }
    }


class SourceDocument(BaseModel):
    """Documento fuente usado en la respuesta"""
    archivo: str
    fragmento: str
    relevancia: float


class QueryResponse(BaseModel):
    """Response con la respuesta del agente"""
    respuesta: str = Field(..., description="Respuesta generada por el agente")
    fuentes: List[SourceDocument] = Field(default_factory=list, description="Documentos consultados")
    obra_social_detectada: Optional[str] = Field(None, description="Obra social identificada en la pregunta")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    ollama_disponible: bool
    indice_cargado: bool
    documentos_indexados: int
