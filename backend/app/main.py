"""
FastAPI Backend - Agente Hospitalario
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import time
from datetime import datetime
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
        # Timestamp inicio
        timestamp_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Iniciar timer total
        start_total = time.time()

        # 1. Extraer entidades del texto
        start_entities = time.time()
        entities = entity_extractor.extract(request.pregunta)
        time_entities = time.time() - start_entities

        # 2. Determinar obra social (prioridad: parámetro > entidad detectada)
        obra_social = request.obra_social if request.obra_social and request.obra_social.strip() else entities['obra_social']

        print(f"\n\n{'🔵'*30}")
        print(f"{'='*60}")
        print(f"🕐 INICIO: {timestamp_inicio}")
        print(f"📝 QUERY: {request.pregunta}")
        print(f"{'='*60}")
        print(f"⏱️  Extracción de entidades: {time_entities:.3f}s")
        print(f"🔍 Entidades detectadas: {entity_extractor.format_summary(entities)}")
        print(f"📋 Obra social final: {obra_social}")

        # 3. Decidir si usar RAG o no
        # Si NO hay obra social detectada Y la pregunta es genérica → NO usar RAG
        usar_rag = True
        preguntas_genericas = ['procedimiento', 'como enrolo', 'como enrollo', 'requisitos basicos', 'documentacion basica']

        if not obra_social and any(keyword in request.pregunta.lower() for keyword in preguntas_genericas):
            usar_rag = False
            print(f"💡 Consulta genérica detectada - NO se usa RAG (protocolo básico en prompt)")

        # Recuperar contexto del RAG solo si es necesario
        start_rag = time.time()
        if usar_rag:
            context = retriever.get_context_for_llm(
                query=request.pregunta,
                top_k=TOP_K_RESULTS,
                obra_social_filter=obra_social
            )
            results = retriever.retrieve(
                query=request.pregunta,
                top_k=TOP_K_RESULTS,
                obra_social_filter=obra_social
            )
        else:
            context = ""
            results = []
        time_rag = time.time() - start_rag

        fuentes = [
            SourceDocument(
                archivo=metadata['archivo'],
                fragmento=chunk[:200] + "..." if len(chunk) > 200 else chunk,
                relevancia=round(score, 3)
            )
            for chunk, metadata, score in results
        ]

        print(f"⏱️  Búsqueda RAG (FAISS + embedding): {time_rag:.3f}s")
        print(f"📚 Documentos recuperados: {len(results)}")

        # 5. Generar respuesta con LLM
        start_llm = time.time()

        if request.use_agent:
            # Modo AGENTE con function calling
            print(f"🤖 MODO AGENTE ACTIVADO (qwen2.5:3b con tools)")

            # Callback para que el agente pueda consultar RAG
            def rag_callback(obra_social_arg, query_arg):
                rag_results = retriever.get_context_for_llm(
                    query=query_arg,
                    top_k=TOP_K_RESULTS,
                    obra_social_filter=obra_social_arg
                )
                return rag_results

            # Llamar al agente
            agent_response = llm_client.generate_response_agent(
                query=request.pregunta,
                historial=request.historial if request.historial else [],
                rag_callback=rag_callback
            )

            respuesta = agent_response["respuesta"]

            # Si el agente usó RAG, actualizar fuentes
            if agent_response["needs_rag"] and agent_response["tool_calls"]:
                tool_call = agent_response["tool_calls"][0]
                args = tool_call['function']['arguments']
                # Recuperar fuentes para mostrar
                temp_results = retriever.retrieve(
                    query=args.get('query', request.pregunta),
                    top_k=TOP_K_RESULTS,
                    obra_social_filter=args.get('obra_social')
                )
                fuentes = [
                    SourceDocument(
                        archivo=metadata['archivo'],
                        fragmento=chunk[:200] + "..." if len(chunk) > 200 else chunk,
                        relevancia=round(score, 3)
                    )
                    for chunk, metadata, score in temp_results
                ]

        else:
            # Modo CLÁSICO (sin agente)
            respuesta = llm_client.generate_response(
                query=request.pregunta,
                context=context,
                obra_social=obra_social,
                historial=request.historial if request.historial else []
            )

        time_llm = time.time() - start_llm

        # Timer total y timestamp fin
        time_total = time.time() - start_total
        timestamp_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"⏱️  Generación LLM (Ollama): {time_llm:.3f}s")
        print(f"⏱️  TIEMPO TOTAL: {time_total:.3f}s")
        print(f"\n{'─'*60}")
        print(f"💬 RESPUESTA DEL BOT:")
        print(f"{'─'*60}")
        print(f"{respuesta}")
        print(f"{'─'*60}")
        print(f"📊 Longitud: {len(respuesta)} caracteres")
        print(f"🕐 FIN: {timestamp_fin}")
        print(f"{'='*60}")
        print(f"{'🔴'*30}\n\n")

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
