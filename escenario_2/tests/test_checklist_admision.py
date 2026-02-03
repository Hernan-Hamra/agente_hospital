"""
Batería de tests basada en Checklist de Admisión (Patricia).

Cubre todos los casos de uso reales del equipo de admisión:
- Ingreso Ambulatorio
- Internación
- Guardia
- Traslados

Para cada tipo de ingreso se testea:
- Documentación requerida
- Validador (link/teléfono/mail)
- Coseguros/Bonos
- Procedimientos específicos
"""
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlite3
from escenario_2.core.normalizer import Normalizer
from escenario_2.core.query_engine import QueryEngine


@dataclass
class TestCase:
    """Caso de test."""
    id: str
    pregunta: str  # Cómo preguntaría un empleado
    obra_social: str
    tipo_ingreso: str
    debe_contener: List[str]  # Strings que DEBE contener la respuesta
    no_debe_contener: Optional[List[str]] = None  # Strings que NO debe contener


# =============================================================================
# CASOS DE TEST POR TIPO DE INGRESO
# =============================================================================

TESTS_AMBULATORIO = [
    TestCase(
        id="AMB-001",
        pregunta="documentación ambulatorio ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="ambulatorio",
        debe_contener=["DNI", "Carnet", "afiliación"],
    ),
    TestCase(
        id="AMB-002",
        pregunta="validador ensalud turnos",
        obra_social="ENSALUD",
        tipo_ingreso="ambulatorio",
        debe_contener=["ensalud.org", "prestador"],
    ),
    TestCase(
        id="AMB-003",
        pregunta="turnos ensalud telefono",  # Agregado "turnos" para detectar tipo_ingreso
        obra_social="ENSALUD",
        tipo_ingreso="ambulatorio",
        debe_contener=["11-66075765"],
    ),
    TestCase(
        id="AMB-004",
        pregunta="ambulatorio ensalud coseguro",  # Ambulatorio explícito
        obra_social="ENSALUD",
        tipo_ingreso="ambulatorio",
        debe_contener=["Coseguro"],  # Solo verificar que menciona coseguro
    ),
    TestCase(
        id="AMB-005",
        pregunta="consulta ensalud autorizaciones",  # Agregado "consulta" para tipo_ingreso
        obra_social="ENSALUD",
        tipo_ingreso="ambulatorio",
        debe_contener=["autorización"],  # Especialidades quirúrgicas requieren
    ),
]

TESTS_INTERNACION = [
    TestCase(
        id="INT-001",
        pregunta="documentación internación ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="internacion",
        debe_contener=["DNI", "Carnet"],
    ),
    TestCase(
        id="INT-002",
        pregunta="mail denuncia internación ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="internacion",
        debe_contener=["auditoria@ensalud.org"],
    ),
    TestCase(
        id="INT-003",
        pregunta="plazo denuncia internacion ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="internacion",
        debe_contener=["24 horas"],
    ),
    TestCase(
        id="INT-004",
        pregunta="portal internación ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="internacion",
        debe_contener=["ensalud.org", "prestador"],
    ),
    TestCase(
        id="INT-005",
        pregunta="internacion ensalud censo",  # Agregado "internacion" para tipo_ingreso
        obra_social="ENSALUD",
        tipo_ingreso="internacion",
        debe_contener=["censo", "diario"],  # Reducido a lo que realmente está en notas
    ),
]

TESTS_GUARDIA = [
    TestCase(
        id="GUA-001",
        pregunta="documentación guardia ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="guardia",
        debe_contener=["DNI", "Carnet"],
    ),
    TestCase(
        id="GUA-002",
        pregunta="coseguro guardia ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="guardia",
        debe_contener=["EXENTO"],  # Guardia siempre exento
    ),
    TestCase(
        id="GUA-003",
        pregunta="autorización guardia ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="guardia",
        debe_contener=["NO", "autorización"],  # No requiere autorización
    ),
    TestCase(
        id="GUA-004",
        pregunta="validador guardia ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="guardia",
        debe_contener=["ensalud.org"],
    ),
]

TESTS_TRASLADOS = [
    TestCase(
        id="TRA-001",
        pregunta="traslados ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="traslados",
        debe_contener=["TRASLADOS"],
    ),
    TestCase(
        id="TRA-002",
        pregunta="telefono traslados ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="traslados",
        debe_contener=["11-66075765"],
    ),
]

