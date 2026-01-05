"""
Indexador de documentos PDF/DOCX a FAISS
"""
import os
from pathlib import Path
from typing import List, Dict
import pdfplumber
from docx import Document
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle


class DocumentIndexer:
    """Indexa documentos PDF/DOCX y crea índice FAISS"""

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

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrae texto de un PDF"""
        print(f"  Extrayendo texto de PDF: {Path(pdf_path).name}")
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return "\n\n".join(text)

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extrae texto de un DOCX"""
        print(f"  Extrayendo texto de DOCX: {Path(docx_path).name}")
        doc = Document(docx_path)
        text = []
        for para in doc.paragraphs:
            if para.text.strip():
                text.append(para.text)
        return "\n".join(text)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Divide texto en chunks con overlap

        Args:
            text: Texto completo
            chunk_size: Tamaño de cada chunk en caracteres
            overlap: Overlap entre chunks
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
        return chunks

    def index_documents(self,
                       data_path: str,
                       docs_path: str = None,
                       chunk_size: int = 500,
                       chunk_overlap: int = 50) -> Dict:
        """
        Indexa todos los documentos PDF/DOCX encontrados

        Args:
            data_path: Ruta a data/obras_sociales/
            docs_path: Ruta opcional a docs/ (checklist general)
            chunk_size: Tamaño de chunks
            chunk_overlap: Overlap entre chunks

        Returns:
            Dict con estadísticas de indexación
        """
        all_chunks = []
        metadata = []

        print("\n=== INDEXANDO DOCUMENTOS ===\n")

        # 1. Indexar obras sociales
        data_path = Path(data_path)
        for os_dir in data_path.iterdir():
            if not os_dir.is_dir():
                continue

            obra_social = os_dir.name.upper()
            print(f"Obra Social: {obra_social}")

            for file_path in os_dir.iterdir():
                if file_path.suffix.lower() == '.pdf':
                    text = self.extract_text_from_pdf(str(file_path))
                elif file_path.suffix.lower() == '.docx':
                    text = self.extract_text_from_docx(str(file_path))
                else:
                    continue

                # Dividir en chunks
                chunks = self.chunk_text(text, chunk_size, chunk_overlap)
                print(f"    → {len(chunks)} chunks generados")

                for chunk in chunks:
                    all_chunks.append(chunk)
                    metadata.append({
                        'archivo': file_path.name,
                        'obra_social': obra_social,
                        'ruta': str(file_path)
                    })

        # 2. Indexar documentos generales (checklist hospital)
        if docs_path:
            docs_path = Path(docs_path)
            print(f"\nDocumentos generales:")
            for file_path in docs_path.glob('*.docx'):
                print(f"  {file_path.name}")
                text = self.extract_text_from_docx(str(file_path))
                chunks = self.chunk_text(text, chunk_size, chunk_overlap)
                print(f"    → {len(chunks)} chunks generados")

                for chunk in chunks:
                    all_chunks.append(chunk)
                    metadata.append({
                        'archivo': file_path.name,
                        'obra_social': 'GENERAL',
                        'ruta': str(file_path)
                    })

        # 3. Generar embeddings
        print(f"\n🔄 Generando embeddings para {len(all_chunks)} chunks...")
        embeddings = self.model.encode(all_chunks, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')

        # 4. Crear índice FAISS
        print("\n🔍 Creando índice FAISS...")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)

        # Guardar chunks de texto junto con metadata
        for i, chunk in enumerate(all_chunks):
            metadata[i]['text'] = chunk

        self.documents = metadata

        stats = {
            'total_documentos': len(set(m['archivo'] for m in metadata)),
            'total_chunks': len(all_chunks),
            'obras_sociales': len(set(m['obra_social'] for m in metadata if m['obra_social'] != 'GENERAL'))
        }

        print(f"\n✅ Indexación completada:")
        print(f"   - Documentos: {stats['total_documentos']}")
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
