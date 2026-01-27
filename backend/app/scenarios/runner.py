"""
Runner de escenarios - Ejecuta queries en diferentes configuraciones

Flujo:
- Modo Consulta: Usa ConsultaRouter (entity detection determinístico)
- Modo Agente: Usa flujo conversacional (futuro)
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.config.loader import ConfigLoader, ScenarioConfig, get_config
from app.llm.client_v2 import create_client_v2, BaseLLMClientV2
from app.rag.retriever_chroma import ChromaRetriever  # Cambio a Chroma
from app.metrics.database import MetricsDB
from app.metrics.collector import QueryMetrics
from app.scenarios.consulta_router import ConsultaRouter

logger = logging.getLogger(__name__)


class ScenarioRunner:
    """
    Ejecutor de escenarios.
    Permite correr queries en diferentes configuraciones y comparar resultados.
    """

    def __init__(self, config_path: str = None):
        """
        Inicializa el runner.

        Args:
            config_path: Ruta al archivo scenarios.yaml (opcional)
        """
        self.config_loader = get_config(config_path)
        self.global_config = self.config_loader.global_config

        # RAG compartido (ChromaDB - se inicializa bajo demanda)
        self._retriever: Optional[ChromaRetriever] = None

        # Clientes LLM por escenario (cache)
        self._clients: Dict[str, BaseLLMClientV2] = {}

        # Routers de consulta por escenario (cache)
        self._consulta_routers: Dict[str, ConsultaRouter] = {}

        # Base de datos de métricas
        self._metrics_db: Optional[MetricsDB] = None
        if self.global_config.metrics_enabled:
            self._metrics_db = MetricsDB(self.global_config.metrics_db_path)

        logger.info(f"ScenarioRunner inicializado con {len(self.config_loader.get_enabled_scenarios())} escenarios")

    # =========================================================================
    # INICIALIZACIÓN LAZY
    # =========================================================================

    def _ensure_rag_loaded(self):
        """Carga el RAG (ChromaDB) si no está cargado"""
        if self._retriever is None:
            logger.info("Cargando ChromaDB RAG...")
            self._retriever = ChromaRetriever(
                embedding_model=self.global_config.rag.embedding_model
            )
            logger.info(f"ChromaDB RAG cargado: {self._retriever.collection.count()} chunks")

    def _get_client(self, scenario_id: str) -> BaseLLMClientV2:
        """Obtiene o crea el cliente LLM para un escenario"""
        if scenario_id not in self._clients:
            config = self.config_loader.get_scenario(scenario_id)
            if config is None:
                raise ValueError(f"Escenario no encontrado: {scenario_id}")

            self._clients[scenario_id] = create_client_v2(config)

        return self._clients[scenario_id]

    def _get_consulta_router(self, scenario_id: str) -> ConsultaRouter:
        """Obtiene o crea el router de consulta para un escenario"""
        if scenario_id not in self._consulta_routers:
            self._ensure_rag_loaded()
            client = self._get_client(scenario_id)
            self._consulta_routers[scenario_id] = ConsultaRouter(
                retriever=self._retriever,
                llm_client=client
            )
        return self._consulta_routers[scenario_id]

    # =========================================================================
    # EJECUCIÓN DE QUERIES
    # =========================================================================

    def run_query(
        self,
        scenario_id: str,
        query: str,
        obra_social: str = None,
        experiment_id: int = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una query en un escenario específico.

        Args:
            scenario_id: ID del escenario (ej: "groq_consulta")
            query: Pregunta del usuario
            obra_social: Obra social para filtrar RAG (IGNORADO en modo consulta)
            experiment_id: ID del experimento para agrupar métricas
            user_id: ID del usuario (para tracking)

        Returns:
            Dict con respuesta y métricas
        """
        # Obtener configuración del escenario
        config = self.config_loader.get_scenario(scenario_id)
        if config is None:
            raise ValueError(f"Escenario no encontrado: {scenario_id}")

        if not config.enabled:
            raise ValueError(f"Escenario deshabilitado: {scenario_id}")

        # =====================================================================
        # MODO CONSULTA: Usar ConsultaRouter (entity detection determinístico)
        # =====================================================================
        if config.mode.type == "consulta":
            return self._run_consulta_mode(
                scenario_id=scenario_id,
                config=config,
                query=query,
                experiment_id=experiment_id,
                user_id=user_id
            )

        # =====================================================================
        # MODO AGENTE: Flujo conversacional (FUTURO)
        # =====================================================================
        elif config.mode.type == "agente":
            raise NotImplementedError("Modo Agente no implementado todavía")

        else:
            raise ValueError(f"Modo no soportado: {config.mode.type}")

    def _run_consulta_mode(
        self,
        scenario_id: str,
        config: ScenarioConfig,
        query: str,
        experiment_id: int = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Ejecuta query en Modo Consulta usando ConsultaRouter.

        Flujo determinístico:
        1. Entity Detection (sin LLM)
        2. Sin entidad → mensaje fijo (sin RAG, sin LLM)
        3. Con entidad → RAG filtrado + LLM
        """
        # Obtener cliente y router
        client = self._get_client(scenario_id)
        router = self._get_consulta_router(scenario_id)

        # Crear métricas
        metrics = client.metrics_collector.new_query(query, obra_social=None)

        # Ejecutar flujo del router
        result = router.process_query(query=query, metrics=metrics)

        # Finalizar métricas
        client.metrics_collector.finalize(metrics)

        # Determinar obra_social detectada para guardar en BD
        detected_obra_social = None
        if result.entity_result and result.entity_result.entity_type == "obra_social":
            detected_obra_social = result.entity_result.entity

        # Extraer info de entity detection
        entity_info = result.entity_result
        entity_detected = entity_info.entity if entity_info else None
        entity_type = entity_info.entity_type if entity_info else None
        entity_confidence = entity_info.confidence if entity_info else None
        llm_skipped = not result.llm_executed

        # Guardar en base de datos
        query_id = None
        if self._metrics_db:
            query_id = self._metrics_db.record_query(
                scenario=scenario_id,
                mode=config.mode.type,
                llm_provider=config.llm.provider,
                llm_model=config.llm.model,
                query_hash=metrics.query_hash,
                query_length=metrics.query_length,
                obra_social=detected_obra_social,
                tokens_input=metrics.tokens_input,
                tokens_output=metrics.tokens_output,
                latency_embedding_ms=metrics.latency_embedding_ms,
                latency_faiss_ms=metrics.latency_faiss_ms,
                latency_llm_ms=metrics.latency_llm_ms,
                cost_input=metrics.cost_input,
                cost_output=metrics.cost_output,
                entity_detected=entity_detected,
                entity_type=entity_type,
                entity_confidence=entity_confidence,
                llm_skipped=llm_skipped,
                rag_used=result.rag_executed,
                rag_chunks_count=result.chunks_count,
                rag_top_similarity=result.top_similarity,
                response_length=metrics.response_length,
                response_words=metrics.response_words,
                success=metrics.success,
                error_message=metrics.error_message,
                user_id=user_id,
                experiment_id=experiment_id
            )

        # Construir resultado
        return {
            "respuesta": result.respuesta,
            "scenario_id": scenario_id,
            "query_id": query_id,
            "metrics": metrics,
            "entity": result.entity_result.to_dict() if result.entity_result else None,
            "rag_executed": result.rag_executed,
            "llm_executed": result.llm_executed,
            "chunks_count": result.chunks_count,
            "top_similarity": result.top_similarity,
            "chunks_info": [c.to_dict() for c in result.chunks_info] if result.chunks_info else [],
            "context_preview": result.context_used[:200] + "..." if result.context_used and len(result.context_used) > 200 else result.context_used
        }

    # =========================================================================
    # COMPARACIÓN DE ESCENARIOS
    # =========================================================================

    def run_comparison(
        self,
        query: str,
        obra_social: str = None,
        scenarios: List[str] = None,
        experiment_id: int = None
    ) -> Dict[str, Any]:
        """
        Ejecuta la misma query en múltiples escenarios y compara.

        Args:
            query: Pregunta a comparar
            obra_social: Obra social para filtrar
            scenarios: Lista de escenarios a comparar (default: los configurados en comparativo)
            experiment_id: ID del experimento

        Returns:
            Dict con resultados de cada escenario y comparación
        """
        # Obtener escenarios a comparar
        if scenarios is None:
            scenarios = self.config_loader.get_comparison_scenarios()

        if not scenarios or len(scenarios) < 2:
            raise ValueError("Se necesitan al menos 2 escenarios para comparar")

        results = {}
        metrics_list = []

        # Ejecutar en cada escenario
        for scenario_id in scenarios:
            try:
                result = self.run_query(
                    scenario_id=scenario_id,
                    query=query,
                    obra_social=obra_social,
                    experiment_id=experiment_id
                )
                results[scenario_id] = result
                metrics_list.append((scenario_id, result.get("metrics")))
            except Exception as e:
                logger.error(f"Error en escenario {scenario_id}: {e}")
                results[scenario_id] = {"error": str(e)}

        # Calcular comparación
        comparison = self._calculate_comparison(metrics_list)

        # Guardar comparación en BD
        if self._metrics_db and len(metrics_list) >= 2:
            m0 = metrics_list[0]
            m1 = metrics_list[1]
            if m0[1] and m1[1]:
                self._metrics_db.record_comparison(
                    query_hash=m0[1].query_hash,
                    scenario_a=m0[0],
                    query_id_a=results.get(m0[0], {}).get("query_id"),
                    metrics_a={
                        "tokens": m0[1].tokens_total,
                        "latency_ms": m0[1].latency_total_ms,
                        "cost_usd": m0[1].cost_total,
                        "precision": 0  # Se puede calcular después
                    },
                    scenario_b=m1[0],
                    query_id_b=results.get(m1[0], {}).get("query_id"),
                    metrics_b={
                        "tokens": m1[1].tokens_total,
                        "latency_ms": m1[1].latency_total_ms,
                        "cost_usd": m1[1].cost_total,
                        "precision": 0
                    },
                    experiment_id=experiment_id
                )

        return {
            "query": query,
            "obra_social": obra_social,
            "results": results,
            "comparison": comparison
        }

    def _calculate_comparison(self, metrics_list: List[tuple]) -> Dict:
        """Calcula métricas de comparación"""
        if len(metrics_list) < 2:
            return {}

        comparison = {
            "scenarios": [m[0] for m in metrics_list],
            "metrics": {}
        }

        # Extraer métricas de cada escenario
        for scenario_id, metrics in metrics_list:
            if metrics:
                comparison["metrics"][scenario_id] = {
                    "tokens_total": metrics.tokens_total,
                    "latency_ms": round(metrics.latency_total_ms, 2),
                    "cost_usd": round(metrics.cost_total, 6),
                    "response_words": metrics.response_words
                }

        # Determinar ganadores
        if len(comparison["metrics"]) >= 2:
            scenarios = list(comparison["metrics"].keys())
            m1 = comparison["metrics"][scenarios[0]]
            m2 = comparison["metrics"][scenarios[1]]

            comparison["winners"] = {
                "tokens": scenarios[0] if m1["tokens_total"] < m2["tokens_total"] else scenarios[1],
                "latency": scenarios[0] if m1["latency_ms"] < m2["latency_ms"] else scenarios[1],
                "cost": scenarios[0] if m1["cost_usd"] < m2["cost_usd"] else scenarios[1],
            }

            comparison["differences"] = {
                "tokens": m1["tokens_total"] - m2["tokens_total"],
                "latency_ms": round(m1["latency_ms"] - m2["latency_ms"], 2),
                "cost_usd": round(m1["cost_usd"] - m2["cost_usd"], 6),
            }

        return comparison

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def list_scenarios(self) -> List[Dict]:
        """Lista todos los escenarios disponibles"""
        scenarios = []
        for scenario_id, config in self.config_loader.get_all_scenarios().items():
            scenarios.append({
                "id": scenario_id,
                "name": config.name,
                "description": config.description,
                "enabled": config.enabled,
                "provider": config.llm.provider,
                "model": config.llm.model,
                "mode": config.mode.type
            })
        return scenarios

    def get_stats(self, scenario_id: str = None, days: int = 7) -> Dict:
        """Obtiene estadísticas de uso"""
        if not self._metrics_db:
            return {"error": "Métricas no habilitadas"}

        if scenario_id:
            return self._metrics_db.get_scenario_stats(scenario_id, days)
        else:
            # Stats de todos los escenarios
            stats = {}
            for sid in self.config_loader.get_enabled_scenarios():
                stats[sid] = self._metrics_db.get_scenario_stats(sid, days)
            return stats

    def health_check(self) -> Dict:
        """Verifica estado del sistema"""
        status = {
            "rag_loaded": self._retriever is not None,
            "rag_documents": self._retriever.collection.count() if self._retriever else 0,
            "rag_type": "ChromaDB",
            "metrics_enabled": self._metrics_db is not None,
            "scenarios": {}
        }

        for scenario_id in self.config_loader.get_enabled_scenarios():
            try:
                client = self._get_client(scenario_id)
                status["scenarios"][scenario_id] = {
                    "available": client.is_available(),
                    "provider": client.provider,
                    "model": client.model
                }
            except Exception as e:
                status["scenarios"][scenario_id] = {
                    "available": False,
                    "error": str(e)
                }

        return status
