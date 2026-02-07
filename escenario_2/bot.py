"""
Bot Telegram para Escenario 2 - Sin LLM.

Flujo:
1. Usuario envía mensaje
2. Normalizar input (sinónimos)
3. Query SQL
4. Formatear respuesta
5. Enviar

Sin RAG, sin LLM, solo lookup estructurado.

Comandos de supervisor (requieren PIN):
- /restriccion:PIN OBRA_SOCIAL TIPO "MENSAJE" [PERMITIDOS]
- /quitar_restriccion:PIN OBRA_SOCIAL [TIPO]
- /restricciones:PIN [OBRA_SOCIAL]

El mensaje con PIN se borra automáticamente.
"""
import os
import re
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

# Configuración de supervisores (cargar desde .env)
SUPERVISOR_IDS: set = set()
SUPERVISOR_PIN: str = ""


def load_supervisors():
    """Carga IDs de supervisores y PIN desde variables de entorno."""
    global SUPERVISOR_IDS, SUPERVISOR_PIN

    # Cargar IDs (opcional)
    ids_str = os.getenv("TELEGRAM_SUPERVISOR_IDS", "")
    if ids_str:
        SUPERVISOR_IDS = {int(id.strip()) for id in ids_str.split(",") if id.strip()}

    # Cargar PIN
    SUPERVISOR_PIN = os.getenv("SUPERVISOR_PIN", "")

    logger.info(f"Supervisores: {len(SUPERVISOR_IDS)} IDs, PIN: {'configurado' if SUPERVISOR_PIN else 'no configurado'}")


def extract_pin_from_command(text: str) -> tuple[str, str]:
    """
    Extrae el PIN de un comando con formato /comando:PIN args...

    Returns:
        (pin, resto_del_comando) o ("", comando_original)
    """
    if not text:
        return "", ""

    parts = text.split(maxsplit=1)
    command_part = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if ":" in command_part:
        cmd, pin = command_part.split(":", 1)
        return pin, f"{cmd} {rest}".strip()

    return "", text


def get_command_args(text: str) -> list[str]:
    """
    Extrae los argumentos de un comando (ignorando el comando y PIN).

    /restriccion:1234 ENSALUD falta_pago "msg" -> ["ENSALUD", "falta_pago", '"msg"']
    /restriccion ENSALUD falta_pago -> ["ENSALUD", "falta_pago"]
    """
    if not text:
        return []

    # Quitar el comando (primera palabra)
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return []

    return parts[1].split()


async def validate_supervisor(update: Update, context: ContextTypes.DEFAULT_TYPE, delete_message: bool = True) -> bool:
    """
    Valida si el usuario es supervisor (por ID o PIN).
    Guarda el texto original en context.user_data['original_text'] antes de borrar.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        delete_message: Si True, borra el mensaje cuando contiene PIN

    Returns:
        True si es supervisor válido
    """
    user_id = update.effective_user.id
    message_text = update.message.text or ""
    chat_id = update.effective_chat.id

    # Guardar texto original para que los handlers lo usen
    context.user_data['original_text'] = message_text
    context.user_data['original_args'] = get_command_args(message_text)

    # 1. Verificar si es supervisor por ID (no necesita PIN)
    if user_id in SUPERVISOR_IDS:
        return True

    # 2. Verificar PIN en el comando
    pin, _ = extract_pin_from_command(message_text)

    if pin and SUPERVISOR_PIN and pin == SUPERVISOR_PIN:
        # PIN correcto - borrar mensaje para ocultar el PIN
        if delete_message:
            try:
                await update.message.delete()
                logger.info(f"Mensaje con PIN borrado (user {user_id})")
            except Exception as e:
                logger.warning(f"No se pudo borrar mensaje: {e}")
        return True

    # 3. No autorizado
    if pin:
        # Intentó con PIN pero era incorrecto
        try:
            await update.message.delete()
        except Exception:
            pass
        await context.bot.send_message(chat_id, "⛔ PIN incorrecto.")
        logger.warning(f"Usuario {user_id} usó PIN incorrecto")
    else:
        # No es supervisor por ID y no usó PIN
        await context.bot.send_message(
            chat_id,
            "⛔ Este comando requiere autorización.\n"
            "Usá el formato: `/comando:PIN argumentos`",
            parse_mode='Markdown'
        )
        logger.warning(f"Usuario {user_id} intentó comando de supervisor sin PIN")

    return False


