"""
Recuperador de documentos con ChromaDB
Soporta filtros nativos por obra_social (filter-first, then search)
Usa embeddings de SentenceTransformer (bge-large-en-v1.5)
"""
from typing import List, Tuple, Optional
import os
import json
import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from ..core.query_rewriter import rewrite_query

logger = logging.getLogger(__name__)


class ChromaRetriever:
    """Busca documentos en ChromaDB con filtros nativos por metadata"""

    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "obras_sociales",
        embedding_model: str = "BAAI/bge-large-en-v1.5"
    ):
        """
        Args:
            persist_directory: Directorio para persistir la DB
            collection_name: Nombre de la colección
            embedding_model: Modelo para generar embeddings
        """
        # Resolver path por defecto
        if persist_directory is None:
            persist_directory = str(
                Path(__file__).parent.parent.parent / "shared" / "data" / "chroma_db"
            )

        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        # Inicializar cliente Chroma con persistencia
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Obtener o crear colección
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Modelo de embeddings
        logger.info(f"Cargando modelo de embeddings: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)

        logger.info(f"ChromaRetriever inicializado: {self.collection.count()} documentos")

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos"""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def add_chunks(self, chunks: List[dict], batch_size: int = 100) -> int:
        """
        Agrega chunks a la colección

        Args:
            chunks: Lista de chunks con formato {obra_social, archivo, chunk_id, texto, ...}
            batch_size: Tamaño del batch para inserción

        Returns:
            Cantidad de chunks agregados
        """
        added = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            ids = []
            documents = []
            metadatas = []

            for chunk in batch:
                chunk_id = f"{chunk['obra_social']}_{chunk['chunk_id']}"
                ids.append(chunk_id)
                documents.append(chunk.get('texto', ''))

                metadata = {
                    "obra_social": chunk.get('obra_social', 'UNKNOWN'),
                    "archivo": chunk.get('archivo', ''),
                    "chunk_id": chunk.get('chunk_id', ''),
                    "es_tabla": chunk.get('es_tabla', False),
                }

                if 'seccion' in chunk:
                    metadata['seccion'] = chunk['seccion']
                if 'tabla_numero' in chunk:
                    metadata['tabla_numero'] = chunk['tabla_numero']

                metadatas.append(metadata)

            # Generar embeddings
            embeddings = self._embed_texts(documents)

            # Upsert
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            added += len(batch)

        logger.info(f"Total chunks en colección: {self.collection.count()}")
        return added

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        obra_social_filter: str = None,
        min_score: float = 0.3,
        use_rewriter: bool = True
    ) -> List[Tuple[str, dict, float]]:
        """
        Recupera documentos relevantes CON FILTRO NATIVO

        Args:
            query: Consulta del usuario
            top_k: Cantidad de resultados
            obra_social_filter: Filtrar por obra social
            min_score: Score mínimo (0-1, cosine similarity)
            use_rewriter: Si True, aplica query rewriting

        Returns:
            Lista de tuplas (chunk_text, metadata, score)
        """
        # Aplicar query rewriting si está habilitado
        search_query = query
        if use_rewriter:
            search_query = rewrite_query(query, obra_social_filter)

        # Construir filtro nativo de Chroma
        where_filter = None
        if obra_social_filter:
            where_filter = {"obra_social": obra_social_filter.upper()}

        # Generar embedding de la query
        query_embedding = self._embed_texts([search_query])[0]

        # Buscar con filtro nativo
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # Procesar resultados
        output = []

        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}

                # Convertir distancia a similaridad
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = 1 - (distance / 2)

                if similarity < min_score:
                    continue

                metadata['text'] = doc
                output.append((doc, metadata, similarity))

        return output

    def count(self) -> int:
        """Retorna cantidad de documentos"""
        return self.collection.count()

    def count_by_obra_social(self) -> dict:
        """Retorna conteo de chunks por obra social"""
        all_data = self.collection.get(include=["metadatas"])

        counts = {}
        for meta in all_data['metadatas']:
            os_name = meta.get('obra_social', 'UNKNOWN')
            counts[os_name] = counts.get(os_name, 0) + 1

        return counts


def load_chunks_from_json_files(retriever: ChromaRetriever, data_dir: str) -> int:
    """
    Carga todos los chunks de los archivos JSON al retriever

    Args:
        retriever: Instancia de ChromaRetriever
        data_dir: Directorio con subcarpetas de obras sociales

    Returns:
        Total de chunks cargados
    """
    total = 0

    for obra_social_dir in os.listdir(data_dir):
        dir_path = os.path.join(data_dir, obra_social_dir)

        if not os.path.isdir(dir_path):
            continue

        for filename in os.listdir(dir_path):
            if not filename.endswith('_chunks_flat.json'):
                continue

            filepath = os.path.join(dir_path, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                chunks = json.load(f)

            retriever.add_chunks(chunks)
            total += len(chunks)
            logger.info(f"Cargados {len(chunks)} chunks de {filename}")

    return total