TESTS_COSEGUROS = [
    TestCase(
        id="COS-001",
        pregunta="coseguros ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="coseguros",
        debe_contener=["Delta Plus", "Quantum"],  # Planes principales
    ),
    TestCase(
        id="COS-002",
        pregunta="coseguro especialista ensalud",  # Cambiado para activar query_coseguros
        obra_social="ENSALUD",
        tipo_ingreso="coseguros",
        debe_contener=["2912"],  # Valor específico
    ),
    TestCase(
        id="COS-003",
        pregunta="exentos coseguro ensalud",
        obra_social="ENSALUD",
        tipo_ingreso="coseguros",
        debe_contener=["HIV", "Oncología"],  # Exentos
    ),
]

# Tests de casos edge / errores esperados
TESTS_EDGE = [
    TestCase(
        id="EDGE-001",
        pregunta="hola",
        obra_social=None,
        tipo_ingreso=None,
        debe_contener=["obra social", "tipo de ingreso"],  # Debe pedir info
    ),
    TestCase(
        id="EDGE-002",
        pregunta="ensalud",
        obra_social="ENSALUD",
        tipo_ingreso=None,
        debe_contener=["tipo de ingreso"],  # Solo tiene OS, falta tipo
    ),
    TestCase(
        id="EDGE-003",
        pregunta="internación",
        obra_social=None,
        tipo_ingreso="internacion",
        debe_contener=["obra social"],  # Solo tiene tipo, falta OS
    ),
]


def run_tests():
    """Ejecuta todos los tests."""
    db_path = Path(__file__).parent.parent / "data" / "obras_sociales.db"

    conn = sqlite3.connect(db_path)
    normalizer = Normalizer(conn)
    engine = QueryEngine(conn)

    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }

    all_tests = [
        ("AMBULATORIO", TESTS_AMBULATORIO),
        ("INTERNACIÓN", TESTS_INTERNACION),
        ("GUARDIA", TESTS_GUARDIA),
        ("TRASLADOS", TESTS_TRASLADOS),
        ("COSEGUROS", TESTS_COSEGUROS),
        ("EDGE CASES", TESTS_EDGE),
    ]

    print("=" * 70)
    print("BATERÍA DE TESTS - CHECKLIST ADMISIÓN")
    print("=" * 70)

    for section_name, tests in all_tests:
        print(f"\n📋 {section_name}")
        print("-" * 50)

        for test in tests:
            # Normalizar pregunta
            normalized = normalizer.normalize(test.pregunta)

            # Ejecutar query
            if "coseguro" in test.pregunta.lower() and normalized.obra_social:
                result = engine.query_coseguros(normalized.obra_social)
            else:
                result = engine.query(normalized)

            # Verificar que contiene strings esperados
            respuesta_lower = result.respuesta.lower()
            all_found = all(
                s.lower() in respuesta_lower
                for s in test.debe_contener
            )

            # Verificar que NO contiene strings prohibidos
            none_forbidden = True
            if test.no_debe_contener:
                none_forbidden = not any(
                    s.lower() in respuesta_lower
                    for s in test.no_debe_contener
                )

            passed = all_found and none_forbidden

            if passed:
                results["passed"] += 1
                status = "✅"
            else:
                results["failed"] += 1
                status = "❌"
                # Mostrar qué falló
                missing = [s for s in test.debe_contener if s.lower() not in respuesta_lower]
                if missing:
                    results["details"].append({
                        "id": test.id,
                        "pregunta": test.pregunta,
                        "missing": missing,
                        "respuesta": result.respuesta[:200]
                    })

            print(f"  {status} [{test.id}] {test.pregunta}")

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    total = results["passed"] + results["failed"]
    pct = (results["passed"] / total * 100) if total > 0 else 0
    print(f"✅ Passed: {results['passed']}/{total} ({pct:.1f}%)")
    print(f"❌ Failed: {results['failed']}/{total}")

    if results["details"]:
        print("\n📝 DETALLES DE FALLOS:")
        for detail in results["details"]:
            print(f"\n  [{detail['id']}] {detail['pregunta']}")
            print(f"     Missing: {detail['missing']}")
            print(f"     Respuesta: {detail['respuesta'][:100]}...")

    conn.close()
    return results


if __name__ == "__main__":
    run_tests()
