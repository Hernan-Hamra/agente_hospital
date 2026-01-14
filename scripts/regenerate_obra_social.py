#!/usr/bin/env python3
"""
Script para regenerar chunks de UNA obra social específica
Sin afectar las otras obras sociales

Uso:
    python3 scripts/regenerate_obra_social.py --obra asi
    python3 scripts/regenerate_obra_social.py --obra ensalud
    python3 scripts/regenerate_obra_social.py --obra iosfa
"""
import sys
from pathlib import Path
import argparse

# Agregar backend al path
sys.path.insert(0, 'backend/scripts')

from convert_docs_to_json_flat import DocumentToJsonFlat


def main():
    parser = argparse.ArgumentParser(description='Regenerar chunks de una obra social')
    parser.add_argument('--obra', required=True, choices=['asi', 'ensalud', 'iosfa'],
                        help='Obra social a regenerar (asi, ensalud, iosfa)')
    args = parser.parse_args()

    obra_social = args.obra.lower()

    print("\n" + "="*70)
    print(f"REGENERANDO CHUNKS DE {obra_social.upper()}")
    print("="*70)

    # Rutas
    data_path = f"data/obras_sociales/{obra_social}"
    output_path = f"data/obras_sociales_json/{obra_social}"

    data_dir = Path(data_path)
    if not data_dir.exists():
        print(f"❌ Error: No existe {data_path}")
        return 1

    print(f"\n📁 Buscando documentos en: {data_path}")

    # Buscar archivos
    archivos = list(data_dir.glob("*.docx")) + list(data_dir.glob("*.pdf"))

    if not archivos:
        print(f"❌ No se encontraron documentos PDF/DOCX en {data_path}")
        return 1

    print(f"✅ Encontrados {len(archivos)} archivo(s):")
    for archivo in archivos:
        print(f"   - {archivo.name}")

    # Crear converter
    converter = DocumentToJsonFlat(
        data_path=data_path,
        output_path=output_path,
        chunk_size=1800,
        overlap=300
    )

    # Procesar cada archivo
    Path(output_path).mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    for archivo in archivos:
        chunks = converter.process_document(archivo, obra_social)
        total_chunks += len(chunks)

        # Guardar JSON
        import json
        output_file = Path(output_path) / f"{archivo.stem}_chunks_flat.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        print(f"✅ Guardado: {output_file.name} ({len(chunks)} chunks)")

    print("\n" + "="*70)
    print(f"✅ REGENERACIÓN COMPLETADA")
    print("="*70)
    print(f"Total chunks: {total_chunks}")
    print(f"\n⚠️  IMPORTANTE: Ahora debes reindexar FAISS:")
    print(f"   python3 scripts/index_data.py")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
