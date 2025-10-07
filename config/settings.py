import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8329685664:AAG0v7R4XaT7S8IIyOXWfY5_zGSTzPjzsdA')

    # Database configuration
    DB_SERVER = os.getenv('DATABASE_SERVER', 'SRV-SW-V3\\SWITCHT')
    DB_NAME = os.getenv('DATABASE_NAME', 'BD_ENGINE_KFC')  # Agrega el nombre de tu base de datos aquí
    DB_USER = os.getenv('DATABASE_USER', 'ConsultaSD')
    DB_PASSWORD = os.getenv('DATABASE_PASSWORD', 'soporte*88')

    # Logging configuration
    LOG_DIR = 'logs'


# Instancia global de configuración
config = Config()