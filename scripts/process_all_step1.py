#!/usr/bin/env python3
"""
Wrapper para ejecutar convert_docs_to_json.py con rutas correctas
"""
import sys
sys.path.insert(0, 'backend/scripts')

from pathlib import Path
from convert_docs_to_json import DocumentToJsonConverter

def main():
    # Rutas absolutas
    data_path = "data/obras_sociales"
    docs_general_path = "docs"
    output_path = "data/obras_sociales_json"

    print(f"✓ Data path: {Path(data_path).absolute()}")
    print(f"✓ Output path: {Path(output_path).absolute()}")
    print(f"✓ Docs general: {Path(docs_general_path).absolute()}\n")

    # Convertir
    converter = DocumentToJsonConverter(data_path, output_path)
    stats = converter.process_all_documents(docs_general_path=docs_general_path)

    return stats

if __name__ == "__main__":
    main()
