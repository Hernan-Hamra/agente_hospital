#!/usr/bin/env python3
"""
Wrapper para ejecutar convert_docs_to_json_flat.py con rutas correctas
"""
import sys
sys.path.insert(0, 'backend/scripts')

from pathlib import Path
from convert_docs_to_json_flat import DocumentToJsonFlat

def main():
    # Rutas desde la raíz del proyecto
    data_path = "data/obras_sociales"
    output_path = "data/obras_sociales_json"

    print(f"✓ Data path: {Path(data_path).absolute()}")
    print(f"✓ Output path: {Path(output_path).absolute()}\n")

    # Parámetros optimizados para bge-large-en-v1.5
    # Modelo max: 512 tokens (~2048 chars)
    # Usamos 1800 chars (~450 tokens) para dejar margen
    chunk_size = 1800
    overlap = 300

    # Convertir
    converter = DocumentToJsonFlat(
        data_path=data_path,
        output_path=output_path,
        chunk_size=chunk_size,
        overlap=overlap
    )

    stats = converter.process_all_documents()

    # Mostrar ejemplo
    print("\n" + "="*70)
    print("EJEMPLO DE CHUNK")
    print("="*70)

    example_file = Path(output_path) / "asi" / "2024-01-04_normas_chunks_flat.json"
    if example_file.exists():
        import json
        with open(example_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            if chunks:
                print("\nPrimer chunk (texto):")
                primer_texto = next((c for c in chunks if not c.get("es_tabla")), chunks[0])
                print(f"  Obra social: {primer_texto['obra_social']}")
                print(f"  Archivo: {primer_texto['archivo']}")
                print(f"  Chunk ID: {primer_texto['chunk_id']}")
                print(f"  Es tabla: {primer_texto['es_tabla']}")
                print(f"  Longitud: {len(primer_texto['texto'])} chars")
                print(f"  Texto (primeros 300 chars):")
                print(f"    {primer_texto['texto'][:300]}...")

                print("\nPrimer chunk (tabla):")
                primer_tabla = next((c for c in chunks if c.get("es_tabla")), None)
                if primer_tabla:
                    print(f"  Tabla #{primer_tabla.get('tabla_numero')}")
                    print(f"  Longitud: {len(primer_tabla['texto'])} chars")
                    print(f"  Texto (primeros 200 chars):")
                    print(f"    {primer_tabla['texto'][:200]}...")

    return stats

if __name__ == "__main__":
    main()
