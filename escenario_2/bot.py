"""
Bot Telegram para Escenario 2 - Sin LLM.

Flujo:
1. Usuario envía mensaje
2. Normalizar input (sinónimos)
3. Query SQL
4. Formatear respuesta
5. Enviar

Sin RAG, sin LLM, solo lookup estructurado.

Comandos de supervisor:
- /restriccion OBRA_SOCIAL TIPO MENSAJE [PERMITIDOS]
- /quitar_restriccion OBRA_SOCIAL [TIPO]
- /restricciones [OBRA_SOCIAL]
"""
import os
import sys
import logging
import sqlite3
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Agregar parent al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from escenario_2.core.normalizer import Normalizer
from escenario_2.core.query_engine import QueryEngine

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# IDs de supervisores (cargar desde .env)
SUPERVISOR_IDS: set = set()


def load_supervisors():
    """Carga IDs de supervisores desde variable de entorno."""
    global SUPERVISOR_IDS
    ids_str = os.getenv("TELEGRAM_SUPERVISOR_IDS", "")
    if ids_str:
        SUPERVISOR_IDS = {int(id.strip()) for id in ids_str.split(",") if id.strip()}
    logger.info(f"Supervisores cargados: {len(SUPERVISOR_IDS)} IDs")


def supervisor_required(func):
    """Decorador para comandos que requieren ser supervisor."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in SUPERVISOR_IDS:
            await update.message.reply_text(
                "⛔ No tenés permisos para usar este comando.\n"
                "Contactá al administrador si necesitás acceso."
            )
            logger.warning(f"Usuario {user_id} intentó usar comando de supervisor")
            return
        return await func(update, context)
    return wrapper


class ConsultaBot:
    """Bot de consultas sin LLM."""

    def __init__(self, db_path: str = None):
        """
        Inicializa el bot.

        Args:
            db_path: Ruta a la base de datos SQLite
        """
        if db_path is None:
            db_path = Path(__file__).parent / "data" / "obras_sociales.db"

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.normalizer = Normalizer(self.conn)
        self.engine = QueryEngine(self.conn)

        logger.info(f"Bot inicializado con DB: {db_path}")

    def process_message(self, text: str) -> str:
        """
        Procesa un mensaje y devuelve la respuesta.

        Args:
            text: Mensaje del usuario

        Returns:
            Respuesta formateada
        """
        # 1. Normalizar
        normalized = self.normalizer.normalize(text)
        logger.info(f"Normalizado: {normalized.to_dict()}")

        # 2. Detectar si es consulta de coseguros
        text_lower = text.lower()
        if any(word in text_lower for word in ['coseguro', 'copago', 'pago', 'valor', 'precio']):
            if normalized.obra_social:
                result = self.engine.query_coseguros(normalized.obra_social)
                return result.respuesta

        # 3. Query normal por tipo de ingreso
        result = self.engine.query(normalized)
        return result.respuesta


# Instancia global del bot
bot_instance: ConsultaBot = None


def get_bot() -> ConsultaBot:
    """Obtiene o crea la instancia del bot."""
    global bot_instance
    if bot_instance is None:
        bot_instance = ConsultaBot()
    return bot_instance


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /start."""
    welcome = """
👋 ¡Hola! Soy el asistente del Grupo Pediátrico.

Puedo ayudarte con información de obras sociales:
• ENSALUD
• ASI
• IOSFA

Preguntame por:
• Ingreso ambulatorio/turnos
• Internación
• Guardia
• Traslados
• Coseguros

Ejemplo: "internación ensalud" o "coseguros asi"
"""
    await update.message.reply_text(welcome.strip())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /help."""
    help_text = """
📖 *Cómo usar este bot:*

Escribí la obra social + tipo de consulta:

*Ejemplos:*
• `ensalud ambulatorio`
• `internación asi`
• `guardia iosfa`
• `coseguros ensalud`

