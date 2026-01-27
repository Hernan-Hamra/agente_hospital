#!/usr/bin/env python3
"""
Test unitario: Chunking
Verifica que la división de textos en chunks funcione correctamente
"""
import sys
import pytest
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path / "scripts"))

from convert_docs_to_json_flat import DocumentToJsonFlat


@pytest.fixture
def converter():
    """Crea un converter con parámetros estándar"""
    return DocumentToJsonFlat(
        data_path="/tmp/test_data",
        output_path="/tmp/test_output",
        chunk_size=1800,
        overlap=300
    )


class TestChunkCreation:
    """Tests de creación de chunks"""

    def test_short_text_single_chunk(self, converter):
        """Texto corto genera un solo chunk"""
        texto = "Este es un texto muy corto"
        metadata_base = {
            "obra_social": "TEST",
            "archivo": "test.txt"
        }

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        assert len(chunks) == 1, "Texto corto debe generar 1 chunk"
        assert chunks[0]['texto'] == texto
        assert chunks[0]['chunk_id'] == "001"
        assert chunks[0]['obra_social'] == "TEST"

    def test_long_text_multiple_chunks(self, converter):
        """Texto largo genera múltiples chunks"""
        # Texto de ~4000 chars (debería generar 2-3 chunks con chunk_size=1800, overlap=300)
        texto = "Lorem ipsum dolor sit amet. " * 150  # ~4200 chars

        metadata_base = {
            "obra_social": "TEST",
            "archivo": "test.txt"
        }

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        # Con 4200 chars, chunk_size=1800, overlap=300:
        # Chunk 1: 0-1800
        # Chunk 2: 1500-3300 (start=1800-300)
        # Chunk 3: 3000-end (start=3300-300)
        assert len(chunks) >= 2, "Texto largo debe generar múltiples chunks"
        assert len(chunks) <= 4, f"Demasiados chunks: {len(chunks)}"

    def test_chunk_ids_sequential(self, converter):
        """Los chunk IDs son secuenciales"""
        texto = "A " * 3000  # Texto largo
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        # Verificar IDs secuenciales: 001, 002, 003, etc.
        expected_ids = [f"{i:03d}" for i in range(1, len(chunks) + 1)]
        actual_ids = [chunk['chunk_id'] for chunk in chunks]

        assert actual_ids == expected_ids, f"IDs no secuenciales: {actual_ids}"

    def test_overlap_between_chunks(self, converter):
        """Verifica que hay overlap entre chunks consecutivos"""
        # Crear texto largo con palabras únicas identificables
        words = [f"WORD{i:04d}" for i in range(1000)]
        texto = " ".join(words)

        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}
        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        if len(chunks) >= 2:
            # Verificar que hay overlap entre chunk 1 y 2
            chunk1_text = chunks[0]['texto']
            chunk2_text = chunks[1]['texto']

            # Con overlap de 300 chars, buscar en un rango más amplio
            # Tomar últimas 50 palabras del chunk 1 (seguro cubre los 300 chars de overlap)
            chunk1_end_words = chunk1_text.split()[-50:]
            # Primeras 100 palabras del chunk 2 (también cubre el overlap)
            chunk2_start_words = chunk2_text.split()[:100]

            # Contar cuántas palabras están en ambos
            overlap_words = [word for word in chunk1_end_words if word in chunk2_start_words]

            # Debe haber al menos 5 palabras en común
            assert len(overlap_words) >= 5, \
                f"Muy poco overlap: solo {len(overlap_words)} palabras en común (esperado >= 5)"

    def test_metadata_preserved(self, converter):
        """Metadata se preserva en todos los chunks"""
        texto = "A " * 3000
        metadata_base = {
            "obra_social": "IOSFA",
            "archivo": "test.docx"
        }

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        for chunk in chunks:
            assert chunk['obra_social'] == "IOSFA"
            assert chunk['archivo'] == "test.docx"
            assert chunk['es_tabla'] == False


