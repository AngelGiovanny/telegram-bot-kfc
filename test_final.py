import sys
import os

print("🧪 Probando importaciones...")

try:
    from config.settings import Config

    print("✅ config.settings importado correctamente")
    print(f"   Token: {'✅ Configurado' if Config.TELEGRAM_TOKEN else '❌ Faltante'}")
    print(f"   DB Server: {Config.DB_SERVER}")

    from utils.logger import logger

    print("✅ utils.logger importado correctamente")

    from bot.database import DatabaseManager

    print("✅ bot.database importado correctamente")

    from bot.handlers import BotHandlers

    print("✅ bot.handlers importado correctamente")

    print("\n🎉 ¡Todas las importaciones funcionan correctamente!")

except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("\n📁 Estructura de carpetas:")
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py'):
                print(f'{subindent}{file}')