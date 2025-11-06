from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime, timedelta
import re
import os

# Importaciones absolutas
from bot.database import DatabaseManager
from utils.logger import logger

# Estados de la conversación
LOCAL, FECHA, AUTORIZACION, REFERENCIA = range(4)


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

    def _create_autorizacion_keyboard(self):
        """Crea teclado específico para autorización"""
        keyboard = [
            [KeyboardButton("✅ Sí, tengo autorización"), KeyboardButton("❌ No tengo autorización")],
            [KeyboardButton("↩️ Volver atrás"), KeyboardButton("❌ Finalizar consulta")]
        ]
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    def _create_referencia_keyboard(self):
        """Crea teclado para referencia"""
        keyboard = [
            [KeyboardButton("No tengo referencia")],
            [KeyboardButton("↩️ Volver atrás")],
            [KeyboardButton("❌ Finalizar consulta")]
        ]
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mensaje de bienvenida - Siempre empieza con local"""
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
        """PRIMERO: Siempre pedir local"""
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
        """SEGUNDO: Siempre pedir fecha"""
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

        # TERCERO: Preguntar por autorización
        await update.message.reply_text(
            f"📅 **Fecha seleccionada:** {context.user_data['fecha_display']}\n\n"
            "✅ ¿Tienes un **número de autorización**?",
            parse_mode='Markdown',
            reply_markup=self._create_autorizacion_keyboard()
        )
        return AUTORIZACION

    async def get_autorizacion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """TERCERO: Preguntar por autorización"""
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

        if user_input == "✅ Sí, tengo autorización":
            await update.message.reply_text(
                "🔢 **Por favor ingresa el número de autorización:**",
                parse_mode='Markdown',
                reply_markup=self._create_base_keyboard(include_back=True)
            )
            return AUTORIZACION

        if user_input == "❌ No tengo autorización":
            context.user_data['autorizacion'] = None
            # SIN AUTORIZACIÓN: Pedir referencia
            await update.message.reply_text(
                f"🔍 **Consulta sin autorización**\n\n"
                f"🏪 Local: {context.user_data['local']}\n"
                f"📅 Fecha: {context.user_data['fecha_display']}\n\n"
                "🔢 ¿Tienes un **número de referencia**?\n\n"
                "Si no tienes, presiona 'No tengo referencia'",
                parse_mode='Markdown',
                reply_markup=self._create_referencia_keyboard()
            )
            return REFERENCIA

        # Si ingresa un número (autorización válida)
        if user_input.isdigit():
            context.user_data['autorizacion'] = user_input
            # CON AUTORIZACIÓN: Ejecutar consulta directa
            await update.message.reply_text(
                f"✅ **Autorización registrada:** {user_input}\n\n"
                "🔍 **Consultando con autorización...**",
                parse_mode='Markdown'
            )
            return await self.execute_query(update, context)
        else:
            await update.message.reply_text(
                "❌ Por favor ingresa un número de autorización válido o selecciona una opción:",
                reply_markup=self._create_autorizacion_keyboard()
            )
            return AUTORIZACION

    async def get_referencia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """CUARTO: Pedir referencia solo si NO hay autorización"""
        user_input = update.message.text.strip()

        # Manejar botones de navegación
        if user_input == "↩️ Volver atrás":
            await update.message.reply_text(
                f"↩️ Volviendo a autorización...\n\n"
                f"🏪 Local: {context.user_data['local']}\n"
                f"📅 Fecha: {context.user_data['fecha_display']}\n\n"
                "✅ ¿Tienes un **número de autorización**?",
                parse_mode='Markdown',
                reply_markup=self._create_autorizacion_keyboard()
            )
            return AUTORIZACION

        if user_input == "❌ Finalizar consulta":
            return await self.cancel(update, context)

        if user_input == "No tengo referencia":
            referencia = None
            referencia_msg = "No especificada"
        else:
            referencia = user_input
            referencia_msg = referencia

        context.user_data['referencia'] = referencia

        # Mostrar resumen y ejecutar consulta CON REFERENCIA (sin autorización)
        resumen = f"""
📋 **Resumen de tu consulta:**

🏪 **Local:** {context.user_data['local']}
📅 **Fecha:** {context.user_data['fecha_display']}
🔢 **Referencia:** {referencia_msg}
✅ **Autorización:** No especificada

🔍 **Procesando consulta...**
        """

        await update.message.reply_text(
            resumen,
            parse_mode='Markdown',
            reply_markup=self._create_base_keyboard(include_back=True, include_cancel=False)
        )

        # Realizar consulta con referencia (sin autorización)
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

            # Respuesta optimizada - Sin ID de conexión visible
            response = f"""
{formatted_results}

🔄 **¿Nueva consulta?** Usa /start
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
/reportes - Generar reportes de conexiones
/help - Mostrar esta ayuda
/cancel - Cancelar la consulta actual

🔄 **Flujo de consulta:**
1. 🏪 Local (siempre)
2. 📅 Fecha (siempre) 
3. ✅ Autorización (si tienes)
4. 🔢 Referencia (solo si no tienes autorización)

📊 **Sistema de Reportes:**
- Genera reportes CSV con todas las conexiones
- Estadísticas por local y fecha

