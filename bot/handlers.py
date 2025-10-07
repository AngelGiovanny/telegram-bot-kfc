from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime, timedelta
import re

# Importaciones absolutas
from bot.database import DatabaseManager
from utils.logger import logger

# Estados de la conversación
LOCAL, FECHA, REFERENCIA, AUTORIZACION = range(4)


class BotHandlers:
    def __init__(self):
        self.db = DatabaseManager()

    def _create_base_keyboard(self, include_back=True, include_cancel=True):
        """Crea teclado base con botones de navegación"""
        keyboard = []
        if include_back:
            keyboard.append([KeyboardButton("↩️ Volver atrás")])
        if include_cancel:
            keyboard.append([KeyboardButton("❌ Finalizar consulta")])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    def _create_fecha_keyboard(self):
        """Crea teclado para selección de fecha"""
        keyboard = [
            [KeyboardButton("Hoy"), KeyboardButton("Ayer")],
            [KeyboardButton("Hace 2 días"), KeyboardButton("Hace 3 días")],
            [KeyboardButton("📅 Ingresar fecha manual")],
            [KeyboardButton("↩️ Volver atrás")],
            [KeyboardButton("❌ Finalizar consulta")]
        ]
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    def _create_optional_keyboard(self):
        """Crea teclado para campos opcionales"""
        keyboard = [
            [KeyboardButton("No tengo")],
            [KeyboardButton("↩️ Volver atrás")],
            [KeyboardButton("❌ Finalizar consulta")]
        ]
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mensaje de bienvenida"""
        # Limpiar datos previos
        context.user_data.clear()

        welcome_message = """
🤖 **Bienvenido al Bot de Consultas KFC** 🍗

Te ayudaré a consultar el estado de las transacciones de forma sencilla.

