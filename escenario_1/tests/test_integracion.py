#!/usr/bin/env python3
"""
Test de sistema: Evaluación end-to-end del bot
Prueba preguntas clave y evalúa la calidad de las respuestas RAG + LLM
Adaptado para Escenario 1 (ChromaDB + Groq)
"""
import sys
from pathlib import Path
import time
import json
from datetime import datetime
import pytest

# Agregar project root al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import os

# Cargar variables de entorno
for env_path in [project_root / "backend" / ".env", project_root / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)
        break

from escenario_1.rag.retriever import ChromaRetriever
from escenario_1.llm.client import GroqClient
from escenario_1.core.router import ConsultaRouter
from escenario_1.core.entity_detector import get_entity_detector, reset_entity_detector
from escenario_1.metrics.collector import QueryMetrics

CHROMA_PATH = str(project_root / "shared" / "data" / "chroma_db")
CONFIG_PATH = str(project_root / "escenario_1" / "config")
GROQ_MODEL = "llama-3.3-70b-versatile"


# ============================================================================
# CASOS DE PRUEBA
# ============================================================================

# Una sola pregunta difícil para test E2E completo (Entity → RAG → LLM)
TEST_CASES = [
    {
        "id": 1,
        "categoria": "Internaciones",
        "pregunta": "¿Qué documentos necesito para una internación programada en IOSFA?",
        "obra_social": "IOSFA",
        "respuesta_esperada": {
            "debe_incluir": ["DNI", "Validador", "autorización", "prestación"],
            "puede_incluir": ["Drive", "enlace"],
            "max_palabras": 30
        },
        "nivel_dificultad": "Media",
        "descripcion": "Procedimiento complejo con autorización previa - prueba pipeline E2E"
    }
]


# ============================================================================
# CRITERIOS DE EVALUACIÓN
# ============================================================================

def evaluar_respuesta(test_case: dict, respuesta: str, tiempo_ms: float, uso_rag: bool) -> dict:
    """
    Evalúa una respuesta del bot según criterios objetivos

    Returns:
        dict con puntajes y detalles de evaluación
    """
    esperado = test_case["respuesta_esperada"]
    respuesta_upper = respuesta.upper()

    # ===== CRITERIO 1: COMPLETITUD (40 puntos) =====
    terminos_encontrados = []
    terminos_faltantes = []

    for termino in esperado["debe_incluir"]:
        if termino.upper() in respuesta_upper:
            terminos_encontrados.append(termino)
        else:
            terminos_faltantes.append(termino)

    completitud = (len(terminos_encontrados) / len(esperado["debe_incluir"])) * 40

    # ===== CRITERIO 2: AUSENCIA DE ERRORES (20 puntos) =====
    errores = []
    for termino_prohibido in esperado.get("no_debe_incluir", []):
        if termino_prohibido.upper() in respuesta_upper:
            errores.append(termino_prohibido)

    sin_errores = 20 if len(errores) == 0 else max(0, 20 - (len(errores) * 10))

    # ===== CRITERIO 3: BREVEDAD (20 puntos) =====
    palabras = len(respuesta.split())
    max_palabras = esperado.get("max_palabras", 50)

    if palabras <= max_palabras:
        brevedad = 20
    elif palabras <= max_palabras * 1.5:
        brevedad = 10
    else:
        brevedad = 0

    # ===== CRITERIO 4: USO CORRECTO DE RAG (10 puntos) =====
    # Si la pregunta requiere info específica de obras sociales, debe usar RAG
    requiere_rag = test_case["categoria"] in ["Protocolo Específico", "Información Tabular", "Internaciones"]
    uso_rag_correcto = 10 if (uso_rag == requiere_rag or uso_rag) else 5

    # ===== CRITERIO 5: VELOCIDAD (10 puntos) =====
    # Considerar que el bot tarda ~180s total (RAG incluido)
    # Para evaluación solo medimos tiempo RAG
    if tiempo_ms < 2000:  # < 2s
        velocidad = 10
    elif tiempo_ms < 5000:  # < 5s
        velocidad = 7
    else:
        velocidad = 5

    # ===== PUNTAJE TOTAL =====
    puntaje_total = completitud + sin_errores + brevedad + uso_rag_correcto + velocidad

    # ===== RESULTADO =====
    return {
        "puntaje_total": round(puntaje_total, 1),
        "desglose": {
            "completitud": round(completitud, 1),
            "sin_errores": sin_errores,
            "brevedad": brevedad,
            "uso_rag": uso_rag_correcto,
            "velocidad": velocidad
        },
        "detalles": {
            "terminos_encontrados": terminos_encontrados,
            "terminos_faltantes": terminos_faltantes,
            "errores": errores,
            "palabras": palabras,
            "max_palabras": max_palabras,
            "tiempo_ms": round(tiempo_ms, 1)
        },
        "aprobado": puntaje_total >= 70,  # 70% para aprobar
        "nivel": "Excelente" if puntaje_total >= 90 else "Bueno" if puntaje_total >= 70 else "Necesita mejora"
    }


