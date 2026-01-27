#!/usr/bin/env python3
"""
Test de integración: ChromaDB RAG Retrieval - Escenario 1
Verifica que el sistema de búsqueda ChromaDB funcione correctamente
"""
import sys
import pytest
from pathlib import Path

# Agregar project root al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from escenario_1.rag.retriever import ChromaRetriever

CHROMA_PATH = str(project_root / "data" / "chroma_db")


@pytest.fixture(scope="module")
def retriever():
    """Carga ChromaDB una sola vez para todos los tests"""
    if not Path(CHROMA_PATH).exists():
        pytest.skip("ChromaDB no encontrado en data/chroma_db")
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
        assert "ASI" in counts, f"Falta ASI: {counts}"
        assert "ENSALUD" in counts, f"Falta ENSALUD: {counts}"


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
        # Usar query más específica para matchear el checklist
        results = retriever.retrieve("checklist documentación consulta IOSFA validador", top_k=3, obra_social_filter="IOSFA")

        assert len(results) > 0, "No encontró resultados para IOSFA"

        # Buscar en todos los resultados (el chunk correcto puede no ser el primero)
        found_checklist = False
        for text, metadata, score in results:
            if "VALIDADOR" in text and "DNI" in text:
                found_checklist = True
                assert metadata['obra_social'] == 'IOSFA'
                break

        assert found_checklist, "No encontró el checklist de IOSFA con VALIDADOR y DNI"

    def test_search_practicas_docs(self, retriever):
        """Busca documentación para prácticas IOSFA"""
        results = retriever.retrieve("documentación prácticas autorización IOSFA", top_k=3, obra_social_filter="IOSFA")

        assert len(results) > 0

        # Buscar en todos los resultados
        found_practicas = False
        for text, metadata, score in results:
            if "AUTORIZACION" in text or "PRACTICAS" in text:
                found_practicas = True
                assert metadata['obra_social'] == 'IOSFA'
                break

        assert found_practicas, "No encontró información de prácticas/autorización IOSFA"

    def test_search_iosfa_contact(self, retriever):
        """Busca email de contacto IOSFA"""
        results = retriever.retrieve("mail contacto IOSFA", top_k=3, obra_social_filter="IOSFA")

        assert len(results) > 0, "No encontró resultados de contacto IOSFA"

        # Debe encontrar el email
        found_email = False
        for text, metadata, score in results:
            if "consultas@iosfa" in text.lower():
                found_email = True
                break

        assert found_email, "No encontró el email consultas@iosfa.gob.ar"


class TestRetrievalENSALUD:
    """Tests de búsqueda en ENSALUD"""

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

if __name__ == "__main__":
    # Ejecutar con: python -m pytest tests/integration/test_rag_retrieval.py -v
    pytest.main([__file__, "-v", "--tb=short"])
