#!/usr/bin/env python3
"""
Ejecuta todos los tests de escenario_1 y genera informe
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

TESTS_DIR = Path(__file__).parent


def run_pytest_module(module_path: Path, test_name: str) -> dict:
    """Ejecuta un módulo pytest y retorna resultados"""
    print(f"\n{test_name}")
    print("─" * 70)

    # Ejecutar pytest con salida verbose pero sin capturar stdout
    result = pytest.main([
        str(module_path),
        "-v",
        "--tb=short",
        "-q"
    ])

    passed = result == pytest.ExitCode.OK
    return {
        "status": "PASSED" if passed else "FAILED",
        "exit_code": int(result)
    }


def run_all_tests():
    """Ejecuta todos los tests y retorna resultados"""
    print("=" * 70)
    print("BATERÍA DE TESTS - ESCENARIO 1")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = {
        "fecha": datetime.now().isoformat(),
        "escenario": "escenario_1",
        "tests": {}
    }

    # Test Entity Detector
    print("\n" + "─" * 70)
    print("1. ENTITY DETECTOR")
    ed_result = run_pytest_module(TESTS_DIR / "test_entity_detector.py", "Entity Detector")
    results["tests"]["entity_detector"] = ed_result
    ed_ok = ed_result["status"] == "PASSED"

    # Test Query Rewriter
    print("\n" + "─" * 70)
    print("2. QUERY REWRITER")
    qr_result = run_pytest_module(TESTS_DIR / "test_query_rewriter.py", "Query Rewriter")
    results["tests"]["query_rewriter"] = qr_result
    qr_ok = qr_result["status"] == "PASSED"

    # Test Retriever
    print("\n" + "─" * 70)
    print("3. RETRIEVER (ChromaDB)")
    ret_result = run_pytest_module(TESTS_DIR / "test_retriever.py", "Retriever")
    results["tests"]["retriever"] = ret_result
    ret_ok = ret_result["status"] == "PASSED"

    # Resumen
    all_passed = ed_ok and qr_ok and ret_ok

    print("\n" + "=" * 70)
    print("RESUMEN BATERÍA DE TESTS")
    print("=" * 70)
    print(f"  Entity Detector: {'✅ PASSED' if ed_ok else '❌ FAILED'}")
    print(f"  Query Rewriter:  {'✅ PASSED' if qr_ok else '❌ FAILED'}")
    print(f"  Retriever:       {'✅ PASSED' if ret_ok else '❌ FAILED'}")
    print("=" * 70)
    print(f"RESULTADO FINAL: {'✅ TESTS UNITARIOS PASARON' if all_passed else '❌ ALGUNOS TESTS FALLARON'}")
    print("=" * 70)

    # Guardar informe
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"reporte_unitarios_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Informe guardado: {report_file}")

    return all_passed, results


if __name__ == "__main__":
    success, _ = run_all_tests()
    sys.exit(0 if success else 1)
