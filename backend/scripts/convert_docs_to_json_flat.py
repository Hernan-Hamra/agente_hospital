"""
Script para convertir documentos PDF/DOCX a JSON flat (sin estructura jerárquica)
Enfoque simple: chunks de tamaño fijo con overlap, metadata clara por chunk

Inspirado en el método de Patricia: dividir documentos y agregar metadata en cada pedazo
Mejoras: automático, con tablas detectadas, overlap entre chunks
"""
import os
import json
from pathlib import Path
from typing import Dict, List
import pdfplumber
from docx import Document
import re


class DocumentToJsonFlat:
    """Convierte documentos a JSON flat con chunks uniformes"""

    def __init__(self, data_path: str, output_path: str, chunk_size: int = 1800, overlap: int = 300):
        """
        Args:
            data_path: Ruta a documentos originales
            output_path: Ruta de salida para JSONs
            chunk_size: Tamaño de cada chunk en caracteres
            overlap: Superposición entre chunks consecutivos
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def extract_text_and_tables_from_pdf(self, pdf_path: Path) -> tuple:
        """
        Extrae texto completo y tablas de PDF

        Returns:
            (texto_completo: str, tablas: list)
        """
        texto_partes = []
        tablas = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extraer TABLAS
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    tabla_data = {
                        "numero": len(tablas) + 1,
                        "pagina": page_num,
                        "filas": len(table),
                        "columnas": len(table[0]) if table else 0,
                        "contenido": table
                    }
                    tablas.append(tabla_data)

                # Extraer TEXTO
                page_text = page.extract_text()
                if page_text:
                    texto_partes.append(page_text.strip())

        texto_completo = "\n\n".join(texto_partes)
        return texto_completo, tablas

    def extract_text_and_tables_from_docx(self, docx_path: Path) -> tuple:
        """
        Extrae texto completo y tablas de DOCX

        Returns:
            (texto_completo: str, tablas: list)
        """
        doc = Document(docx_path)

        # Extraer TABLAS primero (son críticas)
        tablas = []
        for table_idx, table in enumerate(doc.tables):
            tabla_data = {
                "numero": table_idx + 1,
                "filas": len(table.rows),
                "columnas": len(table.columns),
                "contenido": []
            }

            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                tabla_data["contenido"].append(row_data)

            tablas.append(tabla_data)

        # Extraer TEXTO completo
        texto_parrafos = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                texto_parrafos.append(text)

        texto_completo = "\n".join(texto_parrafos)

        return texto_completo, tablas

    def create_chunks_with_overlap(self, texto: str, metadata_base: dict) -> List[Dict]:
        """
        Divide texto en chunks de tamaño fijo con overlap

        Args:
            texto: Texto completo a dividir
            metadata_base: Metadata común (obra_social, archivo)

        Returns:
            Lista de chunks con metadata
        """
        chunks = []

        # Si el texto es muy corto, un solo chunk
        if len(texto) <= self.chunk_size:
            chunks.append({
                **metadata_base,
                "chunk_id": "001",
                "texto": texto,
                "es_tabla": False
            })
            return chunks

        # Dividir con overlap
        start = 0
        chunk_num = 1

        while start < len(texto):
            # Extraer chunk
            end = start + self.chunk_size
            chunk_text = texto[start:end]

            # Intentar cortar en un espacio/salto de línea para no partir palabras
            if end < len(texto):
                # Buscar último espacio o salto de línea en los últimos 100 chars
                last_space = chunk_text.rfind(' ', -100)
                last_newline = chunk_text.rfind('\n', -100)
                cut_point = max(last_space, last_newline)

                if cut_point > 0:
                    chunk_text = chunk_text[:cut_point]
                    end = start + cut_point

            # Crear chunk
            chunks.append({
                **metadata_base,
                "chunk_id": f"{chunk_num:03d}",
                "texto": chunk_text.strip(),
                "es_tabla": False
            })

            chunk_num += 1

            # Avanzar con overlap
            start = end - self.overlap

            # Evitar loop infinito
            if start + self.chunk_size >= len(texto) and start < len(texto):
                # Último chunk
                chunk_text = texto[start:]
                if chunk_text.strip():
                    chunks.append({
                        **metadata_base,
                        "chunk_id": f"{chunk_num:03d}",
                        "texto": chunk_text.strip(),
                        "es_tabla": False
                    })
                break

        return chunks

    def table_to_text(self, tabla: dict) -> str:
        """Convierte tabla a formato texto legible"""
        texto_tabla = f"TABLA #{tabla['numero']} ({tabla['filas']} filas x {tabla['columnas']} columnas)\n\n"

        for row_idx, row in enumerate(tabla["contenido"]):
            # Primera fila como encabezado
            if row_idx == 0:
                texto_tabla += " | ".join([f"**{cell}**" for cell in row if cell]) + "\n"
                texto_tabla += "---\n"
            else:
                texto_tabla += " | ".join([f"{cell}" for cell in row if cell]) + "\n"

        return texto_tabla.strip()

    def process_document(self, file_path: Path, obra_social: str) -> List[Dict]:
        """
        Procesa un documento y genera chunks flat

        Args:
            file_path: Ruta al archivo
            obra_social: Nombre de la obra social

        Returns:
            Lista de chunks con metadata
        """
        print(f"  Procesando: {file_path.name}")

        metadata_base = {
            "obra_social": obra_social.upper(),
            "archivo": file_path.name
        }

        all_chunks = []

        if file_path.suffix.lower() == '.pdf':
            # Procesar PDF (texto + tablas)
            texto_completo, tablas = self.extract_text_and_tables_from_pdf(file_path)

            # 1. Crear chunks de TABLAS (completas, sin dividir)
            for tabla in tablas:
                tabla_texto = self.table_to_text(tabla)
                all_chunks.append({
                    **metadata_base,
                    "chunk_id": f"T{tabla['numero']:03d}",
                    "texto": tabla_texto,
                    "es_tabla": True,
                    "tabla_numero": tabla['numero'],
                    "pagina": tabla['pagina']
                })

            # 2. Crear chunks de TEXTO con overlap
            chunks_texto = self.create_chunks_with_overlap(texto_completo, metadata_base)
            all_chunks.extend(chunks_texto)

        elif file_path.suffix.lower() == '.docx':
            # Procesar DOCX (texto + tablas)
            texto_completo, tablas = self.extract_text_and_tables_from_docx(file_path)

            # 1. Crear chunks de TABLAS (completas, sin dividir)
            for tabla in tablas:
                tabla_texto = self.table_to_text(tabla)
                all_chunks.append({
                    **metadata_base,
                    "chunk_id": f"T{tabla['numero']:03d}",
                    "texto": tabla_texto,
                    "es_tabla": True,
                    "tabla_numero": tabla['numero']
                })

            # 2. Crear chunks de TEXTO con overlap
            chunks_texto = self.create_chunks_with_overlap(texto_completo, metadata_base)
            all_chunks.extend(chunks_texto)

        print(f"    → {len(all_chunks)} chunks generados")
        return all_chunks

    def process_all_documents(self) -> dict:
        """
        Procesa todos los documentos de obras sociales

        Returns:
            Estadísticas del proceso
        """
        print("\n" + "="*70)
        print("CONVERSIÓN A JSON FLAT (chunks uniformes con overlap)")
        print("="*70)
        print(f"Chunk size: {self.chunk_size} chars")
        print(f"Overlap: {self.overlap} chars")
        print("="*70 + "\n")

        stats = {
            "obras_sociales": 0,
            "documentos": 0,
            "chunks_totales": 0,
            "chunks_tablas": 0
        }

        # Procesar cada obra social
        for os_dir in self.data_path.iterdir():
            if not os_dir.is_dir():
                continue

            obra_social = os_dir.name
            print(f"\n{'─'*70}")
            print(f"Obra Social: {obra_social.upper()}")
            print(f"{'─'*70}")

            os_output_dir = self.output_path / obra_social
            os_output_dir.mkdir(exist_ok=True)

            # Procesar cada archivo
            for file_path in os_dir.iterdir():
                if file_path.suffix.lower() not in ['.pdf', '.docx']:
                    continue

                # Generar chunks
                chunks = self.process_document(file_path, obra_social)

                # Contar tablas
                chunks_tablas = sum(1 for c in chunks if c.get("es_tabla", False))

                # Guardar JSON
                output_file = os_output_dir / f"{file_path.stem}_chunks_flat.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=2)

                print(f"    ✅ Guardado: {output_file.name}")
                print(f"       Chunks texto: {len(chunks) - chunks_tablas}")
                print(f"       Chunks tablas: {chunks_tablas}")

                stats["documentos"] += 1
                stats["chunks_totales"] += len(chunks)
                stats["chunks_tablas"] += chunks_tablas

            stats["obras_sociales"] += 1

        # Resumen
        print("\n" + "="*70)
        print("RESUMEN")
        print("="*70)
        print(f"✅ Obras sociales: {stats['obras_sociales']}")
        print(f"✅ Documentos procesados: {stats['documentos']}")
        print(f"✅ Total chunks: {stats['chunks_totales']}")
        print(f"   - Chunks de texto: {stats['chunks_totales'] - stats['chunks_tablas']}")
        print(f"   - Chunks de tablas: {stats['chunks_tablas']}")
        print(f"\n📁 JSONs guardados en: {self.output_path}")
        print("="*70 + "\n")

        return stats


def main():
    # Configuración
    # Rutas relativas desde la raíz del proyecto
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / "data" / "obras_sociales"
    output_path = project_root / "data" / "obras_sociales_json"

    # Parámetros optimizados para bge-large-en-v1.5
    chunk_size = 1800  # ~450 tokens (de 512 max)
    overlap = 300      # ~75 tokens de overlap

    # Convertir
    converter = DocumentToJsonFlat(
        data_path=str(data_path),
        output_path=str(output_path),
        chunk_size=chunk_size,
        overlap=overlap
    )

    stats = converter.process_all_documents()

    # Mostrar ejemplo de chunk
    print("\n" + "="*70)
    print("EJEMPLO DE CHUNK")
    print("="*70)

    # Buscar primer chunk de ASI
    example_file = Path(output_path) / "asi" / "2024-01-04_normas_chunks_flat.json"
    if example_file.exists():
        with open(example_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            if chunks:
                print("\nPrimer chunk de ASI:")
                print(json.dumps(chunks[0], ensure_ascii=False, indent=2))

    return stats


if __name__ == "__main__":
    main()
