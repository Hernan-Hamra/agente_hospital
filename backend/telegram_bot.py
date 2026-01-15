#!/usr/bin/env python3
"""
Bot de Telegram para el Agente Hospitalario
Conexión directa sin n8n usando python-telegram-bot

Modos de ejecución:
1. POLLING (desarrollo): No requiere HTTPS, se conecta directamente a Telegram
2. WEBHOOK (producción): Requiere HTTPS (ngrok para desarrollo)

Uso:
    # Modo polling (desarrollo)
    python telegram_bot.py --mode polling

    # Modo webhook (producción con ngrok)
    python telegram_bot.py --mode webhook --webhook-url https://xxx.ngrok-free.app
"""
import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Importar cliente LLM y RAG
from app.llm.client import create_llm_client
from app.rag.indexer import DocumentIndexer
from app.rag.retriever import DocumentRetriever

# Variables globales para el bot
llm_client = None
retriever = None


def init_rag():
    """Inicializa el sistema RAG"""
    global retriever

    embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
    index_path = Path(__file__).parent / "faiss_index"

    logger.info(f"Cargando índice RAG desde {index_path}...")
    indexer = DocumentIndexer(embedding_model=embedding_model)
    indexer.load_index(str(index_path))
    retriever = DocumentRetriever(indexer, embedding_model=embedding_model)
    logger.info(f"RAG inicializado: {len(indexer.documents)} chunks")


def init_llm():
    """Inicializa el cliente LLM"""
    global llm_client

    llm_client = create_llm_client()
    logger.info(f"LLM inicializado: {llm_client.provider} / {llm_client.model}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "¡Hola! Soy el asistente del Grupo Pediátrico.\n\n"
        "Puedo ayudarte con el enrolamiento de obras sociales:\n"
        "• ENSALUD\n"
        "• ASI\n"
        "• IOSFA\n\n"
        "¿Con qué obra social necesitás ayuda?"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/start - Iniciar conversación\n"
        "/help - Ver esta ayuda\n"
        "/reset - Reiniciar conversación\n\n"
        "Simplemente escribí tu consulta y te respondo."
    )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /reset - limpia el historial"""
    context.user_data['historial'] = []
    await update.message.reply_text("Conversación reiniciada. ¿En qué puedo ayudarte?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto"""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    logger.info(f"[Chat {chat_id}] Usuario: {user_message}")

    # Obtener historial del usuario
    if 'historial' not in context.user_data:
        context.user_data['historial'] = []

    historial = context.user_data['historial']

    # Enviar indicador de "escribiendo..."
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # Callback para RAG
        def rag_callback(obra_social: str, query: str) -> str:
            logger.info(f"[RAG] Buscando: obra_social={obra_social}, query={query}")
            try:
                results = retriever.retrieve(
                    query=query,
                    top_k=3,
                    obra_social_filter=obra_social
                )
                if results:
                    context_parts = []
                    for chunk_text, metadata, score in results:
                        context_parts.append(f"[{metadata['obra_social']}] {chunk_text}")
                    return "\n\n".join(context_parts)
                else:
                    return "No se encontró información relevante."
            except Exception as e:
                logger.error(f"Error en RAG: {e}")
                return "Error al buscar información."

        # Llamar al agente
        resultado = llm_client.generate_response_agent(
            query=user_message,
            historial=historial,
            rag_callback=rag_callback
        )

        respuesta = resultado['respuesta']

        # Actualizar historial
        historial.append({'role': 'user', 'content': user_message})
        historial.append({'role': 'assistant', 'content': respuesta})

        # Detectar cierre de conversación
        cierre_keywords = ['hasta luego', 'perfecto!', 'chau', 'adiós']
        if any(kw in respuesta.lower() for kw in cierre_keywords):
            # Limpiar historial al cerrar conversación
            context.user_data['historial'] = []
            logger.info(f"[Chat {chat_id}] Conversación finalizada, historial limpiado")
        else:
            # Mantener solo últimos 10 mensajes
            context.user_data['historial'] = historial[-10:]

        logger.info(f"[Chat {chat_id}] Bot: {respuesta[:100]}...")

        # Enviar respuesta
        await update.message.reply_text(respuesta)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        await update.message.reply_text(
            "Disculpá, tuve un problema procesando tu consulta. "
            "¿Podés intentar de nuevo?"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores"""
    logger.error(f"Error: {context.error}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Bot de Telegram - Agente Hospitalario')
    parser.add_argument('--mode', choices=['polling', 'webhook'], default='polling',
                        help='Modo de ejecución (default: polling)')
    parser.add_argument('--webhook-url', type=str, default=None,
                        help='URL del webhook (requerido para modo webhook)')
    parser.add_argument('--port', type=int, default=8443,
                        help='Puerto para webhook (default: 8443)')
    args = parser.parse_args()

    # Obtener token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN no configurado en .env")
        sys.exit(1)

    # Inicializar RAG y LLM
    logger.info("Inicializando sistemas...")
    init_rag()
    init_llm()

    # Crear aplicación
    application = Application.builder().token(token).build()

    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Ejecutar según modo
    if args.mode == 'polling':
        logger.info("Iniciando bot en modo POLLING...")
        logger.info("Presioná Ctrl+C para detener")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        # Modo webhook
        if not args.webhook_url:
            logger.error("--webhook-url requerido para modo webhook")
            sys.exit(1)

        webhook_url = f"{args.webhook_url}/telegram"
        logger.info(f"Iniciando bot en modo WEBHOOK: {webhook_url}")

        application.run_webhook(
            listen="0.0.0.0",
            port=args.port,
            url_path="telegram",
            webhook_url=webhook_url
        )


if __name__ == "__main__":
    main()
