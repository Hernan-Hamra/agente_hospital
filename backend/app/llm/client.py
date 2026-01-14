"""
Cliente para interactuar con Ollama (LLM local)
"""
import ollama
import time
from typing import Optional


class OllamaClient:
    """Cliente para generar respuestas con Ollama"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        """
        Args:
            host: URL del servidor Ollama
            model: Nombre del modelo a usar (qwen2.5:3b para function calling)
        """
        self.host = host
        self.model = model
        self.client = ollama.Client(host=host)

        # Definir herramientas disponibles para el agente
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "consulta_rag",
                    "description": "Busca información específica en los documentos de obras sociales (ENSALUD, ASI, IOSFA). Usa esta herramienta cuando necesites requisitos, procedimientos o información detallada de una obra social específica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "obra_social": {
                                "type": "string",
                                "description": "La obra social sobre la que buscar (ENSALUD, ASI o IOSFA)",
                                "enum": ["ENSALUD", "ASI", "IOSFA"]
                            },
                            "query": {
                                "type": "string",
                                "description": "La consulta específica (ej: 'requisitos internación', 'autorizaciones cirugía')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def is_available(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            self.client.list()
            return True
        except Exception as e:
            print(f"Ollama no disponible: {e}")
            return False

    def generate_response(self, query: str, context: str, obra_social: Optional[str] = None, historial: list = None) -> str:
        """
        Genera respuesta usando el LLM

        Args:
            query: Pregunta del usuario
            context: Contexto recuperado del RAG
            obra_social: Obra social específica (opcional)
            historial: Lista de mensajes previos [{"role": "user/assistant", "content": "..."}]

        Returns:
            Respuesta generada
        """
        if historial is None:
            historial = []
        # Construcción del prompt - OPTIMIZADO (40 líneas, 10 casos de uso)
        system_prompt = """Asistente Grupo Pediátrico - Enrolamiento

🔴 REGLAS OBLIGATORIAS:

1. SALUDOS: Solo PRIMERA vez → "Hola! Soy un asistente del Grupo Pediátrico. ¿En qué puedo ayudarte?"
   Si ya saludaste → no repitas saludo | ⚠️ En saludos → IGNORA contexto RAG

2. DESPEDIDAS: "Gracias"/"Chau" → "De nada! ¿Algo más?" o "Hasta luego!"

3. AMBIGÜEDAD: Falta info → preguntá (ej: "¿Y el teléfono?" → "¿De qué obra social?")

4. FUERA DE SCOPE: Clima/deportes/noticias → "Solo respondo enrolamiento del Grupo Pediátrico. ¿En qué puedo ayudarte?"

5. BREVEDAD: Máximo 50 palabras. Terminá SIEMPRE con pregunta.

6. MÚLTIPLES OBRAS SOCIALES: "¿ASI e IOSFA?" → "Preguntá una obra social a la vez. ¿Cuál primero?"

7. CAMBIO DE TEMA: Si el usuario cambia de obra social → adaptate sin confusión

8. USUARIO INCORRECTO: Si dice algo mal → corregí con amabilidad

9. SOBRE EL BOT: "¿Cómo funcionás?" → "Soy asistente del Grupo Pediátrico para enrolamiento de ENSALUD/ASI/IOSFA. ¿Qué necesitás?"

10. PIDE HUMANO: "Quiero hablar con persona" → "Puedo ayudarte con enrolamiento. ¿Qué necesitás?"

🏥 OBRAS SOCIALES: ENSALUD, ASI, IOSFA

📋 PROTOCOLO:
• Consulta: DNI + credencial + validar
• Práctica: Lo anterior + orden autorizada
• Internación: Orden + presupuesto + denuncia
• Guardia: DNI + credencial (sin orden)

⚠️ USO CONTEXTO:
- Si responde la pregunta → úsalo COMPLETO
- Si NO responde → ignóralo
- Saludo/despedida/fuera scope → ignora contexto

❌ PROHIBIDO:
- Inventar errores pasados ("confusiones anteriores")
- Solo disculpate si usuario corrige error REAL
- Inventar datos no en contexto
- Volver a saludar
- Responder ambigüedades sin clarificar

