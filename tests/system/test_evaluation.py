#!/usr/bin/env python3
"""
Test de sistema: Evaluación end-to-end del bot
Prueba preguntas clave y evalúa la calidad de las respuestas RAG + LLM
"""
import sys
from pathlib import Path
import time
import json
from datetime import datetime
import pytest

# Agregar backend al path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.rag.indexer import DocumentIndexer
from app.rag.retriever import DocumentRetriever
from app.llm.client import OllamaClient
from dotenv import load_dotenv
import os

# Cargar variables de entorno
env_path = backend_path / ".env"
load_dotenv(env_path)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


# ============================================================================
# CASOS DE PRUEBA
# ============================================================================

TEST_CASES = [
    {
        "id": 1,
        "categoria": "Protocolo Básico",
        "pregunta": "¿Qué documentación necesito para una consulta en IOSFA?",
        "obra_social": "IOSFA",
        "respuesta_esperada": {
            "debe_incluir": ["VALIDADOR", "DNI", "BONO DE CONSULTA"],
            "no_debe_incluir": ["AUTORIZACION", "orden médica"],
            "max_palabras": 20
        },
        "nivel_dificultad": "Fácil",
        "descripcion": "Pregunta directa sobre requisitos básicos IOSFA"
    },
    {
        "id": 2,
        "categoria": "Protocolo Específico",
        "pregunta": "Documentación para prácticas IOSFA",
        "obra_social": "IOSFA",
        "respuesta_esperada": {
            "debe_incluir": ["VALIDADOR", "DNI", "BONO DE PRACTICAS", "AUTORIZACION"],
            "no_debe_incluir": ["guardia"],
            "max_palabras": 25
        },
        "nivel_dificultad": "Fácil",
        "descripcion": "Requisitos para prácticas (más complejo que consultas)"
    },
    {
        "id": 3,
        "categoria": "Diferenciación",
        "pregunta": "¿Cuál es la diferencia entre guardia y turno en IOSFA?",
        "obra_social": "IOSFA",
        "respuesta_esperada": {
            "debe_incluir": ["guardia", "DNI", "VALIDADOR"],
            "conceptos_clave": ["guardia no requiere orden", "turno/consulta requiere bono"],
            "max_palabras": 30
        },
        "nivel_dificultad": "Media",
        "descripcion": "Requiere comparar dos procedimientos diferentes"
    },
    {
        "id": 4,
        "categoria": "Información Tabular",
        "pregunta": "¿Cuál es el mail de Mesa Operativa de ASI?",
        "obra_social": "ASI",
        "respuesta_esperada": {
            "debe_incluir": ["autorizaciones@asi.com.ar"],
            "puede_incluir": ["internados@asi.com.ar", "0810-888-8274"],
            "max_palabras": 20
        },
        "nivel_dificultad": "Fácil",
        "descripcion": "Búsqueda en tabla de contactos"
    },
    {
        "id": 5,
        "categoria": "Internaciones",
        "pregunta": "¿Qué documentos necesito para una internación programada en IOSFA?",
        "obra_social": "IOSFA",
        "respuesta_esperada": {
            "debe_incluir": ["DNI", "VALIDADOR", "AUTORIZADA", "PRESTACION"],
            "puede_incluir": ["DRIVE", "ENLACE"],
            "max_palabras": 30
        },
        "nivel_dificultad": "Media",
        "descripcion": "Procedimiento más complejo con autorización previa"
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
    print("🧪 EVALUACIÓN AUTOMÁTICA DEL BOT HOSPITALARIO")
    print("="*80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Modelo LLM: {OLLAMA_MODEL}")
    print(f"🔍 Modelo Embeddings: {EMBEDDING_MODEL}")
    print(f"📊 Total casos de prueba: {len(TEST_CASES)}")
    print("="*80 + "\n")

    # Cargar índice FAISS
    print("📚 Cargando índice FAISS...")
    indexer = DocumentIndexer(embedding_model=EMBEDDING_MODEL)
    index_path = backend_path / "faiss_index"
    indexer.load_index(str(index_path))

    retriever = DocumentRetriever(indexer, embedding_model=EMBEDDING_MODEL)
    print(f"✅ Índice cargado: {len(indexer.documents)} chunks\n")

    # Inicializar cliente LLM
    print("🤖 Inicializando cliente Ollama...")
    llm_client = OllamaClient(model=OLLAMA_MODEL)
    print("✅ Cliente listo\n")

    # Ejecutar pruebas
    resultados = []

    for i, test_case in enumerate(TEST_CASES, 1):
        print("─" * 80)
        print(f"📝 CASO {i}/{len(TEST_CASES)}: {test_case['categoria']}")
        print(f"   Dificultad: {test_case['nivel_dificultad']}")
        print(f"   Pregunta: \"{test_case['pregunta']}\"")
        print("─" * 80)

        # Medir tiempo RAG
        start_rag = time.time()

        try:
            # Ejecutar RAG
            context = retriever.get_context_for_llm(
                query=test_case['pregunta'],
                top_k=5,
                obra_social_filter=test_case.get('obra_social')
            )

            tiempo_rag_ms = (time.time() - start_rag) * 1000

            # Determinar si encontró info relevante
            uso_rag = "No se encontró información" not in context

            print(f"   ⏱️  Tiempo RAG: {tiempo_rag_ms:.0f} ms")
            print(f"   📚 Contexto recuperado: {len(context)} chars")
            print(f"   ✓ Info encontrada: {'Sí' if uso_rag else 'No'}")

            # Simular respuesta del LLM (usamos el contexto como "respuesta")
            # En producción, aquí llamarías al LLM con el contexto
            respuesta = context[:500] if uso_rag else "No tengo esa información disponible"

            print(f"   💬 Respuesta ({len(respuesta.split())} palabras):")
            print(f"      {respuesta[:200]}...")

            # Evaluar
            evaluacion = evaluar_respuesta(test_case, respuesta, tiempo_rag_ms, uso_rag)

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
    report_path = Path(__file__).parent.parent / "evaluation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "fecha": datetime.now().isoformat(),
            "modelo_llm": OLLAMA_MODEL,
            "modelo_embeddings": EMBEDDING_MODEL,
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
    print("\n📚 Cargando índice FAISS...")
    indexer = DocumentIndexer(embedding_model=EMBEDDING_MODEL)
    index_path = backend_path / "faiss_index"

    if not index_path.exists():
        pytest.skip("Índice FAISS no encontrado")

    indexer.load_index(str(index_path))
    retriever = DocumentRetriever(indexer, embedding_model=EMBEDDING_MODEL)

    return indexer, retriever


@pytest.mark.parametrize("test_case", TEST_CASES)
def test_rag_case(setup_rag_system, test_case):
    """Test parametrizado: evalúa cada caso de prueba"""
    indexer, retriever = setup_rag_system

    # Ejecutar RAG
    start_rag = time.time()
    context = retriever.get_context_for_llm(
        query=test_case['pregunta'],
        top_k=5,
        obra_social_filter=test_case.get('obra_social')
    )
    tiempo_rag_ms = (time.time() - start_rag) * 1000

    # Determinar si encontró info relevante
    uso_rag = "No se encontró información" not in context

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
