import logging
import os
import json
from datetime import datetime
import csv

# Importaciones absolutas
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

        # Guardar también en CSV para reportes
        self._save_to_csv(user_id, local, fecha, connection_id, status)

    def log_query(self, user_id, local, fecha, referencia, autorizacion):
        """Log de consultas realizadas"""
        log_message = f"QUERY - User: {user_id}, Local: {local}, Fecha: {fecha}, Referencia: {referencia}, Autorizacion: {autorizacion}"
        self.logger.info(log_message)

    def _save_to_csv(self, user_id, local, fecha_consulta, connection_id, status):
        """Guarda los datos en CSV para reportes"""
        try:
            # Crear directorio de reportes si no existe
            report_dir = os.path.join(Config.LOG_DIR, 'reportes')
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)

            # Archivo CSV mensual
            now = datetime.now()
            csv_file = os.path.join(report_dir, f"conexiones_{now.strftime('%Y-%m')}.csv")

            # Verificar si el archivo existe para agregar headers
            file_exists = os.path.isfile(csv_file)

            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Escribir headers si el archivo no existe
                if not file_exists:
                    writer.writerow([
                        'ID_Conexion',
                        'Local',
                        'Fecha_Consulta',
                        'Fecha_Solicitud',
                        'Hora_Solicitud',
                        'Usuario',
                        'Estado'
                    ])

                # Escribir datos
                fecha_solicitud = datetime.now().strftime('%Y-%m-%d')
                hora_solicitud = datetime.now().strftime('%H:%M:%S')

                writer.writerow([
                    connection_id,
                    local,
                    fecha_consulta,
                    fecha_solicitud,
                    hora_solicitud,
                    user_id,
                    status
                ])

        except Exception as e:
            self.logger.error(f"Error guardando en CSV: {e}")

    def get_connection_data(self, local_filter=None, fecha_inicio=None, fecha_fin=None):
        """Obtiene datos de conexiones para reportes"""
        try:
            report_dir = os.path.join(Config.LOG_DIR, 'reportes')
            if not os.path.exists(report_dir):
                return []

            # Buscar todos los archivos CSV de reportes
            csv_files = [f for f in os.listdir(report_dir) if f.startswith('conexiones_') and f.endswith('.csv')]

            all_data = []
            for csv_file in csv_files:
                file_path = os.path.join(report_dir, csv_file)

                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)

                    for row in reader:
                        # Aplicar filtros
                        if local_filter and row['Local'] != local_filter:
                            continue

                        if fecha_inicio and row['Fecha_Solicitud'] < fecha_inicio:
                            continue

                        if fecha_fin and row['Fecha_Solicitud'] > fecha_fin:
                            continue

                        all_data.append(row)

            return all_data

        except Exception as e:
            self.logger.error(f"Error leyendo datos de conexiones: {e}")
            return []


# Instancia global del logger
logger = BotLogger()