"""
Demo de preguntas y respuestas para mostrar a Patricia.

Ejecutar: python3 escenario_2/tests/demo_preguntas_respuestas.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlite3
from escenario_2.core.normalizer import Normalizer
from escenario_2.core.query_engine import QueryEngine


def demo():
    """Muestra preguntas y respuestas del bot."""
    db_path = Path(__file__).parent.parent / "data" / "obras_sociales.db"

    conn = sqlite3.connect(db_path)
    normalizer = Normalizer(conn)
    engine = QueryEngine(conn)

    # Preguntas de ejemplo que haría un empleado de admisión
    preguntas = [
        # Ambulatorio
        "ambulatorio ensalud",
        "turnos asi",

        # Internación
        "internación ensalud",

        # Guardia
        "guardia ensalud",

        # Coseguros
        "coseguros ensalud",

        # Casos que faltan info
        "hola",
        "ensalud",
        "internación",
    ]

    print("=" * 70)
    print("DEMO: PREGUNTAS Y RESPUESTAS DEL BOT")
    print("=" * 70)

    for pregunta in preguntas:
        print(f"\n{'─' * 70}")
        print(f"👤 EMPLEADO: {pregunta}")
        print(f"{'─' * 70}")

        # Normalizar
        normalized = normalizer.normalize(pregunta)

        # Detectar si es coseguro
        if any(word in pregunta.lower() for word in ['coseguro', 'copago']):
            if normalized.obra_social:
                result = engine.query_coseguros(normalized.obra_social)
            else:
                result = engine.query(normalized)
        else:
            result = engine.query(normalized)

        print(f"\n🤖 BOT:\n{result.respuesta}")

    print(f"\n{'=' * 70}")
    print("FIN DEMO")
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    demo()
