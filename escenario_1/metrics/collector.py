"""
Colector de métricas simplificado para Escenario 1
"""
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class QueryMetrics:
    """Contenedor de métricas para una query"""
    # Input
    query_text: str = ""
    obra_social: Optional[str] = None

    # Tokens
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_prompt: int = 0
    tokens_query: int = 0
    tokens_context: int = 0

    # Latencias (ms)
    latency_faiss_ms: float = 0  # También usado para ChromaDB
    latency_llm_ms: float = 0
    latency_total_ms: float = 0

    # RAG
    rag_used: bool = False
    rag_chunks_count: int = 0
    rag_top_similarity: float = 0

    # Respuesta
    response_text: str = ""

    # Estado
    success: bool = True
    error_message: Optional[str] = None

    @property
    def tokens_total(self) -> int:
        return self.tokens_input + self.tokens_output

    def to_dict(self) -> Dict[str, Any]:
        return {
            "obra_social": self.obra_social,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "tokens_total": self.tokens_total,
            "latency_faiss_ms": self.latency_faiss_ms,
            "latency_llm_ms": self.latency_llm_ms,
            "latency_total_ms": self.latency_total_ms,
            "rag_used": self.rag_used,
            "rag_chunks_count": self.rag_chunks_count,
            "rag_top_similarity": self.rag_top_similarity,
            "success": self.success,
            "error_message": self.error_message
        }


def count_tokens_approximate(text: str) -> int:
    """
    Estimación rápida de tokens (sin cargar tokenizer pesado).
    Regla aproximada: 1 token ≈ 4 caracteres.
    """
    return len(text) // 4
