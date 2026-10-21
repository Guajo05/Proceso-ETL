# Proyecto ETL - Sistema de Análisis de Opiniones de Clientes

Este proyecto implementa un proceso ETL (Extract, Transform, Load) en Python para poblar una base de datos transaccional en SQL Server. Los datos provienen de múltiples archivos CSV (encuestas, redes sociales y reseñas web).

## Tecnologías Utilizadas
*   **Lenguaje:** Python 3.x
*   **Librerías:** Pandas, Pyodbc, python-dotenv
*   **Base de Datos:** SQL Server
*   **Arquitectura:** ETL (Extracción, Transformación y Carga)

## Estructura del Proyecto
*   `data/`: Contiene los archivos CSV de origen.
*   `sql/`: Script de creación de base de datos, tablas, vistas y procedimientos.
*   `src/main.py`: Código principal del proceso ETL.

## Funcionalidades del ETL
1.  **Extracción:** Lectura de 6 archivos CSV manejando errores de codificación y líneas corruptas.
2.  **Transformación:** 
    *   Limpieza de IDs (ej. quitar la 'C' de los IDs de clientes y 'P' de productos).
    *   Validación de campos nulos.
    *   Asignación automática de clasificación (Positiva, Neutra, Negativa) según el puntaje.
3.  **Carga:** Inserción respetando el orden de las llaves foráneas, manejo de duplicados y excepciones.
4.  **Resumen:** Impresión en consola de registros procesados, insertados y rechazados.

## Cómo ejecutar el proyecto
1. Clonar el repositorio.
2. Crear y activar un entorno virtual: `python -m venv venv`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Crear un archivo `.env` con las credenciales de conexión:
   ```env
   DB_SERVER=localhost\SQLEXPRESS
   DB_NAME=OpinionesClientesDB