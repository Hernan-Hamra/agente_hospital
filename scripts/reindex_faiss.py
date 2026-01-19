#!/usr/bin/env python3
"""
Re-indexa todos los chunks en FAISS.

Uso:
    python scripts/reindex_faiss.py

Fuente:
    data/obras_sociales_json/*/  (todos los *_chunks_flat.json)

Output:
    backend/faiss_index/
"""
import sys
from pathlib import Path

# Agregar backend al path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from app.rag.indexer import DocumentIndexer


def main():
    # Rutas
    json_path = project_root / "data" / "obras_sociales_json"
    index_path = backend_path / "faiss_index"

    print("="*60)
    print("RE-INDEXACIÓN FAISS")
    print("="*60)
    print(f"\n📁 Fuente: {json_path}")
    print(f"💾 Destino: {index_path}")

    # Verificar que existan JSONs
    json_files = list(json_path.glob("**/*_chunks_flat.json"))
    print(f"\n📄 Archivos encontrados: {len(json_files)}")
    for f in json_files:
        print(f"   - {f.relative_to(json_path)}")

    if not json_files:
        print("\n❌ No se encontraron archivos *_chunks_flat.json")
        return

    # Crear indexador (usar modelo original del proyecto)
    print("\n" + "="*60)
    indexer = DocumentIndexer(
        embedding_model="BAAI/bge-large-en-v1.5"
    )

    # Indexar
    stats = indexer.index_from_json(str(json_path))

    # Guardar
    indexer.save_index(str(index_path))

    # Mostrar resumen por obra social
    print("\n" + "="*60)
    print("📊 RESUMEN POR OBRA SOCIAL:")
    print("="*60)
    by_os = {}
    for doc in indexer.documents:
        os = doc.get('obra_social', 'UNKNOWN')
        by_os[os] = by_os.get(os, 0) + 1

    for os, count in sorted(by_os.items()):
        print(f"   {os}: {count} chunks")

    print("\n✅ Indexación completada!")
    print(f"   Total chunks: {len(indexer.documents)}")


if __name__ == "__main__":
    main()
