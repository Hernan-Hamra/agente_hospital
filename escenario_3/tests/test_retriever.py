#!/usr/bin/env python3
"""
Test de integración: ChromaDB RAG Retrieval - Escenario 3
Verifica que el retriever funcione con shared/data/chroma_db
"""
import sys
import pytest
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from escenario_3.rag.retriever import ChromaRetriever

CHROMA_PATH = str(project_root / "shared" / "data" / "chroma_db")


@pytest.fixture(scope="module")
def retriever():
    """Carga ChromaDB una sola vez para todos los tests"""
    if not Path(CHROMA_PATH).exists():
        pytest.skip("ChromaDB no encontrado en shared/data/chroma_db")
    return ChromaRetriever(persist_directory=CHROMA_PATH)


class TestIndexIntegrity:
    """Tests de integridad del índice ChromaDB"""

    def test_index_loaded(self, retriever):
        """Verifica que el índice se cargó correctamente"""
        count = retriever.count()
        assert count > 0, f"No hay chunks cargados: {count}"

    def test_chunks_by_obra_social(self, retriever):
        """Verifica distribución por obra social"""
        counts = retriever.count_by_obra_social()
        assert len(counts) > 0, "No hay obras sociales"


class TestRetrieval:
    """Tests de búsqueda"""

    def test_search_with_filter(self, retriever):
        """Busca con filtro de obra social"""
        results = retriever.retrieve(
            "documentación consulta",
            top_k=3,
            obra_social_filter="ENSALUD"
        )
        assert len(results) > 0, "No encontró resultados"

        # Verificar que todos son de ENSALUD
        for text, metadata, score in results:
            assert metadata.get('obra_social') == 'ENSALUD'

    def test_search_without_filter(self, retriever):
        """Busca sin filtro"""
        results = retriever.retrieve("documentación", top_k=5)
        assert len(results) > 0, "No encontró resultados sin filtro"

    def test_similarity_ranking(self, retriever):
        """Verifica orden por similarity"""
        results = retriever.retrieve("coseguro", top_k=5)
        assert len(results) >= 2

        scores = [score for _, _, score in results]
        assert scores == sorted(scores, reverse=True), "No están ordenados"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
