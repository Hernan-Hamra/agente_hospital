"""
Router determinístico para Modo Consulta.

Reglas estrictas:
1. Sin entidad → mensaje fijo (NO LLM, NO RAG)
2. Con entidad → RAG filtrado + LLM
3. NO existe RAG general
4. NO se mezclan corpora
"""
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.entities.detector import EntityDetector, EntityResult, get_entity_detector
from app.rag.retriever import DocumentRetriever
from app.llm.client_v2 import BaseLLMClientV2
from app.metrics.collector import QueryMetrics, count_tokens_approximate

logger = logging.getLogger(__name__)


@dataclass
class ConsultaResult:
    """Resultado del Modo Consulta"""
    respuesta: str
    entity_result: EntityResult
    rag_executed: bool
    llm_executed: bool
    context_used: Optional[str]
    chunks_count: int
    top_similarity: float
    metrics: Optional[QueryMetrics]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "respuesta": self.respuesta,
            "entity": self.entity_result.to_dict() if self.entity_result else None,
            "rag_executed": self.rag_executed,
            "llm_executed": self.llm_executed,
            "chunks_count": self.chunks_count,
            "top_similarity": self.top_similarity
        }


# Prompt fijo del sistema (NO incluye conocimiento del dominio)
SYSTEM_PROMPT = """Sos un asistente administrativo del Grupo Pediátrico.
Respondé SOLO con la información del CONTEXTO.
Si la respuesta no está en el contexto, decí: "No tengo esa información".
Máximo 30 palabras.
Español claro (Argentina)."""


class ConsultaRouter:
    """
    Router determinístico para Modo Consulta.

    Flujo:
    1. Entity Detection (sin LLM)
    2. Si entity == null → respuesta fija (sin RAG, sin LLM)
    3. Si entity != null → RAG filtrado → LLM
    """

    def __init__(
        self,
        retriever: DocumentRetriever,
        llm_client: BaseLLMClientV2,
        entity_detector: EntityDetector = None
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.entity_detector = entity_detector or get_entity_detector()

    def process_query(
        self,
        query: str,
        metrics: QueryMetrics = None
    ) -> ConsultaResult:
        """
        Procesa una consulta en Modo Consulta.

        Args:
            query: Pregunta del usuario
            metrics: Objeto de métricas (opcional)

        Returns:
            ConsultaResult con respuesta y metadatos
        """
        start_time = time.perf_counter()

        # =====================================================================
        # PASO 1: Entity Detection (código puro, ~0.1ms)
        # =====================================================================
        entity_start = time.perf_counter()
        entity_result = self.entity_detector.detect(query)
        entity_time_ms = (time.perf_counter() - entity_start) * 1000

        logger.info(f"Entity detection: {entity_result.entity} ({entity_result.confidence}) en {entity_time_ms:.2f}ms")

        # =====================================================================
        # PASO 2: Router determinístico
        # =====================================================================

        # CASO A: Sin entidad → mensaje fijo (NO RAG, NO LLM)
        if not entity_result.detected:
            logger.info("Sin entidad detectada → respuesta fija")

            respuesta = self.entity_detector.get_no_entity_message()

            if metrics:
                metrics.response_text = respuesta
                metrics.tokens_input = 0
                metrics.tokens_output = 0
                metrics.latency_total_ms = (time.perf_counter() - start_time) * 1000

            return ConsultaResult(
                respuesta=respuesta,
                entity_result=entity_result,
                rag_executed=False,
                llm_executed=False,
                context_used=None,
                chunks_count=0,
                top_similarity=0.0,
                metrics=metrics
            )

        # CASO B/C: Con entidad → RAG filtrado + LLM
        logger.info(f"Entidad detectada: {entity_result.entity} → RAG filtrado")

        # =====================================================================
        # PASO 3: RAG filtrado (SOLO a la entidad detectada)
        # =====================================================================
        rag_start = time.perf_counter()

        # NUNCA ejecutar RAG sin filtro
        rag_filter = entity_result.rag_filter
        top_k = 5  # Aumentado para capturar tablas con datos de contacto

        chunks = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            obra_social_filter=rag_filter
        )

        # Construir contexto
        if chunks:
            context_parts = []
            for chunk_text, metadata, score in chunks:
                context_parts.append(chunk_text)
            context = "\n\n".join(context_parts)
            top_similarity = chunks[0][2]
        else:
            context = "No se encontró información relevante."
            top_similarity = 0.0

        rag_time_ms = (time.perf_counter() - rag_start) * 1000

        if metrics:
            metrics.latency_faiss_ms = rag_time_ms
            metrics.rag_used = True
            metrics.rag_chunks_count = len(chunks)
            metrics.rag_top_similarity = top_similarity

        logger.info(f"RAG: {len(chunks)} chunks recuperados (filter={rag_filter}) en {rag_time_ms:.2f}ms")

        # =====================================================================
        # PASO 4: LLM (solo responde con el contexto filtrado)
        # =====================================================================
        llm_start = time.perf_counter()

        # Construir mensajes
        user_content = f"CONTEXTO:\n{context}\n\nPREGUNTA:\n{query}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        # Contar tokens de entrada
        tokens_input = count_tokens_approximate(SYSTEM_PROMPT + user_content)

        if metrics:
            metrics.tokens_input = tokens_input

        # Llamar al LLM
        try:
            llm_result = self._call_llm(messages)
            respuesta = llm_result["respuesta"]
            tokens_output = llm_result.get("tokens_output", count_tokens_approximate(respuesta))
        except Exception as e:
            logger.error(f"Error en LLM: {e}")
            respuesta = "Error al procesar la consulta."
            tokens_output = 0

        llm_time_ms = (time.perf_counter() - llm_start) * 1000

        if metrics:
            metrics.tokens_output = tokens_output
            metrics.latency_llm_ms = llm_time_ms
            metrics.response_text = respuesta
            metrics.latency_total_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"LLM: {tokens_output} tokens output en {llm_time_ms:.2f}ms")

        return ConsultaResult(
            respuesta=respuesta,
            entity_result=entity_result,
            rag_executed=True,
            llm_executed=True,
            context_used=context[:500] + "..." if len(context) > 500 else context,
            chunks_count=len(chunks),
            top_similarity=top_similarity,
            metrics=metrics
        )

    def _call_llm(self, messages: list) -> Dict[str, Any]:
        """
        Llama al LLM con los mensajes construidos.
        Abstrae la diferencia entre Groq y Ollama.
        """
        config = self.llm_client.config
        params = config.llm.parameters

        if config.llm.provider == "groq":
            response = self.llm_client.client.chat.completions.create(
                model=config.llm.model,
                messages=messages,
                max_tokens=params.get("max_tokens", 100),
                temperature=params.get("temperature", 0.1)
            )
            respuesta = response.choices[0].message.content or ""
            tokens_output = response.usage.completion_tokens if response.usage else 0
            return {"respuesta": respuesta, "tokens_output": tokens_output}

        elif config.llm.provider == "ollama":
            response = self.llm_client.client.chat(
                model=config.llm.model,
                messages=messages,
                options={
                    "temperature": params.get("temperature", 0.1),
                    "num_predict": params.get("num_predict", 100),
                    "num_ctx": params.get("num_ctx", 1024)
                }
            )
            respuesta = response["message"]["content"]
            tokens_output = response.get("eval_count", 0)
            return {"respuesta": respuesta, "tokens_output": tokens_output}

        else:
            raise ValueError(f"Provider no soportado: {config.llm.provider}")
