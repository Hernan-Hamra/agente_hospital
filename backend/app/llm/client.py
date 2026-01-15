"""
Cliente dual para LLM: Ollama (local) y Groq (cloud)
Configurable via variable de entorno LLM_PROVIDER
"""
import os
import time
import json
from typing import Optional
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Clase base abstracta para clientes LLM"""

    def __init__(self):
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "consulta_rag",
                    "description": "Busca información de obras sociales ENSALUD/ASI/IOSFA. Usar para mail, teléfono, copagos, requisitos específicos. NO usar para saludos o protocolo básico.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "obra_social": {
                                "type": "string",
                                "description": "Obra social a consultar",
                                "enum": ["ENSALUD", "ASI", "IOSFA"]
                            },
                            "query": {
                                "type": "string",
                                "description": "Qué buscar: mail, teléfono, requisitos, copagos, etc."
                            }
                        },
                        "required": ["obra_social", "query"]
                    }
                }
            }
        ]

        self.system_prompt = """Asistente del Grupo Pediátrico para ENSALUD, ASI e IOSFA.

PROTOCOLO GENERAL (respondé directo, sin RAG):
- Consulta: DNI+credencial | Práctica: +orden | Guardia: sin orden | Internación: +presupuesto+denuncia(24hs)

RAG solo para datos de obra social (mail, tel, copagos, requisitos específicos).
- SIEMPRE especificá obra_social. Si no la dijo, preguntá antes.

RESPUESTAS: Saludos→"¡Hola! ¿Con qué obra social necesitás ayuda?" | Despedidas→"¿Necesitás algo más?"

CIERRE: Si el usuario dice "no/nada/gracias/chau", respondé "¡Perfecto! Hasta luego." y marcá conversación como finalizada.

Máx 30 palabras, español, terminá con pregunta breve.
"""

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def generate_response_agent(self, query: str, historial: list = None, rag_callback=None) -> dict:
        pass


class OllamaClient(BaseLLMClient):
    """Cliente para Ollama (LLM local)"""

    def __init__(self, host: str = None, model: str = None):
        super().__init__()
        import ollama
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self.client = ollama.Client(host=self.host)
        self.provider = "ollama"

    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception as e:
            print(f"Ollama no disponible: {e}")
            return False

    def generate_response_agent(self, query: str, historial: list = None, rag_callback=None) -> dict:
        if historial is None:
            historial = []

        messages = [{'role': 'system', 'content': self.system_prompt}]

        for msg in historial[-8:]:
            if hasattr(msg, 'role'):
                messages.append({'role': msg.role, 'content': msg.content})
            else:
                messages.append({'role': msg['role'], 'content': msg['content']})

        messages.append({'role': 'user', 'content': query})

        print(f"   🤖 Llamando a Ollama (modelo: {self.model})...")

        try:
            start = time.time()
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=self.tools,
                options={'temperature': 0.1, 'num_predict': 150}
            )
            elapsed = time.time() - start
            print(f"   ⏱️  Tiempo: {elapsed:.2f}s")

            message = response['message']

            if 'tool_calls' in message and message['tool_calls']:
                tool_call = message['tool_calls'][0]
                function_name = tool_call['function']['name']
                arguments = tool_call['function']['arguments']

                print(f"   🔧 Tool: {function_name}({arguments})")

                if function_name == 'consulta_rag' and rag_callback:
                    obra_social = arguments.get('obra_social')
                    rag_query = arguments.get('query')

                    context = rag_callback(obra_social, rag_query)

                    messages.append(message)
                    messages.append({'role': 'tool', 'content': context})

                    start2 = time.time()
                    response2 = self.client.chat(
                        model=self.model,
                        messages=messages,
                        options={'temperature': 0.1, 'num_predict': 200}
                    )
                    print(f"   ⏱️  Segunda llamada: {time.time() - start2:.2f}s")

                    return {
                        "respuesta": response2['message']['content'],
                        "tool_calls": [{"name": function_name, "arguments": arguments}],
                        "needs_rag": True
                    }

            return {
                "respuesta": message.get('content', ''),
                "tool_calls": [],
                "needs_rag": False
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"respuesta": f"Error: {str(e)}", "tool_calls": [], "needs_rag": False}


class GroqClient(BaseLLMClient):
    """Cliente para Groq (LLM cloud - gratis)"""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__()
        from groq import Groq
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = Groq(api_key=self.api_key)
        self.provider = "groq"

    def is_available(self) -> bool:
        try:
            # Test simple
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"Groq no disponible: {e}")
            return False

    def generate_response_agent(self, query: str, historial: list = None, rag_callback=None) -> dict:
        if historial is None:
            historial = []

        messages = [{'role': 'system', 'content': self.system_prompt}]

        for msg in historial[-8:]:
            if hasattr(msg, 'role'):
                messages.append({'role': msg.role, 'content': msg.content})
            else:
                messages.append({'role': msg['role'], 'content': msg['content']})

        messages.append({'role': 'user', 'content': query})

        print(f"   🤖 Llamando a Groq (modelo: {self.model})...")

        try:
            start = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                max_tokens=150,
                temperature=0.1
            )
            elapsed = time.time() - start
            print(f"   ⏱️  Tiempo: {elapsed:.2f}s")

            message = response.choices[0].message

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print(f"   🔧 Tool: {function_name}({arguments})")

                if function_name == 'consulta_rag' and rag_callback:
                    obra_social = arguments.get('obra_social')
                    rag_query = arguments.get('query')

                    context = rag_callback(obra_social, rag_query)

                    # Agregar tool call y resultado
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments
                            }
                        }]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": context
                    })

                    start2 = time.time()
                    response2 = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=200,
                        temperature=0.1
                    )
                    print(f"   ⏱️  Segunda llamada: {time.time() - start2:.2f}s")

                    return {
                        "respuesta": response2.choices[0].message.content,
                        "tool_calls": [{"name": function_name, "arguments": arguments}],
                        "needs_rag": True
                    }

            return {
                "respuesta": message.content or '',
                "tool_calls": [],
                "needs_rag": False
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"respuesta": f"Error: {str(e)}", "tool_calls": [], "needs_rag": False}


def create_llm_client(provider: str = None) -> BaseLLMClient:
    """
    Factory para crear el cliente LLM según configuración

    Args:
        provider: "ollama" o "groq". Si no se especifica, usa LLM_PROVIDER del .env

    Returns:
        Instancia de OllamaClient o GroqClient
    """
    provider = provider or os.getenv("LLM_PROVIDER", "ollama")

    if provider.lower() == "groq":
        print(f"🌐 Usando Groq (cloud)")
        return GroqClient()
    else:
        print(f"💻 Usando Ollama (local)")
        return OllamaClient()


# Alias para compatibilidad con código existente
def get_default_client() -> BaseLLMClient:
    """Obtiene el cliente según LLM_PROVIDER"""
    return create_llm_client()
