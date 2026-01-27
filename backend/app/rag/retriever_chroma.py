"""
Recuperador de documentos con ChromaDB
Soporta filtros nativos por obra_social (filter-first, then search)
Usa embeddings de SentenceTransformer (bge-large-en-v1.5)
"""
from typing import List, Tuple, Optional
import os
import json
import logging
import numpy as np

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .query_rewriter import rewrite_query

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
            persist_directory: Directorio para persistir la DB (None = en memoria)
            collection_name: Nombre de la colección
            embedding_model: Modelo para generar embeddings
        """
        self.persist_directory = persist_directory or os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "data", "chroma_db"
        )
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        # Inicializar cliente Chroma con persistencia
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Obtener o crear colección (SIN embedding function - usamos nuestros embeddings)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Usar cosine similarity
        )

        # Modelo de embeddings - AHORA SE USA REALMENTE
        logger.info(f"Cargando modelo de embeddings: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)

        logger.info(f"ChromaRetriever inicializado: {self.collection.count()} documentos")

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos"""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def add_chunks(self, chunks: List[dict], batch_size: int = 100) -> int:
        """
        Agrega chunks a la colección CON EMBEDDINGS PROPIOS

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
                # ID único: OBRA_SOCIAL_chunk_id
                chunk_id = f"{chunk['obra_social']}_{chunk['chunk_id']}"
                ids.append(chunk_id)

                # El texto es el documento
                documents.append(chunk.get('texto', ''))

                # Metadata para filtros
                metadata = {
                    "obra_social": chunk.get('obra_social', 'UNKNOWN'),
                    "archivo": chunk.get('archivo', ''),
                    "chunk_id": chunk.get('chunk_id', ''),
                    "es_tabla": chunk.get('es_tabla', False),
                }

                # Agregar campos opcionales
                if 'seccion' in chunk:
                    metadata['seccion'] = chunk['seccion']
                if 'tabla_numero' in chunk:
                    metadata['tabla_numero'] = chunk['tabla_numero']
                if 'pagina' in chunk:
                    metadata['pagina'] = chunk['pagina']

                metadatas.append(metadata)

            # Generar embeddings con NUESTRO modelo
            embeddings = self._embed_texts(documents)

            # Upsert CON embeddings propios
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            added += len(batch)
            logger.debug(f"Agregados {added}/{len(chunks)} chunks")

        logger.info(f"Total chunks en colección: {self.collection.count()}")
        return added

    def update_chunk(self, obra_social: str, chunk_id: str, nuevo_texto: str, metadata: dict = None):
        """
        Actualiza un chunk específico sin reindexar todo

        Args:
            obra_social: Obra social del chunk
            chunk_id: ID del chunk (ej: "T047")
            nuevo_texto: Nuevo texto del chunk
            metadata: Metadata actualizada (opcional)
        """
        doc_id = f"{obra_social}_{chunk_id}"

        # Generar nuevo embedding
        embedding = self._embed_texts([nuevo_texto])[0]

        update_args = {
            "ids": [doc_id],
            "documents": [nuevo_texto],
            "embeddings": [embedding]
        }

        if metadata:
            update_args["metadatas"] = [metadata]

        self.collection.update(**update_args)
        logger.info(f"Chunk actualizado: {doc_id}")

    def delete_chunk(self, obra_social: str, chunk_id: str):
        """Elimina un chunk específico"""
        doc_id = f"{obra_social}_{chunk_id}"
        self.collection.delete(ids=[doc_id])
        logger.info(f"Chunk eliminado: {doc_id}")

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

        A diferencia de FAISS, aquí el filtro se aplica ANTES de la búsqueda.
        Esto garantiza que siempre obtenemos los top_k de la obra social específica.

        Args:
            query: Consulta del usuario
            top_k: Cantidad de resultados
            obra_social_filter: Filtrar por obra social (ENSALUD, ASI, IOSFA, etc.)
            min_score: Score mínimo para incluir resultado (0-1, cosine similarity)
            use_rewriter: Si True, aplica query rewriting para mejorar retrieval

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

        # Generar embedding de la query (reescrita o original) con NUESTRO modelo
        query_embedding = self._embed_texts([search_query])[0]

        # Buscar con filtro nativo y NUESTRO embedding
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

                # Chroma con cosine devuelve distancia (0 = idéntico, 2 = opuesto)
                # Convertir a similaridad (1 = idéntico, 0 = opuesto)
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = 1 - (distance / 2)

                # Filtrar por score mínimo
                if similarity < min_score:
                    continue

                # Agregar texto al metadata para compatibilidad
                metadata['text'] = doc

                output.append((doc, metadata, similarity))

        return output

    def get_context_for_llm(
        self,
        query: str,
        top_k: int = 5,
        obra_social_filter: str = None
    ) -> str:
        """
        Genera contexto formateado para el LLM

        Args:
            query: Consulta del usuario
            top_k: Cantidad de documentos a recuperar
            obra_social_filter: Filtrar por obra social

        Returns:
            String con contexto formateado
        """
        results = self.retrieve(query, top_k, obra_social_filter)

        if not results:
            return "No se encontró información relevante en la base de datos."

        context_parts = []
        for i, (chunk, metadata, score) in enumerate(results, 1):
            obra_social = metadata.get('obra_social', 'UNKNOWN')
            archivo = metadata.get('archivo', '')
            context_parts.append(
                f"[Fuente {i} - {obra_social} - {archivo} (relevancia: {score:.2f})]\n{chunk}\n"
            )

        return "\n---\n".join(context_parts)

    def count_by_obra_social(self) -> dict:
        """Retorna conteo de chunks por obra social"""
        # Obtener todos los metadatas
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
