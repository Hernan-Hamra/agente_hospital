#!/usr/bin/env python3
"""
Evaluación completa de 20 preguntas para el bot del Grupo Pediátrico.
Genera informe detallado con métricas de negocio y límites de Groq.

Uso: python escenario_1/tests/test_evaluacion_20.py
"""
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

# Setup paths
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

# Imports del escenario (autocontenido)
from escenario_1.rag.retriever import ChromaRetriever
from escenario_1.core.entity_detector import get_entity_detector, reset_entity_detector
from escenario_1.metrics.collector import QueryMetrics
from escenario_1.llm.client import GroqClient
from escenario_1.core.router import ConsultaRouter

# Configuración
CONFIG_PATH = str(project_root / "escenario_1" / "config")
GROQ_MODEL = "llama-3.3-70b-versatile"
DELAY_BETWEEN_QUERIES = 4  # segundos entre queries (límite Groq)


# =============================================================================
# 20 PREGUNTAS DE EVALUACIÓN
# =============================================================================

TEST_CASES = [
    # --- ESPECÍFICAS (valor exacto) ---
    {
        "id": 1, "tipo": "Específica", "categoria": "Coseguro",
        "pregunta": "¿Cuánto cuesta la consulta con un médico especialista en ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["2912"],
        "dificultad": "Fácil"
    },
    {
        "id": 2, "tipo": "Específica", "categoria": "Coseguro",
        "pregunta": "¿Cuál es el coseguro de kinesiología en ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["971"],
        "dificultad": "Fácil"
    },
    {
        "id": 3, "tipo": "Específica", "categoria": "Coseguro",
        "pregunta": "¿Cuánto sale una tomografía en ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["4854"],
        "dificultad": "Media"
    },
    {
        "id": 4, "tipo": "Específica", "categoria": "Contacto",
        "pregunta": "¿Cuál es el teléfono de la mesa operativa de ASI?",
        "obra_social": "ASI",
        "respuesta_esperada": ["0810", "8274"],
        "dificultad": "Fácil"
    },
    {
        "id": 5, "tipo": "Específica", "categoria": "Contacto",
        "pregunta": "¿A qué mail mando el censo de internados de ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["auditoria@ensalud"],
        "dificultad": "Media"
    },
    {
        "id": 6, "tipo": "Específica", "categoria": "Protocolo",
        "pregunta": "¿Cuánto duran las autorizaciones en ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["30"],
        "dificultad": "Fácil"
    },

    # --- GENÉRICAS (listado completo) ---
    {
        "id": 7, "tipo": "Genérica", "categoria": "Coseguro",
        "pregunta": "¿Cuáles son los valores de coseguros de ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["1553", "2912", "971"],
        "dificultad": "Media"
    },
    {
        "id": 8, "tipo": "Genérica", "categoria": "Planes",
        "pregunta": "¿Qué planes tiene ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["Delta", "Krono", "Quantum"],
        "dificultad": "Media"
    },
    {
        "id": 9, "tipo": "Genérica", "categoria": "Exentos",
        "pregunta": "¿Quiénes no pagan coseguro en ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["HIV", "Oncología"],
        "dificultad": "Media"
    },
    {
        "id": 10, "tipo": "Genérica", "categoria": "Contacto",
        "pregunta": "¿Cuáles son los contactos de ASI?",
        "obra_social": "ASI",
        "respuesta_esperada": ["0810", "autorizaciones@asi"],
        "dificultad": "Media"
    },

    # --- DOCUMENTACIÓN/REQUISITOS ---
    {
        "id": 11, "tipo": "Requisitos", "categoria": "Documentación",
        "pregunta": "¿Qué documentos necesito para una consulta en IOSFA?",
        "obra_social": "IOSFA",
        "respuesta_esperada": ["DNI", "Validador"],
        "dificultad": "Fácil"
    },
    {
        "id": 12, "tipo": "Requisitos", "categoria": "Documentación",
        "pregunta": "¿Qué necesito para una internación programada en IOSFA?",
        "obra_social": "IOSFA",
        "respuesta_esperada": ["DNI", "Validador", "autorización"],
        "dificultad": "Media"
    },
    {
        "id": 13, "tipo": "Requisitos", "categoria": "Documentación",
        "pregunta": "¿Qué debo presentar para prácticas en IOSFA?",
        "obra_social": "IOSFA",
        "respuesta_esperada": ["DNI", "Validador", "Bono"],
        "dificultad": "Media"
    },
    {
        "id": 14, "tipo": "Requisitos", "categoria": "Documentación",
        "pregunta": "¿Qué documentación pido para guardia en Grupo Pediátrico?",
        "obra_social": "GRUPO_PEDIATRICO",
        "respuesta_esperada": ["DNI", "credencial"],
        "dificultad": "Fácil"
    },
    {
        "id": 15, "tipo": "Requisitos", "categoria": "Documentación",
        "pregunta": "¿Qué necesito para una internación de urgencia en Grupo Pediátrico?",
        "obra_social": "GRUPO_PEDIATRICO",
        "respuesta_esperada": ["DNI", "Denuncia"],
        "dificultad": "Media"
    },

    # --- COBERTURAS Y AUTORIZACIONES ---
    {
        "id": 16, "tipo": "Cobertura", "categoria": "Autorización",
        "pregunta": "¿Necesito autorización para fisioterapia en ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["autorización", "PREVIA"],
        "dificultad": "Media"
    },
    {
        "id": 17, "tipo": "Cobertura", "categoria": "Planes",
        "pregunta": "¿El plan Quantum de ENSALUD cubre consultas de especialidades?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["cubre", "sin autorización"],
        "dificultad": "Difícil"
    },
    {
        "id": 18, "tipo": "Cobertura", "categoria": "Coseguro",
        "pregunta": "¿El plan Krono Plus de ENSALUD paga coseguro en consultas?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["NO"],
        "dificultad": "Difícil"
    },

    # --- COLOQUIALES (lenguaje natural) ---
    {
        "id": 19, "tipo": "Coloquial", "categoria": "Coseguro",
        "pregunta": "¿Cuánto me sale ir al pediatra en ENSALUD?",
        "obra_social": "ENSALUD",
        "respuesta_esperada": ["1553"],
        "dificultad": "Media"
    },
    {
        "id": 20, "tipo": "Coloquial", "categoria": "Exentos",
        "pregunta": "¿Los pacientes de oncología pagan coseguro en Grupo Pediátrico?",
        "obra_social": "GRUPO_PEDIATRICO",
        "respuesta_esperada": ["no", "exento", "Oncológico"],
        "dificultad": "Difícil"
    },
]


