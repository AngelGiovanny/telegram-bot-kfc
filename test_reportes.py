import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(__file__))


def test_imports():
    print("🧪 Probando importaciones para reportes...")

    try:
        from bot.handlers import BotHandlers
        print("✅ BotHandlers importado correctamente")

        from utils.report_generator import report_generator
        print("✅ ReportGenerator importado correctamente")

        from utils.logger import logger
        print("✅ Logger importado correctamente")

        # Test método de reportes
        bot = BotHandlers()
        print("✅ Instancia de BotHandlers creada")

        print("\n🎉 ¡Todas las importaciones funcionan!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_imports()