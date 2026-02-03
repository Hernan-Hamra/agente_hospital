"""
Cliente LLM para Escenario 3 (Groq)
====================================

Soporta historial de conversación para modo agente.
"""
import os
import logging
from typing import Dict, Any, List, Optional

from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    """Cliente Groq para Escenario 3 - Modo Agente"""

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 300
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")

        self.client = Groq(api_key=api_key)
        logger.info(f"GroqClient inicializado: {model}")

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Genera respuesta del LLM.

        Args:
            messages: Lista de mensajes (system, user, assistant)
            temperature: Override de temperatura
            max_tokens: Override de max tokens

        Returns:
            Dict con respuesta y metadata
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )

            respuesta = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens

            return {
                "respuesta": respuesta,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "model": self.model
            }

        except Exception as e:
            logger.error(f"Error en Groq: {e}")
            raise

    def is_available(self) -> bool:
        """Verifica si el cliente está disponible"""
        try:
            # Test simple
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
