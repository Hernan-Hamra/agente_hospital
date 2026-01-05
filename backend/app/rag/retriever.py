"""
Recuperador de documentos desde FAISS
"""
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer


class DocumentRetriever:
    """Busca documentos relevantes en el índice FAISS"""

    def __init__(self, indexer, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Args:
            indexer: Instancia de DocumentIndexer con índice cargado
            embedding_model: Modelo para generar embeddings de queries
        """
        self.indexer = indexer
        self.model = SentenceTransformer(embedding_model)

    def retrieve(self, query: str, top_k: int = 5, obra_social_filter: str = None) -> List[Tuple[str, dict, float]]:
        """
        Recupera los top_k documentos más relevantes

        Args:
            query: Consulta del usuario
            top_k: Cantidad de resultados a retornar
            obra_social_filter: Filtrar por obra social específica

        Returns:
            Lista de tuplas (chunk_text, metadata, score)
        """
        # Generar embedding de la query
        query_embedding = self.model.encode([query])[0].astype('float32')
        query_embedding = np.array([query_embedding])

        # Normalizar query embedding para cosine similarity
        import faiss
        faiss.normalize_L2(query_embedding)

        # Buscar en FAISS (buscamos más para filtrar después si es necesario)
        search_k = top_k * 3 if obra_social_filter else top_k
        distances, indices = self.indexer.index.search(query_embedding, search_k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:  # FAISS retorna -1 si no hay más resultados
                break

            metadata = self.indexer.documents[idx]

            # Filtrar por obra social si se especificó
            if obra_social_filter:
                if metadata['obra_social'].upper() != obra_social_filter.upper() and metadata['obra_social'] != 'GENERAL':
                    continue

            # Obtener el texto del chunk
            chunk_text = metadata.get('text', f"[Chunk {idx}]")

            # Con IndexFlatIP + vectores normalizados, 'distance' es directamente cosine similarity
            # Rango: -1 (opuestos) a 1 (idénticos)
            # Convertimos a rango 0-1 para mantener compatibilidad
            similarity = (distance + 1.0) / 2.0

            # FILTRO DE RELEVANCIA: Descartar chunks con score < 0.65
            # Threshold ajustado para cosine similarity (más estricto que L2)
            # 0.65 = similitud moderada, 0.8+ = muy similar
            if similarity < 0.65:
                continue

            results.append((chunk_text, metadata, similarity))

            if len(results) >= top_k:
                break

        return results

    def get_context_for_llm(self, query: str, top_k: int = 5, obra_social_filter: str = None) -> str:
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
            obra_social = metadata['obra_social']
            archivo = metadata['archivo']
            context_parts.append(
                f"[Fuente {i} - {obra_social} - {archivo} (relevancia: {score:.2f})]\n{chunk}\n"
            )

        return "\n---\n".join(context_parts)