Español, claro, amable."""

        user_prompt = f"""Contexto disponible:

{context}

---

Pregunta: {query}

INSTRUCCIONES:
1. USA toda la información relevante del contexto
2. Combiná documentación básica + requisitos específicos
3. Máximo 40 palabras pero SIN OMITIR requisitos importantes
4. Terminá siempre con pregunta para guiar al usuario
5. Si el contexto no responde la pregunta, decilo claramente"""

        if obra_social:
            user_prompt += f"\n\nNOTA: La consulta es específicamente sobre la obra social: {obra_social}"

        try:
            # Construir lista de mensajes incluyendo historial
            messages = [{'role': 'system', 'content': system_prompt}]

            # Agregar historial conversacional (sin incluir el último mensaje del usuario)
            # Filtramos los últimos 8 mensajes (4 pares user+assistant) para no sobrecargar
            for msg in historial[-8:]:
                # Convertir mensaje (puede ser dict o Pydantic model)
                if hasattr(msg, 'role'):  # Es un objeto Pydantic
                    msg_role = msg.role
                    msg_content = msg.content
                else:  # Es un dict
                    msg_role = msg['role']
                    msg_content = msg['content']

                # No incluir el último mensaje del usuario (ya está en user_prompt)
                if msg_role == 'user' and msg_content == query:
                    continue
                messages.append({'role': msg_role, 'content': msg_content})

            # Agregar pregunta actual
            messages.append({'role': 'user', 'content': user_prompt})

            print(f"   🤖 Llamando a Ollama (modelo: {self.model})...")
            print(f"   📊 Historial: {len(historial)} mensajes")
            print(f"   📊 Context window: 2048 tokens")

            start_ollama = time.time()
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'num_ctx': 2048,       # Contexto suficiente para RAG
                    'num_predict': 120,    # ~50 palabras máximo para respuestas completas
                    'temperature': 0.1,    # Muy determinista = más rápido y preciso
                    'top_k': 20,           # Limitar opciones = más rápido
                    'top_p': 0.8,          # Nucleus sampling conservador
                    'repeat_penalty': 1.2, # Evitar repeticiones
                    'num_thread': 4        # Paralelizar si tiene CPU multicore
                }
            )
            time_ollama = time.time() - start_ollama

            print(f"   ⏱️  Tiempo de inferencia Ollama: {time_ollama:.3f}s")
            print(f"   📝 Longitud de respuesta: {len(response['message']['content'])} caracteres")

            return response['message']['content']

        except Exception as e:
            return f"Error al generar respuesta: {str(e)}\n\nPor favor verificá que Ollama esté corriendo y el modelo '{self.model}' esté instalado."

    def generate_response_agent(self, query: str, historial: list = None, rag_callback=None) -> dict:
        """
        Genera respuesta usando el agente con function calling

        Args:
            query: Pregunta del usuario
            historial: Lista de mensajes previos
            rag_callback: Función callback para ejecutar consulta_rag(obra_social, query)

        Returns:
            dict con {"respuesta": str, "tool_calls": list, "needs_rag": bool}
        """
        if historial is None:
            historial = []

        # System prompt para el agente
        system_prompt = """Asistente Grupo Pediátrico.

PROTOCOLO BÁSICO:
DNI, credencial, validar, firma, diagnóstico.

TIPOS INGRESO:
• Guardia: DNI + credencial (NO orden)
• Turno: orden + DNI + credencial
• Internación: orden autorizada + presupuesto

OBRAS SOCIALES: ENSALUD, ASI, IOSFA
Otra obra social → "No tengo [X]. Solo ENSALUD/ASI/IOSFA"

🚨 REGLAS CRÍTICAS:
1. MÁXIMO 15 PALABRAS - si te pasás, el sistema falla
2. SI NO SABÉS ALGO → USA consulta_rag OBLIGATORIO
3. NUNCA inventes info (copagos, montos, especialidades)
4. Si no está en tus herramientas → "No tengo esa info. ¿Necesitás otra cosa?"
5. Terminá SIEMPRE con pregunta