class TestTableToText:
    """Tests de conversión de tablas a texto"""

    def test_contact_table_to_sentences(self, converter):
        """Tabla de contactos se convierte a oraciones (mejor para RAG)"""
        tabla = {
            'numero': 1,
            'filas': 3,
            'columnas': 2,
            'contenido': [
                ['Nombre', 'Email'],
                ['Juan', 'juan@example.com'],
                ['María', 'maria@example.com']
            ]
        }

        texto = converter.table_to_text(tabla, obra_social="TEST")

        # Las tablas de contacto ahora se convierten a oraciones
        assert "mail" in texto.lower() or "email" in texto.lower()
        assert "juan@example.com" in texto
        assert "maria@example.com" in texto

    def test_non_contact_table_format(self, converter):
        """Tabla sin emails/teléfonos mantiene formato tabla"""
        tabla = {
            'numero': 1,
            'filas': 3,
            'columnas': 2,
            'contenido': [
                ['Código', 'Precio'],
                ['A001', '$1000'],
                ['B002', '$2000']
            ]
        }

        texto = converter.table_to_text(tabla)

        # Tablas normales tienen formato "TABLA #N"
        assert "TABLA #1" in texto
        assert "$1000" in texto
        assert "$2000" in texto

    def test_table_with_empty_cells(self, converter):
        """Tabla con celdas vacías"""
        tabla = {
            'numero': 2,
            'filas': 2,
            'columnas': 3,
            'contenido': [
                ['Col1', 'Col2', 'Col3'],
                ['A', '', 'C']  # Celda vacía
            ]
        }

        texto = converter.table_to_text(tabla)

        assert "TABLA #2" in texto
        # No debería crashear con celda vacía
        assert isinstance(texto, str)


class TestChunkSizeValidation:
    """Tests de validación de tamaño de chunks"""

    def test_chunks_not_exceed_size(self, converter):
        """Ningún chunk debería exceder chunk_size (excepto último)"""
        texto = "WORD " * 1000  # Texto largo
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        for i, chunk in enumerate(chunks[:-1]):  # Todos excepto el último
            chunk_len = len(chunk['texto'])
            assert chunk_len <= converter.chunk_size + 200, \
                f"Chunk {i} excede tamaño: {chunk_len} > {converter.chunk_size}"

    def test_no_empty_chunks(self, converter):
        """No debe haber chunks vacíos"""
        texto = "WORD " * 1000
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        for i, chunk in enumerate(chunks):
            assert chunk['texto'].strip() != "", f"Chunk {i} está vacío"


class TestEdgeCases:
    """Tests de casos límite"""

    def test_exact_chunk_size(self, converter):
        """Texto exactamente del tamaño del chunk"""
        # Crear texto de exactamente 1800 chars
        texto = "A" * converter.chunk_size
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        assert len(chunks) == 1, "Texto exacto debería generar 1 chunk"

    def test_empty_text(self, converter):
        """Texto vacío"""
        texto = ""
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        # Debería generar 1 chunk vacío o ninguno
        assert len(chunks) <= 1

    def test_text_with_only_spaces(self, converter):
        """Texto solo con espacios"""
        texto = "   \n   \t   "
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        # Debería limpiar espacios
        if len(chunks) > 0:
            assert chunks[0]['texto'].strip() == ""

    def test_text_slightly_larger_than_chunk(self, converter):
        """Texto apenas más grande que chunk_size"""
        # chunk_size + 10 chars
        texto = "A" * (converter.chunk_size + 10)
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        assert len(chunks) == 2, "Texto ligeramente más grande debe generar 2 chunks"


class TestChunkParameters:
    """Tests de diferentes configuraciones de chunking"""

    def test_different_chunk_size(self):
        """Converter con chunk_size diferente"""
        converter = DocumentToJsonFlat(
            data_path="/tmp/test",
            output_path="/tmp/test",
            chunk_size=500,
            overlap=100
        )

        texto = "WORD " * 300  # ~1500 chars
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        # Con chunk_size=500 debería generar ~3 chunks
        assert len(chunks) >= 2

    def test_zero_overlap(self):
        """Converter sin overlap"""
        converter = DocumentToJsonFlat(
            data_path="/tmp/test",
            output_path="/tmp/test",
            chunk_size=1000,
            overlap=0
        )

        texto = "WORD " * 600  # ~3000 chars
        metadata_base = {"obra_social": "TEST", "archivo": "test.txt"}

        chunks = converter.create_chunks_with_overlap(texto, metadata_base)

        # Sin overlap, debería haber cortes limpios
        assert len(chunks) >= 2


if __name__ == "__main__":
    # Ejecutar con: python -m pytest tests/unit/test_chunking.py -v
    pytest.main([__file__, "-v", "--tb=short"])
