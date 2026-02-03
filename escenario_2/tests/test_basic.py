"""
Tests básicos para Escenario 2.
"""
import sys
from pathlib import Path

# Agregar parent al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlite3
from escenario_2.core.normalizer import Normalizer
from escenario_2.core.query_engine import QueryEngine


def test_all():
    """Ejecuta todos los tests."""
    db_path = Path(__file__).parent.parent / "data" / "obras_sociales.db"

    conn = sqlite3.connect(db_path)
    normalizer = Normalizer(conn)
    engine = QueryEngine(conn)

    print("=" * 60)
    print("TESTS ESCENARIO 2 - SQL SIN LLM")
    print("=" * 60)

    # Test 1: Normalización
    print("\n📝 Test 1: Normalización")
    tests_norm = [
        ("internación ensalud", "ENSALUD", "internacion"),
        ("guardia asi", "ASI", "guardia"),
        ("turnos iosfa", "IOSFA", "ambulatorio"),
        ("ambulatorio en salud", "ENSALUD", "ambulatorio"),
    ]

    for text, expected_os, expected_tipo in tests_norm:
        result = normalizer.normalize(text)
        status = "✅" if result.obra_social == expected_os and result.tipo_ingreso == expected_tipo else "❌"
        print(f"  {status} '{text}' → OS={result.obra_social}, tipo={result.tipo_ingreso}")

    # Test 2: Query Engine
    print("\n📝 Test 2: Query Engine")
    tests_query = [
        ("ambulatorio ensalud", True),
        ("internacion ensalud", True),
        ("guardia ensalud", True),
        ("traslados ensalud", True),
    ]

    for text, should_succeed in tests_query:
        normalized = normalizer.normalize(text)
        result = engine.query(normalized)
        status = "✅" if result.success == should_succeed else "❌"
        print(f"  {status} '{text}' → success={result.success}")
        if result.success:
            print(f"      Preview: {result.respuesta[:80]}...")

    # Test 3: Coseguros
    print("\n📝 Test 3: Coseguros")
    result = engine.query_coseguros("ENSALUD")
    status = "✅" if result.success else "❌"
    print(f"  {status} Coseguros ENSALUD → success={result.success}")
    if result.success:
        print(f"      Preview: {result.respuesta[:100]}...")

    # Test 4: Casos edge
    print("\n📝 Test 4: Casos edge (sin info completa)")
    edge_cases = [
        ("hola", False),  # Sin OS ni tipo
        ("ensalud", False),  # Solo OS
        ("internacion", False),  # Solo tipo
    ]

    for text, should_succeed in edge_cases:
        normalized = normalizer.normalize(text)
        result = engine.query(normalized)
        status = "✅" if result.success == should_succeed else "❌"
        print(f"  {status} '{text}' → is_valid={normalized.is_valid}, success={result.success}")
        if not result.success and result.error == "missing_info":
            print(f"      Msg: {result.respuesta[:60]}...")

    print("\n" + "=" * 60)
    print("TESTS COMPLETADOS")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    test_all()
