#!/usr/bin/env python3
"""
Script para indexar documentos PDF/DOCX en FAISS

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
DATA_PATH = os.getenv("DATA_PATH", "../data/obras_sociales")
DOCS_PATH = os.getenv("DOCS_PATH", "../docs")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("📚 INDEXACIÓN DE DOCUMENTOS - AGENTE HOSPITALARIO")
    print("="*70 + "\n")

    # Resolver paths relativos
    script_dir = Path(__file__).parent.parent
    data_path = (script_dir / DATA_PATH).resolve()
    docs_path = (script_dir / DOCS_PATH).resolve()
    index_path = (backend_path / FAISS_INDEX_PATH).resolve()

    print(f"📁 Configuración:")
    print(f"   Obras sociales: {data_path}")
    print(f"   Documentos generales: {docs_path}")
    print(f"   Índice de salida: {index_path}")
    print(f"   Chunk size: {CHUNK_SIZE} caracteres")
    print(f"   Chunk overlap: {CHUNK_OVERLAP} caracteres\n")

    # Verificar que existan los directorios
    if not data_path.exists():
        print(f"❌ Error: No existe {data_path}")
        return 1

    if not docs_path.exists():
        print(f"⚠️ Advertencia: No existe {docs_path} (se omitirán docs generales)")
        docs_path = None

    # Crear indexador
    indexer = DocumentIndexer(embedding_model=EMBEDDING_MODEL)

    # Indexar documentos
    try:
        stats = indexer.index_documents(
            data_path=str(data_path),
            docs_path=str(docs_path) if docs_path else None,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        # Guardar índice
        indexer.save_index(str(index_path))

        print("\n" + "="*70)
        print("✅ INDEXACIÓN COMPLETADA EXITOSAMENTE")
        print("="*70)
        print(f"\n📊 Estadísticas:")
        print(f"   Total documentos: {stats['total_documentos']}")
        print(f"   Total chunks: {stats['total_chunks']}")
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
