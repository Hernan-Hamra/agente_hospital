#!/usr/bin/env python3
"""
Script para ejecutar escenarios de prueba.

Uso:
    # Ejecutar una query en un escenario específico
    python scripts/run_scenario.py --scenario groq_consulta --query "¿Qué documentos necesito para IOSFA?"

    # Comparar dos escenarios
    python scripts/run_scenario.py --compare --query "¿Cuál es el mail de ASI?"

    # Ejecutar batch de pruebas (usa archivo JSON de test queries)
    python scripts/run_scenario.py --batch --scenario groq_consulta

    # Ejecutar batch con archivo de queries específico
    python scripts/run_scenario.py --batch --scenario groq_consulta --queries-file data/test_queries_escenario1.json

    # Ver escenarios disponibles
    python scripts/run_scenario.py --list

    # Health check
    python scripts/run_scenario.py --health
"""
import sys
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

# Agregar backend al path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from app.scenarios.runner import ScenarioRunner


# Archivo de queries por defecto para batch
DEFAULT_QUERIES_FILE = "data/test_queries_escenario1.json"

# Queries de prueba básicas (fallback si no hay archivo JSON)
FALLBACK_QUERIES = [
    {"id": 1, "query": "¿Qué documentos necesito para una consulta en IOSFA?", "obra_social": None, "respuesta_esperada": "validador, DNI, bono de consulta"},
    {"id": 2, "query": "¿Cuál es el mail de Mesa Operativa de ASI?", "obra_social": None, "respuesta_esperada": "autorizaciones@asi.com.ar"},
    {"id": 3, "query": "Hola, buen día", "obra_social": None, "respuesta_esperada": "solicitar obra social o aclaración"},
]

# Costos de referencia Groq (USD por millón de tokens)
GROQ_COSTS = {
    "free": {"input": 0.0, "output": 0.0, "nota": "Plan gratuito - sin costo"},
    "paid": {"input": 0.59, "output": 0.79, "nota": "Plan pago (llama-3.3-70b-versatile)"}
}


def run_single_query(runner: ScenarioRunner, scenario: str, query: str, obra_social: str = None):
    """Ejecuta una query individual"""
    print(f"\n{'='*60}")
    print(f"Escenario: {scenario}")
    print(f"Query: {query}")
    if obra_social:
        print(f"Obra Social (forzada): {obra_social}")
    print(f"{'='*60}")

    try:
        result = runner.run_query(
            scenario_id=scenario,
            query=query,
            obra_social=obra_social
        )

        metrics = result.get("metrics")
        entity = result.get("entity", {})

        # Mostrar entity detection
        print(f"\n🔍 Entity Detection:")
        if entity and entity.get("detected"):
            print(f"   Entidad:      {entity.get('entity')} ({entity.get('entity_type')})")
            print(f"   Matched:      \"{entity.get('matched_term')}\"")
            print(f"   Confidence:   {entity.get('confidence')}")
            print(f"   RAG filter:   {entity.get('rag_filter')}")
        else:
            print(f"   Sin entidad detectada → respuesta fija (sin LLM, sin RAG)")

        print(f"\n📝 Respuesta:")
        print(f"   {result['respuesta']}")

        print(f"\n📊 Flujo:")
        print(f"   RAG ejecutado: {'✅' if result.get('rag_executed') else '❌'}")
        print(f"   LLM ejecutado: {'✅' if result.get('llm_executed') else '❌'}")

        print(f"\n📊 Métricas:")
        print(f"   Tokens entrada:  {metrics.tokens_input}")
        print(f"   Tokens salida:   {metrics.tokens_output}")
        print(f"   Tokens total:    {metrics.tokens_total}")
        print(f"   Latencia LLM:    {metrics.latency_llm_ms:.0f} ms")
        print(f"   Latencia total:  {metrics.latency_total_ms:.0f} ms")
        print(f"   Costo:           ${metrics.cost_total:.6f} USD")
        print(f"   RAG chunks:      {result.get('chunks_count', 0)}")
        print(f"   Palabras resp:   {metrics.response_words}")

        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_comparison(runner: ScenarioRunner, query: str, obra_social: str = None):
    """Ejecuta comparación entre escenarios"""
    print(f"\n{'='*60}")
    print(f"COMPARACIÓN DE ESCENARIOS")
    print(f"Query: {query}")
    if obra_social:
        print(f"Obra Social: {obra_social}")
    print(f"{'='*60}")

    try:
        result = runner.run_comparison(
            query=query,
            obra_social=obra_social
        )

        # Mostrar resultados por escenario
        for scenario_id, scenario_result in result["results"].items():
            print(f"\n📦 {scenario_id}:")
            if "error" in scenario_result:
                print(f"   ❌ Error: {scenario_result['error']}")
            else:
                print(f"   Respuesta: {scenario_result['respuesta'][:100]}...")

        # Mostrar comparación
        comparison = result.get("comparison", {})
        if "metrics" in comparison:
            print(f"\n📊 MÉTRICAS COMPARATIVAS:")
            print(f"{'─'*60}")
            print(f"{'Escenario':<25} {'Tokens':>10} {'Latencia':>12} {'Costo':>12}")
            print(f"{'─'*60}")

            for scenario_id, metrics in comparison["metrics"].items():
                print(f"{scenario_id:<25} {metrics['tokens_total']:>10} {metrics['latency_ms']:>10.0f}ms ${metrics['cost_usd']:>10.6f}")

            print(f"{'─'*60}")

            if "winners" in comparison:
                print(f"\n🏆 GANADORES:")
                print(f"   Menos tokens:  {comparison['winners']['tokens']}")
                print(f"   Más rápido:    {comparison['winners']['latency']}")
                print(f"   Más barato:    {comparison['winners']['cost']}")

            if "differences" in comparison:
                print(f"\n📈 DIFERENCIAS:")
                diff = comparison["differences"]
                print(f"   Tokens:   {diff['tokens']:+d}")
                print(f"   Latencia: {diff['latency_ms']:+.0f} ms")
                print(f"   Costo:    ${diff['cost_usd']:+.6f}")

        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def load_test_queries(queries_file: str = None) -> tuple[list, dict]:
    """Carga queries de prueba desde archivo JSON o usa fallback"""
    if queries_file:
        file_path = project_root / queries_file
    else:
        file_path = project_root / DEFAULT_QUERIES_FILE

    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        queries = data.get("queries", [])
        metadata = {
            "escenario": data.get("escenario", ""),
            "fecha": data.get("fecha", ""),
            "delay_segundos": data.get("delay_segundos", 10),
            "categorias_cubiertas": data.get("categorias_cubiertas", []),
            "obras_sociales_cubiertas": data.get("obras_sociales_cubiertas", {})
        }
        print(f"📂 Queries cargadas desde: {file_path}")
        return queries, metadata
    else:
        print(f"⚠️  Archivo no encontrado: {file_path}")
        print(f"   Usando queries de fallback ({len(FALLBACK_QUERIES)} queries)")
        return FALLBACK_QUERIES, {"delay_segundos": 5}