Por favor, ingresa el número de local (ejemplo: kfc004):
        """

        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=self._create_base_keyboard(include_back=False)
        )
        return LOCAL

    async def get_local(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe el número de local"""
        user_input = update.message.text.strip()

        # Manejar botones de navegación
        if user_input == "❌ Finalizar consulta":
            return await self.cancel(update, context)

        local = user_input.upper().strip()

        # Validar formato del local
        if not re.match(r'^KFC\d{3}$', local):
            await update.message.reply_text(
                "❌ Formato incorrecto. Por favor ingresa el local en el formato: kfc004\n\n"
                "Ejemplos válidos: kfc001, kfc023, kfc156",
                reply_markup=self._create_base_keyboard(include_back=False)
            )
            return LOCAL

        context.user_data['local'] = local

        await update.message.reply_text(
            f"🏪 **Local registrado:** {local}\n\n"
            "📅 Ahora selecciona la fecha de la transacción:",
            parse_mode='Markdown',
            reply_markup=self._create_fecha_keyboard()
        )
        return FECHA

    async def get_fecha(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe la fecha de la transacción"""
        fecha_input = update.message.text

        # Manejar botones de navegación
        if fecha_input == "↩️ Volver atrás":
            await update.message.reply_text(
                "↩️ Volviendo al ingreso de local...\n\n"
                "Por favor, ingresa el número de local (ejemplo: kfc004):",
                reply_markup=self._create_base_keyboard(include_back=False)
            )
            return LOCAL

        if fecha_input == "❌ Finalizar consulta":
            return await self.cancel(update, context)

        # Mapear opciones rápidas
        fecha_map = {
            "Hoy": datetime.now(),
            "Ayer": datetime.now() - timedelta(days=1),
            "Hace 2 días": datetime.now() - timedelta(days=2),
            "Hace 3 días": datetime.now() - timedelta(days=3)
        }

        if fecha_input in fecha_map:
            fecha = fecha_map[fecha_input]
            fecha_str = fecha.strftime("%Y%m%d")
            fecha_display = fecha.strftime("%d/%m/%Y")
            context.user_data['fecha'] = fecha_str
            context.user_data['fecha_display'] = fecha_display
        elif fecha_input == "📅 Ingresar fecha manual":
            await update.message.reply_text(
                "📅 Por favor ingresa la fecha en formato **DD/MM/AAAA**\n"
                "Ejemplo: 27/08/2024",
                parse_mode='Markdown',
                reply_markup=self._create_base_keyboard()
            )
            return FECHA
        else:
            # Intentar parsear fecha manual
            try:
                fecha_dt = datetime.strptime(fecha_input, "%d/%m/%Y")
                fecha_str = fecha_dt.strftime("%Y%m%d")
                fecha_display = fecha_dt.strftime("%d/%m/%Y")
                context.user_data['fecha'] = fecha_str
                context.user_data['fecha_display'] = fecha_display
            except ValueError:
                await update.message.reply_text(
                    "❌ Formato de fecha incorrecto. Usa **DD/MM/AAAA** (ejemplo: 27/08/2024)\n\n"
                    "Por favor ingresa la fecha nuevamente:",
                    parse_mode='Markdown',
                    reply_markup=self._create_fecha_keyboard()
                )
                return FECHA

        await update.message.reply_text(
            f"📅 **Fecha seleccionada:** {context.user_data['fecha_display']}\n\n"
            "🔢 ¿Tienes un **número de referencia**? (Opcional)\n\n"
            "Si no tienes, presiona 'No tengo'",
            parse_mode='Markdown',
            reply_markup=self._create_optional_keyboard()
        )
        return REFERENCIA

    async def get_referencia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe el número de referencia (opcional)"""
        user_input = update.message.text.strip()

        # Manejar botones de navegación
        if user_input == "↩️ Volver atrás":
            await update.message.reply_text(
                f"↩️ Volviendo a selección de fecha...\n\n"
                f"🏪 Local actual: {context.user_data['local']}\n"
                "📅 Selecciona la fecha de la transacción:",
                reply_markup=self._create_fecha_keyboard()
            )
            return FECHA

        if user_input == "❌ Finalizar consulta":
            return await self.cancel(update, context)

        if user_input == "No tengo":
            referencia = None
            referencia_msg = "No especificada"
        else:
            referencia = user_input
            referencia_msg = referencia

        context.user_data['referencia'] = referencia

        await update.message.reply_text(
            f"🔢 **Referencia:** {referencia_msg}\n\n"
            "✅ ¿Tienes un **número de autorización**? (Opcional)\n\n"
            "Si no tienes, presiona 'No tengo'",
            parse_mode='Markdown',
            reply_markup=self._create_optional_keyboard()
        )
        return AUTORIZACION

    async def get_autorizacion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe el número de autorización (opcional)"""
        user_input = update.message.text.strip()

        # Manejar botones de navegación
        if user_input == "↩️ Volver atrás":
            await update.message.reply_text(
                f"↩️ Volviendo a ingreso de referencia...\n\n"
                f"🏪 Local: {context.user_data['local']}\n"
                f"📅 Fecha: {context.user_data['fecha_display']}\n\n"
                "🔢 ¿Tienes un número de referencia? (Opcional)\n\n"
                "Si no tienes, presiona 'No tengo'",
                reply_markup=self._create_optional_keyboard()
            )
            return REFERENCIA

        if user_input == "❌ Finalizar consulta":
            return await self.cancel(update, context)

        if user_input == "No tengo":
            autorizacion = None
            autorizacion_msg = "No especificada"
        else:
            autorizacion = user_input
            autorizacion_msg = autorizacion

        context.user_data['autorizacion'] = autorizacion

        # Mostrar resumen antes de ejecutar
        resumen = f"""
📋 **Resumen de tu consulta:**

🏪 **Local:** {context.user_data['local']}
📅 **Fecha:** {context.user_data['fecha_display']}
🔢 **Referencia:** {context.user_data.get('referencia', 'No especificada')}
✅ **Autorización:** {autorizacion_msg}

🔍 **Procesando consulta...**
        """

        await update.message.reply_text(
            resumen,
            parse_mode='Markdown',
            reply_markup=self._create_base_keyboard(include_back=True, include_cancel=False)
        )

        # Realizar consulta
        await self.execute_query(update, context)
        return ConversationHandler.END

    async def skip_referencia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Salta el ingreso de referencia (comando /skip)"""
        context.user_data['referencia'] = None

        await update.message.reply_text(
            "🔢 Referencia: No especificada\n\n"
            "✅ ¿Tienes un **número de autorización**? (Opcional)\n\n"
            "Si no tienes, presiona 'No tengo'",
            parse_mode='Markdown',
            reply_markup=self._create_optional_keyboard()
        )
        return AUTORIZACION

    async def skip_autorizacion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Salta el ingreso de autorización (comando /skip)"""
        context.user_data['autorizacion'] = None

        # Mostrar resumen antes de ejecutar
        resumen = f"""
📋 **Resumen de tu consulta:**

🏪 **Local:** {context.user_data['local']}
📅 **Fecha:** {context.user_data['fecha_display']}
🔢 **Referencia:** {context.user_data.get('referencia', 'No especificada')}
✅ **Autorización:** No especificada

🔍 **Procesando consulta...**
        """

        await update.message.reply_text(
            resumen,
            parse_mode='Markdown',
            reply_markup=self._create_base_keyboard(include_back=True, include_cancel=False)
        )

        await self.execute_query(update, context)
        return ConversationHandler.END

    async def execute_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ejecuta la consulta en la base de datos"""
        user_data = context.user_data

        try:
            results, connection_id = self.db.execute_query(
                merchant_id=user_data['local'],
                fecha_transaccion=user_data['fecha'],
                numero_referencia=user_data.get('referencia'),
                numero_autorizacion=user_data.get('autorizacion')
            )

            formatted_results = self.db.format_results(results)

            # Agregar información de la consulta
            response = f"""
📊 **Resultados de la Consulta**

🔗 **ID de Conexión:** `{connection_id}`
🏪 **Local:** {user_data['local']}
📅 **Fecha:** {user_data['fecha_display']}
🔢 **Referencia:** {user_data.get('referencia', 'No especificada')}
✅ **Autorización:** {user_data.get('autorizacion', 'No especificada')}

{formatted_results}

🔄 ¿Quieres hacer otra consulta? Usa /start
            """

            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=self._create_base_keyboard(include_back=False, include_cancel=False)
            )

        except Exception as e:
            error_message = f"""
❌ **Error en la consulta**

No se pudo completar la consulta. Error: {str(e)}

🔧 **Por favor verifica:**
- Que el local exista
- Que la fecha sea correcta  
- Que tengas conexión a la red

🔄 **Intenta nuevamente con /start**
            """
            await update.message.reply_text(
                error_message,
                parse_mode='Markdown',
                reply_markup=self._create_base_keyboard(include_back=False, include_cancel=False)
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancela la conversación"""
        # Limpiar datos
        context.user_data.clear()

        cancel_message = """
❌ **Consulta finalizada**

Todos los datos han sido descartados.

🔄 Si quieres iniciar una nueva consulta, usa /start

👋 ¡Hasta pronto!
        """

        await update.message.reply_text(
            cancel_message,
            parse_mode='Markdown',
            reply_markup=self._create_base_keyboard(include_back=False, include_cancel=False)
        )
        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra la ayuda mejorada"""
        help_text = """
🤖 **Bot de Consultas KFC - Comandos Disponibles**

/start - Iniciar una nueva consulta
/help - Mostrar esta ayuda
/cancel - Cancelar la consulta actual

🔄 **Flujo de consulta:**
1. 🏪 Ingresa el local (ej: kfc004)
2. 📅 Selecciona la fecha
3. 🔢 Ingresa referencia (opcional)
4. ✅ Ingresa autorización (opcional)

📋 **Características:**
- ↩️ Puedes volver atrás en cualquier momento
- ❌ Puedes finalizar la consulta cuando quieras
- 📊 Resultados detallados con ID de transacción
- 📝 Logs automáticos de todas las consultas

🔧 **Soporte:** Si tienes problemas, contacta al administrador.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')