#!/usr/bin/env python3
"""
Bot de Telegram - Escenario 1: Modo Consulta + Groq + ChromaDB RAG
===================================================================

Bot autocontenido para consultas sobre obras sociales.
- CPU + Modo Consulta (sin memoria conversacional)
- Entity Detection determinístico
- ChromaDB RAG con filtro nativo por obra_social
- Groq gratis (llama-3.3-70b-versatile)

Uso:
    python escenario_1/bot.py
    # o desde la raíz del proyecto:
    python -m escenario_1.bot

Requisitos:
    - TELEGRAM_BOT_TOKEN en .env o variable de entorno
    - GROQ_API_KEY en .env o variable de entorno
    - ChromaDB con chunks indexados (data/chroma_db/)
"""
import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno
from dotenv import load_dotenv

# Intentar cargar .env desde varias ubicaciones
for env_path in [
    project_root / "backend" / ".env",
    project_root / ".env",
    Path(__file__).parent / ".env"
]:
    if env_path.exists():
        load_dotenv(env_path)
        break

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Imports locales del escenario
from escenario_1.rag.retriever import ChromaRetriever
from escenario_1.llm.client import GroqClient
from escenario_1.core.router import ConsultaRouter
from escenario_1.core.entity_detector import get_entity_detector
from escenario_1.metrics.collector import QueryMetrics

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Componentes globales (se inicializan en main)
retriever: ChromaRetriever = None
llm_client: GroqClient = None
router: ConsultaRouter = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "Hola! Soy el asistente del Grupo Pediátrico.\n\n"
        "Preguntame sobre obras sociales (ENSALUD, ASI, IOSFA, Grupo Pediátrico)."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_text(
        "Escribi tu consulta y te respondo.\n\n"
        "Ejemplos:\n"
        "- ¿Cuánto cuesta una consulta con especialista de ENSALUD?\n"
        "- ¿Qué documentos necesito para guardia de IOSFA?\n"
        "- ¿Qué planes tiene ENSALUD?"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - muestra estado del sistema"""
    try:
        rag_count = retriever.count() if retriever else 0
        counts_by_os = retriever.count_by_obra_social() if retriever else {}
        llm_ok = llm_client.is_available() if llm_client else False

        status_text = (
            "Estado del Sistema - Escenario 1\n"
            "===================================\n"
            f"Modo: Consulta (sin memoria)\n"
            "-----------------------------------\n"
            f"RAG: {'OK' if rag_count > 0 else 'ERROR'}\n"
            f"  Tipo: ChromaDB\n"
            f"  Chunks: {rag_count}\n"
        )

        if counts_by_os:
            for os_name, count in sorted(counts_by_os.items()):
                status_text += f"    - {os_name}: {count}\n"

        status_text += (
            "-----------------------------------\n"
            f"LLM: {'OK' if llm_ok else 'ERROR'}\n"
            f"  Provider: Groq\n"
            f"  Modelo: {llm_client.model if llm_client else 'N/A'}"
        )

        await update.message.reply_text(status_text)
    except Exception as e:
        await update.message.reply_text(f"Error verificando estado: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de texto"""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    logger.info(f"[Chat {chat_id}] Query: {user_message}")

    # Indicador de "escribiendo..."
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # Crear métricas
        metrics = QueryMetrics(query_text=user_message)

        # Ejecutar query
        result = router.process_query(query=user_message, metrics=metrics)

        respuesta = result.respuesta
        entity = result.entity_result

        # Log métricas en terminal
        entity_name = entity.entity if entity and entity.detected else 'None'
        entity_conf = entity.confidence if entity else '-'
        chunks = result.chunks_count
        top_sim = result.top_similarity
        rag_time = metrics.latency_faiss_ms
        llm_time = metrics.latency_llm_ms
        total_time = metrics.latency_total_ms
        tokens_in = metrics.tokens_input
        tokens_out = metrics.tokens_output

        logger.info(f"{'='*60}")
        logger.info(f"METRICAS - Escenario 1 (ChromaDB+Groq)")
        logger.info(f"{'='*60}")
        logger.info(f"Query: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        logger.info(f"Entidad: {entity_name} ({entity_conf})")
        logger.info(f"RAG: {chunks} chunks | sim: {top_sim:.3f} | {rag_time:.0f}ms")
        logger.info(f"LLM: {tokens_in}->{tokens_out} tokens | {llm_time:.0f}ms")
        logger.info(f"Total: {total_time:.0f}ms")
        logger.info(f"Respuesta: {respuesta[:100]}{'...' if len(respuesta) > 100 else ''}")
        logger.info(f"{'='*60}")

        # Enviar respuesta al usuario
        await update.message.reply_text(respuesta)

    except Exception as e:
        logger.error(f"[Chat {chat_id}] Error: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "Disculpa, hubo un error procesando tu consulta. "
            "Intenta de nuevo."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores globales"""
    logger.error(f"Error: {context.error}")


def initialize_components():
    """Inicializa los componentes del bot"""
    global retriever, llm_client, router

    logger.info("Inicializando componentes...")

    # ChromaDB RAG
    chroma_path = str(project_root / "data" / "chroma_db")
    logger.info(f"Cargando ChromaDB desde: {chroma_path}")
    retriever = ChromaRetriever(persist_directory=chroma_path)
    logger.info(f"ChromaDB: {retriever.count()} chunks cargados")

    # Groq LLM
    logger.info("Inicializando cliente Groq...")
    llm_client = GroqClient()
    if llm_client.is_available():
        logger.info(f"Groq OK: {llm_client.model}")
    else:
        logger.warning("Groq no disponible")

    # Entity detector y Router
    logger.info("Inicializando router...")
    entity_detector = get_entity_detector(
        str(Path(__file__).parent / "config" / "entities.yaml")
    )
    router = ConsultaRouter(
        retriever=retriever,
        llm_client=llm_client,
        entity_detector=entity_detector,
        config_path=str(Path(__file__).parent / "config" / "scenario.yaml")
    )

    logger.info("Componentes inicializados correctamente")


def main():
    """Función principal"""
    # Verificar token de Telegram
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN no configurado")
        sys.exit(1)

    # Inicializar componentes
    try:
        initialize_components()
    except Exception as e:
        logger.error(f"Error inicializando componentes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Crear aplicación de Telegram
    application = Application.builder().token(token).build()

    # Registrar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Iniciar bot
    logger.info("=" * 60)
    logger.info("BOT TELEGRAM - ESCENARIO 1")
    logger.info("=" * 60)
    logger.info("Configuracion:")
    logger.info("  - CPU (no GPU)")
    logger.info("  - Modo Consulta (sin memoria)")
    logger.info(f"  - ChromaDB RAG ({retriever.count()} chunks)")
    logger.info(f"  - Groq gratis ({llm_client.model})")
    logger.info("=" * 60)
    logger.info("Bot iniciado. Presiona Ctrl+C para detener.")
    logger.info("=" * 60)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
