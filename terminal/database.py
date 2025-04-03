import sqlite3
from datetime import datetime

def get_db_connection():
    """Establece conexión con la base de datos SQLite"""
    conn = sqlite3.connect('monitoring.db')  # Cambiado a un nombre más descriptivo
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
                password TEXT NOT NULL,
                role INTEGER NOT NULL DEFAULT 1,  # 1=usuario normal, 2=admin
                dni TEXT UNIQUE NOT NULL,  # Cambiado a TEXT para manejar diferentes formatos
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
                angulo_min INTEGER NOT NULL DEFAULT 45,
                angulo_max INTEGER NOT NULL DEFAULT 135,
                hombros_min REAL NOT NULL DEFAULT 0.5,
                hombros_max REAL NOT NULL DEFAULT 1.5,
                manos_min INTEGER NOT NULL DEFAULT 30,
                manos_max INTEGER NOT NULL DEFAULT 150,
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
                tipo TEXT NOT NULL,  # 'postura', 'movimiento', 'conexion'
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

        # Insertar valores por defecto si es necesario
        if not conn.execute("SELECT 1 FROM usuarios WHERE username = 'admin'").fetchone():
            conn.execute('''
                INSERT INTO usuarios (nombre, username, password, role, dni)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Administrador', 'admin', 'hashed_password_here', 2, '00000000'))

        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        conn.rollback()
    finally:
        conn.close()

