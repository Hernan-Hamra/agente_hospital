"""
Collector de métricas para Escenario 3
=======================================

Extiende las métricas base con información de historial.
"""
import time
from dataclasses import dataclass, field
from typing import Optional


def count_tokens_approximate(text: str) -> int:
    """Estimación aproximada de tokens (4 chars ~ 1 token)"""
    if not text:
        return 0
    return len(text) // 4


@dataclass
class QueryMetrics:
    """Métricas de una query en modo agente"""
    query_text: str
    obra_social: Optional[str] = None

    # Tiempos
    latency_faiss_ms: float = 0.0
    latency_llm_ms: float = 0.0
    latency_total_ms: float = 0.0

    # Tokens
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_context: int = 0
    tokens_history: int = 0  # Nuevo: tokens del historial

    # RAG
    rag_used: bool = False
    rag_chunks_count: int = 0
    rag_top_similarity: float = 0.0

    # Historial
    history_turns: int = 0

    # Response
    response_text: str = ""

    # Timestamps
    timestamp: float = field(default_factory=time.time)