🔧 **Soporte:** Si tienes problemas, contacta al administrador.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    # ... (Los métodos de reportes se mantienen igual)
    async def reportes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /reportes"""
        print(f"🔍 Comando /reportes recibido de usuario: {update.effective_user.id}")

        from utils.report_generator import report_generator

        # Crear teclado para selección de tipo de reporte
        keyboard = [
            [KeyboardButton("📊 Reporte CSV"), KeyboardButton("📈 Reporte Detallado")],
            [KeyboardButton("❌ Cancelar")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        await update.message.reply_text(
            "📊 **Sistema de Reportes**\n\n"
            "Selecciona el tipo de reporte que deseas generar:\n\n"
            "• 📊 **Reporte CSV**: Archivo CSV con todos los datos de conexiones\n"
            "• 📈 **Reporte Detallado**: Archivo de texto con estadísticas y análisis\n",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

        context.user_data['reporte_pendiente'] = True
        print("✅ Estado cambiado a: WAITING_REPORT_TYPE")
        return "WAITING_REPORT_TYPE"

    async def handle_report_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja la selección de tipo de reporte"""
        print(f"🔍 Tipo de reporte seleccionado: {update.message.text}")

        from utils.report_generator import report_generator

        user_input = update.message.text

        if user_input == "❌ Cancelar":
            await update.message.reply_text(
                "❌ Generación de reporte cancelada.",
                reply_markup=self._create_base_keyboard(include_back=False, include_cancel=False)
            )
            return ConversationHandler.END

        # Guardar tipo de reporte
        context.user_data['tipo_reporte'] = user_input

        # Obtener locales disponibles
        locales = report_generator.get_available_locals()

        if not locales:
            await update.message.reply_text(
                "📊 **Sistema de Reportes**\n\n"
                "❌ No hay datos de conexiones registrados todavía.\n\n"
                "Los reportes se generan automáticamente cuando los usuarios "
                "realizan consultas con /start",
                parse_mode='Markdown',
                reply_markup=self._create_base_keyboard(include_back=False, include_cancel=False)
            )
            return ConversationHandler.END

        # Crear teclado para selección de local
        keyboard = []
        row = []
        for i, local in enumerate(locales):
            row.append(KeyboardButton(local))
            if len(row) == 2 or i == len(locales) - 1:
                keyboard.append(row)
                row = []

        keyboard.append([KeyboardButton("🏪 Todos los locales")])
        keyboard.append([KeyboardButton("↩️ Volver"), KeyboardButton("❌ Cancelar")])

        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        await update.message.reply_text(
            f"📊 **{user_input}**\n\n"
            "Selecciona el local para el reporte:\n\n"
            f"📍 **Locales disponibles:** {len(locales)}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

        return "WAITING_REPORT_LOCAL"

    async def handle_report_local(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja la selección de local para reporte"""
        print(f"🔍 Local seleccionado para reporte: {update.message.text}")

        from utils.report_generator import report_generator

        user_input = update.message.text

        if user_input == "❌ Cancelar":
            await update.message.reply_text(
                "❌ Generación de reporte cancelada.",
                reply_markup=self._create_base_keyboard(include_back=False, include_cancel=False)
            )
            return ConversationHandler.END

        if user_input == "↩️ Volver":
            await self.reportes_command(update, context)
            return "WAITING_REPORT_TYPE"

        # Determinar el filtro de local
        local_filter = None if user_input == "🏪 Todos los locales" else user_input
        tipo_reporte = context.user_data.get('tipo_reporte', '📊 Reporte CSV')

        await update.message.reply_text(
            f"⏳ **Generando {tipo_reporte}...**\n\n"
            f"🔍 **Local:** {user_input}\n"
            "Por favor espera mientras se procesan los datos...",
            parse_mode='Markdown'
        )

        # Generar reporte según el tipo
        if tipo_reporte == "📊 Reporte CSV":
            filepath, message = report_generator.generate_connections_report(local_filter=local_filter)
            file_type = "document"
        else:  # Reporte Detallado
            filepath, message = report_generator.generate_detailed_report(local_filter=local_filter)
            file_type = "document"

        if filepath:
            # Enviar archivo
            with open(filepath, 'rb') as file:
                if file_type == "document":
                    await update.message.reply_document(
                        document=file,
                        filename=os.path.basename(filepath),
                        caption=message,
                        parse_mode='Markdown'
                    )

            # Limpiar archivo temporal después de enviar
            try:
                os.remove(filepath)
            except:
                pass

            # Mensaje adicional
            await update.message.reply_text(
                "✅ **Reporte completado**\n\n"
                "¿Necesitas otro reporte? Usa /reportes nuevamente.",
                parse_mode='Markdown',
                reply_markup=self._create_base_keyboard(include_back=False, include_cancel=False)
            )
        else:
            await update.message.reply_text(
                f"❌ **Error al generar reporte**\n\n{message}",
                parse_mode='Markdown'
            )

        # Limpiar datos temporales
        context.user_data.pop('reporte_pendiente', None)
        context.user_data.pop('tipo_reporte', None)

        return ConversationHandler.END