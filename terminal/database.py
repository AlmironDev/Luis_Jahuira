import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

def get_db_connection():
    """Establece conexión con la base de datos PostgreSQL en Neon"""
    try:
        conn = psycopg2.connect(
            'postgresql://neondb_owner:npg_U1WXNbyich6g@ep-sweet-frost-aggb3hti-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """Ejecuta una consulta y retorna los resultados"""
    conn = get_db_connection()
    if conn is None:
        return None
        
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                result = None
        else:
            conn.commit()
            result = None
            
        return result
    except psycopg2.Error as e:
        print(f"Error en la consulta: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = get_db_connection()
    
    if conn is None:
        print("No se pudo establecer conexión con la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                role INTEGER NOT NULL DEFAULT 1, 
                dni TEXT UNIQUE NOT NULL,  
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT true
            )
        ''')

        # Tabla de cámaras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camaras (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                descripcion TEXT,
                muslo_rodilla_pie INTEGER NOT NULL DEFAULT 90,  
                espalda_cadera_muslo INTEGER NOT NULL DEFAULT 90, 
                hombros_brazos INTEGER NOT NULL DEFAULT 90, 
                espalda_cuello_cabeza INTEGER NOT NULL DEFAULT 90,  
                manos_muneca INTEGER NOT NULL DEFAULT 90,   
                ubicacion TEXT,
                activa BOOLEAN DEFAULT true,
                fecha_instalacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de notificaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificaciones (
                id SERIAL PRIMARY KEY,
                id_usuario INTEGER NOT NULL,
                id_camara INTEGER NOT NULL,
                mensaje TEXT NOT NULL,
                tipo TEXT NOT NULL,
                leida BOOLEAN DEFAULT false,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
                FOREIGN KEY (id_camara) REFERENCES camaras(id)
            )
        ''')

        # Tabla de configuración del sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion (
                id SERIAL PRIMARY KEY,
                parametro TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                descripcion TEXT
            )
        ''')
        
        # Tabla de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alertas (
                id SERIAL PRIMARY KEY,
                id_camara INTEGER NOT NULL,
                tipo_angulo TEXT NOT NULL,
                valor_angulo REAL NOT NULL,
                angulo_objetivo REAL NOT NULL,
                nivel_alerta TEXT NOT NULL,
                duracion_segundos INTEGER,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_camara) REFERENCES camaras(id)
            )
        ''')

        # Tabla de pausas activas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pausas_activas (
                id SERIAL PRIMARY KEY,
                id_usuario INTEGER NOT NULL,
                mensaje TEXT,
                imagen TEXT,
                hora_pausa TIME,
                dias_semana TEXT,
                activa BOOLEAN DEFAULT true,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
            )
        ''')

        # Crear índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alertas_nivel ON alertas(nivel_alerta)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alertas_camara ON alertas(id_camara)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(id_usuario)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notificaciones_camara ON notificaciones(id_camara)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha ON notificaciones(fecha)')

        conn.commit()
        print("Base de datos inicializada correctamente")
        
    except psycopg2.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Función adicional para consultas simples (sin RealDictCursor)
def execute_simple_query(query, params=None):
    """Ejecuta una consulta simple y retorna los resultados (sin RealDictCursor)"""
    conn = get_db_connection()
    if conn is None:
        return None
        
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        # Para SELECT retornar resultados
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = None
            
        return result
    except psycopg2.Error as e:
        print(f"Error en la consulta: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Inicializar la base de datos al ejecutar el script
    init_db()