# =============================================================================
# LÍMITES DE GROQ (Plan Gratuito)
# =============================================================================

GROQ_LIMITS = {
    "tokens_per_minute": 12000,
    "tokens_per_day": 100000,
    "requests_per_minute": 30,
    "requests_per_day": 1000,
    "avg_tokens_per_query": 800,  # Estimado (prompt + contexto + respuesta)
}


def calculate_groq_limits(avg_tokens: int) -> Dict[str, Any]:
    """Calcula límites operativos basados en tokens promedio por query."""
    return {
        "queries_per_minute": GROQ_LIMITS["tokens_per_minute"] // avg_tokens,
        "queries_per_hour": (GROQ_LIMITS["tokens_per_minute"] // avg_tokens) * 60,
        "queries_per_day": GROQ_LIMITS["tokens_per_day"] // avg_tokens,
        "recommended_delay_seconds": 4,
        "safe_queries_per_hour": 15 * 60 // 4,  # Con delay de 4 seg
    }


def evaluar_respuesta(test_case: Dict, respuesta: str) -> Dict[str, Any]:
    """Evalúa si la respuesta contiene los términos esperados."""
    respuesta_lower = respuesta.lower()

    terminos_encontrados = []
    terminos_faltantes = []

    for termino in test_case["respuesta_esperada"]:
        if termino.lower() in respuesta_lower:
            terminos_encontrados.append(termino)
        else:
            terminos_faltantes.append(termino)

    total = len(test_case["respuesta_esperada"])
    encontrados = len(terminos_encontrados)

    # Puntaje: porcentaje de términos encontrados
    puntaje = (encontrados / total) * 100 if total > 0 else 0

    return {
        "puntaje": round(puntaje, 1),
        "aprobado": puntaje >= 50,  # Al menos 50% de términos
        "terminos_encontrados": terminos_encontrados,
        "terminos_faltantes": terminos_faltantes,
        "total_esperados": total,
    }


def run_evaluation():
    """Ejecuta la evaluación completa."""
    print("=" * 80)
    print("EVALUACIÓN COMPLETA - 20 PREGUNTAS")
    print("Bot del Grupo Pediátrico - Escenario 1 (ChromaDB + Groq)")
    print("=" * 80)

    # Inicializar componentes
    print("\n[1/3] Inicializando componentes...")

    retriever = ChromaRetriever()
    print(f"   ✅ ChromaDB: {retriever.collection.count()} chunks")

    llm_client = GroqClient()
    print(f"   ✅ LLM: {GROQ_MODEL}")

    reset_entity_detector()
    entity_detector = get_entity_detector(f"{CONFIG_PATH}/entities.yaml")
    print(f"   ✅ Entity Detector listo")

    router = ConsultaRouter(
        retriever=retriever,
        llm_client=llm_client,
        entity_detector=entity_detector,
        config_path=f"{CONFIG_PATH}/scenario.yaml"
    )
    print(f"   ✅ Router listo\n")

    # Ejecutar evaluación
    print("[2/3] Ejecutando 20 preguntas...\n")

    resultados = []
    total_tokens_input = 0
    total_tokens_output = 0
    total_latency_ms = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"─── Pregunta {i}/20 [{test['tipo']}] [{test['dificultad']}] ───")
        print(f"    {test['pregunta']}")

        start_time = time.time()

        try:
            metrics = QueryMetrics(query_text=test['pregunta'])
            result = router.process_query(query=test['pregunta'], metrics=metrics)

            latency_ms = (time.time() - start_time) * 1000
            respuesta = result.respuesta

            # Evaluar
            evaluacion = evaluar_respuesta(test, respuesta)

            # Acumular métricas
            tokens_in = metrics.tokens_input or 0
            tokens_out = metrics.tokens_output or 0
            total_tokens_input += tokens_in
            total_tokens_output += tokens_out
            total_latency_ms += latency_ms

            status = "✅" if evaluacion["aprobado"] else "❌"
            print(f"    {status} Puntaje: {evaluacion['puntaje']}/100")
            print(f"    💬 \"{respuesta[:80]}...\"")

            if evaluacion["terminos_faltantes"]:
                print(f"    ⚠️  Faltaron: {evaluacion['terminos_faltantes']}")

            resultados.append({
                "test_case": test,
                "respuesta": respuesta,
                "evaluacion": evaluacion,
                "metricas": {
                    "tokens_input": tokens_in,
                    "tokens_output": tokens_out,
                    "latency_ms": round(latency_ms, 1),
                    "chunks_count": result.chunks_count,
                    "similarity": round(result.top_similarity, 3),
                },
                "exito": True,
            })

        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            resultados.append({
                "test_case": test,
                "respuesta": f"ERROR: {str(e)}",
                "evaluacion": {"puntaje": 0, "aprobado": False},
                "metricas": {},
                "exito": False,
            })

        print()

        # Delay entre queries (límite Groq)
        if i < len(TEST_CASES):
            time.sleep(DELAY_BETWEEN_QUERIES)

    # Calcular métricas finales
    print("\n[3/3] Generando informe...\n")

    aprobados = sum(1 for r in resultados if r["evaluacion"]["aprobado"])
    exitosos = sum(1 for r in resultados if r["exito"])
    puntaje_promedio = sum(r["evaluacion"]["puntaje"] for r in resultados) / len(resultados)

    tokens_total = total_tokens_input + total_tokens_output
    avg_tokens = tokens_total // len(TEST_CASES) if TEST_CASES else 0
    avg_latency = total_latency_ms / len(TEST_CASES) if TEST_CASES else 0

    # Límites de Groq
    groq_limits = calculate_groq_limits(avg_tokens if avg_tokens > 0 else 800)

    # Generar informe
    informe = {
        "metadata": {
            "fecha": datetime.now().isoformat(),
            "escenario": "Escenario 1 - Modo Consulta",
            "rag": "ChromaDB",
            "llm": GROQ_MODEL,
            "total_preguntas": len(TEST_CASES),
        },
        "resumen": {
            "preguntas_totales": len(TEST_CASES),
            "preguntas_exitosas": exitosos,
            "preguntas_aprobadas": aprobados,
            "puntaje_promedio": round(puntaje_promedio, 1),
            "tasa_aprobacion": round(aprobados / len(TEST_CASES) * 100, 1),
        },
        "metricas_tokens": {
            "total_tokens_input": total_tokens_input,
            "total_tokens_output": total_tokens_output,
            "total_tokens": tokens_total,
            "promedio_tokens_por_query": avg_tokens,
            "promedio_latency_ms": round(avg_latency, 1),
        },
        "limites_groq": {
            "plan": "Gratuito",
            "tokens_por_minuto": GROQ_LIMITS["tokens_per_minute"],
            "tokens_por_dia": GROQ_LIMITS["tokens_per_day"],
            "requests_por_dia": GROQ_LIMITS["requests_per_day"],
        },
        "capacidad_operativa": {
            "tokens_promedio_por_query": avg_tokens,
            "queries_maximas_por_minuto": groq_limits["queries_per_minute"],
            "queries_maximas_por_hora": groq_limits["queries_per_hour"],
            "queries_maximas_por_dia": groq_limits["queries_per_day"],
            "queries_seguras_por_hora": groq_limits["safe_queries_per_hour"],
            "delay_recomendado_segundos": DELAY_BETWEEN_QUERIES,
        },
        "por_tipo": {},
        "por_dificultad": {},
        "por_categoria": {},
        "por_obra_social": {},
        "resultados_detallados": resultados,
    }

    # Agrupar por tipo
    for tipo in ["Específica", "Genérica", "Requisitos", "Cobertura", "Coloquial"]:
        items = [r for r in resultados if r["test_case"]["tipo"] == tipo]
        if items:
            aprobados_tipo = sum(1 for r in items if r["evaluacion"]["aprobado"])
            informe["por_tipo"][tipo] = {
                "total": len(items),
                "aprobados": aprobados_tipo,
                "porcentaje": round(aprobados_tipo / len(items) * 100, 1),
            }

    # Agrupar por dificultad
    for dif in ["Fácil", "Media", "Difícil"]:
        items = [r for r in resultados if r["test_case"]["dificultad"] == dif]
        if items:
            aprobados_dif = sum(1 for r in items if r["evaluacion"]["aprobado"])
            informe["por_dificultad"][dif] = {
                "total": len(items),
                "aprobados": aprobados_dif,
                "porcentaje": round(aprobados_dif / len(items) * 100, 1),
            }

    # Agrupar por categoría
    categorias = set(r["test_case"]["categoria"] for r in resultados)
    for cat in categorias:
        items = [r for r in resultados if r["test_case"]["categoria"] == cat]
        aprobados_cat = sum(1 for r in items if r["evaluacion"]["aprobado"])
        informe["por_categoria"][cat] = {
            "total": len(items),
            "aprobados": aprobados_cat,
            "porcentaje": round(aprobados_cat / len(items) * 100, 1),
        }

    # Agrupar por obra social
    obras = set(r["test_case"]["obra_social"] for r in resultados)
    for os in obras:
        items = [r for r in resultados if r["test_case"]["obra_social"] == os]
        aprobados_os = sum(1 for r in items if r["evaluacion"]["aprobado"])
        informe["por_obra_social"][os] = {
            "total": len(items),
            "aprobados": aprobados_os,
            "porcentaje": round(aprobados_os / len(items) * 100, 1),
        }

    # Guardar informe JSON
    reports_dir = project_root / "escenario_1" / "reports"
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"evaluacion_20_{timestamp}.json"

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(informe, f, indent=2, ensure_ascii=False)

    # Imprimir resumen
    print("=" * 80)
    print("RESUMEN DE EVALUACIÓN")
    print("=" * 80)

    print(f"\n📊 RESULTADOS GENERALES")
    print(f"   Preguntas: {exitosos}/{len(TEST_CASES)} ejecutadas")
    print(f"   Aprobadas: {aprobados}/{len(TEST_CASES)} ({informe['resumen']['tasa_aprobacion']}%)")
    print(f"   Puntaje promedio: {puntaje_promedio:.1f}/100")

    print(f"\n📈 POR TIPO DE PREGUNTA")
    for tipo, data in informe["por_tipo"].items():
        print(f"   {tipo}: {data['aprobados']}/{data['total']} ({data['porcentaje']}%)")

    print(f"\n🎚️  POR DIFICULTAD")
    for dif, data in informe["por_dificultad"].items():
        print(f"   {dif}: {data['aprobados']}/{data['total']} ({data['porcentaje']}%)")

    print(f"\n🏢 POR OBRA SOCIAL")
    for os, data in informe["por_obra_social"].items():
        print(f"   {os}: {data['aprobados']}/{data['total']} ({data['porcentaje']}%)")

    print(f"\n💰 MÉTRICAS DE TOKENS")
    print(f"   Total tokens: {tokens_total:,}")
    print(f"   Promedio por query: {avg_tokens:,} tokens")
    print(f"   Latencia promedio: {avg_latency:.0f} ms")

    print(f"\n⚡ CAPACIDAD OPERATIVA (Groq Gratis)")
    print(f"   Límite diario: {GROQ_LIMITS['tokens_per_day']:,} tokens")
    print(f"   Queries máximas/día: {groq_limits['queries_per_day']}")
    print(f"   Queries seguras/hora: {groq_limits['safe_queries_per_hour']} (con delay {DELAY_BETWEEN_QUERIES}s)")
    print(f"   Queries máximas/minuto: {groq_limits['queries_per_minute']}")

    print(f"\n📄 Informe guardado: {json_path}")
    print("=" * 80)

    return informe, json_path


if __name__ == "__main__":
    informe, path = run_evaluation()
