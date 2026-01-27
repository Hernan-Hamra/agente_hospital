"""
Cliente LLM para Escenario 1 (Groq)
Simplificado y autocontenido.
"""
import os
import logging
from typing import Dict, List, Any

from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    """Cliente para Groq Cloud - Modo Consulta"""

    def __init__(
        self,
        api_key: str = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 150
    ):
        """
        Args:
            api_key: API key de Groq (o usa GROQ_API_KEY env var)
            model: Modelo a usar
            temperature: Temperatura para generación
            max_tokens: Máximo de tokens en respuesta
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no configurado")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client = Groq(api_key=self.api_key)
        logger.info(f"GroqClient inicializado: modelo={self.model}")

    def is_available(self) -> bool:
        """Verifica si Groq está disponible"""
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

    def generate(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Genera respuesta a partir de mensajes.

        Args:
            messages: Lista de mensajes [{"role": "...", "content": "..."}]

        Returns:
            Dict con respuesta y tokens
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            respuesta = response.choices[0].message.content or ""

            tokens_input = 0
            tokens_output = 0
            if hasattr(response, 'usage') and response.usage:
                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens

            logger.info(f"Groq respuesta: {len(respuesta)} chars, {tokens_input}+{tokens_output} tokens")

            return {
                "respuesta": respuesta,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "model": self.model,
                "provider": "groq"
            }

        except Exception as e:
            logger.error(f"Error en Groq: {e}")
            return {
                "respuesta": f"Error: {str(e)}",
                "tokens_input": 0,
                "tokens_output": 0,
                "model": self.model,
                "provider": "groq",
                "error": str(e)
            }
