"""
Cliente LLM v2 - Configurable desde YAML
Soporta múltiples escenarios con configuración externa.

Diferencias con client.py:
- Recibe ScenarioConfig en constructor (no lee de .env)
- Modo consulta separado de modo agente
- Integrado con sistema de métricas
- Sin hardcoding de parámetros
"""
import os
import time
import json
import logging
from typing import Optional, Dict, List, Callable, Any
from abc import ABC, abstractmethod

from app.config.loader import ScenarioConfig
from app.metrics.collector import QueryMetrics, MetricsCollector, count_tokens_approximate

logger = logging.getLogger(__name__)


class BaseLLMClientV2(ABC):
    """Clase base para clientes LLM configurables"""

    def __init__(self, config: ScenarioConfig):
        self.config = config
        self.provider = config.llm.provider
        self.model = config.llm.model
        self.mode = config.mode.type

        # Inicializar colector de métricas
        self.metrics_collector = MetricsCollector(
            scenario=config.name,
            mode=config.mode.type,
            llm_provider=config.llm.provider,
            llm_model=config.llm.model
        )

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el LLM está disponible"""
        pass

    @abstractmethod
    def generate_response(
        self,
        query: str,
        context: str,
        obra_social: str = None,
        metrics: QueryMetrics = None
    ) -> Dict[str, Any]:
        """Genera respuesta en modo consulta (sin historial)"""
        pass

    def _build_messages_consulta(self, query: str, context: str) -> List[Dict]:
        """Construye los mensajes para modo consulta"""
        user_content = self.config.prompt.user_template.format(
            context=context,
            query=query
        )

        return [
            {"role": "system", "content": self.config.prompt.system},
            {"role": "user", "content": user_content}
        ]

    def _count_input_tokens(self, messages: List[Dict]) -> int:
        """Cuenta tokens de entrada aproximados"""
        total_text = ""
        for msg in messages:
            total_text += msg.get("content", "")
        return count_tokens_approximate(total_text)


class GroqClientV2(BaseLLMClientV2):
    """Cliente para Groq (cloud) - Modo Consulta"""

    def __init__(self, config: ScenarioConfig, api_key: str = None):
        super().__init__(config)
        from groq import Groq

        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no configurado")

        self.client = Groq(api_key=self.api_key)
        logger.info(f"GroqClientV2 inicializado: modelo={self.model}")

    def is_available(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.warning(f"Groq no disponible: {e}")
            return False

    def generate_response(
        self,
        query: str,
        context: str,
        obra_social: str = None,
        metrics: QueryMetrics = None
    ) -> Dict[str, Any]:
        """Genera respuesta en modo consulta"""

        # Crear métricas si no se proporcionaron
        if metrics is None:
            metrics = self.metrics_collector.new_query(query, obra_social)

        # Construir mensajes
        messages = self._build_messages_consulta(query, context)
        metrics.tokens_input = self._count_input_tokens(messages)

        # Obtener parámetros de configuración
        params = self.config.llm.parameters

        try:
            with self.metrics_collector.measure_llm(metrics):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=params.get("max_tokens", 150),
                    temperature=params.get("temperature", 0.1),
                    top_p=params.get("top_p", 0.9)
                )

            # Extraer respuesta y tokens
            respuesta = response.choices[0].message.content or ""
            metrics.response_text = respuesta

            # Usar tokens reportados por Groq si están disponibles
            if hasattr(response, 'usage') and response.usage:
                metrics.tokens_input = response.usage.prompt_tokens
                metrics.tokens_output = response.usage.completion_tokens
            else:
                metrics.tokens_output = count_tokens_approximate(respuesta)

            # Calcular costos
            metrics.compute_costs(
                self.config.costs.input_per_million,
                self.config.costs.output_per_million
            )

            metrics.success = True
            logger.info(f"Groq respuesta: {len(respuesta)} chars, {metrics.tokens_total} tokens")

            return {
                "respuesta": respuesta,
                "metrics": metrics,
                "provider": "groq",
                "model": self.model
            }

        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            logger.error(f"Error en Groq: {e}")

            return {
                "respuesta": f"Error: {str(e)}",
                "metrics": metrics,
                "provider": "groq",
                "model": self.model
            }


class OllamaClientV2(BaseLLMClientV2):
    """Cliente para Ollama (local) - Modo Consulta"""

    def __init__(self, config: ScenarioConfig):
        super().__init__(config)
        import ollama

        self.host = config.llm.host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.Client(host=self.host)
        logger.info(f"OllamaClientV2 inicializado: modelo={self.model}, host={self.host}")

    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama no disponible: {e}")
            return False

    def generate_response(
        self,
        query: str,
        context: str,
        obra_social: str = None,
        metrics: QueryMetrics = None
    ) -> Dict[str, Any]:
        """Genera respuesta en modo consulta"""

        # Crear métricas si no se proporcionaron
        if metrics is None:
            metrics = self.metrics_collector.new_query(query, obra_social)

        # Construir mensajes
        messages = self._build_messages_consulta(query, context)
        metrics.tokens_input = self._count_input_tokens(messages)

        # Obtener parámetros de configuración
        params = self.config.llm.parameters

        try:
            with self.metrics_collector.measure_llm(metrics):
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": params.get("temperature", 0.1),
                        "num_predict": params.get("num_predict", 150),
                        "num_ctx": params.get("num_ctx", 2048),
                        "top_k": params.get("top_k", 20),
                        "top_p": params.get("top_p", 0.8),
                        "repeat_penalty": params.get("repeat_penalty", 1.2)
                    }
                )

            # Extraer respuesta
            respuesta = response["message"]["content"]
            metrics.response_text = respuesta

            # Usar tokens reportados por Ollama si están disponibles
            if "prompt_eval_count" in response:
                metrics.tokens_input = response["prompt_eval_count"]
            if "eval_count" in response:
                metrics.tokens_output = response["eval_count"]
            else:
                metrics.tokens_output = count_tokens_approximate(respuesta)

            # Costos (local = 0, pero podemos agregar electricidad)
            metrics.compute_costs(0, 0)

            metrics.success = True
            logger.info(f"Ollama respuesta: {len(respuesta)} chars, {metrics.tokens_total} tokens")

            return {
                "respuesta": respuesta,
                "metrics": metrics,
                "provider": "ollama",
                "model": self.model
            }

        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            logger.error(f"Error en Ollama: {e}")

            return {
                "respuesta": f"Error: {str(e)}",
                "metrics": metrics,
                "provider": "ollama",
                "model": self.model
            }


def create_client_v2(config: ScenarioConfig) -> BaseLLMClientV2:
    """Factory para crear el cliente según configuración"""
    provider = config.llm.provider.lower()

    if provider == "groq":
        return GroqClientV2(config)
    elif provider == "ollama":
        return OllamaClientV2(config)
    else:
        raise ValueError(f"Provider no soportado: {provider}")
