"""
Tests para restricciones temporales de obras sociales.

Casos de uso:
- Falta de pago: solo permite guardia
- Convenio suspendido: bloquea todo
- Cupo agotado: bloquea internaciones programadas
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlite3
from escenario_2.core.normalizer import Normalizer
from escenario_2.core.query_engine import QueryEngine


def test_restricciones():
    """Test completo de restricciones temporales."""
    db_path = Path(__file__).parent.parent / "data" / "obras_sociales.db"

    conn = sqlite3.connect(db_path)
    normalizer = Normalizer(conn)
    engine = QueryEngine(conn)

    print("=" * 70)
    print("TESTS DE RESTRICCIONES TEMPORALES")
    print("=" * 70)

    # =========================================================================
    # Test 1: Sin restricciones - comportamiento normal
    # =========================================================================
    print("\n📋 Test 1: Sin restricciones (comportamiento normal)")

    normalized = normalizer.normalize("internación ensalud")
    result = engine.query(normalized)

    assert result.success, "Debería funcionar sin restricciones"
    assert "⛔" not in result.respuesta, "No debería tener alerta"
    print("  ✅ Internación ENSALUD funciona normalmente")

    # =========================================================================
    # Test 2: Agregar restricción - solo guardia permitida
    # =========================================================================
    print("\n📋 Test 2: Restricción por falta de pago (solo guardia)")

    # Agregar restricción
    success = engine.add_restriccion(
        obra_social="ENSALUD",
        tipo_restriccion="falta_pago",
        mensaje="ENSALUD tiene pagos pendientes. Solo se permite ingreso por GUARDIA.",
        tipos_permitidos="guardia"
    )
    assert success, "Debería agregar la restricción"
    print("  ✅ Restricción agregada")

    # Verificar que guardia sigue funcionando SIN alerta
    normalized = normalizer.normalize("guardia ensalud")
    result = engine.query(normalized)
    assert result.success, "Guardia debería funcionar"
    assert "⛔" not in result.respuesta, "Guardia NO debería tener alerta"
    print("  ✅ Guardia funciona sin alerta")

    # Verificar que internación muestra alerta
    normalized = normalizer.normalize("internación ensalud")
    result = engine.query(normalized)
    assert result.success, "Debería devolver info pero con alerta"
    assert "⛔" in result.respuesta, "Internación DEBE mostrar alerta"
    assert "pagos pendientes" in result.respuesta.lower(), "Debe mencionar el motivo"
    print("  ✅ Internación muestra alerta de restricción")
    print(f"     Preview: {result.respuesta[:80]}...")

    # Verificar que ambulatorio también muestra alerta
    normalized = normalizer.normalize("ambulatorio ensalud")
    result = engine.query(normalized)
    assert "⛔" in result.respuesta, "Ambulatorio DEBE mostrar alerta"
    print("  ✅ Ambulatorio muestra alerta de restricción")

    # =========================================================================
    # Test 3: Listar restricciones activas
    # =========================================================================
    print("\n📋 Test 3: Listar restricciones activas")

    restricciones = engine.list_restricciones()
    assert len(restricciones) >= 1, "Debe haber al menos 1 restricción"
    print(f"  ✅ Restricciones activas: {len(restricciones)}")
    for r in restricciones:
        print(f"     - {r['obra_social_codigo']}: {r['tipo_restriccion']}")

    # =========================================================================
    # Test 4: Remover restricción
    # =========================================================================
    print("\n📋 Test 4: Remover restricción")

    count = engine.remove_restriccion("ENSALUD", "falta_pago")
    assert count >= 1, "Debería remover al menos 1 restricción"
    print(f"  ✅ Restricciones removidas: {count}")

    # Verificar que internación ya no muestra alerta
    normalized = normalizer.normalize("internación ensalud")
    result = engine.query(normalized)
    assert "⛔" not in result.respuesta, "Ya no debería tener alerta"
    print("  ✅ Internación funciona normalmente de nuevo")

    # =========================================================================
    # Test 5: Restricción con tipos bloqueados específicos
    # =========================================================================
    print("\n📋 Test 5: Restricción con tipos bloqueados específicos")

    # Agregar restricción que solo bloquea internación y traslados
    engine.add_restriccion(
        obra_social="ENSALUD",
        tipo_restriccion="cupo_agotado",
        mensaje="Cupo de internaciones agotado para este mes.",
        tipos_bloqueados="internacion,traslados"
    )

    # Verificar ambulatorio SIN alerta
    normalized = normalizer.normalize("ambulatorio ensalud")
    result = engine.query(normalized)
    assert "⛔" not in result.respuesta, "Ambulatorio NO debe tener alerta"
    print("  ✅ Ambulatorio funciona sin alerta")

    # Verificar guardia SIN alerta
    normalized = normalizer.normalize("guardia ensalud")
    result = engine.query(normalized)
    assert "⛔" not in result.respuesta, "Guardia NO debe tener alerta"
    print("  ✅ Guardia funciona sin alerta")

    # Verificar internación CON alerta
    normalized = normalizer.normalize("internación ensalud")
    result = engine.query(normalized)
    assert "⛔" in result.respuesta, "Internación DEBE tener alerta"
    print("  ✅ Internación muestra alerta")

    # Limpiar
    engine.remove_restriccion("ENSALUD")

    print("\n" + "=" * 70)
    print("TODOS LOS TESTS PASARON")
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    test_restricciones()
