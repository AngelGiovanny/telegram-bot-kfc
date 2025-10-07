import logging
import os
from datetime import datetime

# Corrección en la importación
from config.settings import Config


class BotLogger:
    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        """Configura el sistema de logging"""
        # Crear directorio de logs si no existe
        if not os.path.exists(Config.LOG_DIR):
            os.makedirs(Config.LOG_DIR)

        # Estructura por mes y día
        now = datetime.now()
        month_dir = now.strftime("%Y-%m")
        day_file = now.strftime("%Y-%m-%d") + ".log"

        log_path = os.path.join(Config.LOG_DIR, month_dir, day_file)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger('KFCBot')

    def log_connection(self, user_id, local, fecha, connection_id, status="success"):
        """Log de conexiones a la base de datos"""
        log_message = f"CONNECTION - User: {user_id}, Local: {local}, Fecha: {fecha}, ConnectionID: {connection_id}, Status: {status}"
        self.logger.info(log_message)

    def log_query(self, user_id, local, fecha, referencia, autorizacion):
        """Log de consultas realizadas"""
        log_message = f"QUERY - User: {user_id}, Local: {local}, Fecha: {fecha}, Referencia: {referencia}, Autorizacion: {autorizacion}"
        self.logger.info(log_message)


# Instancia global del logger
logger = BotLogger()