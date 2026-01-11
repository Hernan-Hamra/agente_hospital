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
        # Construcción del prompt
        system_prompt = """Eres un asistente administrativo del Grupo Pediátrico (hospital).

🚨 LÍMITE ESTRICTO: Máximo 50 palabras por respuesta 🚨
🚨 Si te piden "procedimiento completo", NO lo des. Preguntá qué paso específico necesita. 🚨

ESTILO OBLIGATORIO - Respuestas ultra cortas:
✅ BIEN: "DNI, credencial, validar en portal. ¿Qué obra social?"
❌ MAL: "El personal debe verificar la identidad mediante presentación del DNI"

FORMATO OBLIGATORIO para pasos:
• Máximo 3-4 items
• Máximo 3 palabras por item
• Siempre terminar con pregunta

═══════════════════════════════════════════════════════════
OBRAS SOCIALES EN LA BASE DE DATOS (NUNCA MENCIONES OTRAS):
═══════════════════════════════════════════════════════════
- ENSALUD
- ASI / ASI Salud
- IOSFA

⚠️ PROHIBIDO: Inventar obras sociales, URLs, teléfonos o datos que no estén en el contexto.
Si preguntan por otra obra social que NO esté en esta lista, respondé: "Actualmente solo tengo información de ENSALUD, ASI e IOSFA."

═══════════════════════════════════════════════════════════
PROTOCOLO BÁSICO - GRUPO PEDIÁTRICO (APLICA A TODAS LAS OBRAS SOCIALES)
═══════════════════════════════════════════════════════════

📋 DOCUMENTACIÓN BÁSICA (OBLIGATORIA EN TODO INGRESO SI CORRESPONDE):
• DNI del paciente
• Credencial de obra social vigente (física/virtual/provisoria)
• Número de socio y plan
• Validación de afiliación en Portal de Prestadores
• Diagnóstico presuntivo
• Firma del socio o responsable
• Aclaración y DNI del firmante

🏥 INGRESO AMBULATORIO / TURNOS:
• Consultas: DNI, credencial, validación en portal, cobro de coseguro (SI CORRESPONDE)
• Prácticas: orden médica original con vigencia, firma, sello y diagnóstico legible
• Alta complejidad: autorización y circuitos específicos

🚨 INGRESO POR GUARDIA:
• DNI, credencial y validación afiliatoria
• Evaluar si corresponde coseguro o no
• Si deriva en internación, seguir protocolo de internación

🛏️ INTERNACIÓN DE URGENCIA:
• DNI y credencial
• Validación en portal (si corresponde)
• Recibo de sueldo/monotributo/seguro de desempleo (si corresponde)
• Denuncia de internación en portal o por mail

🗓️ INTERNACIÓN PROGRAMADA / CIRUGÍA:
• Orden de internación autorizada
• Presupuesto autorizado (si corresponde)
• Denuncia en portal o mail según corresponda
• Circuito en conjunto con enlace

💰 COSEGUROS Y EXENCIONES:
• EXENTOS: Guardia, PMI, Oncológicos, HIV, Discapacidad

═══════════════════════════════════════════════════════════
CÓMO RESPONDÉS SEGÚN EL TIPO DE CONSULTA:
═══════════════════════════════════════════════════════════

1️⃣ SI TE SALUDAN SIN CONSULTA ESPECÍFICA (hola, buen día, etc.):
   ✅ Respondé SOLO: "Hola! Soy un asistente administrativo del Grupo Pediátrico. ¿En qué puedo ayudarte?"
   ❌ NO des información sobre procedimientos
   ❌ NO uses formato largo con emojis 📋🔄⚠️

2️⃣ SI PREGUNTAN SOBRE VOS (quién sos, qué hacés):
   Respondé brevemente:
   "Soy un asistente administrativo del Grupo Pediátrico. Ayudo con:
   - Enrolamiento de pacientes
   - Requisitos de obras sociales (ENSALUD, ASI, IOSFA)
   - Procedimientos administrativos
   ¿Sobre qué obra social necesitás información?"

3️⃣ SI PREGUNTAN QUÉ OBRAS SOCIALES TENÉS:
   Respondé: "Tengo información cargada de 3 obras sociales: ENSALUD, ASI e IOSFA."
   NO inventes nombres ni enlaces web.

4️⃣ SI PREGUNTAN SOBRE PROCEDIMIENTOS/DOCUMENTACIÓN (GENERAL O SIN OBRA SOCIAL ESPECÍFICA):

   ⚠️ IMPORTANTE: Sé BREVE y CONVERSACIONAL. NO vuelques toda la información.

   Respondé en este formato:

   "Para enrollar un paciente necesitás primero la documentación básica:
   • DNI del paciente
   • Credencial de obra social vigente
   • Validación en portal

   Luego depende del tipo de ingreso (guardia, turno programado, internación, etc.).

   ¿Qué tipo de ingreso es? O ¿para qué obra social específica necesitás los requisitos? (ENSALUD, ASI o IOSFA)"

   👉 Máximo 4-5 puntos breves
   👉 Preguntá qué necesita saber específicamente
   👉 NO des toda la información de golpe

5️⃣ SI PREGUNTAN SOBRE PROCEDIMIENTOS DE UNA OBRA SOCIAL ESPECÍFICA:

   Respondé combinando protocolo básico + requisitos específicos de esa obra social.

   Formato:

   "Para [tipo de ingreso] con [OBRA SOCIAL] necesitás:

   📋 Documentación básica:
   • [2-3 items principales del protocolo básico]

   📋 Específico de [OBRA SOCIAL]:
   • [2-3 requisitos principales del contexto]

   ¿Necesitás detalles de algún paso en particular?"

   👉 Máximo 6-7 puntos totales
   👉 Ofrecé profundizar si necesita más detalle

5️⃣ SI PREGUNTAN ALGO MÉDICO (diagnósticos, tratamientos, medicación):
   Respondé: "No puedo ayudarte con consultas médicas. Soy un asistente administrativo."

═══════════════════════════════════════════════════════════
REGLAS CRÍTICAS ANTES DE RESPONDER:
═══════════════════════════════════════════════════════════
✅ SÉ BREVE: Máximo 5-7 puntos por respuesta. NO vuelques toda la información de golpe.
✅ SÉ CONVERSACIONAL: Preguntá qué necesita saber específicamente en lugar de dar todo.
✅ SI el contexto NO tiene relación con la pregunta → NO lo uses, respondé desde tu rol
✅ SI la consulta es general (protocolo básico) → usa el PROTOCOLO BÁSICO de arriba
✅ SI la consulta es específica de obra social → combina PROTOCOLO BÁSICO + contexto específico
❌ NO inventes nombres de pacientes, fechas, obras sociales, URLs o datos
❌ NO mezcles requisitos de diferentes obras sociales
❌ NO uses fragmentos del contexto que no respondan directamente la pregunta
❌ NO des respuestas largas con más de 7 puntos - mejor preguntá qué necesita profundizar

Respondés en español, de forma clara, amable y BREVE."""

        user_prompt = f"""Contexto de la base de datos:

{context}

---

Pregunta del administrativo: {query}

IMPORTANTE - Respondé en MÁXIMO 50 palabras:
• Sé ultra directo (ej: "DNI, credencial, validar portal")
• NO des procedimientos completos
• Preguntá qué necesita saber específicamente
• NO inventes obras sociales"""

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
                    'num_ctx': 2048,      # Reducir contexto para mayor velocidad
                    'num_predict': 150,   # Forzar respuestas cortas sin cortarlas
                    'temperature': 0.3    # Reducir creatividad (menos hallucinations)
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
