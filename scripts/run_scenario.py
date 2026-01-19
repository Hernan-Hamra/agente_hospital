#!/usr/bin/env python3
"""
Script para ejecutar escenarios de prueba.

Uso:
    # Ejecutar una query en un escenario específico
    python scripts/run_scenario.py --scenario groq_consulta --query "¿Qué documentos necesito para IOSFA?"

    # Comparar dos escenarios
    python scripts/run_scenario.py --compare --query "¿Cuál es el mail de ASI?"

    # Ejecutar batch de pruebas
    python scripts/run_scenario.py --batch --scenario groq_consulta

    # Ver escenarios disponibles
    python scripts/run_scenario.py --list

    # Health check
    python scripts/run_scenario.py --health
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Agregar backend al path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from app.scenarios.runner import ScenarioRunner


# Queries de prueba predefinidas
TEST_QUERIES = [
    {"query": "¿Qué documentos necesito para una consulta en IOSFA?", "obra_social": "IOSFA"},
    {"query": "¿Cuál es el mail de Mesa Operativa de ASI?", "obra_social": "ASI"},
    {"query": "¿Necesito orden médica para guardia?", "obra_social": None},
    {"query": "Requisitos para internación programada", "obra_social": "IOSFA"},
    {"query": "¿Cuál es el teléfono de ENSALUD?", "obra_social": "ENSALUD"},
]


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


def run_batch(runner: ScenarioRunner, scenario: str):
    """Ejecuta batch de pruebas"""
    print(f"\n{'='*60}")
    print(f"BATCH DE PRUEBAS - {scenario}")
    print(f"{'='*60}")

    # Crear experimento
    if runner._metrics_db:
        experiment_id = runner._metrics_db.create_experiment(
            name=f"batch_{scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Batch de {len(TEST_QUERIES)} queries en {scenario}"
        )
        print(f"Experimento ID: {experiment_id}")
    else:
        experiment_id = None

    results = []
    total_tokens = 0
    total_cost = 0
    total_latency = 0

    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] {test['query'][:50]}...")

        try:
            result = runner.run_query(
                scenario_id=scenario,
                query=test["query"],
                obra_social=test.get("obra_social"),
                experiment_id=experiment_id
            )

            metrics = result.get("metrics")
            total_tokens += metrics.tokens_total
            total_cost += metrics.cost_total
            total_latency += metrics.latency_total_ms

            print(f"   ✅ {metrics.tokens_total} tokens, {metrics.latency_total_ms:.0f}ms, ${metrics.cost_total:.6f}")
            results.append({"success": True, **test, "metrics": metrics.to_dict()})

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({"success": False, **test, "error": str(e)})

    # Resumen
    successful = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}")
    print(f"RESUMEN BATCH")
    print(f"{'='*60}")
    print(f"Queries ejecutadas: {len(TEST_QUERIES)}")
    print(f"Exitosas:           {successful}")
    print(f"Fallidas:           {len(TEST_QUERIES) - successful}")
    print(f"{'─'*60}")
    print(f"Total tokens:       {total_tokens}")
    print(f"Total latencia:     {total_latency:.0f} ms")
    print(f"Total costo:        ${total_cost:.6f} USD")
    print(f"{'─'*60}")
    print(f"Promedio tokens:    {total_tokens/len(TEST_QUERIES):.0f}")
    print(f"Promedio latencia:  {total_latency/len(TEST_QUERIES):.0f} ms")
    print(f"Promedio costo:     ${total_cost/len(TEST_QUERIES):.6f} USD")

    # Guardar resultados
    report_path = project_root / "reports" / f"batch_{scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "scenario": scenario,
            "timestamp": datetime.now().isoformat(),
            "experiment_id": experiment_id,
            "summary": {
                "total_queries": len(TEST_QUERIES),
                "successful": successful,
                "total_tokens": total_tokens,
                "total_latency_ms": total_latency,
                "total_cost_usd": total_cost
            },
            "results": results
        }, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nReporte guardado: {report_path}")


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
                        help="Ejecutar batch de pruebas predefinidas")
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
        run_batch(runner, args.scenario)
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
