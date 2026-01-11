#!/usr/bin/env python3
"""
Script para indexar chunks FINALES (*_FINAL.json) en FAISS

Uso:
    python scripts/index_data.py
"""
import sys
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.rag.indexer import DocumentIndexer
import os
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = backend_path / ".env"
load_dotenv(env_path)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
JSON_PATH = os.getenv("JSON_PATH", "../data/obras_sociales_json")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("📚 INDEXACIÓN DE CHUNKS FINALES - AGENTE HOSPITALARIO")
    print("="*70 + "\n")

    # Resolver paths relativos
    script_dir = Path(__file__).parent.parent
    json_path = (script_dir / JSON_PATH).resolve()
    index_path = (backend_path / FAISS_INDEX_PATH).resolve()

    print(f"📁 Configuración:")
    print(f"   Chunks JSON: {json_path}")
    print(f"   Índice de salida: {index_path}")
    print(f"   Modelo: {EMBEDDING_MODEL}\n")

    # Verificar que exista el directorio
    if not json_path.exists():
        print(f"❌ Error: No existe {json_path}")
        return 1

    # Crear indexador
    indexer = DocumentIndexer(embedding_model=EMBEDDING_MODEL)

    # Indexar desde JSONs
    try:
        stats = indexer.index_from_json(json_path=str(json_path))

        # Guardar índice
        indexer.save_index(str(index_path))

        print("\n" + "="*70)
        print("✅ INDEXACIÓN COMPLETADA EXITOSAMENTE")
        print("="*70)
        print(f"\n📊 Estadísticas:")
        print(f"   Archivos JSON procesados: {stats['total_documentos']}")
        print(f"   Total chunks indexados: {stats['total_chunks']}")
        print(f"   Obras sociales: {stats['obras_sociales']}")
        print(f"\n💾 Índice guardado en: {index_path}")
        print(f"\n🚀 Ahora podés iniciar el backend:")
        print(f"   cd backend")
        print(f"   uvicorn app.main:app --reload\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error durante la indexación: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