🔧 USA consulta_rag cuando:
- Preguntan detalles de ENSALUD/ASI/IOSFA (circuitos, autorizaciones, requisitos)
- Preguntan info que NO es protocolo básico
- Cualquier duda → mejor consultar RAG que inventar

EJEMPLOS CORRECTOS:
User: "protocolo básico"
Bot: DNI, credencial, validar. ¿Qué tipo ingreso?

User: "guardia"
Bot: Guardia: DNI + credencial. ¿Obra social?

User: "cuánto es copago dermatología"
Bot: [USA consulta_rag porque no sabés] → Si RAG no tiene info → No tengo esa info. ¿Algo más?

User: "osde"
Bot: No tengo OSDE. Solo ENSALUD/ASI/IOSFA
"""

        # Construir mensajes
        messages = [{'role': 'system', 'content': system_prompt}]

        # Agregar historial
        for msg in historial[-8:]:
            if hasattr(msg, 'role'):
                msg_role = msg.role
                msg_content = msg.content
            else:
                msg_role = msg['role']
                msg_content = msg['content']
            messages.append({'role': msg_role, 'content': msg_content})

        # Agregar pregunta actual
        messages.append({'role': 'user', 'content': query})

        print(f"   🤖 Llamando a Ollama AGENTE (modelo: {self.model})...")
        print(f"   📊 Historial: {len(historial)} mensajes")

        try:
            start = time.time()
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=self.tools,
                options={
                    'temperature': 0.1,  # Más determinista
                    'num_predict': 40  # Forzar 15 palabras máximo (~3 tokens por palabra)
                }
            )
            elapsed = time.time() - start

            print(f"   ⏱️  Tiempo de inferencia: {elapsed:.3f}s")

            message = response['message']

            # Verificar si hay tool calls
            if 'tool_calls' in message and message['tool_calls']:
                tool_call = message['tool_calls'][0]
                function_name = tool_call['function']['name']
                arguments = tool_call['function']['arguments']

                print(f"   🔧 Tool call: {function_name}({arguments})")

                # Si hay callback para RAG, ejecutarlo
                if function_name == 'consulta_rag' and rag_callback:
                    obra_social = arguments.get('obra_social')
                    rag_query = arguments.get('query')

                    # Ejecutar RAG
                    print(f"   📚 Ejecutando RAG: obra_social={obra_social}, query={rag_query}")
                    context = rag_callback(obra_social, rag_query)

                    # Llamar de nuevo al LLM con el resultado
                    messages.append(message)
                    messages.append({
                        'role': 'tool',
                        'content': context
                    })

                    # Segunda llamada
                    print(f"   🤖 Segunda llamada con resultado de RAG...")
                    start2 = time.time()
                    response2 = self.client.chat(
                        model=self.model,
                        messages=messages,
                        options={
                            'temperature': 0.1,
                            'num_predict': 200  # Respuestas completas después de RAG
                        }
                    )
                    elapsed2 = time.time() - start2
                    print(f"   ⏱️  Tiempo segunda llamada: {elapsed2:.3f}s")

                    return {
                        "respuesta": response2['message']['content'],
                        "tool_calls": [tool_call],
                        "needs_rag": True
                    }

                return {
                    "respuesta": f"[Herramienta {function_name} requerida pero no disponible]",
                    "tool_calls": [tool_call],
                    "needs_rag": True
                }
            else:
                # No necesita herramientas, respuesta directa
                return {
                    "respuesta": message['content'],
                    "tool_calls": [],
                    "needs_rag": False
                }

        except Exception as e:
            print(f"   ❌ Error en agente: {e}")
            return {
                "respuesta": f"Error: {str(e)}",
                "tool_calls": [],
                "needs_rag": False
            }

    def pull_model(self):
        """Descarga el modelo si no está disponible"""
        try:
            print(f"Descargando modelo {self.model}...")
            self.client.pull(self.model)
            print(f"✅ Modelo {self.model} descargado correctamente")
        except Exception as e:
            print(f"❌ Error descargando modelo: {e}")
