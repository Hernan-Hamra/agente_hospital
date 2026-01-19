"""
Colector de métricas para instrumentación de queries
"""
import time
import hashlib
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class QueryMetrics:
    """Contenedor de métricas para una query"""
    # Identificación
    scenario: str = ""
    mode: str = ""
    llm_provider: str = ""
    llm_model: str = ""

    # Input
    query_text: str = ""
    query_hash: str = ""
    query_length: int = 0
    obra_social: Optional[str] = None

    # Tokens
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_prompt: int = 0
    tokens_context: int = 0

    # Latencias (ms)
    latency_embedding_ms: float = 0
    latency_faiss_ms: float = 0
    latency_llm_ms: float = 0
    latency_total_ms: float = 0

    # Costos
    cost_input: float = 0
    cost_output: float = 0
    cost_total: float = 0

    # RAG
    rag_used: bool = False
    rag_chunks_count: int = 0
    rag_top_similarity: float = 0

    # Respuesta
    response_text: str = ""
    response_length: int = 0
    response_words: int = 0

    # Estado
    success: bool = True
    error_message: Optional[str] = None

    # Timestamps internos
    _start_time: float = field(default=0, repr=False)
    _phase_times: Dict[str, float] = field(default_factory=dict, repr=False)

    def compute_hash(self):
        """Calcula hash del query para comparaciones"""
        self.query_hash = hashlib.md5(self.query_text.encode()).hexdigest()[:16]
        self.query_length = len(self.query_text)

    def compute_response_stats(self):
        """Calcula estadísticas de la respuesta"""
        self.response_length = len(self.response_text)
        self.response_words = len(self.response_text.split())

    def compute_costs(self, input_price_per_million: float, output_price_per_million: float):
        """Calcula costos basado en tokens y precios"""
        self.cost_input = (self.tokens_input / 1_000_000) * input_price_per_million
        self.cost_output = (self.tokens_output / 1_000_000) * output_price_per_million
        self.cost_total = self.cost_input + self.cost_output

    @property
    def tokens_total(self) -> int:
        return self.tokens_input + self.tokens_output

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para persistencia"""
        return {
            "scenario": self.scenario,
            "mode": self.mode,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "query_hash": self.query_hash,
            "query_length": self.query_length,
            "obra_social": self.obra_social,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "tokens_total": self.tokens_total,
            "latency_embedding_ms": self.latency_embedding_ms,
            "latency_faiss_ms": self.latency_faiss_ms,
            "latency_llm_ms": self.latency_llm_ms,
            "latency_total_ms": self.latency_total_ms,
            "cost_input": self.cost_input,
            "cost_output": self.cost_output,
            "cost_total": self.cost_total,
            "rag_used": self.rag_used,
            "rag_chunks_count": self.rag_chunks_count,
            "rag_top_similarity": self.rag_top_similarity,
            "response_length": self.response_length,
            "response_words": self.response_words,
            "success": self.success,
            "error_message": self.error_message
        }


class MetricsCollector:
    """Colector de métricas con context managers para timing"""

    def __init__(self, scenario: str, mode: str, llm_provider: str, llm_model: str):
        self.scenario = scenario
        self.mode = mode
        self.llm_provider = llm_provider
        self.llm_model = llm_model

    def new_query(self, query_text: str, obra_social: str = None) -> QueryMetrics:
        """Crea un nuevo objeto de métricas para una query"""
        metrics = QueryMetrics(
            scenario=self.scenario,
            mode=self.mode,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            query_text=query_text,
            obra_social=obra_social
        )
        metrics.compute_hash()
        metrics._start_time = time.perf_counter()
        return metrics

    @contextmanager
    def measure_embedding(self, metrics: QueryMetrics):
        """Context manager para medir tiempo de embedding"""
        start = time.perf_counter()
        try:
            yield
        finally:
            metrics.latency_embedding_ms = (time.perf_counter() - start) * 1000

    @contextmanager
    def measure_faiss(self, metrics: QueryMetrics):
        """Context manager para medir tiempo de búsqueda FAISS"""
        start = time.perf_counter()
        try:
            yield
        finally:
            metrics.latency_faiss_ms = (time.perf_counter() - start) * 1000

    @contextmanager
    def measure_llm(self, metrics: QueryMetrics):
        """Context manager para medir tiempo de LLM"""
        start = time.perf_counter()
        try:
            yield
        finally:
            metrics.latency_llm_ms = (time.perf_counter() - start) * 1000

    def finalize(self, metrics: QueryMetrics):
        """Finaliza la medición y calcula totales"""
        metrics.latency_total_ms = (time.perf_counter() - metrics._start_time) * 1000
        metrics.compute_response_stats()


def count_tokens_approximate(text: str) -> int:
    """
    Estimación rápida de tokens (sin cargar tokenizer pesado).
    Regla aproximada: 1 token ≈ 4 caracteres en inglés, ~3.5 en español.
    """
    return len(text) // 4


def count_tokens_tiktoken(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Conteo preciso de tokens usando tiktoken (si está disponible).
    Funciona bien para modelos OpenAI-like.
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        return count_tokens_approximate(text)
    except Exception:
        return count_tokens_approximate(text)