# ============================================================================
# EJECUTOR DE PRUEBAS
# ============================================================================

def ejecutar_evaluacion():
    """Ejecuta todas las pruebas y genera reporte"""

    print("\n" + "="*80)
    print("🧪 EVALUACIÓN AUTOMÁTICA DEL BOT - ESCENARIO 1")
    print("="*80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Modelo LLM: {GROQ_MODEL}")
    print(f"🔍 RAG: ChromaDB")
    print(f"📊 Total casos de prueba: {len(TEST_CASES)}")
    print("="*80 + "\n")

    # Cargar ChromaDB
    print("📚 Cargando ChromaDB...")
    retriever = ChromaRetriever(persist_directory=CHROMA_PATH)
    print(f"✅ ChromaDB cargado: {retriever.count()} chunks\n")

    # Inicializar cliente LLM
    print("🤖 Inicializando cliente Groq...")
    llm_client = GroqClient()
    print("✅ Cliente listo\n")

    # Inicializar router
    reset_entity_detector()
    entity_detector = get_entity_detector(f"{CONFIG_PATH}/entities.yaml")
    router = ConsultaRouter(
        retriever=retriever,
        llm_client=llm_client,
        entity_detector=entity_detector,
        config_path=f"{CONFIG_PATH}/scenario.yaml"
    )

    # Ejecutar pruebas
    resultados = []

    for i, test_case in enumerate(TEST_CASES, 1):
        print("─" * 80)
        print(f"📝 CASO {i}/{len(TEST_CASES)}: {test_case['categoria']}")
        print(f"   Dificultad: {test_case['nivel_dificultad']}")
        print(f"   Pregunta: \"{test_case['pregunta']}\"")
        print("─" * 80)

        # Medir tiempo total
        start_time = time.time()

        try:
            # Ejecutar query completa (Entity → RAG → LLM)
            metrics = QueryMetrics(query_text=test_case['pregunta'])
            result = router.process_query(query=test_case['pregunta'], metrics=metrics)

            tiempo_total_ms = (time.time() - start_time) * 1000

            # Extraer datos
            uso_rag = result.rag_executed
            respuesta = result.respuesta

            print(f"   ⏱️  Tiempo total: {tiempo_total_ms:.0f} ms")
            print(f"   📚 Chunks recuperados: {result.chunks_count}")
            print(f"   🎯 Similarity: {result.top_similarity:.3f}")
            print(f"   ✓ RAG ejecutado: {'Sí' if uso_rag else 'No'}")

            print(f"   💬 Respuesta ({len(respuesta.split())} palabras):")
            print(f"      {respuesta[:200]}...")

            # Evaluar
            evaluacion = evaluar_respuesta(test_case, respuesta, tiempo_total_ms, uso_rag)

            print(f"\n   📊 EVALUACIÓN:")
            print(f"      Puntaje: {evaluacion['puntaje_total']}/100 ({evaluacion['nivel']})")
            print(f"      ├─ Completitud: {evaluacion['desglose']['completitud']}/40")
            print(f"      ├─ Sin errores: {evaluacion['desglose']['sin_errores']}/20")
            print(f"      ├─ Brevedad: {evaluacion['desglose']['brevedad']}/20")
            print(f"      ├─ Uso RAG: {evaluacion['desglose']['uso_rag']}/10")
            print(f"      └─ Velocidad: {evaluacion['desglose']['velocidad']}/10")

            if evaluacion['detalles']['terminos_faltantes']:
                print(f"   ⚠️  Faltaron: {', '.join(evaluacion['detalles']['terminos_faltantes'])}")

            if evaluacion['detalles']['errores']:
                print(f"   ❌ Errores: {', '.join(evaluacion['detalles']['errores'])}")

            resultado = {
                "test_case": test_case,
                "respuesta": respuesta,
                "evaluacion": evaluacion,
                "exito": True
            }

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            resultado = {
                "test_case": test_case,
                "respuesta": None,
                "evaluacion": {"puntaje_total": 0, "aprobado": False},
                "exito": False,
                "error": str(e)
            }

        resultados.append(resultado)
        print()

    # ========================================================================
    # REPORTE FINAL
    # ========================================================================

    print("\n" + "="*80)
    print("📊 REPORTE FINAL DE EVALUACIÓN")
    print("="*80)

    casos_exitosos = sum(1 for r in resultados if r['exito'])
    casos_aprobados = sum(1 for r in resultados if r.get('evaluacion', {}).get('aprobado', False))

    puntaje_promedio = sum(r.get('evaluacion', {}).get('puntaje_total', 0) for r in resultados) / len(resultados)

    print(f"\n✅ Casos ejecutados: {casos_exitosos}/{len(TEST_CASES)}")
    print(f"🎯 Casos aprobados (≥70): {casos_aprobados}/{len(TEST_CASES)}")
    print(f"📈 Puntaje promedio: {puntaje_promedio:.1f}/100")

    # Por categoría
    print(f"\n📋 Resultados por Categoría:")
    categorias = set(tc['categoria'] for tc in TEST_CASES)
    for categoria in categorias:
        casos_cat = [r for r in resultados if r['test_case']['categoria'] == categoria]
        puntaje_cat = sum(r.get('evaluacion', {}).get('puntaje_total', 0) for r in casos_cat) / len(casos_cat)
        print(f"   {categoria:25s}: {puntaje_cat:.1f}/100")

    # Por dificultad
    print(f"\n🎚️  Resultados por Dificultad:")
    dificultades = set(tc['nivel_dificultad'] for tc in TEST_CASES)
    for dificultad in dificultades:
        casos_dif = [r for r in resultados if r['test_case']['nivel_dificultad'] == dificultad]
        puntaje_dif = sum(r.get('evaluacion', {}).get('puntaje_total', 0) for r in casos_dif) / len(casos_dif)
        print(f"   {dificultad:15s}: {puntaje_dif:.1f}/100")

    # Tiempo promedio
    tiempos = [r['evaluacion']['detalles']['tiempo_ms'] for r in resultados if r['exito']]
    if tiempos:
        print(f"\n⏱️  Tiempo promedio RAG: {sum(tiempos)/len(tiempos):.0f} ms")

    # Guardar reporte JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(__file__).parent.parent / "reports" / f"reporte_integracion_{timestamp}.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "modelo_llm": GROQ_MODEL,
            "rag_type": "ChromaDB",
            "resumen": {
                "casos_totales": len(TEST_CASES),
                "casos_exitosos": casos_exitosos,
                "casos_aprobados": casos_aprobados,
                "puntaje_promedio": round(puntaje_promedio, 1)
            },
            "resultados_detallados": resultados
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Reporte detallado guardado en: {report_path}")
    print("="*80 + "\n")

    # Conclusión
    if puntaje_promedio >= 80:
        print("🎉 EXCELENTE: El bot está funcionando muy bien")
    elif puntaje_promedio >= 70:
        print("✅ BUENO: El bot funciona correctamente con margen de mejora")
    else:
        print("⚠️  NECESITA MEJORA: El bot requiere ajustes")

    return resultados


# ============================================================================
# PYTEST FIXTURES Y TESTS
# ============================================================================

@pytest.fixture(scope="module")
def setup_rag_system():
    """Setup del sistema RAG para todos los tests"""
    print("\n📚 Cargando ChromaDB...")
    retriever = ChromaRetriever(persist_directory=CHROMA_PATH)

    if retriever.count() == 0:
        pytest.skip("ChromaDB vacío o no encontrado")

    return retriever


@pytest.mark.parametrize("test_case", TEST_CASES)
def test_rag_case(setup_rag_system, test_case):
    """Test parametrizado: evalúa cada caso de prueba (solo RAG)"""
    retriever = setup_rag_system

    # Ejecutar RAG
    start_rag = time.time()
    chunks = retriever.retrieve(
        query=test_case['pregunta'],
        top_k=5,
        obra_social_filter=test_case.get('obra_social')
    )
    tiempo_rag_ms = (time.time() - start_rag) * 1000

    # Determinar si encontró info relevante
    context = "\n".join([chunk[0] for chunk in chunks]) if chunks else ""
    uso_rag = len(chunks) > 0

    # Simular respuesta (en producción usaría el LLM real)
    respuesta = context[:500] if uso_rag else "No tengo esa información disponible"

    # Evaluar
    evaluacion = evaluar_respuesta(test_case, respuesta, tiempo_rag_ms, uso_rag)

    # Assertions
    assert evaluacion['puntaje_total'] >= 70, \
        f"Puntaje bajo: {evaluacion['puntaje_total']}/100 - {evaluacion['detalles']}"

    assert uso_rag, "No encontró contexto en RAG"

    # Log para debug
    print(f"\n{'='*70}")
    print(f"Test: {test_case['categoria']}")
    print(f"Puntaje: {evaluacion['puntaje_total']}/100 ({evaluacion['nivel']})")
    print(f"Completitud: {evaluacion['desglose']['completitud']}/40")
    print(f"Tiempo RAG: {tiempo_rag_ms:.0f} ms")


def test_full_evaluation_report():
    """Test que genera reporte completo (igual al script original)"""
    resultados = ejecutar_evaluacion()

    # Verificar que al menos 80% de casos pasaron
    casos_aprobados = sum(1 for r in resultados if r.get('evaluacion', {}).get('aprobado', False))
    tasa_aprobacion = casos_aprobados / len(TEST_CASES)

    assert tasa_aprobacion >= 0.80, \
        f"Solo {casos_aprobados}/{len(TEST_CASES)} casos aprobados ({tasa_aprobacion*100:.0f}%)"

    # Verificar puntaje promedio
    puntaje_promedio = sum(r.get('evaluacion', {}).get('puntaje_total', 0) for r in resultados) / len(resultados)

    assert puntaje_promedio >= 70, \
        f"Puntaje promedio muy bajo: {puntaje_promedio:.1f}/100"


if __name__ == "__main__":
    # Ejecutar evaluación directa (sin pytest)
    ejecutar_evaluacion()

    # O ejecutar con pytest:
    # python -m pytest tests/system/test_evaluation.py -v