*Obras sociales disponibles:*
ENSALUD, ASI, IOSFA

*Tipos de ingreso:*
ambulatorio, internación, guardia, traslados
"""
    # Agregar comandos de supervisor si corresponde
    user_id = update.effective_user.id
    if user_id in SUPERVISOR_IDS:
        help_text += """

━━━━━━━━━━━━━━━━━━━━
👤 *COMANDOS DE SUPERVISOR*

/restriccion OS TIPO "MSG" [PERMITIDOS]
  Agregar restricción

/quitar_restriccion OS [TIPO]
  Quitar restricción

/restricciones [OS]
  Ver restricciones activas
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensajes de texto."""
    user_text = update.message.text
    user_id = update.effective_user.id

    logger.info(f"[User {user_id}] Mensaje: {user_text}")

    try:
        bot = get_bot()
        response = bot.process_message(user_text)

        logger.info(f"[User {user_id}] Respuesta: {response[:100]}...")

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        await update.message.reply_text(
            "Ocurrió un error procesando tu consulta. Por favor intentá de nuevo."
        )


# =============================================================================
# COMANDOS DE SUPERVISOR
# =============================================================================

@supervisor_required
async def restriccion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Agregar restricción a una obra social.

    Uso:
        /restriccion ENSALUD falta_pago "Solo guardia por pagos pendientes" guardia
        /restriccion ASI convenio_suspendido "Convenio suspendido temporalmente"

    Args (en context.args):
        0: obra_social (ENSALUD, ASI, IOSFA)
        1: tipo_restriccion (falta_pago, convenio_suspendido, cupo_agotado)
        2: mensaje (entre comillas)
        3: tipos_permitidos (opcional, ej: "guardia" o "guardia,ambulatorio")
    """
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Uso: /restriccion OBRA_SOCIAL TIPO \"MENSAJE\" [PERMITIDOS]\n\n"
            "Ejemplos:\n"
            "• `/restriccion ENSALUD falta_pago \"Solo guardia\" guardia`\n"
            "• `/restriccion ASI convenio_suspendido \"Suspendido\"`\n\n"
            "Tipos: falta_pago, convenio_suspendido, cupo_agotado",
            parse_mode='Markdown'
        )
        return

    # Parsear argumentos
    obra_social = context.args[0].upper()

    # Reconstruir el mensaje (puede tener espacios)
    full_text = update.message.text
    # Extraer texto entre comillas
    import re
    match = re.search(r'"([^"]+)"', full_text)
    if not match:
        await update.message.reply_text(
            "❌ El mensaje debe ir entre comillas.\n"
            "Ejemplo: `/restriccion ENSALUD falta_pago \"Solo guardia\"`",
            parse_mode='Markdown'
        )
        return

    mensaje = match.group(1)
    tipo_restriccion = context.args[1].lower()

    # Tipos permitidos (opcional, después de las comillas)
    tipos_permitidos = None
    after_quotes = full_text.split('"')[-1].strip()
    if after_quotes:
        tipos_permitidos = after_quotes.replace(" ", "")

    # Agregar restricción
    bot = get_bot()
    success = bot.engine.add_restriccion(
        obra_social=obra_social,
        tipo_restriccion=tipo_restriccion,
        mensaje=mensaje,
        tipos_permitidos=tipos_permitidos
    )

    if success:
        response = f"✅ Restricción agregada:\n\n"
        response += f"• Obra social: {obra_social}\n"
        response += f"• Tipo: {tipo_restriccion}\n"
        response += f"• Mensaje: {mensaje}\n"
        if tipos_permitidos:
            response += f"• Solo permite: {tipos_permitidos}\n"
        else:
            response += f"• Bloquea: TODOS los ingresos\n"

        logger.info(f"[Supervisor {update.effective_user.id}] Restricción agregada: {obra_social} - {tipo_restriccion}")
    else:
        response = f"❌ Error: Obra social '{obra_social}' no encontrada."

    await update.message.reply_text(response)