def evaluate_response(respuesta: str, esperada: str) -> dict:
    """Evalúa si la respuesta contiene la información esperada"""
    if not esperada:
        return {"match": None, "reason": "Sin respuesta esperada definida"}

    respuesta_lower = respuesta.lower()
    esperada_lower = esperada.lower()

    # Dividir esperada en términos clave
    terminos = [t.strip() for t in esperada_lower.replace(",", " ").split() if len(t.strip()) > 2]

    # Contar cuántos términos clave aparecen en la respuesta
    matches = sum(1 for t in terminos if t in respuesta_lower)
    match_ratio = matches / len(terminos) if terminos else 0

    # Criterio: 60% de términos clave deben estar presentes
    is_match = match_ratio >= 0.6

    return {
        "match": is_match,
        "match_ratio": match_ratio,
        "terminos_esperados": len(terminos),
        "terminos_encontrados": matches,
        "reason": f"{matches}/{len(terminos)} términos clave"
    }


def calculate_costs(tokens_input: int, tokens_output: int) -> dict:
    """Calcula costos para plan FREE y PAGO"""
    return {
        "free": {
            "input_usd": 0.0,
            "output_usd": 0.0,
            "total_usd": 0.0,
            "nota": "Groq FREE - Sin costo real"
        },
        "paid": {
            "input_usd": (tokens_input / 1_000_000) * GROQ_COSTS["paid"]["input"],
            "output_usd": (tokens_output / 1_000_000) * GROQ_COSTS["paid"]["output"],
            "total_usd": (tokens_input / 1_000_000) * GROQ_COSTS["paid"]["input"] +
                        (tokens_output / 1_000_000) * GROQ_COSTS["paid"]["output"],
            "nota": f"Referencia si fuera Groq PAGO (${GROQ_COSTS['paid']['input']}/1M in, ${GROQ_COSTS['paid']['output']}/1M out)"
        }
    }


def calculate_percentile(values: list, percentile: int) -> float:
    """Calcula el percentil de una lista de valores"""
    if not values:
        return 0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * percentile / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_values) else f
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


# Límites Groq FREE tier (llama-3.3-70b-versatile)
GROQ_LIMITS = {
    "rpm": 30,      # Requests per minute
    "rpd": 1000,    # Requests per day
    "tpm": 12000,   # Tokens per minute
    "tpd": 100000   # Tokens per day
}


