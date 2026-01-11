"""
Indexador de chunks FINALES a FAISS
"""
import json
from pathlib import Path
from typing import Dict
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle


class DocumentIndexer:
    """Indexa chunks FINALES (*_chunks_FINAL.json) en FAISS"""

    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Args:
            embedding_model: Modelo de sentence-transformers para embeddings
        """
        print(f"Cargando modelo de embeddings: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.documents = []  # Almacena metadata de documentos

    def index_from_json(self, json_path: str) -> Dict:
        """
        Indexa chunks desde archivos *_chunks_FINAL.json

        Args:
            json_path: Ruta a data/obras_sociales_json/

        Returns:
            Dict con estadísticas de indexación
        """
        all_chunks = []
        metadata = []

        print("\n=== INDEXANDO CHUNKS FINALES ===\n")

        json_path = Path(json_path)

        # Buscar todos los *_FINAL.json en subdirectorios
        final_json_files = list(json_path.glob("**/*_FINAL.json"))

        if not final_json_files:
            raise ValueError(f"No se encontraron archivos *_FINAL.json en {json_path}")

        print(f"📁 Encontrados {len(final_json_files)} archivos *_FINAL.json\n")

        for json_file in final_json_files:
            # Determinar obra social desde el path
            obra_social = json_file.parent.name.upper()

            print(f"📄 {obra_social}: {json_file.name}")

            # Cargar JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)

            print(f"   → {len(chunks_data)} chunks cargados")

            # Procesar cada chunk
            for chunk_obj in chunks_data:
                # El texto completo del chunk
                chunk_text = chunk_obj.get('texto', '')

                if not chunk_text or not chunk_text.strip():
                    continue

                # Agregar chunk
                all_chunks.append(chunk_text)

                # Metadata del chunk (preservar estructura completa)
                chunk_metadata = {
                    'obra_social': chunk_obj.get('obra_social', chunk_obj.get('institucion', obra_social)),
                    'archivo': chunk_obj.get('archivo', json_file.name),
                    'capitulo': chunk_obj.get('capitulo', ''),
                    'seccion': chunk_obj.get('seccion', ''),
                    'tipo': chunk_obj.get('tipo', ''),
                    'es_tabla': chunk_obj.get('es_tabla', False),
                    'text': chunk_text,  # Texto del chunk
                    'json_source': str(json_file)  # Trazabilidad
                }

                # Agregar metadata adicional si existe
                if 'metadata' in chunk_obj:
                    chunk_metadata['metadata_extra'] = chunk_obj['metadata']

                metadata.append(chunk_metadata)

        if not all_chunks:
            raise ValueError("No se encontraron chunks válidos en los JSONs")

        print(f"\n📊 Total chunks a indexar: {len(all_chunks)}")

        # Generar embeddings
        print(f"\n🔄 Generando embeddings...")
        embeddings = self.model.encode(all_chunks, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')

        # Normalizar embeddings para cosine similarity
        faiss.normalize_L2(embeddings)

        # Crear índice FAISS con Inner Product (equivalente a cosine con vectores normalizados)
        print("\n🔍 Creando índice FAISS (Cosine Similarity)...")
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)

        self.documents = metadata

        stats = {
            'total_documentos': len(final_json_files),
            'total_chunks': len(all_chunks),
            'obras_sociales': len(set(m['obra_social'] for m in metadata))
        }

        print(f"\n✅ Indexación completada:")
        print(f"   - Archivos JSON: {stats['total_documentos']}")
        print(f"   - Chunks: {stats['total_chunks']}")
        print(f"   - Obras sociales: {stats['obras_sociales']}")

        return stats

    def save_index(self, index_path: str):
        """Guarda el índice FAISS y metadata"""
        index_path = Path(index_path)
        index_path.mkdir(parents=True, exist_ok=True)

        # Guardar índice FAISS
        faiss.write_index(self.index, str(index_path / "index.faiss"))

        # Guardar metadata
        with open(index_path / "documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)

        print(f"\n💾 Índice guardado en: {index_path}")

    def load_index(self, index_path: str):
        """Carga un índice FAISS existente"""
        index_path = Path(index_path)

        # Cargar índice FAISS
        self.index = faiss.read_index(str(index_path / "index.faiss"))

        # Cargar metadata
        with open(index_path / "documents.pkl", "rb") as f:
            self.documents = pickle.load(f)

        print(f"✅ Índice cargado: {len(self.documents)} chunks")
