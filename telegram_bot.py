#!/usr/bin/env python3
"""
Bot de Telegram para Agente Hospitalario
Conecta Telegram con FastAPI usando python-telegram-bot
"""
import os
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Token del bot de Telegram
TELEGRAM_TOKEN = "8349108962:AAF5X6fI0znZP-9C-9ziSY50QHAdefNO_b4"

# URL de la API FastAPI
FASTAPI_URL = "http://localhost:8000/query"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "👋 Hola! Soy el Agente Hospitalario del Grupo Pediátrico.\n\n"
        "Preguntame sobre:\n"
        "- Documentación para enrolar pacientes\n"
        "- Procedimientos de obras sociales\n"
        "- Requisitos administrativos\n\n"
        "Ejemplo: ¿Qué documentos necesito para enrolar un paciente de ENSALUD?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes del usuario"""
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Enviar mensaje de "procesando..."
    processing_msg = await update.message.reply_text("⏳ Procesando tu consulta...")

    try:
        # Llamar a FastAPI
        response = requests.post(
            FASTAPI_URL,
            json={"pregunta": user_message, "obra_social": None},
            timeout=300  # 5 minutos timeout
        )

        if response.status_code == 200:
            data = response.json()
            respuesta = data.get("respuesta", "No pude obtener una respuesta.")

            # Borrar mensaje de "procesando"
            await processing_msg.delete()

            # Enviar respuesta (Telegram tiene límite de 4096 caracteres)
            if len(respuesta) > 4000:
                # Dividir en chunks
                for i in range(0, len(respuesta), 4000):
                    await update.message.reply_text(respuesta[i:i+4000])
            else:
                await update.message.reply_text(respuesta)
        else:
            await processing_msg.edit_text(
                f"❌ Error al procesar la consulta (código {response.status_code})"
            )

    except requests.exceptions.Timeout:
        await processing_msg.edit_text(
            "⏱️ La consulta tardó demasiado. Probá con una pregunta más específica."
        )
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Error: {str(e)}\n\nAsegurate que FastAPI esté corriendo en localhost:8000"
        )


def main():
    """Inicia el bot"""
    print("🤖 Iniciando bot de Telegram...")
    print(f"📡 Conectando a FastAPI en {FASTAPI_URL}")

    # Crear aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Registrar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot iniciado. Presioná Ctrl+C para detener.\n")
    print("💬 Probá mandando un mensaje a @agente_gpediatrico_bot en Telegram")

    # Iniciar bot (polling)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
