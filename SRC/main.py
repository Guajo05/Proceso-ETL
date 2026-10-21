import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

load_dotenv()

# Variables globales para el resumen
stats = {
    'procesados': 0,
    'insertados': 0,
    'rechazados': 0,
    'errores': []
}

def obtener_conexion():
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'Trusted_Connection=yes;'
    )
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

def cargar_datos(conn):
    print("\n🚀 Iniciando proceso de carga (Load)...")
    cursor = conn.cursor()
    
    try:
        # ---------------------------------------------------------
        # 1. CARGAR CATEGORÍAS
        # ---------------------------------------------------------
        print("📦 Cargando Categorías...")
        df_products = pd.read_csv('Data/products.csv')
        categorias_unicas = df_products['Categoría'].unique()
        
        for cat in categorias_unicas:
            cursor.execute("SELECT IdCategoria FROM Categoria WHERE Nombre = ?", cat)
            if not cursor.fetchone():
                cursor.execute("INSERT INTO Categoria (Nombre) VALUES (?)", cat)
        conn.commit()
        
        # ---------------------------------------------------------
        # 2. CARGAR CLIENTES
        # ---------------------------------------------------------
        print("👥 Cargando Clientes...")
        df_clients = pd.read_csv('Data/clients.csv')
        df_clients.rename(columns={'clieIdCliente': 'IdCliente'}, inplace=True)
        
        for _, row in df_clients.iterrows():
            stats['procesados'] += 1
            try:
                cursor.execute(
                    "INSERT INTO Cliente (IdCliente, Nombre, Email) VALUES (?, ?, ?)", 
                    int(row['IdCliente']), row['Nombre'], row['Email']
                )
                stats['insertados'] += 1
            except pyodbc.IntegrityError:
                # Si el cliente ya existe (por el ID o Email duplicado), lo ignoramos
                pass
            except Exception as e:
                stats['rechazados'] += 1
                stats['errores'].append(f"Error Cliente {row['IdCliente']}: {e}")
        conn.commit()

        # ---------------------------------------------------------
        # 3. CARGAR FUENTES DE DATOS
        # ---------------------------------------------------------
        print("🌐 Cargando Fuentes de Datos...")
        df_fuentes = pd.read_csv('Data/fuente_datos.csv')
        for _, row in df_fuentes.iterrows():
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM Fuente_Datos WHERE IdFuente = ?) "
                "INSERT INTO Fuente_Datos (IdFuente, TipoFuente, FechaCarga) VALUES (?, ?, ?)",
                row['IdFuente'], row['IdFuente'], row['TipoFuente'], row['FechaCarga']
            )
        conn.commit()

        # ---------------------------------------------------------
        # 4. CARGAR CLASIFICACIONES (Positiva, Negativa, Neutra)
        # ---------------------------------------------------------
        print("⭐ Cargando Clasificaciones...")
        for clasif in ['Positiva', 'Negativa', 'Neutra']:
            cursor.execute("IF NOT EXISTS (SELECT 1 FROM Clasificacion WHERE Tipo = ?) INSERT INTO Clasificacion (Tipo) VALUES (?)", clasif, clasif)
        conn.commit()

        # ---------------------------------------------------------
        # 5. CARGAR PRODUCTOS
        # ---------------------------------------------------------
        print("🛒 Cargando Productos...")
        # Creamos un diccionario para saber el ID de la categoría
        cursor.execute("SELECT Nombre, IdCategoria FROM Categoria")
        mapa_categorias = {row[0]: row[1] for row in cursor.fetchall()}
        
        for _, row in df_products.iterrows():
            id_cat = mapa_categorias.get(row['Categoría'])
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM Producto WHERE IdProducto = ?) "
                "INSERT INTO Producto (IdProducto, Nombre, IdCategoria) VALUES (?, ?, ?)",
                int(row['IdProducto']), int(row['IdProducto']), row['Nombre'], id_cat
            )
        conn.commit()

        # ---------------------------------------------------------
        # 6. CARGAR OPINIONES (Surveys, Social, Web)
        # ---------------------------------------------------------
        print("📝 Cargando Opiniones (esto puede tardar un momento)...")
        
        # Diccionarios para validar las FK
        cursor.execute("SELECT IdCliente FROM Cliente")
        clientes_validos = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT IdProducto FROM Producto")
        productos_validos = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT Tipo, IdClasificacion FROM Clasificacion")
        mapa_clasificaciones = {row[0]: row[1] for row in cursor.fetchall()}

        # --- 6.1 Procesar Surveys ---
        df_surveys = pd.read_csv('Data/surveys_part.csv')
        for _, row in df_surveys.iterrows():
            stats['procesados'] += 1
            try:
                # Validaciones
                if int(row['IdCliente']) not in clientes_validos:
                    raise ValueError(f"IdCliente {row['IdCliente']} no existe")
                if int(row['IdProducto']) not in productos_validos:
                    raise ValueError(f"IdProducto {row['IdProducto']} no existe")
                
                id_clasif = mapa_clasificaciones.get(row['Clasificación'], 3) # 3=Neutra por defecto
                
                cursor.execute(
                    "INSERT INTO Opinion (IdOrigen, Canal, Fecha, Comentario, Puntaje, IdCliente, IdProducto, IdClasificacion, IdFuente) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    str(row['IdOpinion']), 'Encuesta', row['Fecha'], row['Comentario'], int(row['PuntajeSatisfacción']),
                    int(row['IdCliente']), int(row['IdProducto']), id_clasif, 'F002' # F002 = CSV
                )
                stats['insertados'] += 1
            except Exception as e:
                stats['rechazados'] += 1
                stats['errores'].append(f"Survey {row['IdOpinion']}: {str(e)}")

        # --- 6.2 Procesar Social Comments ---
        df_social = pd.read_csv('Data/social_comments.csv', on_bad_lines='skip')
        df_social['IdCliente'] = pd.to_numeric(df_social['IdCliente'].astype(str).str.replace('C', ''), errors='coerce').fillna(0).astype(int)
        df_social['IdProducto'] = pd.to_numeric(df_social['IdProducto'].astype(str).str.replace('P', ''), errors='coerce').fillna(0).astype(int)
        
        for _, row in df_social.iterrows():
            stats['procesados'] += 1
            try:
                if row['IdCliente'] != 0 and row['IdCliente'] not in clientes_validos:
                    raise ValueError(f"IdCliente {row['IdCliente']} no existe")
                if row['IdProducto'] not in productos_validos:
                    raise ValueError(f"IdProducto {row['IdProducto']} no existe")
                
                # Si el comentario no tiene clasificación explícita, usamos Neutra (3)
                cursor.execute(
                    "INSERT INTO Opinion (IdOrigen, Canal, Fecha, Comentario, Puntaje, IdCliente, IdProducto, IdClasificacion, IdFuente) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    str(row['IdComment']), 'Red Social', row['Fecha'], row['Comentario'], None,
                    row['IdCliente'] if row['IdCliente'] != 0 else None, row['IdProducto'], 3, 'F003' # F003 = Social
                )
                stats['insertados'] += 1
            except Exception as e:
                stats['rechazados'] += 1
                stats['errores'].append(f"Social {row['IdComment']}: {str(e)}")

        # --- 6.3 Procesar Web Reviews ---
        df_web = pd.read_csv('Data/web_reviews.csv', engine='python', on_bad_lines='skip')
        df_web['IdCliente'] = pd.to_numeric(df_web['IdCliente'].astype(str).str.replace('C', ''), errors='coerce').fillna(0).astype(int)
        df_web['IdProducto'] = pd.to_numeric(df_web['IdProducto'].astype(str).str.replace('P', ''), errors='coerce').fillna(0).astype(int)
        
        for _, row in df_web.iterrows():
            stats['procesados'] += 1
            try:
                if row['IdCliente'] != 0 and row['IdCliente'] not in clientes_validos:
                    raise ValueError(f"IdCliente {row['IdCliente']} no existe")
                if row['IdProducto'] not in productos_validos:
                    raise ValueError(f"IdProducto {row['IdProducto']} no existe")
                
                # Calcular clasificación basada en el Rating
                if int(row['Rating']) >= 4: id_clasif = mapa_clasificaciones['Positiva']
                elif int(row['Rating']) <= 2: id_clasif = mapa_clasificaciones['Negativa']
                else: id_clasif = mapa_clasificaciones['Neutra']

                cursor.execute(
                    "INSERT INTO Opinion (IdOrigen, Canal, Fecha, Comentario, Puntaje, IdCliente, IdProducto, IdClasificacion, IdFuente) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    str(row['IdReview']), 'Web', row['Fecha'], row['Comentario'], int(row['Rating']),
                    row['IdCliente'] if row['IdCliente'] != 0 else None, row['IdProducto'], id_clasif, 'F001' # F001 = Web
                )
                stats['insertados'] += 1
            except Exception as e:
                stats['rechazados'] += 1
                stats['errores'].append(f"Web {row['IdReview']}: {str(e)}")
                
        conn.commit()
        print("✅ Carga finalizada.")

    except Exception as e:
        print(f"❌ Error general durante la carga: {e}")
        conn.rollback()
    finally:
        cursor.close()

def mostrar_resumen():
    print("\n" + "="*50)
    print("📊 RESUMEN DEL PROCESO ETL")
    print("="*50)
    print(f"Total de registros procesados: {stats['procesados']}")
    print(f"Total de registros insertados: {stats['insertados']}")
    print(f"Total de registros rechazados: {stats['rechazados']}")
    
    if stats['errores']:
        print("\n⚠️ Detalle de los primeros 5 errores/rechazos:")
        for error in stats['errores'][:5]:
            print(f" - {error}")
        if len(stats['errores']) > 5:
            print(f" ... y {len(stats['errores']) - 5} errores más.")
    print("="*50)

if __name__ == "__main__":
    conexion = obtener_conexion()
    if conexion:
        cargar_datos(conexion)
        conexion.close()
        mostrar_resumen()