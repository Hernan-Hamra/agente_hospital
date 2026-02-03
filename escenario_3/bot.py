#!/usr/bin/env python3
"""
Bot de Telegram - Escenario 3: Modo Agente + Groq + ChromaDB RAG
=================================================================

Bot conversacional con memoria para consultas sobre obras sociales.
- Modo Agente (con memoria conversacional)
- Entity Detection determinístico
- ChromaDB RAG con filtro nativo por obra_social
- Groq gratis (llama-3.3-70b-versatile)

Uso:
    python escenario_3/bot.py
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno
from dotenv import load_dotenv

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
from escenario_3.rag.retriever import ChromaRetriever
from escenario_3.llm.client import GroqClient
from escenario_3.core.router import AgenteRouter
from escenario_3.core.entity_detector import get_entity_detector
from escenario_3.metrics.collector import QueryMetrics

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Componentes globales
retriever: ChromaRetriever = None
llm_client: GroqClient = None

# Routers por chat_id (cada usuario tiene su propio historial)
routers: Dict[int, AgenteRouter] = {}


def get_router(chat_id: int) -> AgenteRouter:
    """Obtiene o crea un router para el chat"""
    if chat_id not in routers:
        routers[chat_id] = AgenteRouter(
            retriever=retriever,
            llm_client=llm_client,
            entity_detector=get_entity_detector(
                str(Path(__file__).parent / "config" / "entities.yaml")
            ),
            config_path=str(Path(__file__).parent / "config" / "scenario.yaml")
        )
    return routers[chat_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    chat_id = update.effective_chat.id
    # Limpiar historial al iniciar
    if chat_id in routers:
        routers[chat_id].clear_history()

    await update.message.reply_text(
        "Hola! Soy el asistente del Grupo Pediátrico (Modo Agente).\n\n"
        "Preguntame sobre obras sociales (ENSALUD, ASI, IOSFA, Grupo Pediátrico).\n\n"
        "Puedo recordar nuestra conversación para darte respuestas contextualizadas."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/start - Iniciar conversación (limpia historial)\n"
        "/clear - Limpiar historial de conversación\n"
        "/status - Ver estado del sistema\n\n"
        "Ejemplos de consultas:\n"
        "- ¿Cuánto cuesta una consulta con especialista de ENSALUD?\n"
        "- ¿Y qué planes tienen? (usa contexto anterior)\n"
        "- ¿Qué documentos necesito para guardia de IOSFA?"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /clear - limpia historial"""
    chat_id = update.effective_chat.id
    if chat_id in routers:
        routers[chat_id].clear_history()
    await update.message.reply_text("Historial de conversación limpiado.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    try:
        chat_id = update.effective_chat.id
        router = get_router(chat_id) if chat_id in routers else None
        history_turns = len(router.history) // 2 if router else 0

        rag_count = retriever.count() if retriever else 0
        counts_by_os = retriever.count_by_obra_social() if retriever else {}
        llm_ok = llm_client.is_available() if llm_client else False

        status_text = (
            "Estado del Sistema - Escenario 3 (Modo Agente)\n"
            "===============================================\n"
            f"Modo: Agente (con memoria)\n"
            f"Historial: {history_turns} turnos\n"
            "-----------------------------------------------\n"
            f"RAG: {'OK' if rag_count > 0 else 'ERROR'}\n"
            f"  Tipo: ChromaDB (shared)\n"
            f"  Chunks: {rag_count}\n"
        )

        if counts_by_os:
            for os_name, count in sorted(counts_by_os.items()):
                status_text += f"    - {os_name}: {count}\n"

        status_text += (
            "-----------------------------------------------\n"
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
        # Obtener router del usuario
        router = get_router(chat_id)

        # Crear métricas
        metrics = QueryMetrics(query_text=user_message)

        # Ejecutar query
        result = router.process_query(query=user_message, metrics=metrics)

        respuesta = result.respuesta
        entity = result.entity_result

        # Log métricas
        entity_name = entity.entity if entity and entity.detected else 'None'
        entity_conf = entity.confidence if entity else '-'
        chunks = result.chunks_count
        top_sim = result.top_similarity
        history = result.history_turns
        rag_time = metrics.latency_faiss_ms
        llm_time = metrics.latency_llm_ms
        total_time = metrics.latency_total_ms
        tokens_in = metrics.tokens_input
        tokens_out = metrics.tokens_output

        logger.info(f"{'='*60}")
        logger.info(f"METRICAS - Escenario 3 (Modo Agente)")
        logger.info(f"{'='*60}")
        logger.info(f"Query: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        logger.info(f"Entidad: {entity_name} ({entity_conf})")
        logger.info(f"RAG: {chunks} chunks | sim: {top_sim:.3f} | {rag_time:.0f}ms")
        logger.info(f"LLM: {tokens_in}->{tokens_out} tokens | {llm_time:.0f}ms")
        logger.info(f"Historial: {history} turnos")
        logger.info(f"Total: {total_time:.0f}ms")
        logger.info(f"{'='*60}")

        await update.message.reply_text(respuesta)

    except Exception as e:
        logger.error(f"[Chat {chat_id}] Error: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "Disculpa, hubo un error procesando tu consulta. Intenta de nuevo."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores globales"""
    logger.error(f"Error: {context.error}")


def initialize_components():
    """Inicializa los componentes del bot"""
    global retriever, llm_client

    logger.info("Inicializando componentes...")

    # ChromaDB RAG (shared)
    chroma_path = str(project_root / "shared" / "data" / "chroma_db")
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
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Iniciar bot
    logger.info("=" * 60)
    logger.info("BOT TELEGRAM - ESCENARIO 3 (MODO AGENTE)")
    logger.info("=" * 60)
    logger.info("Configuracion:")
    logger.info("  - CPU (no GPU)")
    logger.info("  - Modo Agente (con memoria conversacional)")
    logger.info(f"  - ChromaDB RAG ({retriever.count()} chunks)")
    logger.info(f"  - Groq gratis ({llm_client.model})")
    logger.info("=" * 60)
    logger.info("Bot iniciado. Presiona Ctrl+C para detener.")
    logger.info("=" * 60)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