def run_batch(runner: ScenarioRunner, scenario: str, queries_file: str = None, delay: int = None):
    """Ejecuta batch de pruebas con evaluación de respuestas e informe completo"""

    # Cargar queries
    test_queries, metadata = load_test_queries(queries_file)
    query_delay = delay if delay is not None else metadata.get("delay_segundos", 10)

    print(f"\n{'='*70}")
    print(f"BATCH DE PRUEBAS - ESCENARIO 1")
    print(f"{'='*70}")
    print(f"Escenario:     {metadata.get('escenario', scenario)}")
    print(f"Total queries: {len(test_queries)}")
    print(f"Delay:         {query_delay} segundos entre queries")
    print(f"{'='*70}")

    # Crear experimento
    if runner._metrics_db:
        experiment_id = runner._metrics_db.create_experiment(
            name=f"escenario1_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Escenario 1: Modo Consulta + Groq FREE + RAG - {len(test_queries)} queries"
        )
        print(f"Experimento ID: {experiment_id}")
    else:
        experiment_id = None

    results = []
    total_tokens_input = 0
    total_tokens_output = 0
    correct_answers = 0

    # Acumuladores para tokens desglosados
    total_tokens_prompt = 0   # System prompt + template
    total_tokens_query = 0    # Query del usuario
    total_tokens_context = 0  # Contexto RAG (chunks)

    # Acumuladores para estadísticas detalladas
    latencies_total = []
    latencies_llm = []
    latencies_faiss = []
    latencies_embedding = []

    start_time = datetime.now()

    for i, test in enumerate(test_queries, 1):
        query_id = test.get("id", i)
        categoria = test.get("categoria", "N/A")
        obra_social = test.get("obra_social")
        query = test.get("query", "")
        esperada = test.get("respuesta_esperada", "")

        print(f"\n[{i}/{len(test_queries)}] ID:{query_id} | {categoria} | {obra_social or 'Sin OS'}")
        print(f"   📝 Query: {query[:60]}...")

        try:
            result = runner.run_query(
                scenario_id=scenario,
                query=query,
                obra_social=obra_social,
                experiment_id=experiment_id
            )

            metrics = result.get("metrics")
            total_tokens_input += metrics.tokens_input
            total_tokens_output += metrics.tokens_output

            # Acumular tokens desglosados
            total_tokens_prompt += metrics.tokens_prompt
            total_tokens_query += metrics.tokens_query
            total_tokens_context += metrics.tokens_context

            # Acumular latencias
            latencies_total.append(metrics.latency_total_ms)
            latencies_llm.append(metrics.latency_llm_ms)
            latencies_faiss.append(metrics.latency_faiss_ms)
            latencies_embedding.append(metrics.latency_embedding_ms)

            # Evaluar respuesta
            evaluation = evaluate_response(result['respuesta'], esperada)
            if evaluation["match"]:
                correct_answers += 1
                status_icon = "✅"
            elif evaluation["match"] is None:
                status_icon = "⚠️"
            else:
                status_icon = "❌"

            print(f"   {status_icon} {metrics.tokens_total} tokens, {metrics.latency_total_ms:.0f}ms")
            print(f"   💬 Respuesta: {result['respuesta'][:100]}...")
            print(f"   🎯 Esperado: {esperada[:60]}...")
            print(f"   📊 Evaluación: {evaluation['reason']}")

            results.append({
                "id": query_id,
                "categoria": categoria,
                "obra_social": obra_social,
                "query": query,
                "respuesta_esperada": esperada,
                "respuesta_real": result['respuesta'],
                "evaluacion": evaluation,
                "success": True,
                "entity": result.get('entity', {}),
                "rag_executed": result.get('rag_executed'),
                "llm_executed": result.get('llm_executed'),
                "chunks_count": result.get('chunks_count', 0),
                "top_similarity": result.get('top_similarity', 0),
                "chunks_info": result.get('chunks_info', []),
                "metrics": {
                    "tokens_input": metrics.tokens_input,
                    "tokens_output": metrics.tokens_output,
                    "tokens_total": metrics.tokens_total,
                    "tokens_prompt": metrics.tokens_prompt,
                    "tokens_query": metrics.tokens_query,
                    "tokens_context": metrics.tokens_context,
                    "latency_embedding_ms": metrics.latency_embedding_ms,
                    "latency_faiss_ms": metrics.latency_faiss_ms,
                    "latency_llm_ms": metrics.latency_llm_ms,
                    "latency_total_ms": metrics.latency_total_ms,
                    "response_words": metrics.response_words
                }
            })

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "id": query_id,
                "categoria": categoria,
                "obra_social": obra_social,
                "query": query,
                "respuesta_esperada": esperada,
                "respuesta_real": None,
                "evaluacion": {"match": False, "reason": f"Error: {str(e)}"},
                "success": False,
                "error": str(e)
            })

        # Delay entre queries (excepto la última)
        if i < len(test_queries) and query_delay > 0:
            print(f"   ⏳ Esperando {query_delay}s...")
            time.sleep(query_delay)

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULAR MÉTRICAS AGREGADAS
    # ═══════════════════════════════════════════════════════════════════════════
    costs = calculate_costs(total_tokens_input, total_tokens_output)
    successful = sum(1 for r in results if r["success"])
    total_tokens = total_tokens_input + total_tokens_output
    precision = correct_answers / len(test_queries) if test_queries else 0
    total_latency = sum(latencies_total)

    # Precisión por categoría
    precision_by_category = {}
    for r in results:
        cat = r.get('categoria', 'N/A')
        if cat not in precision_by_category:
            precision_by_category[cat] = {"total": 0, "correct": 0}
        precision_by_category[cat]["total"] += 1
        if r.get('evaluacion', {}).get('match'):
            precision_by_category[cat]["correct"] += 1

    # Precisión por obra social
    precision_by_os = {}
    for r in results:
        os_name = r.get('obra_social') or 'Sin OS'
        if os_name not in precision_by_os:
            precision_by_os[os_name] = {"total": 0, "correct": 0}
        precision_by_os[os_name]["total"] += 1
        if r.get('evaluacion', {}).get('match'):
            precision_by_os[os_name]["correct"] += 1

    # Queries fallidas
    failed_queries = [r for r in results if not r.get('evaluacion', {}).get('match')]

    # Estadísticas de latencia
    latency_stats = {
        "total": {
            "min": min(latencies_total) if latencies_total else 0,
            "max": max(latencies_total) if latencies_total else 0,
            "avg": sum(latencies_total) / len(latencies_total) if latencies_total else 0,
            "p50": calculate_percentile(latencies_total, 50),
            "p95": calculate_percentile(latencies_total, 95)
        },
        "llm": {
            "min": min(latencies_llm) if latencies_llm else 0,
            "max": max(latencies_llm) if latencies_llm else 0,
            "avg": sum(latencies_llm) / len(latencies_llm) if latencies_llm else 0,
            "p50": calculate_percentile(latencies_llm, 50),
            "p95": calculate_percentile(latencies_llm, 95)
        },
        "faiss": {
            "min": min(latencies_faiss) if latencies_faiss else 0,
            "max": max(latencies_faiss) if latencies_faiss else 0,
            "avg": sum(latencies_faiss) / len(latencies_faiss) if latencies_faiss else 0
        },
        "embedding": {
            "min": min(latencies_embedding) if latencies_embedding else 0,
            "max": max(latencies_embedding) if latencies_embedding else 0,
            "avg": sum(latencies_embedding) / len(latencies_embedding) if latencies_embedding else 0
        }
    }

    # Consumo de límites Groq
    groq_usage = {
        "tokens_used": total_tokens,
        "tokens_limit_daily": GROQ_LIMITS["tpd"],
        "tokens_percent": (total_tokens / GROQ_LIMITS["tpd"]) * 100,
        "requests_used": len(test_queries),
        "requests_limit_daily": GROQ_LIMITS["rpd"],
        "requests_percent": (len(test_queries) / GROQ_LIMITS["rpd"]) * 100
    }

    # ═══════════════════════════════════════════════════════════════════════════
    # INFORME FINAL EN CONSOLA
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'═'*80}")
    print(f"{'INFORME FINAL - ESCENARIO 1':^80}")
    print(f"{'═'*80}")
    print(f"Modo Consulta + CPU + Groq FREE + RAG + Sin Memoria Conversacional")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*80}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 1. RESUMEN EJECUTIVO
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"📋 1. RESUMEN EJECUTIVO")
    print(f"{'─'*80}")
    verdict = "✅ APROBADO" if precision >= 0.8 else "⚠️ REVISAR" if precision >= 0.6 else "❌ FALLIDO"
    print(f"   Veredicto:         {verdict}")
    print(f"   Precisión:         {precision*100:.1f}% ({correct_answers}/{len(test_queries)} correctas)")
    print(f"   Tokens totales:    {total_tokens:,}")
    print(f"   Latencia promedio: {latency_stats['total']['avg']:.0f}ms")
    print(f"   Costo (FREE):      $0.00 USD")

    # ─────────────────────────────────────────────────────────────────────────────
    # 2. EJECUCIÓN
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"📊 2. RESUMEN EJECUCIÓN")
    print(f"{'─'*80}")
    print(f"   Queries totales:   {len(test_queries)}")
    print(f"   Ejecutadas OK:     {successful}")
    print(f"   Con errores:       {len(test_queries) - successful}")
    print(f"   Tiempo total:      {elapsed:.0f} segundos ({elapsed/60:.1f} min)")

    # ─────────────────────────────────────────────────────────────────────────────
    # 3. PRECISIÓN POR CATEGORÍA
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"🎯 3. PRECISIÓN POR CATEGORÍA")
    print(f"{'─'*80}")
    print(f"   {'Categoría':<15} {'Correctas':>10} {'Total':>8} {'Precisión':>10}")
    print(f"   {'-'*45}")
    for cat, data in sorted(precision_by_category.items()):
        pct = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        icon = "✅" if pct >= 80 else "⚠️" if pct >= 60 else "❌"
        print(f"   {cat:<15} {data['correct']:>10} {data['total']:>8} {pct:>9.1f}% {icon}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 4. PRECISIÓN POR OBRA SOCIAL
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"🏥 4. PRECISIÓN POR OBRA SOCIAL")
    print(f"{'─'*80}")
    print(f"   {'Obra Social':<15} {'Correctas':>10} {'Total':>8} {'Precisión':>10}")
    print(f"   {'-'*45}")
    for os_name, data in sorted(precision_by_os.items()):
        pct = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        icon = "✅" if pct >= 80 else "⚠️" if pct >= 60 else "❌"
        print(f"   {os_name:<15} {data['correct']:>10} {data['total']:>8} {pct:>9.1f}% {icon}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 5. TOKENS (DESGLOSE POR COMPONENTE)
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"📈 5. TOKENS (DESGLOSE POR COMPONENTE)")
    print(f"{'─'*80}")

    # Promedios por query
    n_queries = len(test_queries)
    avg_prompt = total_tokens_prompt / n_queries if n_queries > 0 else 0
    avg_query = total_tokens_query / n_queries if n_queries > 0 else 0
    avg_context = total_tokens_context / n_queries if n_queries > 0 else 0
    avg_input = total_tokens_input / n_queries if n_queries > 0 else 0
    avg_output = total_tokens_output / n_queries if n_queries > 0 else 0
    avg_total = total_tokens / n_queries if n_queries > 0 else 0

    print(f"\n   ┌─ INPUT (enviado a Groq) ─────────────────────────────────────────────┐")
    print(f"   │                                                                        │")
    print(f"   │  {'Componente':<20} {'Total':>12} {'Promedio/Query':>18} {'%':>8}    │")
    print(f"   │  {'-'*60}    │")
    print(f"   │  {'System Prompt':<20} {total_tokens_prompt:>12,} {avg_prompt:>15.0f} tk {total_tokens_prompt/total_tokens_input*100 if total_tokens_input > 0 else 0:>7.1f}%   │")
    print(f"   │  {'Query Usuario':<20} {total_tokens_query:>12,} {avg_query:>15.0f} tk {total_tokens_query/total_tokens_input*100 if total_tokens_input > 0 else 0:>7.1f}%   │")
    print(f"   │  {'Contexto RAG':<20} {total_tokens_context:>12,} {avg_context:>15.0f} tk {total_tokens_context/total_tokens_input*100 if total_tokens_input > 0 else 0:>7.1f}%   │")
    print(f"   │  {'-'*60}    │")
    print(f"   │  {'TOTAL INPUT':<20} {total_tokens_input:>12,} {avg_input:>15.0f} tk {100.0:>7.1f}%   │")
    print(f"   │                                                                        │")
    print(f"   └────────────────────────────────────────────────────────────────────────┘")

    print(f"\n   ┌─ OUTPUT (respuesta de Groq) ──────────────────────────────────────────┐")
    print(f"   │                                                                        │")
    print(f"   │  {'Componente':<20} {'Total':>12} {'Promedio/Query':>18}             │")
    print(f"   │  {'-'*60}    │")
    print(f"   │  {'Respuesta LLM':<20} {total_tokens_output:>12,} {avg_output:>15.0f} tk             │")
    print(f"   │                                                                        │")
    print(f"   └────────────────────────────────────────────────────────────────────────┘")

    print(f"\n   ┌─ TOTALES ─────────────────────────────────────────────────────────────┐")
    print(f"   │                                                                        │")
    print(f"   │  Total Input:          {total_tokens_input:>10,} tokens                          │")
    print(f"   │  Total Output:         {total_tokens_output:>10,} tokens                          │")
    print(f"   │  ────────────────────────────────────                                  │")
    print(f"   │  TOTAL TEST:           {total_tokens:>10,} tokens                          │")
    print(f"   │  Promedio por Query:   {avg_total:>10.0f} tokens                          │")
    print(f"   │                                                                        │")
    print(f"   └────────────────────────────────────────────────────────────────────────┘")

    print(f"\n   📊 Desglose por Query:")
    print(f"   {'#':<3} {'Prompt':>8} {'Query':>8} {'RAG':>8} {'Input':>8} {'Output':>8} {'Total':>8}")
    print(f"   {'-'*60}")
    for r in results:
        m = r.get('metrics', {})
        print(f"   {r['id']:<3} {m.get('tokens_prompt', 0):>8} {m.get('tokens_query', 0):>8} {m.get('tokens_context', 0):>8} {m.get('tokens_input', 0):>8} {m.get('tokens_output', 0):>8} {m.get('tokens_total', 0):>8}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 6. LATENCIA (DESGLOSE RAG)
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"⏱️  6. LATENCIA (DESGLOSE RAG)")
    print(f"{'─'*80}")
    print(f"   {'Fase':<15} {'Min':>8} {'Max':>8} {'Avg':>8} {'P50':>8} {'P95':>8}")
    print(f"   {'-'*55}")
    print(f"   {'Embedding':<15} {latency_stats['embedding']['min']:>7.0f}ms {latency_stats['embedding']['max']:>7.0f}ms {latency_stats['embedding']['avg']:>7.0f}ms {'-':>8} {'-':>8}")
    print(f"   {'FAISS':<15} {latency_stats['faiss']['min']:>7.0f}ms {latency_stats['faiss']['max']:>7.0f}ms {latency_stats['faiss']['avg']:>7.0f}ms {'-':>8} {'-':>8}")
    print(f"   {'LLM (Groq)':<15} {latency_stats['llm']['min']:>7.0f}ms {latency_stats['llm']['max']:>7.0f}ms {latency_stats['llm']['avg']:>7.0f}ms {latency_stats['llm']['p50']:>7.0f}ms {latency_stats['llm']['p95']:>7.0f}ms")
    print(f"   {'-'*55}")
    print(f"   {'TOTAL':<15} {latency_stats['total']['min']:>7.0f}ms {latency_stats['total']['max']:>7.0f}ms {latency_stats['total']['avg']:>7.0f}ms {latency_stats['total']['p50']:>7.0f}ms {latency_stats['total']['p95']:>7.0f}ms")

    # ─────────────────────────────────────────────────────────────────────────────
    # 7. CONSUMO LÍMITES GROQ
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"📉 7. CONSUMO LÍMITES GROQ FREE")
    print(f"{'─'*80}")
    print(f"   Tokens:    {groq_usage['tokens_used']:>8,} / {groq_usage['tokens_limit_daily']:>8,} ({groq_usage['tokens_percent']:.1f}% del límite diario)")
    print(f"   Requests:  {groq_usage['requests_used']:>8} / {groq_usage['requests_limit_daily']:>8} ({groq_usage['requests_percent']:.1f}% del límite diario)")
    remaining_queries = int((GROQ_LIMITS["tpd"] - total_tokens) / (total_tokens / len(test_queries))) if total_tokens > 0 else GROQ_LIMITS["rpd"]
    print(f"   Queries restantes estimadas: ~{remaining_queries}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 8. COSTO
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"💰 8. COSTO")
    print(f"{'─'*80}")
    print(f"   ┌─ GROQ FREE (tier actual) ──────────────────────────────────────────┐")
    print(f"   │ Costo real:          $0.00 USD                                     │")
    print(f"   │ Nota: El plan gratuito de Groq no tiene costo por tokens           │")
    print(f"   └────────────────────────────────────────────────────────────────────┘")
    print(f"")
    print(f"   ┌─ GROQ PAGO (solo referencia) ──────────────────────────────────────┐")
    print(f"   │ Si estuvieras usando el plan PAGO de Groq:                         │")
    print(f"   │   Input:  {total_tokens_input:>8,} tokens × $0.59/1M = ${costs['paid']['input_usd']:.4f}           │")
    print(f"   │   Output: {total_tokens_output:>8,} tokens × $0.79/1M = ${costs['paid']['output_usd']:.4f}           │")
    print(f"   │   Total referencia:              ${costs['paid']['total_usd']:.4f} USD               │")
    print(f"   └────────────────────────────────────────────────────────────────────┘")

    # ─────────────────────────────────────────────────────────────────────────────
    # 9. QUERIES FALLIDAS
    # ─────────────────────────────────────────────────────────────────────────────
    if failed_queries:
        print(f"\n{'─'*80}")
        print(f"❌ 9. QUERIES FALLIDAS ({len(failed_queries)} de {len(test_queries)})")
        print(f"{'─'*80}")
        for r in failed_queries:
            print(f"\n   Query {r['id']} [{r.get('categoria', 'N/A')}] - {r.get('obra_social') or 'Sin OS'}")
            print(f"   Pregunta:  {r['query']}")
            print(f"   Esperado:  {r.get('respuesta_esperada', 'N/A')}")
            print(f"   Real:      {r.get('respuesta_real', 'Error')[:120] if r.get('respuesta_real') else 'Error'}...")
            print(f"   Eval:      {r.get('evaluacion', {}).get('reason', 'N/A')}")
            if r.get('chunks_info'):
                print(f"   Chunks usados:")
                for chunk in r.get('chunks_info', [])[:2]:
                    print(f"      - [{chunk.get('obra_social')}/{chunk.get('chunk_id')}] sim={chunk.get('similarity', 0):.3f}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 10. DETALLE DE QUERIES
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"📋 10. DETALLE DE QUERIES")
    print(f"{'─'*80}")
    print(f"   {'#':<3} {'Cat':<12} {'OS':<8} {'Tokens':>7} {'LLM':>6} {'Total':>6} {'Sim':>5} {'OK':>3}")
    print(f"   {'-'*55}")
    for r in results:
        cat = r.get('categoria', 'N/A')[:10]
        os_name = (r.get('obra_social') or 'N/A')[:6]
        tokens = r.get('metrics', {}).get('tokens_total', 0)
        llm_ms = r.get('metrics', {}).get('latency_llm_ms', 0)
        total_ms = r.get('metrics', {}).get('latency_total_ms', 0)
        sim = r.get('top_similarity', 0)
        ok = "✅" if r.get('evaluacion', {}).get('match') else "❌"
        print(f"   {r['id']:<3} {cat:<12} {os_name:<8} {tokens:>7} {llm_ms:>5.0f}ms {total_ms:>5.0f}ms {sim:>5.2f} {ok:>3}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 11. PREGUNTAS Y RESPUESTAS
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"📝 11. PREGUNTAS Y RESPUESTAS")
    print(f"{'─'*80}")
    for r in results:
        ok = "✅" if r.get('evaluacion', {}).get('match') else "❌"
        print(f"\n   {ok} Query {r['id']}: {r['query']}")
        print(f"      Esperado: {r.get('respuesta_esperada', 'N/A')}")
        real = r.get('respuesta_real', 'Error')
        if real:
            print(f"      Real:     {real[:150]}{'...' if len(real) > 150 else ''}")
        else:
            print(f"      Real:     [ERROR]")
        print(f"      Eval:     {r.get('evaluacion', {}).get('reason', 'N/A')}")

    # ─────────────────────────────────────────────────────────────────────────────
    # 12. RECOMENDACIONES
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"💡 12. RECOMENDACIONES")
    print(f"{'─'*80}")
    recommendations = []

    if precision < 0.8:
        recommendations.append("⚠️ Precisión < 80%: Revisar chunks de obras sociales con bajo rendimiento")

    # Categorías con problemas
    for cat, data in precision_by_category.items():
        pct = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        if pct < 60:
            recommendations.append(f"❌ Categoría '{cat}' con {pct:.0f}% precisión: Revisar documentación fuente")

    # OS con problemas
    for os_name, data in precision_by_os.items():
        pct = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        if pct < 60:
            recommendations.append(f"❌ Obra Social '{os_name}' con {pct:.0f}% precisión: Verificar indexación")

    if latency_stats['total']['p95'] > 3000:
        recommendations.append(f"⚠️ P95 latencia ({latency_stats['total']['p95']:.0f}ms) > 3s: Considerar optimización")

    if groq_usage['tokens_percent'] > 50:
        recommendations.append(f"⚠️ Consumo tokens al {groq_usage['tokens_percent']:.0f}% del límite diario")

    if not recommendations:
        recommendations.append("✅ Sistema funcionando correctamente. No hay acciones urgentes.")

    for rec in recommendations:
        print(f"   {rec}")

    print(f"\n{'═'*80}")

    # ═══════════════════════════════════════════════════════════════════════════
    # GUARDAR REPORTE JSON
    # ═══════════════════════════════════════════════════════════════════════════
    report_path = project_root / "reports" / f"escenario1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)

    report_data = {
        "escenario": "Escenario 1: Modo Consulta + CPU + Groq FREE + RAG + Sin Memoria",
        "timestamp": datetime.now().isoformat(),
        "experiment_id": experiment_id,
        "configuracion": {
            "scenario_id": scenario,
            "queries_file": str(queries_file or DEFAULT_QUERIES_FILE),
            "delay_segundos": query_delay,
            "categorias_cubiertas": metadata.get("categorias_cubiertas", []),
            "obras_sociales_cubiertas": metadata.get("obras_sociales_cubiertas", {})
        },
        "resumen_ejecutivo": {
            "veredicto": "APROBADO" if precision >= 0.8 else "REVISAR" if precision >= 0.6 else "FALLIDO",
            "precision": precision,
            "correct_answers": correct_answers,
            "total_queries": len(test_queries),
            "total_tokens": total_tokens,
            "latency_avg_ms": latency_stats['total']['avg'],
            "costo_usd": 0.0
        },
        "ejecucion": {
            "total_queries": len(test_queries),
            "successful": successful,
            "failed": len(test_queries) - successful,
            "elapsed_seconds": elapsed
        },
        "precision_por_categoria": {
            cat: {
                "correct": data["correct"],
                "total": data["total"],
                "precision": data["correct"] / data["total"] if data["total"] > 0 else 0
            }
            for cat, data in precision_by_category.items()
        },
        "precision_por_obra_social": {
            os_name: {
                "correct": data["correct"],
                "total": data["total"],
                "precision": data["correct"] / data["total"] if data["total"] > 0 else 0
            }
            for os_name, data in precision_by_os.items()
        },
        "tokens": {
            "totales": {
                "input": total_tokens_input,
                "output": total_tokens_output,
                "total": total_tokens
            },
            "desglose_input": {
                "system_prompt": total_tokens_prompt,
                "query_usuario": total_tokens_query,
                "contexto_rag": total_tokens_context
            },
            "promedios_por_query": {
                "prompt": avg_prompt,
                "query": avg_query,
                "contexto_rag": avg_context,
                "input_total": avg_input,
                "output": avg_output,
                "total": avg_total
            },
            "porcentajes_input": {
                "system_prompt": total_tokens_prompt / total_tokens_input * 100 if total_tokens_input > 0 else 0,
                "query_usuario": total_tokens_query / total_tokens_input * 100 if total_tokens_input > 0 else 0,
                "contexto_rag": total_tokens_context / total_tokens_input * 100 if total_tokens_input > 0 else 0
            }
        },
        "latencia": {
            "total_ms": total_latency,
            "promedio_ms": latency_stats['total']['avg'],
            "desglose": latency_stats
        },
        "groq_usage": groq_usage,
        "costo": {
            "groq_free": {
                "total_usd": 0.0,
                "nota": "Plan gratuito de Groq - sin costo por tokens"
            },
            "groq_pago_referencia": {
                "input_usd": costs['paid']['input_usd'],
                "output_usd": costs['paid']['output_usd'],
                "total_usd": costs['paid']['total_usd'],
                "nota": "Costo si estuvieras usando plan pago de Groq",
                "tarifas": {
                    "input_por_millon": GROQ_COSTS["paid"]["input"],
                    "output_por_millon": GROQ_COSTS["paid"]["output"]
                }
            }
        },
        "queries_fallidas": [
            {
                "id": r["id"],
                "categoria": r.get("categoria"),
                "obra_social": r.get("obra_social"),
                "query": r["query"],
                "esperada": r.get("respuesta_esperada"),
                "real": r.get("respuesta_real"),
                "chunks_info": r.get("chunks_info", [])
            }
            for r in failed_queries
        ],
        "recomendaciones": recommendations,
        "queries": results
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📁 Reporte JSON guardado: {report_path}")


def list_scenarios(runner: ScenarioRunner):
    """Lista escenarios disponibles"""
    print(f"\n{'='*60}")
    print("ESCENARIOS DISPONIBLES")
    print(f"{'='*60}")

    for scenario in runner.list_scenarios():
        status = "✅" if scenario["enabled"] else "❌"
        print(f"\n{status} {scenario['id']}")
        print(f"   Nombre:    {scenario['name']}")
        print(f"   Provider:  {scenario['provider']}")
        print(f"   Modelo:    {scenario['model']}")
        print(f"   Modo:      {scenario['mode']}")
        print(f"   {scenario['description']}")


def health_check(runner: ScenarioRunner):
    """Verifica estado del sistema"""
    print(f"\n{'='*60}")
    print("HEALTH CHECK")
    print(f"{'='*60}")

    status = runner.health_check()

    print(f"\n📚 RAG:")
    print(f"   Cargado:     {'✅' if status['rag_loaded'] else '❌'}")
    print(f"   Documentos:  {status['rag_documents']}")

    print(f"\n📊 Métricas:")
    print(f"   Habilitadas: {'✅' if status['metrics_enabled'] else '❌'}")

    print(f"\n🤖 Escenarios:")
    for scenario_id, scenario_status in status["scenarios"].items():
        if scenario_status["available"]:
            print(f"   ✅ {scenario_id}: {scenario_status['provider']}/{scenario_status['model']}")
        else:
            error = scenario_status.get("error", "No disponible")
            print(f"   ❌ {scenario_id}: {error}")


def main():
    parser = argparse.ArgumentParser(
        description="Ejecutor de escenarios del Agente Hospitalario",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/run_scenario.py --scenario groq_consulta --query "¿Qué necesito para IOSFA?"
  python scripts/run_scenario.py --compare --query "¿Mail de ASI?"
  python scripts/run_scenario.py --batch --scenario groq_consulta
  python scripts/run_scenario.py --batch --queries-file data/test_queries_escenario1.json --delay 10
  python scripts/run_scenario.py --list
  python scripts/run_scenario.py --health
        """
    )

    parser.add_argument("--scenario", "-s", type=str, default="groq_consulta",
                        help="ID del escenario a usar (default: groq_consulta)")
    parser.add_argument("--query", "-q", type=str,
                        help="Query a ejecutar")
    parser.add_argument("--obra-social", "-o", type=str,
                        help="Obra social para filtrar (ENSALUD, ASI, IOSFA)")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Comparar escenarios configurados")
    parser.add_argument("--batch", "-b", action="store_true",
                        help="Ejecutar batch de pruebas desde archivo JSON")
    parser.add_argument("--queries-file", type=str,
                        help=f"Archivo JSON con queries de prueba (default: {DEFAULT_QUERIES_FILE})")
    parser.add_argument("--delay", "-d", type=int,
                        help="Delay en segundos entre queries (default: 10 para Groq FREE)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="Listar escenarios disponibles")
    parser.add_argument("--health", action="store_true",
                        help="Verificar estado del sistema")
    parser.add_argument("--config", type=str,
                        help="Ruta al archivo de configuración (default: config/scenarios.yaml)")

    args = parser.parse_args()

    # Inicializar runner
    try:
        runner = ScenarioRunner(config_path=args.config)
    except Exception as e:
        print(f"❌ Error inicializando runner: {e}")
        sys.exit(1)

    # Ejecutar según argumentos
    if args.list:
        list_scenarios(runner)
    elif args.health:
        health_check(runner)
    elif args.batch:
        run_batch(runner, args.scenario, args.queries_file, args.delay)
    elif args.compare:
        if not args.query:
            print("❌ Se requiere --query para comparar")
            sys.exit(1)
        run_comparison(runner, args.query, args.obra_social)
    elif args.query:
        run_single_query(runner, args.scenario, args.query, args.obra_social)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