def supervisor_required(func):
    """Decorador para comandos que requieren ser supervisor."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await validate_supervisor(update, context):
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

━━━━━━━━━━━━━━━━━━━━
👤 *COMANDOS DE SUPERVISOR* (requieren PIN)

`/restriccion:PIN OS TIPO "MSG" [PERMITIDOS]`
  Agregar restricción

`/quitar_restriccion:PIN OS [TIPO]`
  Quitar restricción

`/restricciones:PIN [OS]`
  Ver restricciones activas

_El mensaje con PIN se borra automáticamente._
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
        /restriccion:PIN ENSALUD falta_pago "Solo guardia" guardia
        /restriccion ENSALUD falta_pago "Solo guardia" guardia  (si es supervisor por ID)

    Args:
        obra_social (ENSALUD, ASI, IOSFA)
        tipo_restriccion (falta_pago, convenio_suspendido, cupo_agotado)
        mensaje (entre comillas)
        tipos_permitidos (opcional, ej: "guardia")
    """
    chat_id = update.effective_chat.id

    # Usar texto guardado (el mensaje original puede haber sido borrado)
    full_text = context.user_data.get('original_text', '')
    args = context.user_data.get('original_args', [])

    if len(args) < 3:
        await context.bot.send_message(
            chat_id,
            "❌ Uso: `/restriccion:PIN OS TIPO \"MENSAJE\" [PERMITIDOS]`\n\n"
            "Ejemplos:\n"
            "• `/restriccion:1234 ENSALUD falta_pago \"Solo guardia\" guardia`\n"
            "• `/restriccion:1234 ASI convenio_suspendido \"Suspendido\"`\n\n"
            "Tipos: falta_pago, convenio_suspendido, cupo_agotado",
            parse_mode='Markdown'
        )
        return

    # Parsear argumentos
    obra_social = args[0].upper()
    tipo_restriccion = args[1].lower()

    # Extraer texto entre comillas
    match = re.search(r'"([^"]+)"', full_text)
    if not match:
        await context.bot.send_message(
            chat_id,
            "❌ El mensaje debe ir entre comillas.\n"
            "Ejemplo: `/restriccion:1234 ENSALUD falta_pago \"Solo guardia\"`",
            parse_mode='Markdown'
        )
        return

    mensaje = match.group(1)

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

    await context.bot.send_message(chat_id, response)


@supervisor_required
async def quitar_restriccion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Quitar restricción de una obra social.

    Uso:
        /quitar_restriccion:PIN ENSALUD falta_pago  (quita tipo específico)
        /quitar_restriccion:PIN ENSALUD             (quita todas)
    """
    chat_id = update.effective_chat.id
    args = context.user_data.get('original_args', [])

    if len(args) < 1:
        await context.bot.send_message(
            chat_id,
            "❌ Uso: `/quitar_restriccion:PIN OS [TIPO]`\n\n"
            "Ejemplos:\n"
            "• `/quitar_restriccion:1234 ENSALUD falta_pago`\n"
            "• `/quitar_restriccion:1234 ENSALUD` (quita todas)",
            parse_mode='Markdown'
        )
        return

    obra_social = args[0].upper()
    tipo_restriccion = args[1].lower() if len(args) > 1 else None

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

    await context.bot.send_message(chat_id, response)


@supervisor_required
async def listar_restricciones_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Listar restricciones activas.

    Uso:
        /restricciones:PIN          (todas)
        /restricciones:PIN ENSALUD  (de una OS específica)
    """
    chat_id = update.effective_chat.id
    args = context.user_data.get('original_args', [])

    obra_social = args[0].upper() if args else None

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

    await context.bot.send_message(chat_id, response, parse_mode='Markdown')


async def mi_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el ID del usuario (útil para obtener tu ID de Telegram)."""
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

    # Agregar handlers - Comandos de supervisor (soportan formato /cmd:PIN)
    application.add_handler(MessageHandler(
        filters.Regex(r'^/restriccion(:\d+)?(\s|$)'),
        restriccion_command
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r'^/quitar_restriccion(:\d+)?(\s|$)'),
        quitar_restriccion_command
    ))
    application.add_handler(MessageHandler(
        filters.Regex(r'^/restricciones(:\d+)?(\s|$)'),
        listar_restricciones_command
    ))

    # Agregar handler de mensajes (debe ir al final)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar bot
    logger.info("Bot iniciando... (Ctrl+C para detener)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
