#!/usr/bin/env python3
"""
Procesa checklist_general_grupo_pediatrico.docx a formato JSON compatible con el RAG.

Uso:
    python scripts/process_grupo_pediatrico.py

Output:
    data/obras_sociales_json/grupo_pediatrico/checklist_general_chunks_flat.json
"""
import json
from pathlib import Path
from docx import Document


def extract_sections(doc_path: str) -> list:
    """
    Extrae secciones del documento como chunks.
    Cada título en mayúsculas + su contenido = 1 chunk.
    """
    doc = Document(doc_path)
    chunks = []
    current_section = None
    current_content = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detectar títulos de sección (texto en mayúsculas o con formato específico)
        is_title = (
            text.isupper() or
            text.startswith("INGRESO") or
            text.startswith("INTERNACIÓN") or
            text.startswith("COSEGUROS") or
            text.startswith("DOCUMENTACIÓN")
        )

        if is_title and len(text) > 5:
            # Guardar sección anterior si existe
            if current_section and current_content:
                chunk_text = f"{current_section}\n" + "\n".join(current_content)
                chunks.append({
                    "seccion": current_section,
                    "texto": chunk_text
                })

            # Iniciar nueva sección
            current_section = text
            current_content = []
        else:
            # Agregar al contenido actual
            if current_section:
                current_content.append(text)

    # Guardar última sección
    if current_section and current_content:
        chunk_text = f"{current_section}\n" + "\n".join(current_content)
        chunks.append({
            "seccion": current_section,
            "texto": chunk_text
        })

    return chunks


def process_docx_to_json(
    docx_path: str,
    output_dir: str,
    obra_social: str = "GRUPO_PEDIATRICO"
) -> dict:
    """
    Procesa un DOCX a formato JSON compatible con el indexador RAG.

    Args:
        docx_path: Ruta al archivo .docx
        output_dir: Directorio de salida para el JSON
        obra_social: Valor para el campo obra_social

    Returns:
        Estadísticas del procesamiento
    """
    docx_path = Path(docx_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📄 Procesando: {docx_path.name}")

    # Extraer secciones
    sections = extract_sections(str(docx_path))

    # Convertir a formato chunks_flat
    chunks = []
    for i, section in enumerate(sections, 1):
        chunk = {
            "obra_social": obra_social,
            "archivo": docx_path.name,
            "chunk_id": f"{i:03d}",
            "texto": section["texto"],
            "seccion": section["seccion"],
            "es_tabla": False
        }
        chunks.append(chunk)
        print(f"   → Chunk {i:03d}: {section['seccion'][:50]}...")

    # Guardar JSON
    output_file = output_dir / f"{docx_path.stem}_chunks_flat.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Guardado: {output_file}")
    print(f"   - Chunks: {len(chunks)}")

    return {
        "archivo": str(docx_path),
        "output": str(output_file),
        "chunks": len(chunks),
        "obra_social": obra_social
    }


def main():
    # Rutas
    project_root = Path(__file__).parent.parent
    docx_path = project_root / "data" / "grupo_pediatrico" / "checklist_general_grupo_pediatrico.docx"
    output_dir = project_root / "data" / "obras_sociales_json" / "grupo_pediatrico"

    if not docx_path.exists():
        print(f"❌ No se encontró: {docx_path}")
        return

    # Procesar
    stats = process_docx_to_json(
        docx_path=str(docx_path),
        output_dir=str(output_dir),
        obra_social="GRUPO_PEDIATRICO"
    )

    print(f"\n📊 Resumen:")
    print(f"   Archivo: {stats['archivo']}")
    print(f"   Chunks: {stats['chunks']}")
    print(f"   Obra social: {stats['obra_social']}")

    print(f"\n⚠️  IMPORTANTE: Después de procesar, re-indexar con:")
    print(f"   python scripts/reindex_faiss.py")


if __name__ == "__main__":
    main()
