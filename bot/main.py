from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters

# Importaciones absolutas
from config.settings import Config
from bot.handlers import BotHandlers, LOCAL, FECHA, REFERENCIA, AUTORIZACION
from utils.logger import logger


class KFCBot:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.application = Application.builder().token(self.token).build()
        self.handlers = BotHandlers()

        self.setup_handlers()

    def setup_handlers(self):
        """Configura los manejadores de comandos"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.handlers.start)],
            states={
                LOCAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_local)],
                FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_fecha)],
                REFERENCIA: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_referencia),
                    CommandHandler('skip', self.handlers.skip_referencia)
                ],
                AUTORIZACION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.get_autorizacion),
                    CommandHandler('skip', self.handlers.skip_autorizacion)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.handlers.cancel)]
        )

        self.application.add_handler(conv_handler)

        # Comando de ayuda
        self.application.add_handler(CommandHandler('help', self.handlers.help_command))
        self.application.add_handler(CommandHandler('cancel', self.handlers.cancel))

    def run(self):
        """Inicia el bot"""
        logger.logger.info("Iniciando bot de KFC...")
        print("🤖 Bot de KFC iniciado...")
        print("✅ Botones de navegación activados: ↩️ Volver atrás, ❌ Finalizar consulta")

        self.application.run_polling()


def main():
    bot = KFCBot()
    bot.run()


if __name__ == '__main__':
    main()