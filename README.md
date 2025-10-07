# 🤖 KFC Telegram Bot v2.0

Bot de Telegram para consultas de transacciones KFC con interfaz conversacional mejorada y sistema de reportes.

## 🎯 Características Principales

### 🔄 Navegación Intuitiva
- Botones "↩️ Volver atrás" en cada paso
- "❌ Finalizar consulta" en cualquier momento
- Teclados contextuales para mejor UX

### 📊 Sistema de Reportes
- Comando `/reportes` para generar reportes
- Reportes CSV con todos los datos de conexiones
- Reportes detallados con estadísticas
- Filtrado por local o todos los locales

### 🗄️ Base de Datos
- Conexión a SQL Server
- Consultas de transacciones por local y fecha
- Búsqueda por referencia y autorización opcional

### 📝 Logging Avanzado
- Logs organizados por mes y día
- Registro de todas las conexiones
- IDs de transacción para trazabilidad

### 🐳 Docker
- Configuración Docker completa
- Fácil despliegue en cualquier entorno

## 🚀 Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/AngelGiovanny/telegram-bot-kfc_v2.git
cd telegram-bot-kfc_v2

# Instalar dependencias
pip install -r requirements.txt

# Configurar entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar
python main.py
