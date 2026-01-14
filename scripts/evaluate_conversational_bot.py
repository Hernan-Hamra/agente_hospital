#!/usr/bin/env python3
"""
Evaluación Conversacional Completa del Bot Hospitalario
Simula conversaciones reales de enroladores con métricas detalladas
"""
import sys
import os
from pathlib import Path
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np

# Agregar backend al path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from app.rag.indexer import DocumentIndexer
from app.rag.retriever import DocumentRetriever
from app.llm.client import OllamaClient
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = backend_path / ".env"
load_dotenv(env_path)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


def convert_to_native_types(obj):
    """Convierte numpy types a Python natives para JSON serialization"""
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    else:
        return obj


# ============================================================================
# CONVERSACIONES DE PRUEBA
# ============================================================================

CONVERSACIONES = [
    {
        "nombre": "Usuario Nuevo - Primer Contacto",
        "contexto": "Enrolador que nunca usó el sistema",
        "preguntas": [
            {
                "id": 1,
                "tipo": "saludo_inicial",
                "pregunta": "Hola",
                "evaluacion": {
                    "debe_incluir": ["hola", "bienvenid", "ayud"],
                    "debe_saludar": True,
                    "debe_ofrecer_ayuda": True,
                    "max_palabras": 25
                }
            },
            {
                "id": 2,
                "tipo": "consulta_basica",
                "pregunta": "¿Qué documentos necesito para una consulta en IOSFA?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["VALIDADOR", "DNI", "BONO"],
                    "no_debe_incluir": ["AUTORIZACION"],
                    "max_palabras": 20
                }
            },
            {
                "id": 3,
                "tipo": "pregunta_seguimiento",
                "pregunta": "¿Y para prácticas?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["VALIDADOR", "DNI", "BONO", "AUTORIZACION"],
                    "debe_mantener_contexto": True,
                    "max_palabras": 25
                }
            },
            {
                "id": 4,
                "tipo": "pregunta_ambigua",
                "pregunta": "¿Y el teléfono?",
                "evaluacion": {
                    "debe_reppreguntar": True,
                    "frases_esperadas": ["teléfono de qué", "qué teléfono", "de quién"]
                }
            },
            {
                "id": 5,
                "tipo": "consulta_tabla",
                "pregunta": "Dame el mail de Mesa Operativa de ASI",
                "obra_social": "ASI",
                "evaluacion": {
                    "debe_incluir": ["autorizaciones@asi.com.ar"],
                    "max_palabras": 15,
                    "es_tabla": True
                }
            },
            {
                "id": 6,
                "tipo": "pregunta_compleja",
                "pregunta": "¿Cuál es la diferencia entre guardia y turno en IOSFA?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["guardia", "DNI", "VALIDADOR"],
                    "max_palabras": 40
                }
            },
            {
                "id": 7,
                "tipo": "consulta_out_of_scope",
                "pregunta": "¿Cuál es el clima hoy?",
                "evaluacion": {
                    "debe_rechazar": True,
                    "frases_esperadas": ["no tengo", "solo puedo", "obras sociales"]
                }
            },
            {
                "id": 8,
                "tipo": "consulta_multiobra",
                "pregunta": "¿Cuál es el mail de contacto de ASI y de ENSALUD?",
                "evaluacion": {
                    "debe_incluir": ["autorizaciones@asi.com.ar"],
                    "debe_mencionar": ["ASI", "ENSALUD"],
                    "max_palabras": 50
                }
            },
            {
                "id": 9,
                "tipo": "reformulacion",
                "pregunta": "No entendí, ¿podés explicarme mejor los requisitos de IOSFA para prácticas?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_reformular": True,
                    "debe_incluir": ["AUTORIZACION"],
                    "max_palabras": 30
                }
            },
            {
                "id": 10,
                "tipo": "despedida",
                "pregunta": "Gracias, eso es todo",
                "evaluacion": {
                    "debe_despedirse": True,
                    "frases_esperadas": ["de nada", "para servirte", "ayuda"]
                }
            }
        ]
    },
    {
        "nombre": "Usuario Avanzado - Consultas Complejas",
        "contexto": "Enrolador experimentado con consultas específicas",
        "preguntas": [
            {
                "id": 1,
                "tipo": "consulta_directa",
                "pregunta": "Requisitos internación programada IOSFA",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["DNI", "VALIDADOR", "AUTORIZADA"],
                    "max_palabras": 30
                }
            },
            {
                "id": 2,
                "tipo": "consulta_tabla_especifica",
                "pregunta": "Copago de consulta médica en ENSALUD",
                "obra_social": "ENSALUD",
                "evaluacion": {
                    "debe_incluir": ["500", "2000"],
                    "es_tabla": True,
                    "max_palabras": 20
                }
            },
            {
                "id": 3,
                "tipo": "comparacion",
                "pregunta": "¿Qué diferencia hay entre documentación de consulta en ASI e IOSFA?",
                "evaluacion": {
                    "debe_comparar": True,
                    "debe_mencionar": ["ASI", "IOSFA"],
                    "max_palabras": 60
                }
            },
            {
                "id": 4,
                "tipo": "consulta_negativa",
                "pregunta": "¿Necesito autorización para consulta en IOSFA?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["no", "sin"],
                    "no_debe_incluir": ["sí", "requiere autorización"]
                }
            },
            {
                "id": 5,
                "tipo": "consulta_contactos",
                "pregunta": "Dame todos los contactos de ASI",
                "obra_social": "ASI",
                "evaluacion": {
                    "debe_incluir": ["autorizaciones@asi.com.ar", "0810"],
                    "es_tabla": True
                }
            },
            {
                "id": 6,
                "tipo": "pregunta_con_typo",
                "pregunta": "Documentacion IOFSA consulta",
                "evaluacion": {
                    "debe_tolerar_typo": True,
                    "debe_incluir": ["VALIDADOR", "DNI"]
                }
            },
            {
                "id": 7,
                "tipo": "consulta_secuencial",
                "pregunta": "Ahora dame lo mismo pero para ENSALUD",
                "obra_social": "ENSALUD",
                "evaluacion": {
                    "debe_mantener_contexto": True
                }
            },
            {
                "id": 8,
                "tipo": "validacion",
                "pregunta": "¿Estás seguro que el copago de ENSALUD es $500?",
                "obra_social": "ENSALUD",
                "evaluacion": {
                    "debe_confirmar": True,
                    "frases_esperadas": ["sí", "correcto", "tabla"]
                }
            },
            {
                "id": 9,
                "tipo": "caso_edge",
                "pregunta": "¿Qué pasa si no tengo el VALIDADOR en IOSFA?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["obligatorio", "requerido", "necesario"]
                }
            },
            {
                "id": 10,
                "tipo": "multiatributo",
                "pregunta": "Dame mail, teléfono y horarios de ASI",
                "obra_social": "ASI",
                "evaluacion": {
                    "debe_incluir": ["autorizaciones@asi.com.ar"],
                    "debe_mencionar_que_falta": True  # No tenemos horarios
                }
            }
        ]
    },
    {
        "nombre": "Flujo Completo - Enrolamiento Real",
        "contexto": "Simulación paso a paso de enrolamiento",
        "preguntas": [
            {
                "id": 1,
                "tipo": "inicio_flujo",
                "pregunta": "Hola, necesito enrolar un paciente de IOSFA que viene a consulta",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_guiar": True,
                    "max_palabras": 30
                }
            },
            {
                "id": 2,
                "tipo": "confirmacion_doc",
                "pregunta": "¿Qué documentos le pido?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["VALIDADOR", "DNI", "BONO"],
                    "max_palabras": 20
                }
            },
            {
                "id": 3,
                "tipo": "problema",
                "pregunta": "El paciente no tiene el validador",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_orientar": True,
                    "frases_esperadas": ["obligatorio", "necesario"]
                }
            },
            {
                "id": 4,
                "tipo": "cambio_tipo",
                "pregunta": "Ah, en realidad viene a una práctica, no consulta",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_actualizar": True,
                    "debe_incluir": ["AUTORIZACION"]
                }
            },
            {
                "id": 5,
                "tipo": "consulta_proceso",
                "pregunta": "¿Dónde verifico si tiene autorización?",
                "obra_social": "IOSFA",
                "evaluacion": {
                    "debe_incluir": ["DRIVE", "ENLACE"]
                }
            },
            {
                "id": 6,
                "tipo": "cambio_obra",
                "pregunta": "Ahora tengo un paciente de ASI, ¿qué necesito?",
                "obra_social": "ASI",
                "evaluacion": {
                    "debe_cambiar_contexto": True,
                    "debe_preguntar": True
                }
            },
            {
                "id": 7,
                "tipo": "contacto_urgente",
                "pregunta": "Necesito llamar a ASI, ¿cuál es el teléfono?",
                "obra_social": "ASI",
                "evaluacion": {
                    "debe_incluir": ["0810"],
                    "max_palabras": 15
                }
            },
            {
                "id": 8,
                "tipo": "multiples_pacientes",
                "pregunta": "Ahora tengo 3 pacientes de ENSALUD, ¿hay copagos?",
                "obra_social": "ENSALUD",
                "evaluacion": {
                    "debe_incluir": ["copago", "500"]
                }
            },
            {
                "id": 9,
                "tipo": "urgencia",
                "pregunta": "Es urgente, ¿puedo atender sin todos los papeles?",
                "evaluacion": {
                    "debe_ser_claro": True,
                    "no_debe_inventar": True
                }
            },
            {
                "id": 10,
                "tipo": "cierre",
                "pregunta": "Perfecto, gracias por todo",
                "evaluacion": {
                    "debe_despedirse": True,
                    "tono": "profesional"
                }
            }
        ]
    }
]


