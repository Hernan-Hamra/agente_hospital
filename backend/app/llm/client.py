"""
Cliente para interactuar con Ollama (LLM local)
"""
import ollama
from typing import Optional


class OllamaClient:
    """Cliente para generar respuestas con Ollama"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Args:
            host: URL del servidor Ollama
            model: Nombre del modelo a usar
        """
        self.host = host
        self.model = model
        self.client = ollama.Client(host=host)

    def is_available(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            self.client.list()
            return True
        except Exception as e:
            print(f"Ollama no disponible: {e}")
            return False

    def generate_response(self, query: str, context: str, obra_social: Optional[str] = None) -> str:
        """
        Genera respuesta usando el LLM

        Args:
            query: Pregunta del usuario
            context: Contexto recuperado del RAG
            obra_social: Obra social específica (opcional)

        Returns:
            Respuesta generada
        """
        # Construcción del prompt
        system_prompt = """Eres un asistente administrativo del Grupo Pediátrico (hospital).
Tu rol es ayudar al personal administrativo con consultas sobre enrolamiento de pacientes y procedimientos de obras sociales.

CÓMO RESPONDÉS:
1. Si te preguntan sobre VOS (quién sos, qué hacés, tu función):
   - Siempre saluda al iniciar la conversación
   -Respondé que sos un asistente administrativo del Grupo Pediátrico
   - Explicá que ayudás con enrolamiento de pacientes y consultas sobre obras sociales
   - NO digas "No tengo esa información"

2. Si te preguntan sobre PROCEDIMIENTOS/DOCUMENTACIÓN:
   - Usá SOLO la información del contexto que te paso
   - Si no está en el contexto, decís: "No tengo esa información cargada en mi base de datos"
   - NO inventes requisitos ni procedimientos

3. Si te preguntan algo MÉDICO (diagnósticos, tratamientos, medicación):
   - Respondé: "No puedo ayudarte con consultas médicas. Soy un asistente administrativo."

FORMATO:
- Respondés en español, de forma clara, paso a paso y amablemente.
- Usás formato con viñetas o numeración para mejor lectura
- Hablás de forma simple y directa (el personal administrativo NO es técnico)"""

        user_prompt = f"""Contexto de la base de datos:

{context}

---

Pregunta del administrativo: {query}"""

        if obra_social:
            user_prompt += f"\n\nNOTA: La consulta es específicamente sobre la obra social: {obra_social}"

        user_prompt += """

REGLAS CRÍTICAS ANTES DE RESPONDER:
1. Si el contexto NO tiene relación con la pregunta, NO lo uses - respondé desde tu rol
2. Si te saludan (hola, buen día, etc.) sin consulta específica, presentate brevemente sin inventar información
3. NO inventes nombres de pacientes, fechas, o detalles que no mencione el usuario
4. NO uses fragmentos del contexto que no respondan directamente la pregunta
5. Si el contexto está vacío o irrelevante, solo respondé sobre tu función como asistente

Respondé de forma estructurada siguiendo este formato SOLO cuando corresponda (consultas sobre procedimientos):

📋 Documentación requerida:
[Lista de documentos]

🔄 Pasos a seguir:
1. [Paso 1]
2. [Paso 2]
...

⚠️ Observaciones importantes:
[Información adicional relevante]

📞 Contacto:
[Si hay datos de contacto específicos]"""

        try:
            response = self.client.chat(model=self.model, messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ])

            return response['message']['content']

        except Exception as e:
            return f"Error al generar respuesta: {str(e)}\n\nPor favor verificá que Ollama esté corriendo y el modelo '{self.model}' esté instalado."

    def pull_model(self):
        """Descarga el modelo si no está disponible"""
        try:
            print(f"Descargando modelo {self.model}...")
            self.client.pull(self.model)
            print(f"✅ Modelo {self.model} descargado correctamente")
        except Exception as e:
            print(f"❌ Error descargando modelo: {e}")
