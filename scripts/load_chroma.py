#!/usr/bin/env python3
"""
Script para cargar chunks en ChromaDB
Uso: python scripts/load_chroma.py [--test-query "consulta"]
"""
import sys
import os
import argparse
import logging

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.rag.retriever_chroma import ChromaRetriever, load_chunks_from_json_files

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Cargar chunks en ChromaDB')
    parser.add_argument('--data-dir', default='data/obras_sociales_json',
                        help='Directorio con los JSONs de chunks')
    parser.add_argument('--test-query', type=str, default=None,
                        help='Query de prueba después de cargar')
    parser.add_argument('--test-obra-social', type=str, default=None,
                        help='Obra social para filtrar en test')
    parser.add_argument('--reset', action='store_true',
                        help='Eliminar colección existente antes de cargar')
    args = parser.parse_args()

    # Ruta absoluta al directorio de datos
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        args.data_dir
    )

    logger.info(f"Inicializando ChromaRetriever...")
    retriever = ChromaRetriever()

    # Reset si se solicita
    if args.reset:
        logger.info("Eliminando colección existente...")
        retriever.client.delete_collection(retriever.collection_name)
        retriever.collection = retriever.client.create_collection(
            name=retriever.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    # Cargar chunks
    logger.info(f"Cargando chunks desde {data_dir}...")
    total = load_chunks_from_json_files(retriever, data_dir)
    logger.info(f"✅ Cargados {total} chunks en total")

    # Mostrar conteo por obra social
    counts = retriever.count_by_obra_social()
    logger.info("Chunks por obra social:")
    for os_name, count in sorted(counts.items()):
        logger.info(f"  - {os_name}: {count}")

    # Test query si se especifica
    if args.test_query:
        logger.info(f"\n🔍 Test query: '{args.test_query}'")
        if args.test_obra_social:
            logger.info(f"   Filtro: obra_social={args.test_obra_social}")

        results = retriever.retrieve(
            args.test_query,
            top_k=3,
            obra_social_filter=args.test_obra_social
        )

        if results:
            for i, (text, meta, score) in enumerate(results, 1):
                logger.info(f"\n--- Resultado {i} (score: {score:.3f}) ---")
                logger.info(f"Obra social: {meta.get('obra_social')}")
                logger.info(f"Archivo: {meta.get('archivo')}")
                logger.info(f"Chunk ID: {meta.get('chunk_id')}")
                logger.info(f"Texto: {text[:300]}...")
        else:
            logger.info("❌ No se encontraron resultados")


if __name__ == "__main__":
    main()