# ============================================================================
# FUNCIONES DE EVALUACIÓN
# ============================================================================

def evaluar_pregunta(pregunta_data: dict, respuesta: str, tiempo_rag: float,
                     tiempo_llm: float, chunks_rag: List) -> dict:
    """
    Evalúa una pregunta individual con métricas detalladas

    Returns:
        dict con puntajes y detalles
    """
    evaluacion = pregunta_data.get("evaluacion", {})
    respuesta_upper = respuesta.upper()

    # Inicializar scores
    scores = {
        "precision": 0,
        "completitud": 0,
        "concision": 0,
        "habilidades_conv": 0,
        "performance": 0
    }

    detalles = {
        "terminos_encontrados": [],
        "terminos_faltantes": [],
        "palabras": len(respuesta.split()),
        "tiempo_total": tiempo_rag + tiempo_llm,
        "chunks_usados": len(chunks_rag)
    }

    # === 1. PRECISIÓN (25 pts) ===
    if "debe_incluir" in evaluacion:
        total_terminos = len(evaluacion["debe_incluir"])
        encontrados = []
        faltantes = []

        for termino in evaluacion["debe_incluir"]:
            if termino.upper() in respuesta_upper:
                encontrados.append(termino)
            else:
                faltantes.append(termino)

        scores["precision"] = (len(encontrados) / total_terminos) * 25 if total_terminos > 0 else 25
        detalles["terminos_encontrados"] = encontrados
        detalles["terminos_faltantes"] = faltantes
    else:
        scores["precision"] = 25  # No aplica

    # Verificar que NO incluya términos prohibidos
    if "no_debe_incluir" in evaluacion:
        errores = [t for t in evaluacion["no_debe_incluir"] if t.upper() in respuesta_upper]
        if errores:
            scores["precision"] -= 10
            detalles["errores"] = errores

    # === 2. COMPLETITUD (20 pts) ===
    if "debe_incluir" in evaluacion:
        scores["completitud"] = (len(encontrados) / total_terminos) * 20 if total_terminos > 0 else 20
    else:
        scores["completitud"] = 20

    # === 3. CONCISIÓN (15 pts) ===
    max_palabras = evaluacion.get("max_palabras", 50)
    palabras = len(respuesta.split())

    if palabras <= max_palabras:
        scores["concision"] = 15
    elif palabras <= max_palabras * 1.5:
        scores["concision"] = 8
    else:
        scores["concision"] = 0

    # === 4. HABILIDADES CONVERSACIONALES (30 pts) ===
    hab_score = 0
    detalles["habilidades"] = {}

    # Saludo (si aplica)
    if evaluacion.get("debe_saludar"):
        saludo_ok = any(s in respuesta_upper for s in ["HOLA", "BIENVENID", "BUENOS"])
        hab_score += 6 if saludo_ok else 0
        detalles["habilidades"]["saludo"] = saludo_ok

    # Ofrecer ayuda
    if evaluacion.get("debe_ofrecer_ayuda"):
        ayuda_ok = any(s in respuesta_upper for s in ["AYUD", "PUEDO", "NECESIT"])
        hab_score += 6 if ayuda_ok else 0
        detalles["habilidades"]["ofrece_ayuda"] = ayuda_ok

    # Repregunta cuando es ambiguo
    if evaluacion.get("debe_reppreguntar"):
        repregunta_ok = "?" in respuesta
        hab_score += 6 if repregunta_ok else 0
        detalles["habilidades"]["repregunta"] = repregunta_ok

    # Despedida
    if evaluacion.get("debe_despedirse"):
        despedida_ok = any(s in respuesta_upper for s in ["GRACIAS", "NADA", "SERVIR"])
        hab_score += 6 if despedida_ok else 0
        detalles["habilidades"]["despedida"] = despedida_ok

    # Rechazar consultas fuera de alcance
    if evaluacion.get("debe_rechazar"):
        rechaza_ok = any(s in respuesta_upper for s in ["NO TENGO", "NO PUEDO", "SOLO PUEDO"])
        hab_score += 6 if rechaza_ok else 0
        detalles["habilidades"]["rechaza_out_of_scope"] = rechaza_ok

    scores["habilidades_conv"] = min(hab_score, 30)

    # === 5. PERFORMANCE (10 pts) ===
    tiempo_total = tiempo_rag + tiempo_llm

    if tiempo_total < 8:
        scores["performance"] = 10
    elif tiempo_total < 12:
        scores["performance"] = 7
    else:
        scores["performance"] = 5

    # === PUNTAJE TOTAL ===
    puntaje_total = sum(scores.values())

    return {
        "puntaje_total": round(puntaje_total, 1),
        "scores": scores,
        "detalles": detalles,
        "aprobado": puntaje_total >= 70
    }


