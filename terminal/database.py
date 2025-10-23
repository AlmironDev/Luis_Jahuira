import sqlite3
from datetime import datetime

def get_db_connection():
    """Establece conexión con la base de datos SQLite"""
    conn = sqlite3.connect('monitoring.db') 
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = get_db_connection()
    
    try:
        # Tabla de usuarios
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                role INTEGER NOT NULL DEFAULT 1, 
                dni TEXT UNIQUE NOT NULL,  
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT 1
            )
        ''')

        # Tabla de cámaras
        conn.execute('''
            CREATE TABLE IF NOT EXISTS camaras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                descripcion TEXT,
                muslo_rodilla_pie INTEGER NOT NULL DEFAULT 90,  
                espalda_cadera_muslo INTEGER NOT NULL DEFAULT 90, 
                hombros_brazos INTEGER NOT NULL DEFAULT 90, 
                espalda_cuello_cabeza INTEGER NOT NULL DEFAULT 90,  
                manos_muneca INTEGER NOT NULL DEFAULT 90,   
                ubicacion TEXT,
                activa BOOLEAN DEFAULT 1,
                fecha_instalacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id) REFERENCES notificaciones(id_camara)
            )
        ''')

        # Tabla de notificaciones
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_camara INTEGER NOT NULL,
                mensaje TEXT NOT NULL,
                tipo TEXT NOT NULL,  -- 'postura', 'movimiento', 'conexion'
                leida BOOLEAN DEFAULT 0,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
                FOREIGN KEY (id_camara) REFERENCES camaras(id)
            )
        ''')

        # Tabla de configuración del sistema
        conn.execute('''
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parametro TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                descripcion TEXT
            )
        ''')
        
        # En tu archivo de base de datos o donde creas las tablas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_camara INTEGER NOT NULL,
                tipo_angulo TEXT NOT NULL,           -- Ej: 'rodilla_izq', 'codo_der', etc.
                valor_angulo REAL NOT NULL,          -- Valor numérico del ángulo detectado
                angulo_objetivo REAL NOT NULL,       -- Valor objetivo (90° o 180°)
                nivel_alerta TEXT NOT NULL,          -- 'WARNING' o 'CRITICAL'
                duracion_segundos INTEGER,           -- Duración en segundos de la mala postura
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_camara) REFERENCES camaras(id)
            )
        ''')

        # También crear índices para mejor performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas(fecha)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alertas_nivel ON alertas(nivel_alerta)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alertas_camara ON alertas(id_camara)')
                
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pausas_activas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                mensaje TEXT,
                imagen TEXT,
                hora_pausa TIMESTAMP,  -- Almacenar como texto en formato HH:MM o como TIMESTAMP
                dias_semana TEXT,  -- Para especificar días de la semana (ej. "Lunes,Miércoles,Viernes")
                activa BOOLEAN DEFAULT 1,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
            )
        ''')

        
        # Índices para mejorar el rendimiento de las consultas
        conn.execute('CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(id_usuario)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_notificaciones_camara ON notificaciones(id_camara)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha ON notificaciones(fecha)')



        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        conn.rollback()
    finally:
        conn.close()