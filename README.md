# Luis Jahuira — Sistema de Monitoreo Ergonómico en el Lugar de Trabajo

## Resumen

Este proyecto es un **sistema de monitoreo de bienestar y postura en el lugar de trabajo** diseñado para fomentar hábitos laborales saludables mediante análisis en tiempo real con visión por computadora e intervenciones proactivas para el bienestar. El sistema atiende a administradores y empleados, proporcionando monitoreo continuo de la postura, generación automática de alertas y recordatorios programados para pausas activas.

**Usuarios principales:**
- **Administradores del lugar de trabajo:** Configuran cámaras, gestionan usuarios, revisan análisis de postura y alertas.
- **Empleados:** Reciben retroalimentación sobre su postura, recordatorios para pausas activas y pueden visualizar sus datos de monitoreo.

**Capacidades principales:**
- Análisis de postura en tiempo real mediante visión por computadora (MediaPipe)
- Generación automática de alertas ante detección de mala postura
- Recordatorios programados para pausas activas con instrucciones visuales
- Gestión de usuarios basada en roles y autenticación segura
- Panel web para administración y monitoreo del sistema
- Soporte multi-cámara con configuración individual por dispositivo

El sistema integra cámaras IP con detección de postura basada en IA para identificar problemas ergonómicos como inclinación hacia adelante de la cabeza, asimetría de hombros y posición incorrecta de manos, generando intervenciones adecuadas para promover el bienestar en el trabajo.

## Organización del Proyecto

Es una **aplicación web basada en Flask** con arquitectura modular organizada por dominios funcionales. Usa SQLite para persistencia de datos e integra MediaPipe para capacidades de visión por computadora.

### Sistemas y Servicios Principales

**1. Capa de Base de Datos** (`terminal/database.py`, `terminal/monitoring.db`)  
- Base de datos SQLite con esquema completo para usuarios, cámaras, alertas y datos de bienestar  
- Gestión centralizada de conexiones e inicialización del esquema  
- Tablas principales: `usuarios`, `camaras`, `alertas`, `notificaciones`, `pausas_activas`, `configuracion`

**2. Capa de Interfaz Web** (`terminal/templates/`)  
- Interfaz responsiva basada en Bootstrap con organización modular de plantillas  
- Panel principal (`index.html`) con acceso a todos los módulos del sistema  
- Interfaces especializadas para configuración de cámaras, gestión de alertas y administración de usuarios

**3. Gestión de Rutas** (`terminal/routes/`)  
- Configuración modular de rutas Flask agrupadas por dominio funcional  
- Orquestación central mediante la función `configure_all_routes()`  
- Módulos separados para: usuarios, autenticación, cámaras, videos, notificaciones, alertas y pausas activas

**4. Servicio de Procesamiento de Video** (`terminal/services/video_streamer.py`)  
- Procesamiento en tiempo real de flujos de video usando MediaPipe  
- Soporte concurrente para múltiples cámaras mediante hilos (threading)  
- Análisis de postura con parámetros configurables y generación de alertas

**5. Sistema de Autenticación** (`terminal/routes/login.py`, `terminal/routes/usuarios.py`)  
- Control de acceso basado en roles (usuarios normales vs administradores)  
- Hashing seguro de contraseñas y manejo de sesiones  
- Operaciones CRUD para usuarios con gestión de perfiles

### Archivos y Directorios Principales



```
terminal/
├── app.py # Punto de entrada de la aplicación Flask
├── database.py # Gestión de conexión y esquema de base de datos
├── monitoring.db # Archivo SQLite con datos del sistema
├── routes/ # Definición modular de rutas
│ ├── init.py # Configuración central de rutas
│ ├── login.py # Rutas de autenticación
│ ├── usuarios.py # Gestión de usuarios
│ ├── videos.py # Streaming de video y control de cámaras
│ ├── camaras.py # Configuración de cámaras
│ ├── alertas.py # Gestión y visualización de alertas
│ ├── pausas.py # Administración de pausas activas
│ └── notificacion.py # Manejo de notificaciones
├── services/ # Servicios con lógica principal
│ ├── video_streamer.py # Servicio principal de procesamiento de video
│ └── video_processor.py # Procesamiento de video legado
├── templates/ # Plantillas HTML Jinja2
│ ├── index.html # Panel principal
│ ├── login.html # Interfaz de autenticación
│ ├── video/ # Plantillas relacionadas a video
│ ├── pausas_activas/ # Plantillas para pausas activas
│ └── alertas/ # Plantillas para gestión de alertas
└── static/ # Recursos estáticos (CSS, JS, imágenes)
└── uploads/pausas/ # Imágenes para instrucciones de pausas
```


### Funciones y Clases Clave

**Aplicación Principal (`terminal/app.py`)**  
- `Flask(__name__)`: Instancia principal de la aplicación  
- `configure_all_routes(app)`: Función orquestadora para registro centralizado de rutas

