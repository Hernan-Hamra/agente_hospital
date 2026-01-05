"""
FastAPI Backend - Agente Hospitalario
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
from dotenv import load_dotenv

from app.models import QueryRequest, QueryResponse, HealthResponse, SourceDocument
from app.rag.indexer import DocumentIndexer
from app.rag.retriever import DocumentRetriever
from app.rag.entity_extractor import EntityExtractor
from app.llm.client import OllamaClient

# Cargar variables de entorno
load_dotenv()

# Configuración
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DATA_PATH = os.getenv("DATA_PATH", "../data/obras_sociales")
DOCS_PATH = os.getenv("DOCS_PATH", "../docs")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# Inicializar FastAPI
app = FastAPI(
    title="Agente Hospitalario - Grupo Pediátrico",
    description="Sistema RAG para consultas administrativas de obras sociales",
    version="0.1.0"
)

# CORS (para n8n y Telegram)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globales
indexer: DocumentIndexer = None
retriever: DocumentRetriever = None
llm_client: OllamaClient = None
entity_extractor: EntityExtractor = EntityExtractor()


@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar el servidor"""
    global indexer, retriever, llm_client

    print("\n" + "=" * 60)
    print("🏥 AGENTE HOSPITALARIO - GRUPO PEDIÁTRICO")
    print("=" * 60 + "\n")

    # 1. Inicializar LLM
    print("🤖 Inicializando cliente Ollama...")
    llm_client = OllamaClient(host=OLLAMA_HOST, model=OLLAMA_MODEL)

    if llm_client.is_available():
        print(f"   ✅ Ollama disponible en {OLLAMA_HOST}")
        print(f"   📦 Modelo: {OLLAMA_MODEL}")
    else:
        print(f"   ⚠️ Ollama no disponible - las consultas fallarán")

    # 2. Cargar índice FAISS
    print(f"\n📚 Cargando índice RAG...")
    indexer = DocumentIndexer(embedding_model=EMBEDDING_MODEL)

    index_path = Path(FAISS_INDEX_PATH)
    if index_path.exists() and (index_path / "index.faiss").exists():
        try:
            indexer.load_index(str(index_path))
            print(f"   ✅ Índice cargado: {len(indexer.documents)} chunks")
        except Exception as e:
            print(f"   ❌ Error cargando índice: {e}")
            print(f"   💡 Ejecutá: python scripts/index_data.py")
            indexer = None
    else:
        print(f"   ⚠️ No se encontró índice en {index_path}")
        print(f"   💡 Ejecutá: python scripts/index_data.py")
        indexer = None

    # 3. Inicializar retriever
    if indexer:
        retriever = DocumentRetriever(indexer, embedding_model=EMBEDDING_MODEL)
        print(f"   ✅ Retriever inicializado")

    print("\n" + "=" * 60)
    print("🚀 Servidor listo - http://localhost:8000")
    print("📖 Documentación - http://localhost:8000/docs")
    print("=" * 60 + "\n")


@app.get("/", tags=["Health"])
async def root():
    """Endpoint raíz"""
    return {
        "message": "Agente Hospitalario - Grupo Pediátrico",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check del sistema"""
    return HealthResponse(
        status="ok" if (indexer and llm_client and llm_client.is_available()) else "degraded",
        version="0.1.0",
        ollama_disponible=llm_client.is_available() if llm_client else False,
        indice_cargado=indexer is not None,
        documentos_indexados=len(indexer.documents) if indexer else 0
    )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_agent(request: QueryRequest):
    """
    Consulta al agente hospitalario

    Ejemplo:
    ```json
    {
        "pregunta": "¿Qué documentos necesito para enrolar un paciente de ENSALUD?",
        "obra_social": "ENSALUD"
    }
    ```
    """
    # Validar que el sistema esté listo
    if not indexer:
        raise HTTPException(
            status_code=503,
            detail="Índice RAG no cargado. Ejecutá: python scripts/index_data.py"
        )

    if not llm_client or not llm_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama no disponible. Verificá que esté corriendo."
        )

    try:
        # 1. Extraer entidades del texto
        entities = entity_extractor.extract(request.pregunta)

        # 2. Determinar obra social (prioridad: parámetro > entidad detectada)
        obra_social = request.obra_social if request.obra_social and request.obra_social.strip() else entities['obra_social']

        print(f"\n🔍 Entidades detectadas: {entity_extractor.format_summary(entities)}")
        print(f"📋 Obra social final: {obra_social}\n")

        # 3. Recuperar contexto del RAG
        context = retriever.get_context_for_llm(
            query=request.pregunta,
            top_k=TOP_K_RESULTS,
            obra_social_filter=obra_social
        )

        # 4. Obtener documentos para metadata de respuesta
        results = retriever.retrieve(
            query=request.pregunta,
            top_k=TOP_K_RESULTS,
            obra_social_filter=obra_social
        )

        fuentes = [
            SourceDocument(
                archivo=metadata['archivo'],
                fragmento=chunk[:200] + "..." if len(chunk) > 200 else chunk,
                relevancia=round(score, 3)
            )
            for chunk, metadata, score in results
        ]

        # 5. Generar respuesta con LLM
        respuesta = llm_client.generate_response(
            query=request.pregunta,
            context=context,
            obra_social=obra_social
        )

        # 6. Detectar obra social mencionada
        obra_social_detectada = obra_social
        if not obra_social_detectada:
            # Detectar en los resultados
            obras_sociales = set(m['obra_social'] for _, m, _ in results if m['obra_social'] != 'GENERAL')
            if len(obras_sociales) == 1:
                obra_social_detectada = list(obras_sociales)[0]

        return QueryResponse(
            respuesta=respuesta,
            fuentes=fuentes,
            obra_social_detectada=obra_social_detectada
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando consulta: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