@supervisor_required
async def quitar_restriccion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Quitar restricción de una obra social.

    Uso:
        /quitar_restriccion ENSALUD falta_pago  (quita tipo específico)
        /quitar_restriccion ENSALUD             (quita todas)
    """
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Uso: /quitar_restriccion OBRA_SOCIAL [TIPO]\n\n"
            "Ejemplos:\n"
            "• `/quitar_restriccion ENSALUD falta_pago`\n"
            "• `/quitar_restriccion ENSALUD` (quita todas)",
            parse_mode='Markdown'
        )
        return

    obra_social = context.args[0].upper()
    tipo_restriccion = context.args[1].lower() if len(context.args) > 1 else None

    bot = get_bot()
    count = bot.engine.remove_restriccion(obra_social, tipo_restriccion)

    if count > 0:
        response = f"✅ Se quitaron {count} restricción(es) de {obra_social}"
        if tipo_restriccion:
            response += f" (tipo: {tipo_restriccion})"
        logger.info(f"[Supervisor {update.effective_user.id}] Restricciones removidas: {obra_social} x{count}")
    else:
        response = f"ℹ️ No había restricciones activas para {obra_social}"
        if tipo_restriccion:
            response += f" del tipo {tipo_restriccion}"

    await update.message.reply_text(response)


@supervisor_required
async def listar_restricciones_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Listar restricciones activas.

    Uso:
        /restricciones          (todas)
        /restricciones ENSALUD  (de una OS específica)
    """
    obra_social = context.args[0].upper() if context.args else None

    bot = get_bot()
    restricciones = bot.engine.list_restricciones(obra_social)

    if not restricciones:
        if obra_social:
            response = f"ℹ️ No hay restricciones activas para {obra_social}"
        else:
            response = "ℹ️ No hay restricciones activas"
    else:
        response = "📋 *RESTRICCIONES ACTIVAS*\n\n"
        for r in restricciones:
            response += f"⛔ *{r['obra_social_codigo']}* - {r['tipo_restriccion']}\n"
            response += f"   {r['mensaje']}\n"
            if r['tipos_permitidos']:
                response += f"   Solo permite: {r['tipos_permitidos']}\n"
            if r['tipos_bloqueados']:
                response += f"   Bloquea: {r['tipos_bloqueados']}\n"
            response += f"   Desde: {r['fecha_inicio']}\n\n"

    await update.message.reply_text(response, parse_mode='Markdown')


@supervisor_required
async def mi_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el ID del usuario (útil para agregar supervisores)."""
    user = update.effective_user
    await update.message.reply_text(
        f"👤 Tu información:\n"
        f"• ID: `{user.id}`\n"
        f"• Username: @{user.username or 'N/A'}\n"
        f"• Nombre: {user.first_name}",
        parse_mode='Markdown'
    )


def main():
    """Punto de entrada principal."""
    # Cargar variables de entorno
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN no encontrado en variables de entorno")
        sys.exit(1)

    # Cargar supervisores
    load_supervisors()

    # Verificar que la DB existe
    db_path = Path(__file__).parent / "data" / "obras_sociales.db"
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        logger.error("Ejecutá primero: python escenario_2/data/init_db.py")
        sys.exit(1)

    # Crear aplicación
    application = Application.builder().token(token).build()

    # Agregar handlers - Comandos generales
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mi_id", mi_id_command))

    # Agregar handlers - Comandos de supervisor
    application.add_handler(CommandHandler("restriccion", restriccion_command))
    application.add_handler(CommandHandler("quitar_restriccion", quitar_restriccion_command))
    application.add_handler(CommandHandler("restricciones", listar_restricciones_command))

    # Agregar handler de mensajes (debe ir al final)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar bot
    logger.info("Bot iniciando... (Ctrl+C para detener)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
