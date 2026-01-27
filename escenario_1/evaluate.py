#!/usr/bin/env python3
"""
Evaluación completa de Escenario 1
==================================

Ejecuta batería de 20 preguntas y genera informe con métricas.

Uso:
    python escenario_1/evaluate.py
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load env
from dotenv import load_dotenv
for env_path in [project_root / "backend" / ".env", project_root / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)
        break

# Imports del escenario
from escenario_1.rag.retriever import ChromaRetriever
from escenario_1.llm.client import GroqClient
from escenario_1.core.router import ConsultaRouter
from escenario_1.core.entity_detector import get_entity_detector, reset_entity_detector
from escenario_1.metrics.collector import QueryMetrics


@dataclass
class TestResult:
    """Resultado de un test individual"""
    id: int
    categoria: str
    obra_social: Optional[str]
    query: str
    respuesta_esperada: str
    respuesta_bot: str
    entity_detected: Optional[str]
    entity_confidence: str
    rag_executed: bool
    chunks_count: int
    top_similarity: float
    tokens_input: int
    tokens_output: int
    latency_rag_ms: float
    latency_llm_ms: float
    latency_total_ms: float
    contiene_esperado: bool
    success: bool


def load_test_queries() -> List[Dict]:
    """Carga las queries de test desde el JSON local del escenario"""
    test_file = Path(__file__).parent / "data" / "test_queries.json"
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data["queries"]


def check_response(respuesta: str, esperado: str) -> bool:
    """Verifica si la respuesta contiene lo esperado"""
    respuesta_lower = respuesta.lower()
    esperado_lower = esperado.lower()

    # Verificar si contiene el texto esperado
    if esperado_lower in respuesta_lower:
        return True

    # Verificar tokens individuales (para casos como "24 horas" -> "24")
    tokens_esperados = esperado_lower.split()
    for token in tokens_esperados:
        if len(token) > 2 and token in respuesta_lower:
            return True

    return False


def run_evaluation(delay_seconds: int = 3) -> List[TestResult]:
    """Ejecuta la evaluación completa"""

    print("=" * 80)
    print("EVALUACIÓN ESCENARIO 1 - 20 PREGUNTAS")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Inicializar componentes
    print("\n📦 Inicializando componentes...")

    chroma_path = str(project_root / "data" / "chroma_db")
    retriever = ChromaRetriever(persist_directory=chroma_path)
    print(f"   ChromaDB: {retriever.count()} chunks")

    llm_client = GroqClient()
    print(f"   Groq: {llm_client.model}")

    reset_entity_detector()
    entity_detector = get_entity_detector(
        str(Path(__file__).parent / "config" / "entities.yaml")
    )

    router = ConsultaRouter(
        retriever=retriever,
        llm_client=llm_client,
        entity_detector=entity_detector,
        config_path=str(Path(__file__).parent / "config" / "scenario.yaml")
    )

    # Cargar queries
    queries = load_test_queries()
    print(f"\n📝 Queries a evaluar: {len(queries)}")
    print(f"⏱️  Delay entre queries: {delay_seconds}s (rate limit Groq)")

    results = []

    print("\n" + "─" * 80)
    print(f"{'ID':<4} {'Categoría':<15} {'OS':<10} {'OK':<4} {'Sim':<6} {'ms':<6} Query")
    print("─" * 80)

    for i, q in enumerate(queries):
        query_id = q["id"]
        categoria = q["categoria"]
        obra_social = q.get("obra_social")
        query = q["query"]
        esperado = q["respuesta_esperada"]

        # Ejecutar query
        metrics = QueryMetrics(query_text=query, obra_social=obra_social)
        result = router.process_query(query=query, metrics=metrics)

        # Evaluar resultado
        contiene = check_response(result.respuesta, esperado)

        # Crear TestResult
        test_result = TestResult(
            id=query_id,
            categoria=categoria,
            obra_social=obra_social,
            query=query,
            respuesta_esperada=esperado,
            respuesta_bot=result.respuesta,
            entity_detected=result.entity_result.entity if result.entity_result else None,
            entity_confidence=result.entity_result.confidence if result.entity_result else "none",
            rag_executed=result.rag_executed,
            chunks_count=result.chunks_count,
            top_similarity=result.top_similarity,
            tokens_input=metrics.tokens_input,
            tokens_output=metrics.tokens_output,
            latency_rag_ms=metrics.latency_faiss_ms,
            latency_llm_ms=metrics.latency_llm_ms,
            latency_total_ms=metrics.latency_total_ms,
            contiene_esperado=contiene,
            success=contiene
        )
        results.append(test_result)

        # Print progress
        status = "✅" if contiene else "❌"
        os_str = obra_social[:8] if obra_social else "N/A"
        query_short = query[:40] + "..." if len(query) > 40 else query
        print(f"{query_id:<4} {categoria:<15} {os_str:<10} {status:<4} {result.top_similarity:.3f} {metrics.latency_total_ms:>5.0f} {query_short}")

        # Rate limit delay (excepto última query)
        if i < len(queries) - 1:
            time.sleep(delay_seconds)

    print("─" * 80)

    return results


def generate_report(results: List[TestResult]) -> Dict[str, Any]:
    """Genera informe completo"""

    total = len(results)
    exitosos = sum(1 for r in results if r.success)

    # Métricas agregadas
    latencias = [r.latency_total_ms for r in results if r.latency_total_ms > 0]
    tokens_in = [r.tokens_input for r in results if r.tokens_input > 0]
    tokens_out = [r.tokens_output for r in results if r.tokens_output > 0]
    similarities = [r.top_similarity for r in results if r.top_similarity > 0]

    # Por categoría
    categorias = {}
    for r in results:
        cat = r.categoria
        if cat not in categorias:
            categorias[cat] = {"total": 0, "exitosos": 0, "queries": []}
        categorias[cat]["total"] += 1
        if r.success:
            categorias[cat]["exitosos"] += 1
        categorias[cat]["queries"].append(r.id)

    for cat in categorias:
        categorias[cat]["porcentaje"] = round(
            categorias[cat]["exitosos"] / categorias[cat]["total"] * 100, 1
        )

    # Por obra social
    obras_sociales = {}
    for r in results:
        os = r.obra_social or "SIN_OS"
        if os not in obras_sociales:
            obras_sociales[os] = {"total": 0, "exitosos": 0}
        obras_sociales[os]["total"] += 1
        if r.success:
            obras_sociales[os]["exitosos"] += 1

    for os in obras_sociales:
        obras_sociales[os]["porcentaje"] = round(
            obras_sociales[os]["exitosos"] / obras_sociales[os]["total"] * 100, 1
        )

    # Fallos
    fallos = [asdict(r) for r in results if not r.success]

    report = {
        "escenario": "Escenario 1: Modo Consulta + ChromaDB + Groq Gratis",
        "fecha": datetime.now().isoformat(),
        "resumen": {
            "total_queries": total,
            "exitosos": exitosos,
            "fallidos": total - exitosos,
            "porcentaje_exito": round(exitosos / total * 100, 1)
        },
        "metricas": {
            "latencia": {
                "promedio_ms": round(sum(latencias) / len(latencias), 1) if latencias else 0,
                "min_ms": round(min(latencias), 1) if latencias else 0,
                "max_ms": round(max(latencias), 1) if latencias else 0
            },
            "tokens": {
                "input_promedio": round(sum(tokens_in) / len(tokens_in)) if tokens_in else 0,
                "output_promedio": round(sum(tokens_out) / len(tokens_out)) if tokens_out else 0,
                "total_input": sum(tokens_in),
                "total_output": sum(tokens_out)
            },
            "similarity": {
                "promedio": round(sum(similarities) / len(similarities), 3) if similarities else 0,
                "min": round(min(similarities), 3) if similarities else 0,
                "max": round(max(similarities), 3) if similarities else 0
            }
        },
        "por_categoria": categorias,
        "por_obra_social": obras_sociales,
        "fallos": fallos,
        "detalle_completo": [asdict(r) for r in results]
    }

    return report


def print_report(report: Dict[str, Any]):
    """Imprime informe formateado"""

    print("\n" + "=" * 80)
    print("INFORME DE EVALUACIÓN - ESCENARIO 1")
    print("=" * 80)

    r = report["resumen"]
    print(f"\n📊 RESUMEN:")
    print(f"   Total queries: {r['total_queries']}")
    print(f"   Exitosos: {r['exitosos']} ({r['porcentaje_exito']}%)")
    print(f"   Fallidos: {r['fallidos']}")

    m = report["metricas"]
    print(f"\n⏱️  LATENCIAS:")
    print(f"   Promedio: {m['latencia']['promedio_ms']}ms")
    print(f"   Rango: {m['latencia']['min_ms']}ms - {m['latencia']['max_ms']}ms")

    print(f"\n🔢 TOKENS:")
    print(f"   Input promedio: {m['tokens']['input_promedio']}")
    print(f"   Output promedio: {m['tokens']['output_promedio']}")
    print(f"   Total: {m['tokens']['total_input']} input, {m['tokens']['total_output']} output")

    print(f"\n🎯 SIMILARITY RAG:")
    print(f"   Promedio: {m['similarity']['promedio']}")
    print(f"   Rango: {m['similarity']['min']} - {m['similarity']['max']}")

    print(f"\n📁 POR CATEGORÍA:")
    for cat, data in report["por_categoria"].items():
        print(f"   {cat}: {data['exitosos']}/{data['total']} ({data['porcentaje']}%)")

    print(f"\n🏥 POR OBRA SOCIAL:")
    for os, data in report["por_obra_social"].items():
        print(f"   {os}: {data['exitosos']}/{data['total']} ({data['porcentaje']}%)")

    if report["fallos"]:
        print(f"\n❌ FALLOS ({len(report['fallos'])}):")
        for f in report["fallos"]:
            print(f"\n   [{f['id']}] {f['query'][:50]}...")
            print(f"       Esperado: {f['respuesta_esperada']}")
            print(f"       Bot dijo: {f['respuesta_bot'][:60]}...")
            print(f"       Entity: {f['entity_detected']} | Sim: {f['top_similarity']:.3f}")

    print("\n" + "=" * 80)


def save_report(report: Dict[str, Any]):
    """Guarda el informe en archivo JSON"""

    # Crear carpeta de reportes en escenario_1
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Nombre con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"reporte_evaluacion_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Informe guardado: {report_file}")

    # También guardar último como "latest"
    latest_file = reports_dir / "reporte_evaluacion_latest.json"
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report_file


def main():
    """Función principal"""

    # Verificar API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY no configurado")
        sys.exit(1)

    # Ejecutar evaluación (3 segundos de delay para rate limit)
    results = run_evaluation(delay_seconds=3)

    # Generar informe
    report = generate_report(results)

    # Mostrar informe
    print_report(report)

    # Guardar informe
    report_file = save_report(report)

    # Código de salida según resultado
    success_rate = report["resumen"]["porcentaje_exito"]
    if success_rate >= 80:
        print(f"\n✅ Evaluación APROBADA ({success_rate}% >= 80%)")
        return 0
    else:
        print(f"\n⚠️  Evaluación MEJORABLE ({success_rate}% < 80%)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
