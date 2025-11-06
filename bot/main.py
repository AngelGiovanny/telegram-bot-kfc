from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters

# Importaciones absolutas
from config.settings import Config
from bot.handlers import BotHandlers, LOCAL, FECHA, AUTORIZACION, REFERENCIA
from utils.logger import logger


class KFCBot:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.application = Application.builder().token(self.token).build()
        self.handlers = BotHandlers()

        self.setup_handlers()

    def setup_handlers(self):
        """Configura los manejadores de comandos"""
        print("🔧 Configurando handlers...")

        # Conversation handler para consultas principales (FLUJO CORREGIDO)
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.handlers.start)],
            states={
                LOCAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_local)],
                FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_fecha)],
                AUTORIZACION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_autorizacion)],
                REFERENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_referencia)],
            },
            fallbacks=[CommandHandler('cancel', self.handlers.cancel)]
        )

        self.application.add_handler(conv_handler)
        print("✅ Handler de consultas principal configurado")

        # Conversation handler para reportes
        report_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('reportes', self.handlers.reportes_command)],
            states={
                "WAITING_REPORT_TYPE": [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_report_type)
                ],
                "WAITING_REPORT_LOCAL": [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_report_local)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.handlers.cancel)]
        )

        self.application.add_handler(report_conv_handler)
        print("✅ Handler de reportes configurado")

        # Comandos simples
        self.application.add_handler(CommandHandler('help', self.handlers.help_command))
        self.application.add_handler(CommandHandler('cancel', self.handlers.cancel))
        print("✅ Comandos simples configurados")

        # Debug: listar todos los handlers
        print(f"📋 Total de handlers registrados: {len(self.application.handlers)}")

    def run(self):
        """Inicia el bot"""
        logger.logger.info("Iniciando bot de KFC...")
        print("🤖 Bot de KFC iniciado...")
        print("✅ Comandos disponibles: /start, /reportes, /help, /cancel")
        print("🔄 Nuevo flujo: Local → Fecha → Autorización → (Referencia si es necesario)")

        self.application.run_polling()


def main():
    bot = KFCBot()
    bot.run()


if __name__ == '__main__':
    main()