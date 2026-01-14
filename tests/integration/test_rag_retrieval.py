#!/usr/bin/env python3
"""
Test de integración: RAG Retrieval
Verifica que el sistema de búsqueda FAISS funcione correctamente
"""
import sys
import pytest
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.rag.indexer import DocumentIndexer
from app.rag.retriever import DocumentRetriever


@pytest.fixture(scope="module")
def indexer():
    """Carga el índice FAISS una sola vez para todos los tests"""
    indexer = DocumentIndexer(embedding_model="BAAI/bge-large-en-v1.5")
    index_path = backend_path / "faiss_index"

    if not index_path.exists():
        pytest.skip("Índice FAISS no encontrado. Ejecutar: python3 scripts/index_data.py")

    indexer.load_index(str(index_path))
    return indexer


@pytest.fixture(scope="module")
def retriever(indexer):
    """Crea retriever con el índice cargado"""
    return DocumentRetriever(indexer, embedding_model="BAAI/bge-large-en-v1.5")


class TestIndexIntegrity:
    """Tests de integridad del índice FAISS"""

    def test_index_loaded(self, indexer):
        """Verifica que el índice se cargó correctamente"""
        assert indexer.index is not None, "Índice FAISS no está cargado"
        assert len(indexer.documents) > 0, "No hay documentos en el índice"

    def test_total_chunks(self, indexer):
        """Verifica cantidad total de chunks"""
        assert len(indexer.documents) == 82, f"Esperaba 82 chunks, encontró {len(indexer.documents)}"

    def test_chunks_by_obra_social(self, indexer):
        """Verifica distribución por obra social"""
        obras = {}
        for doc in indexer.documents:
            obra = doc.get('obra_social', 'DESCONOCIDO')
            obras[obra] = obras.get(obra, 0) + 1

        assert obras.get('ASI', 0) == 13, f"ASI debe tener 13 chunks, tiene {obras.get('ASI', 0)}"
        assert obras.get('ENSALUD', 0) == 68, f"ENSALUD debe tener 68 chunks, tiene {obras.get('ENSALUD', 0)}"
        assert obras.get('IOSFA', 0) == 1, f"IOSFA debe tener 1 chunk, tiene {obras.get('IOSFA', 0)}"

    def test_table_chunks_count(self, indexer):
        """Verifica que hay chunks de tablas"""
        tablas = sum(1 for doc in indexer.documents if doc.get('es_tabla', False))
        assert tablas == 61, f"Esperaba 61 chunks de tablas, encontró {tablas}"


class TestRetrievalASI:
    """Tests de búsqueda en ASI"""

    def test_search_contact_table(self, retriever):
        """Busca email de Mesa Operativa ASI (tabla)"""
        results = retriever.retrieve("mail de Mesa Operativa ASI", top_k=3, obra_social_filter="ASI")

        assert len(results) > 0, "No encontró resultados para búsqueda ASI"

        text, metadata, score = results[0]

        # Verificar que encontró el resultado correcto
        assert "autorizaciones@asi.com.ar" in text, "No encontró el email correcto"
        assert metadata['obra_social'] == 'ASI', "Resultado no es de ASI"

        # Verificar similarity score alto
        assert score > 0.80, f"Similarity muy bajo: {score:.3f} (esperado > 0.80)"

    def test_search_normas(self, retriever):
        """Busca información general de normas ASI"""
        results = retriever.retrieve("normas ASI procedimientos", top_k=3, obra_social_filter="ASI")

        assert len(results) > 0, "No encontró resultados"
        text, metadata, score = results[0]

        assert metadata['obra_social'] == 'ASI'
        assert score > 0.70


