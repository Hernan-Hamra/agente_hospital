"""
ChromaDB Retriever para Escenario 3
====================================

Usa SentenceTransformer para embeddings (igual que escenario_1).
Apunta a shared/data/chroma_db
"""
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from ..core.query_rewriter import rewrite_query

logger = logging.getLogger(__name__)


class ChromaRetriever:
    """
    Retriever basado en ChromaDB.
    Usa el índice compartido en shared/data/chroma_db
    """

    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "obras_sociales",
        embedding_model: str = "BAAI/bge-large-en-v1.5"
    ):
        """
        Inicializa el retriever.

        Args:
            persist_directory: Ruta a la base de datos ChromaDB
            collection_name: Nombre de la colección
            embedding_model: Modelo de embeddings a usar
        """
        if persist_directory is None:
            # Default: shared/data/chroma_db
            persist_directory = str(
                Path(__file__).parent.parent.parent / "shared" / "data" / "chroma_db"
            )

        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        logger.info(f"Inicializando ChromaDB desde: {persist_directory}")

        # Inicializar cliente ChromaDB con persistencia
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Obtener o crear colección
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Modelo de embeddings (SentenceTransformer directo)
        logger.info(f"Cargando modelo de embeddings: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)

        logger.info(f"ChromaDB cargado: {self.collection.count()} documentos")

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos"""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        obra_social_filter: str = None,
        min_score: float = 0.3,
        use_rewriter: bool = True
    ) -> List[Tuple[str, Dict, float]]:
        """
        Busca chunks relevantes.

        Args:
            query: Texto de búsqueda
            top_k: Número de resultados
            obra_social_filter: Filtrar por obra social (opcional)
            min_score: Score mínimo
            use_rewriter: Si usar query rewriting

        Returns:
            Lista de (texto, metadata, similarity_score)
        """
        # Aplicar query rewriting si está habilitado
        search_query = query
        if use_rewriter:
            search_query = rewrite_query(query, obra_social_filter)

        # Construir filtro nativo
        where_filter = None
        if obra_social_filter:
            where_filter = {"obra_social": obra_social_filter.upper()}

        # Generar embedding de la query
        query_embedding = self._embed_texts([search_query])[0]

        # Ejecutar query
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"Error en query: {e}")
            return []

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
        """Retorna el número total de chunks"""
        return self.collection.count()

    def count_by_obra_social(self) -> Dict[str, int]:
        """Retorna conteo por obra social"""
        all_data = self.collection.get(include=["metadatas"])
        counts = {}
        if all_data and all_data['metadatas']:
            for meta in all_data['metadatas']:
                os_name = meta.get('obra_social', 'UNKNOWN')
                counts[os_name] = counts.get(os_name, 0) + 1
        return counts
