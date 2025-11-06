import os
import csv
from datetime import datetime
from utils.logger import logger


class ReportGenerator:
    def __init__(self):
        self.reports_dir = 'reports'
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_connections_report(self, local_filter=None, fecha_inicio=None, fecha_fin=None):
        """Genera reporte de conexiones en CSV"""
        try:
            # Obtener datos de conexiones
            connection_data = logger.get_connection_data(local_filter, fecha_inicio, fecha_fin)

            if not connection_data:
                return None, "No se encontraron datos de conexiones para los filtros aplicados"

            # Crear nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_suffix = f"_{local_filter}" if local_filter else "_todos"
            filename = f"reporte_conexiones{local_suffix}_{timestamp}.csv"
            filepath = os.path.join(self.reports_dir, filename)

            # Escribir archivo CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if connection_data:
                    # Usar las keys del primer registro como headers
                    fieldnames = connection_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)

                    writer.writeheader()
                    for row in connection_data:
                        writer.writerow(row)

            # Generar resumen
            total_registros = len(connection_data)
            locales = set(row['Local'] for row in connection_data)

            resumen = (
                f"📊 **Reporte Generado Exitosamente**\n\n"
                f"📁 **Archivo:** {filename}\n"
                f"📈 **Total de registros:** {total_registros}\n"
                f"🏪 **Locales incluidos:** {len(locales)}\n"
                f"📅 **Período:** {min(row['Fecha_Solicitud'] for row in connection_data)} "
                f"a {max(row['Fecha_Solicitud'] for row in connection_data)}"
            )

            return filepath, resumen

        except Exception as e:
            error_msg = f"Error generando reporte: {str(e)}"
            logger.logger.error(error_msg)
            return None, error_msg

    def generate_detailed_report(self, local_filter=None):
        """Genera un reporte detallado con estadísticas - MÉTODO FALTANTE"""
        try:
            connection_data = logger.get_connection_data(local_filter)

            if not connection_data:
                return None, "No se encontraron datos de conexiones"

            # Estadísticas
            total_consultas = len(connection_data)
            locales = set(row['Local'] for row in connection_data)
            fechas = set(row['Fecha_Solicitud'] for row in connection_data)

            # Contar por local
            consultas_por_local = {}
            for row in connection_data:
                local = row['Local']
                consultas_por_local[local] = consultas_por_local.get(local, 0) + 1

            # Crear archivo de resumen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_detallado_{local_filter if local_filter else 'todos'}_{timestamp}.txt"
            filepath = os.path.join(self.reports_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("           REPORTE DETALLADO DE CONEXIONES\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total de consultas: {total_consultas}\n")
                f.write(f"Locales únicos: {len(locales)}\n")
                f.write(f"Rango de fechas: {min(fechas)} a {max(fechas)}\n\n")

                f.write("-" * 40 + "\n")
                f.write("CONSULTAS POR LOCAL\n")
                f.write("-" * 40 + "\n")

                for local, count in sorted(consultas_por_local.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"{local}: {count} consultas\n")

                f.write("\n" + "=" * 60 + "\n")
                f.write("DETALLE DE CONEXIONES\n")
                f.write("=" * 60 + "\n\n")

                for i, row in enumerate(connection_data[:50], 1):  # Mostrar máximo 50
                    f.write(f"Consulta #{i}:\n")
                    f.write(f"  ID: {row['ID_Conexion']}\n")
                    f.write(f"  Local: {row['Local']}\n")
                    f.write(f"  Fecha consultada: {row['Fecha_Consulta']}\n")
                    f.write(f"  Fecha solicitud: {row['Fecha_Solicitud']}\n")
                    f.write(f"  Hora: {row['Hora_Solicitud']}\n")
                    f.write(f"  Estado: {row['Estado']}\n")
                    f.write("-" * 30 + "\n")

            resumen = (
                f"📊 **Reporte Detallado Generado**\n\n"
                f"📁 **Archivo:** {filename}\n"
                f"📈 **Total consultas:** {total_consultas}\n"
                f"🏪 **Locales:** {len(locales)}\n"
                f"📅 **Días con actividad:** {len(fechas)}\n"
                f"📋 **Se muestran las primeras 50 conexiones**"
            )

            return filepath, resumen

        except Exception as e:
            error_msg = f"Error generando reporte detallado: {str(e)}"
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