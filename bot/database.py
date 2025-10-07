import pyodbc
import uuid
from datetime import datetime

# Importaciones corregidas
from config.settings import Config
from utils.logger import logger


class DatabaseManager:
    def __init__(self):
        self.connection_string = self._build_connection_string()

    def _build_connection_string(self):
        """Construye la cadena de conexión para SQL Server"""
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={Config.DB_SERVER};"
            f"DATABASE={Config.DB_NAME};"
            f"UID={Config.DB_USER};"
            f"PWD={Config.DB_PASSWORD};"
            f"Trusted_Connection=no;"
        )

    def execute_query(self, merchant_id, fecha_transaccion, numero_referencia=None, numero_autorizacion=None):
        """Ejecuta la consulta SQL con los parámetros proporcionados"""
        connection_id = str(uuid.uuid4())

        try:
            # Log de conexión
            logger.log_connection("telegram_user", merchant_id, fecha_transaccion, connection_id, "attempt")

            # Construir merchantid completo
            merchantid_completo = f"000000{merchant_id}"

            # Formatear fecha para SQL (YYYYMMDD)
            fecha_sql = fecha_transaccion.replace("/", "")

            print(f"🔍 Ejecutando consulta para local: {merchantid_completo}, fecha: {fecha_sql}")

            # Conectar a la base de datos
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()

                # Construir consulta base
                query = """
                SELECT 
                    SUBSTRING(t.Merchantid, 7, 6) AS Codigo_Comercio,
                    t.tid_red,
                    FORMAT(CONVERT(date, t.Fecha_Transaccion, 112), 'dd/MM/yyyy') AS Fecha,
                    MAX(CASE 
                            WHEN t.tipo_transaccion = '01' AND t.estado = 0 AND Resultado_Externo = '00'  
                                THEN 'Compra Vigente'
                            WHEN t.tipo_transaccion = '01' AND t.estado = 0 AND Resultado_Externo != '00'  
                                THEN 'Compra Rechazada ' + m.descripcion
                            WHEN t.tipo_transaccion = '01' AND t.estado = 1 
                                THEN 'Pago Anulado'
                            WHEN t.tipo_transaccion = '01' AND t.estado = 2 
                                THEN 'Pago Reversado'
                        END) AS estado_transaccion,
                    t.numero_referencia,
                    COALESCE(MAX(CASE WHEN t.tipo_transaccion = '01' THEN t.Numero_Autorizacion END), 
                             MAX(t.Numero_Autorizacion)) AS Numero_Autorizacion_Final,  	
                    max(t.Face_Value) as Valor 
                FROM TB_LOG_TRANSACCION t WITH (NOLOCK)
                INNER JOIN TB_MENSAJE_02 m ON m.idExterno = t.Resultado_Externo
                WHERE t.Merchantid = ?
                AND CONVERT(varchar, t.Fecha_Transaccion, 112) = ?
                """

                params = [merchantid_completo, fecha_sql]

                # Agregar filtros opcionales
                if numero_referencia:
                    query += " AND t.numero_referencia = ?"
                    params.append(numero_referencia)

                if numero_autorizacion:
                    query += " AND (t.Numero_Autorizacion = ? OR EXISTS (SELECT 1 FROM TB_LOG_TRANSACCION t2 WHERE t2.Numero_Autorizacion = ? AND t2.numero_referencia = t.numero_referencia))"
                    params.extend([numero_autorizacion, numero_autorizacion])

                # Agregar GROUP BY y ORDER BY
                query += """
                GROUP BY 
                    SUBSTRING(t.Merchantid, 7, 6), 
                    t.tid_red, 
                    FORMAT(CONVERT(date, t.Fecha_Transaccion, 112), 'dd/MM/yyyy'),
                    t.numero_referencia
                ORDER BY FORMAT(CONVERT(date, t.Fecha_Transaccion, 112), 'dd/MM/yyyy')
                """

                print(f"📊 Ejecutando consulta SQL...")
                # Ejecutar consulta
                cursor.execute(query, params)
                results = cursor.fetchall()

                print(f"✅ Consulta exitosa. Resultados: {len(results)}")

                # Log de consulta exitosa
                logger.log_connection("telegram_user", merchant_id, fecha_transaccion, connection_id, "success")
                logger.log_query("telegram_user", merchant_id, fecha_transaccion, numero_referencia,
                                 numero_autorizacion)

                return results, connection_id

        except Exception as e:
            # Log de error
            error_msg = f"❌ Error en consulta: {str(e)}"
            print(error_msg)
            logger.log_connection("telegram_user", merchant_id, fecha_transaccion, connection_id, f"error: {str(e)}")
            raise e

    def format_results(self, results):
        """Formatea los resultados para una respuesta amigable"""
        if not results:
            return "❌ No se encontraron transacciones con los criterios especificados."

        formatted_results = []
        for row in results:
            codigo_comercio, tid_red, fecha, estado, referencia, autorizacion, valor = row

            formatted_result = f"""
🏪 **Local:** {codigo_comercio}
🆔 **TID:** {tid_red}
📅 **Fecha:** {fecha}
📊 **Estado:** {estado}
🔢 **Referencia:** {referencia}
✅ **Autorización:** {autorizacion}
💰 **Valor:** ${float(valor) if valor else 0:,.2f}
{'-' * 30}
            """
            formatted_results.append(formatted_result)

        return "\n".join(formatted_results)