**Gestión de Base de Datos (`terminal/database.py`)**  
- `get_db_connection()`: Retorna una conexión SQLite configurada con row factory  
- `init_db()`: Crea tablas e índices necesarios para el sistema

**Procesamiento de Video (`terminal/services/video_streamer.py`)**  
- `VideoStreamer`: Clase principal para el procesamiento concurrente de múltiples cámaras  
- `_stream_worker()`: Función en hilo para captura y procesamiento de video por cámara  
- `_process_frame()`: Análisis individual de cada cuadro con integración MediaPipe  
- `_check_head_posture()`, `_check_shoulders_posture()`: Funciones específicas para análisis ergonómico

**Autenticación (`terminal/routes/login.py`)**  
- `login_required()`: Decorador para protección de rutas con validación de roles opcional  
- `login()`: Validación de credenciales y establecimiento de sesión

## Glosario de Términos Específicos del Código

### Entidades Principales  
- **`usuarios`**: Tabla de gestión de usuarios con datos de autenticación y perfil (`terminal/database.py:16-25`)  
- **`camaras`**: Configuración de cámaras con parámetros para análisis de postura (`terminal/database.py:28-43`)  
- **`alertas`**: Alertas críticas generadas por el análisis ergonómico (`terminal/database.py:67-75`)  
- **`notificaciones`**: Mensajes dirigidos a usuarios por parte del sistema (`terminal/database.py:46-56`)  
- **`pausas_activas`**: Programación de pausas activas con instrucciones visuales (`terminal/database.py:78-86`)

### Procesamiento de Video  
- **`VideoStreamer`**: Servicio principal que maneja múltiples cámaras concurrentes (`terminal/services/video_streamer.py:29`)  
- **`_stream_worker`**: Función en hilo que procesa cada feed de cámara (`terminal/services/video_streamer.py:157`)  
- **`video_feed`**: Endpoint MJPEG para streaming en vivo (`terminal/routes/videos.py:62`)  
- **`frame_queue`**: Buffer que almacena cuadros procesados por cámara (`terminal/services/video_streamer.py`)  
- **`PostureState`**: Enumeración que define la calidad de postura: BUENA, ADVERTENCIA, MALA (`terminal/services/video_streamer.py:20`)

### Parámetros de Análisis de Postura  
- **`angulo_min/angulo_max`**: Límites de ángulo de cabeza/cuello para detección (`terminal/database.py:33-34`)  
- **`hombros_min/hombros_max`**: Parámetros de distancia entre hombros para análisis (`terminal/database.py:35-36`)  
- **`manos_min/manos_max`**: Umbrales para posición ergonómica de las manos (`terminal/database.py:37-38`)  
- **`max_neck_angle`**: Ángulo crítico de cuello para generación de alerta (`terminal/services/video_streamer.py`)

### Sistema de Alertas  
- **`AlertType`**: Enum que categoriza alertas: POSTURA, MANOS, MOVIMIENTO (`terminal/services/video_streamer.py:32`)  
- **`AlertLevel`**: Clasificación de severidad: INFO, ADVERTENCIA, CRÍTICA (`terminal/services/video_streamer.py:34`)  
- **`severidad`**: Campo de severidad en base de datos para alertas (`terminal/routes/alertas.py`)  
- **`alert_cooldown`**: Mecanismo para evitar spam de alertas (`terminal/services/video_streamer.py`)  
- **`_trigger_alert`**: Función para generar y registrar alertas ergonómicas (`terminal/services/video_streamer.py:399`)

### Campos de Estado del Sistema  
- **`activa/activo`**: Booleano que indica si cámara/usuario/pausa está activo (`terminal/database.py`)  
- **`leida`**: Booleano que indica si notificación fue leída (`terminal/database.py:52`)  
- **`role`**: Nivel de permiso de usuario: 1=normal, 2=administrador (`terminal/database.py:21`)

### Sistema de Bienestar  
- **`hora_pausa`**: Hora programada para recordatorio de pausa activa (`terminal/database.py:82`)  
- **`dias_semana`**: Cadena CSV con días de la semana para pausas: "Lunes,Miércoles,Viernes" (`terminal/database.py:83`)  
- **`bad_posture_start`**: Timestamp para medir duración de mala postura (`terminal/services/video_streamer.py`)

### Componentes de Arquitectura  
- **`configure_all_routes`**: Función que orquesta el registro modular de rutas (`terminal/routes/__init__.py:10`)  
- **`get_db_connection`**: Función que retorna conexión SQLite configurada (`terminal/database.py:4`)  
- **`monitoring.db`**: Archivo SQLite que almacena todos los datos del sistema (`terminal/database.py:5`)  
- **`login_required`**: Decorador de autenticación con verificación de roles (`terminal/routes/login.py:58`)  
- **`_process_frame`**: Función principal para análisis de cuadros de video (`terminal/services/video_streamer.py:201`)