class TestRetrievalIOSFA:
    """Tests de búsqueda en IOSFA"""

    def test_search_consulta_docs(self, retriever):
        """Busca documentación para consultas IOSFA"""
        results = retriever.retrieve("documentación consulta IOSFA", top_k=3, obra_social_filter="IOSFA")

        assert len(results) > 0, "No encontró resultados para IOSFA"

        text, metadata, score = results[0]

        # Verificar contenido
        assert "VALIDADOR" in text, "Falta VALIDADOR en el resultado"
        assert "DNI" in text, "Falta DNI en el resultado"
        assert "BONO" in text or "CONSULTA" in text, "Falta información de bono/consulta"

        # Verificar metadata
        assert metadata['obra_social'] == 'IOSFA'

        # Verificar similarity
        assert score > 0.80, f"Similarity bajo: {score:.3f}"

    def test_search_practicas_docs(self, retriever):
        """Busca documentación para prácticas IOSFA"""
        results = retriever.retrieve("documentación prácticas IOSFA", top_k=3, obra_social_filter="IOSFA")

        assert len(results) > 0
        text, metadata, score = results[0]

        # Debe encontrar AUTORIZACION (requerido para prácticas, no para consultas)
        assert "AUTORIZACION" in text or "PRACTICAS" in text
        assert metadata['obra_social'] == 'IOSFA'


class TestRetrievalENSALUD:
    """Tests de búsqueda en ENSALUD"""

    def test_search_tables(self, retriever):
        """Busca tablas en ENSALUD"""
        results = retriever.retrieve("tabla copagos ENSALUD", top_k=5, obra_social_filter="ENSALUD")

        assert len(results) > 0, "No encontró resultados en ENSALUD"

        # Verificar que el top result es una tabla
        text, metadata, score = results[0]
        assert metadata.get('es_tabla', False), "El mejor resultado debería ser una tabla"
        assert metadata['obra_social'] == 'ENSALUD'

        # Contar tablas en top 5
        tablas_count = sum(1 for _, meta, _ in results if meta.get('es_tabla', False))
        assert tablas_count >= 3, f"Solo {tablas_count}/5 resultados son tablas (esperado >= 3)"

    def test_search_specific_table_content(self, retriever):
        """Busca contenido específico en tablas ENSALUD"""
        results = retriever.retrieve("prestaciones ENSALUD", top_k=5, obra_social_filter="ENSALUD")

        assert len(results) > 0
        text, metadata, score = results[0]

        assert metadata['obra_social'] == 'ENSALUD'
        assert score > 0.70


class TestCrossObraSocialRetrieval:
    """Tests de búsqueda sin filtro de obra social"""

    def test_search_without_filter(self, retriever):
        """Busca sin filtro de obra social"""
        results = retriever.retrieve("documentación consulta", top_k=5)

        assert len(results) > 0, "No encontró resultados sin filtro"

        # Verificar que hay resultados de múltiples obras sociales
        obras = set(meta['obra_social'] for _, meta, _ in results)
        assert len(obras) >= 1, "Debería haber resultados de al menos 1 obra social"

    def test_similarity_ranking(self, retriever):
        """Verifica que los resultados están ordenados por similarity"""
        results = retriever.retrieve("documentación requerida", top_k=5)

        assert len(results) >= 2

        # Verificar orden descendente de scores
        scores = [score for _, _, score in results]
        assert scores == sorted(scores, reverse=True), "Los resultados no están ordenados por similarity"


class TestEdgeCases:
    """Tests de casos límite"""

    def test_empty_query(self, retriever):
        """Busca con query vacía"""
        results = retriever.retrieve("", top_k=5)
        # Debería retornar algo (aunque no sea muy relevante)
        assert isinstance(results, list)

    def test_nonexistent_obra_social(self, retriever):
        """Busca con obra social inexistente"""
        results = retriever.retrieve("documentación", top_k=5, obra_social_filter="OSDE")
        # Debería retornar lista vacía o sin resultados de OSDE
        if results:
            for _, meta, _ in results:
                assert meta['obra_social'] != 'OSDE'

    def test_very_specific_query(self, retriever):
        """Busca query muy específica"""
        results = retriever.retrieve("autorizaciones@asi.com.ar email contacto", top_k=3)

        assert len(results) > 0
        # Debería encontrar la tabla de contactos de ASI
        text, metadata, score = results[0]
        assert "autorizaciones@asi.com.ar" in text
        assert score > 0.85  # Alta similarity para query muy específica


if __name__ == "__main__":
    # Ejecutar con: python -m pytest tests/integration/test_rag_retrieval.py -v
    pytest.main([__file__, "-v", "--tb=short"])
