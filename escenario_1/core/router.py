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
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

import yaml

from .entity_detector import EntityDetector, EntityResult, get_entity_detector
from ..metrics.collector import QueryMetrics, count_tokens_approximate

logger = logging.getLogger(__name__)


@dataclass
class ChunkInfo:
    """Información de un chunk recuperado"""
    text: str
    obra_social: str
    chunk_id: str
    similarity: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text_preview": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "obra_social": self.obra_social,
            "chunk_id": self.chunk_id,
            "similarity": round(self.similarity, 4)
        }


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
    chunks_info: list  # Lista de ChunkInfo
    metrics: Optional[QueryMetrics]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "respuesta": self.respuesta,
            "entity": self.entity_result.to_dict() if self.entity_result else None,
            "rag_executed": self.rag_executed,
            "llm_executed": self.llm_executed,
            "chunks_count": self.chunks_count,
            "top_similarity": self.top_similarity,
            "chunks_info": [c.to_dict() for c in self.chunks_info] if self.chunks_info else []
        }


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
        retriever,  # ChromaRetriever
        llm_client,  # GroqClient
        entity_detector: EntityDetector = None,
        config_path: str = None
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.entity_detector = entity_detector or get_entity_detector()

        # Cargar config del escenario
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "scenario.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.system_prompt = self.config.get("prompt", {}).get("system", "")
        self.top_k = self.config.get("rag", {}).get("top_k", 3)

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
                chunks_info=[],
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

        chunks = self.retriever.retrieve(
            query=query,
            top_k=self.top_k,
            obra_social_filter=rag_filter
        )

        # Construir contexto y chunks_info
        chunks_info = []
        if chunks:
            context_parts = []
            for chunk_text, metadata, score in chunks:
                context_parts.append(chunk_text)
                chunks_info.append(ChunkInfo(
                    text=chunk_text,
                    obra_social=metadata.get("obra_social", "N/A"),
                    chunk_id=metadata.get("chunk_id", "N/A"),
                    similarity=score
                ))
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
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]

        # Contar tokens de entrada
        tokens_system_prompt = count_tokens_approximate(self.system_prompt)
        tokens_query = count_tokens_approximate(query)
        tokens_context = count_tokens_approximate(context)
        tokens_template = count_tokens_approximate("CONTEXTO:\n\nPREGUNTA:\n")
        tokens_input = tokens_system_prompt + tokens_query + tokens_context + tokens_template

        if metrics:
            metrics.tokens_input = tokens_input
            metrics.tokens_prompt = tokens_system_prompt + tokens_template
            metrics.tokens_query = tokens_query
            metrics.tokens_context = tokens_context

        # Llamar al LLM
        try:
            llm_result = self.llm_client.generate(messages)
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
            chunks_info=chunks_info,
            metrics=metrics
        )