# Continúa en el siguiente bloque...

def leer_documento_original(archivo_path: Path) -> str:
    """
    Lee el documento original (PDF o DOCX) para comparación
    """
    try:
        if archivo_path.suffix.lower() == '.pdf':
            import pdfplumber
            texto_partes = []
            with pdfplumber.open(archivo_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texto_partes.append(text.strip())
            return "\n\n".join(texto_partes[:2])  # Primeras 2 páginas

        elif archivo_path.suffix.lower() == '.docx':
            from docx import Document
            doc = Document(archivo_path)
            parrafos = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return "\n".join(parrafos[:10])  # Primeros 10 párrafos

    except Exception as e:
        return f"[Error leyendo documento: {e}]"

    return "[Documento no encontrado]"


def obtener_json_intermedio(chunk_metadata: dict, project_root: Path) -> dict:
    """
    Obtiene el JSON intermedio correspondiente al chunk
    """
    obra_social = chunk_metadata.get("obra_social", "").lower()
    archivo = chunk_metadata.get("archivo", "")
    archivo_base = Path(archivo).stem

    # Buscar JSON intermedio
    intermedio_path = project_root / "data" / "obras_sociales_json" / obra_social / f"{archivo_base}_INTERMEDIO.json"

    if intermedio_path.exists():
        try:
            with open(intermedio_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    return None


def comparar_documentos(chunk_text: str, chunk_metadata: dict, project_root: Path) -> dict:
    """
    Compara el chunk con el documento original y el JSON intermedio
    """
    obra_social = chunk_metadata.get("obra_social", "").lower()
    archivo = chunk_metadata.get("archivo", "")

    # Ruta al documento original
    doc_original_path = project_root / "data" / "obras_sociales" / obra_social / archivo

    # Obtener texto original
    texto_original = leer_documento_original(doc_original_path)

    # Obtener JSON intermedio
    json_intermedio = obtener_json_intermedio(chunk_metadata, project_root)

    # Comparación
    comparacion = {
        "archivo_original": str(doc_original_path),
        "texto_original_preview": texto_original[:500] if texto_original else "[No disponible]",
        "json_intermedio_disponible": json_intermedio is not None,
        "chunk_preserva_info": True,  # Simplificado por ahora
        "es_tabla": chunk_metadata.get("es_tabla", False),
        "tabla_numero": chunk_metadata.get("tabla_numero"),
        "pagina": chunk_metadata.get("pagina")
    }

    if json_intermedio:
        comparacion["json_intermedio_preview"] = str(json_intermedio)[:500]

    return comparacion


# ============================================================================
# EJECUTOR PRINCIPAL
# ============================================================================

def ejecutar_evaluacion_conversacional():
    """
    Ejecuta la evaluación conversacional completa
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_filename = f"conversational_evaluation_{timestamp}.txt"
    report_path = project_root / "reports" / report_filename

    print("\n" + "="*80)
    print("🏥 EVALUACIÓN CONVERSACIONAL COMPLETA - AGENTE HOSPITALARIO")
    print("="*80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Modelo LLM: {OLLAMA_MODEL}")
    print(f"🔍 Modelo Embeddings: {EMBEDDING_MODEL}")
    print(f"💬 Conversaciones: {len(CONVERSACIONES)}")
    print(f"📊 Total preguntas: {sum(len(c['preguntas']) for c in CONVERSACIONES)}")
    print("="*80 + "\n")

    # Cargar RAG
    print("📚 Cargando sistema RAG...")
    indexer = DocumentIndexer(embedding_model=EMBEDDING_MODEL)
    index_path = backend_path / "faiss_index"
    indexer.load_index(str(index_path))
    retriever = DocumentRetriever(indexer, embedding_model=EMBEDDING_MODEL)
    print(f"✅ Índice cargado: {len(indexer.documents)} chunks\n")

    # Inicializar LLM
    print("🤖 Inicializando LLM...")
    llm_client = OllamaClient(model=OLLAMA_MODEL)
    print("✅ LLM listo\n")

    # Resultados globales
    todas_evaluaciones = []
    metricas_globales = {
        "precision": [],
        "completitud": [],
        "concision": [],
        "habilidades_conv": [],
        "performance": [],
        "tiempos_rag": [],
        "tiempos_llm": []
    }

    # Procesar cada conversación
    for idx_conv, conversacion in enumerate(CONVERSACIONES, 1):
        print("\n" + "="*80)
        print(f"💬 CONVERSACIÓN {idx_conv}/{len(CONVERSACIONES)}: {conversacion['nombre']}")
        print("="*80)
        print(f"Contexto: {conversacion['contexto']}\n")

        resultados_conv = []
        historial = []  # Historial de la conversación

        for idx_preg, pregunta_data in enumerate(conversacion['preguntas'], 1):
            print(f"─" * 80)
            print(f"Pregunta {idx_preg}/10: {pregunta_data['pregunta']}")

            # === EJECUTAR RAG ===
            start_rag = time.time()
            obra_social_filter = pregunta_data.get("obra_social")

            try:
                chunks = retriever.retrieve(
                    query=pregunta_data['pregunta'],
                    top_k=3,
                    obra_social_filter=obra_social_filter
                )
            except Exception as e:
                print(f"❌ Error en RAG: {e}")
                chunks = []

            tiempo_rag = (time.time() - start_rag) * 1000

            # Obtener contexto
            if chunks:
                context_parts = []
                for chunk_text, metadata, score in chunks:
                    context_parts.append(f"[Fuente: {metadata['obra_social']}]\n{chunk_text}")
                context = "\n\n".join(context_parts)
            else:
                context = "No se encontró información relevante."

            # === EJECUTAR LLM ===
            start_llm = time.time()

            # Prompt mejorado
            system_prompt = """Eres un asistente hospitalario para enroladores. 
Reglas:
- Responde de forma BREVE y PRECISA
- Máximo 20 palabras si es posible
- Si la pregunta es ambigua, pide clarificación
- Saluda cuando te saluden
- Despídete cuando te despidan
- Solo usa información del contexto proporcionado
- Si no sabes algo, dilo claramente"""

            user_prompt = f"""Contexto disponible:
{context}

Pregunta del usuario: {pregunta_data['pregunta']}

Responde de forma clara y concisa:"""

            try:
                respuesta = llm_client.generate_response(
                    query=pregunta_data['pregunta'],
                    context=context,
                    obra_social=obra_social_filter,
                    historial=historial  # CON historial para mantener contexto conversacional
                )
            except Exception as e:
                respuesta = f"[Error en LLM: {e}]"

            tiempo_llm = (time.time() - start_llm) * 1000

            print(f"⏱️  RAG: {tiempo_rag:.0f}ms | LLM: {tiempo_llm:.0f}ms | Total: {(tiempo_rag + tiempo_llm):.0f}ms")
            print(f"💬 Respuesta ({len(respuesta.split())} palabras): {respuesta[:100]}...")

            # === EVALUAR ===
            evaluacion = evaluar_pregunta(
                pregunta_data,
                respuesta,
                tiempo_rag,
                tiempo_llm,
                chunks
            )

            print(f"📊 Puntaje: {evaluacion['puntaje_total']}/100")

            # === COMPARAR CON ORIGINALES ===
            comparaciones = []
            if chunks:
                for chunk_text, metadata, score in chunks[:1]:  # Solo el top chunk
                    comp = comparar_documentos(chunk_text, metadata, project_root)
                    comparaciones.append(comp)

            # Guardar resultado
            resultado = {
                "conversacion": conversacion['nombre'],
                "pregunta_num": idx_preg,
                "pregunta_data": pregunta_data,
                "respuesta": respuesta,
                "evaluacion": evaluacion,
                "tiempos": {
                    "rag_ms": tiempo_rag,
                    "llm_ms": tiempo_llm,
                    "total_ms": tiempo_rag + tiempo_llm
                },
                "chunks_rag": [
                    {
                        "texto": chunk_text[:200],
                        "metadata": metadata,
                        "similarity": score
                    }
                    for chunk_text, metadata, score in chunks
                ],
                "comparaciones": comparaciones
            }

            resultados_conv.append(resultado)
            todas_evaluaciones.append(resultado)

            # Actualizar métricas globales
            metricas_globales["precision"].append(evaluacion['scores']['precision'])
            metricas_globales["completitud"].append(evaluacion['scores']['completitud'])
            metricas_globales["concision"].append(evaluacion['scores']['concision'])
            metricas_globales["habilidades_conv"].append(evaluacion['scores']['habilidades_conv'])
            metricas_globales["performance"].append(evaluacion['scores']['performance'])
            metricas_globales["tiempos_rag"].append(tiempo_rag)
            metricas_globales["tiempos_llm"].append(tiempo_llm)

            # Agregar al historial (formato correcto para generate_response)
            historial.append({
                "role": "user",
                "content": pregunta_data['pregunta']
            })
            historial.append({
                "role": "assistant",
                "content": respuesta
            })

        # Resumen de conversación
        puntaje_prom_conv = sum(r['evaluacion']['puntaje_total'] for r in resultados_conv) / len(resultados_conv)
        print(f"\n📊 Resumen Conversación {idx_conv}: {puntaje_prom_conv:.1f}/100")

    # === GENERAR REPORTE ===
    print("\n" + "="*80)
    print("📝 Generando reporte detallado...")
    print("="*80)

    generar_reporte_completo(todas_evaluaciones, metricas_globales, report_path)

    print(f"\n✅ Reporte guardado en: {report_path}")
    print(f"📊 Total evaluaciones: {len(todas_evaluaciones)}")
    print(f"📈 Puntaje promedio: {sum(metricas_globales['precision'])/len(metricas_globales['precision']):.1f}/100")
    print("\n" + "="*80)

    return todas_evaluaciones, report_path



def generar_reporte_completo(evaluaciones: List, metricas_globales: dict, report_path: Path):
    """
    Genera el reporte completo en formato texto
    """
    with open(report_path, 'w', encoding='utf-8') as f:
        # ENCABEZADO
        f.write("="*80 + "\n")
        f.write("         🏥 EVALUACIÓN CONVERSACIONAL - AGENTE HOSPITALARIO\n")
        f.write("="*80 + "\n\n")
        f.write(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"🤖 Modelo LLM: {OLLAMA_MODEL}\n")
        f.write(f"🔍 Modelo Embeddings: {EMBEDDING_MODEL}\n")
        f.write(f"📊 Total evaluaciones: {len(evaluaciones)}\n\n")

        # MÉTRICAS GLOBALES
        f.write("="*80 + "\n")
        f.write("                         📊 MÉTRICAS GLOBALES\n")
        f.write("="*80 + "\n\n")

        # Calcular promedios
        precision_prom = sum(metricas_globales['precision']) / len(metricas_globales['precision'])
        completitud_prom = sum(metricas_globales['completitud']) / len(metricas_globales['completitud'])
        concision_prom = sum(metricas_globales['concision']) / len(metricas_globales['concision'])
        habilidades_prom = sum(metricas_globales['habilidades_conv']) / len(metricas_globales['habilidades_conv'])
        performance_prom = sum(metricas_globales['performance']) / len(metricas_globales['performance'])
        tiempo_rag_prom = sum(metricas_globales['tiempos_rag']) / len(metricas_globales['tiempos_rag'])
        tiempo_llm_prom = sum(metricas_globales['tiempos_llm']) / len(metricas_globales['tiempos_llm'])

        f.write(f"┌{'─'*78}┐\n")
        f.write(f"│ {'MÉTRICA':<30} │ {'VALOR':>10} │ {'OBJETIVO':>10} │ {'ESTADO':>20} │\n")
        f.write(f"├{'─'*78}┤\n")
        f.write(f"│ {'Precisión':<30} │ {precision_prom:>9.1f}% │ {'≥85%':>10} │ {('✅ CUMPLE' if precision_prom >= 85 else '⚠️  MEJORAR'):>20} │\n")
        f.write(f"│ {'Completitud':<30} │ {completitud_prom:>9.1f}% │ {'≥80%':>10} │ {('✅ CUMPLE' if completitud_prom >= 80 else '⚠️  MEJORAR'):>20} │\n")
        f.write(f"│ {'Concisión':<30} │ {concision_prom:>9.1f}% │ {'≥70%':>10} │ {('✅ CUMPLE' if concision_prom >= 70 else '⚠️  MEJORAR'):>20} │\n")
        f.write(f"│ {'Habilidades Conv.':<30} │ {habilidades_prom:>9.1f}% │ {'≥75%':>10} │ {('✅ CUMPLE' if habilidades_prom >= 75 else '⚠️  MEJORAR'):>20} │\n")
        f.write(f"│ {'Performance':<30} │ {performance_prom:>9.1f}% │ {'≥80%':>10} │ {('✅ CUMPLE' if performance_prom >= 80 else '⚠️  MEJORAR'):>20} │\n")
        f.write(f"│ {'Tiempo RAG promedio':<30} │ {tiempo_rag_prom:>8.0f}ms │ {'<3000ms':>10} │ {('✅ CUMPLE' if tiempo_rag_prom < 3000 else '⚠️  MEJORAR'):>20} │\n")
        f.write(f"│ {'Tiempo LLM promedio':<30} │ {tiempo_llm_prom:>8.0f}ms │ {'<8000ms':>10} │ {('✅ CUMPLE' if tiempo_llm_prom < 8000 else '⚠️  MEJORAR'):>20} │\n")
        f.write(f"└{'─'*78}┘\n\n")

        # DETALLES POR CONVERSACIÓN
        conversaciones = {}
        for eval in evaluaciones:
            conv_nombre = eval['conversacion']
            if conv_nombre not in conversaciones:
                conversaciones[conv_nombre] = []
            conversaciones[conv_nombre].append(eval)

        for conv_nombre, evals_conv in conversaciones.items():
            f.write("\n" + "="*80 + "\n")
            f.write(f"          💬 {conv_nombre}\n")
            f.write("="*80 + "\n\n")

            for eval in evals_conv:
                f.write(f"┌{'─'*78}┐\n")
                f.write(f"│ PREGUNTA {eval['pregunta_num']}/10{' '*(66-len(f'PREGUNTA {eval['pregunta_num']}/10'))} │\n")
                f.write(f"├{'─'*78}┤\n")
                f.write(f"│ Pregunta: {eval['pregunta_data']['pregunta'][:60]:<60} │\n")
                f.write(f"│{' '*78}│\n")

                # TIEMPOS
                f.write(f"│ ⏱️  TIEMPOS:{' '*66}│\n")
                f.write(f"│   ├─ RAG: {eval['tiempos']['rag_ms']:.0f}ms{' '*(66-len(f'   ├─ RAG: {eval['tiempos']['rag_ms']:.0f}ms'))}│\n")
                f.write(f"│   ├─ LLM: {eval['tiempos']['llm_ms']:.0f}ms{' '*(66-len(f'   ├─ LLM: {eval['tiempos']['llm_ms']:.0f}ms'))}│\n")
                f.write(f"│   └─ TOTAL: {eval['tiempos']['total_ms']:.0f}ms{' '*(64-len(f'   └─ TOTAL: {eval['tiempos']['total_ms']:.0f}ms'))}│\n")
                f.write(f"│{' '*78}│\n")

                # CONTEXTO RAG
                if eval['chunks_rag']:
                    chunk_top = eval['chunks_rag'][0]
                    f.write(f"│ 🔍 CHUNK RAG (Top-1):{' '*57}│\n")
                    f.write(f"│   Obra social: {chunk_top['metadata']['obra_social']}{' '*(62-len(f'   Obra social: {chunk_top['metadata']['obra_social']}'))}│\n")
                    f.write(f"│   Archivo: {chunk_top['metadata']['archivo'][:50]}{' '*(66-len(f'   Archivo: {chunk_top['metadata']['archivo'][:50]}'))}│\n")
                    f.write(f"│   Similarity: {chunk_top['similarity']:.3f}{' '*(65-len(f'   Similarity: {chunk_top['similarity']:.3f}'))}│\n")
                    f.write(f"│   Texto: {chunk_top['texto'][:50]}...{' '*(57-len(f'   Texto: {chunk_top['texto'][:50]}...'))}│\n")
                    f.write(f"│{' '*78}│\n")

                # RESPUESTA BOT
                respuesta_preview = eval['respuesta'][:60] if len(eval['respuesta']) <= 60 else eval['respuesta'][:57] + "..."
                f.write(f"│ 💬 RESPUESTA BOT ({len(eval['respuesta'].split())} palabras):{' '*(42-len(f'💬 RESPUESTA BOT ({len(eval['respuesta'].split())} palabras):'))}│\n")
                f.write(f"│   {respuesta_preview}{' '*(75-len(respuesta_preview))}│\n")
                f.write(f"│{' '*78}│\n")

                # EVALUACIÓN
                ev = eval['evaluacion']
                f.write(f"│ 📊 EVALUACIÓN:{' '*64}│\n")
                f.write(f"│   ├─ Precisión: {ev['scores']['precision']:.1f}/25{' '*(60-len(f'   ├─ Precisión: {ev['scores']['precision']:.1f}/25'))}│\n")
                f.write(f"│   ├─ Completitud: {ev['scores']['completitud']:.1f}/20{' '*(58-len(f'   ├─ Completitud: {ev['scores']['completitud']:.1f}/20'))}│\n")
                f.write(f"│   ├─ Concisión: {ev['scores']['concision']:.1f}/15{' '*(60-len(f'   ├─ Concisión: {ev['scores']['concision']:.1f}/15'))}│\n")
                f.write(f"│   ├─ Habilidades Conv.: {ev['scores']['habilidades_conv']:.1f}/30{' '*(50-len(f'   ├─ Habilidades Conv.: {ev['scores']['habilidades_conv']:.1f}/30'))}│\n")
                f.write(f"│   ├─ Performance: {ev['scores']['performance']:.1f}/10{' '*(58-len(f'   ├─ Performance: {ev['scores']['performance']:.1f}/10'))}│\n")
                f.write(f"│   └─ PUNTAJE TOTAL: {ev['puntaje_total']:.1f}/100{' '*(55-len(f'   └─ PUNTAJE TOTAL: {ev['puntaje_total']:.1f}/100'))}│\n")

                f.write(f"└{'─'*78}┘\n\n")

        # ANÁLISIS DE CAUSAS
        f.write("\n" + "="*80 + "\n")
        f.write("                      🔍 ANÁLISIS DE CAUSAS\n")
        f.write("="*80 + "\n\n")

        # Problemas detectados
        problemas = []

        if concision_prom < 70:
            problemas.append({
                "nombre": "CONCISIÓN BAJA",
                "valor": f"{concision_prom:.1f}%",
                "objetivo": "≥70%",
                "impacto": "Enrolador pierde tiempo leyendo respuestas largas",
                "causa": "Prompt no enfatiza brevedad, modelo verboso",
                "solucion": "Modificar system prompt, agregar ejemplos few-shot"
            })

        if habilidades_prom < 75:
            problemas.append({
                "nombre": "HABILIDADES CONVERSACIONALES BAJAS",
                "valor": f"{habilidades_prom:.1f}%",
                "objetivo": "≥75%",
                "impacto": "Experiencia de usuario pobre",
                "causa": "No detecta saludos/despedidas, no repregunta cuando es ambiguo",
                "solucion": "Mejorar prompt con reglas conversacionales, agregar ejemplos"
            })

        if precision_prom < 85:
            problemas.append({
                "nombre": "PRECISIÓN BAJA",
                "valor": f"{precision_prom:.1f}%",
                "objetivo": "≥85%",
                "impacto": "Información incorrecta al enrolador",
                "causa": "RAG recupera chunks incorrectos o LLM alucina",
                "solucion": "Aumentar TOP_K, mejorar prompt anti-alucinación"
            })

        for i, problema in enumerate(problemas, 1):
            f.write(f"{i}. {problema['nombre']} ({problema['valor']} - Objetivo: {problema['objetivo']})\n")
            f.write(f"   Causa raíz: {problema['causa']}\n")
            f.write(f"   Impacto: {problema['impacto']}\n")
            f.write(f"   Solución: {problema['solucion']}\n\n")

        # CONCLUSIONES
        f.write("\n" + "="*80 + "\n")
        f.write("                 ✅ CONCLUSIONES Y RECOMENDACIONES\n")
        f.write("="*80 + "\n\n")

        puntaje_total = (precision_prom + completitud_prom + concision_prom + habilidades_prom + performance_prom) / 5

        if puntaje_total >= 80:
            f.write("🎯 ESTADO GENERAL: EXCELENTE\n\n")
        elif puntaje_total >= 70:
            f.write("🎯 ESTADO GENERAL: BUENO\n\n")
        else:
            f.write("🎯 ESTADO GENERAL: NECESITA MEJORA\n\n")

        f.write("✅ FORTALEZAS:\n")
        if precision_prom >= 85:
            f.write("   • Alta precisión en respuestas\n")
        if tiempo_rag_prom < 3000:
            f.write("   • Buen tiempo de respuesta RAG\n")
        if performance_prom >= 80:
            f.write("   • Performance general aceptable\n")

        f.write("\n⚠️  ÁREAS DE MEJORA:\n")
        for problema in problemas:
            f.write(f"   • {problema['nombre']}: {problema['solucion']}\n")

        f.write("\n" + "="*80 + "\n")

    # También guardar JSON (convirtiendo numpy types)
    json_path = report_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        data = {
            "fecha": datetime.now().isoformat(),
            "metricas_globales": convert_to_native_types(metricas_globales),
            "evaluaciones": convert_to_native_types(evaluaciones)
        }
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    evaluaciones, report_path = ejecutar_evaluacion_conversacional()
    print(f"\n✅ Evaluación completada. Ver reporte en: {report_path}")

