import os
import pandas as pd
from datetime import datetime
from utils.logger import logger


class ReportGenerator:
    def __init__(self):
        self.reports_dir = 'reports'
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_connections_report(self, local_filter=None, fecha_inicio=None, fecha_fin=None):
        """Genera reporte de conexiones en Excel"""
        try:
            # Obtener datos de conexiones
            connection_data = logger.get_connection_data(local_filter, fecha_inicio, fecha_fin)

            if not connection_data:
                return None, "No se encontraron datos de conexiones para los filtros aplicados"

            # Convertir a DataFrame de pandas
            df = pd.DataFrame(connection_data)

            # Ordenar por fecha de solicitud (más reciente primero)
            df['Fecha_Solicitud'] = pd.to_datetime(df['Fecha_Solicitud'])
            df = df.sort_values('Fecha_Solicitud', ascending=False)

            # Crear nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_suffix = f"_{local_filter}" if local_filter else "_todos"
            filename = f"reporte_conexiones{local_suffix}_{timestamp}.xlsx"
            filepath = os.path.join(self.reports_dir, filename)

            # Crear Excel con múltiples hojas
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Hoja de datos completos
                df.to_excel(writer, sheet_name='Conexiones', index=False)

                # Hoja de resumen por local
                if not local_filter:
                    summary = df.groupby('Local').agg({
                        'ID_Conexion': 'count',
                        'Fecha_Solicitud': ['min', 'max']
                    }).round(2)

                    summary.columns = ['Total_Conexiones', 'Primera_Conexion', 'Ultima_Conexion']
                    summary = summary.sort_values('Total_Conexiones', ascending=False)
                    summary.to_excel(writer, sheet_name='Resumen_Por_Local')

                # Hoja de resumen por fecha
                daily_summary = df.groupby('Fecha_Solicitud').agg({
                    'ID_Conexion': 'count'
                }).rename(columns={'ID_Conexion': 'Conexiones_Dia'})

                daily_summary = daily_summary.sort_index(ascending=False)
                daily_summary.to_excel(writer, sheet_name='Resumen_Por_Fecha')

            return filepath, f"Reporte generado exitosamente. {len(connection_data)} registros encontrados."

        except Exception as e:
            error_msg = f"Error generando reporte: {str(e)}"
            logger.logger.error(error_msg)
            return None, error_msg

    def get_available_locals(self):
        """Obtiene lista de locales disponibles en los reportes"""
        try:
            connection_data = logger.get_connection_data()
            locales = set(row['Local'] for row in connection_data)
            return sorted(locales)
        except Exception as e:
            logger.logger.error(f"Error obteniendo locales: {e}")
            return []


# Instancia global del report generator
report_generator = ReportGenerator()