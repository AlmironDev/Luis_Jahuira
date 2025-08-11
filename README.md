# Luis Jahuira Workplace Ergonomics Monitoring System

## Overview

This project is a **workplace wellness and posture monitoring system** designed to promote healthy work habits through real-time computer vision analysis and proactive wellness interventions. The system serves workplace administrators and employees by providing continuous posture monitoring, automated alert generation, and scheduled wellness breaks.

**Primary Users:**
- **Workplace Administrators**: Configure cameras, manage users, review posture analytics and alerts
- **Employees**: Receive posture feedback, wellness break reminders, and view their monitoring data

**Core Capabilities:**
- Real-time posture analysis using computer vision (MediaPipe)
- Automated alert generation for poor posture detection
- Scheduled active break reminders with visual instructions
- Role-based user management and authentication
- Web-based dashboard for system administration and monitoring
- Multi-camera support with individual configuration parameters

The system integrates IP cameras with AI-powered pose detection to identify ergonomic issues like forward head posture, shoulder asymmetry, and improper hand positioning, then generates appropriate interventions to promote workplace wellness.

## Project Organization

This is a **Flask-based web application** with a modular architecture organized around functional domains. The system uses SQLite for data persistence and integrates with MediaPipe for computer vision capabilities.

### Core Systems and Services

**1. Database Layer** (`terminal/database.py`, `terminal/monitoring.db`)
- SQLite database with comprehensive schema for users, cameras, alerts, and wellness data
- Centralized connection management and schema initialization
- Tables: `usuarios`, `camaras`, `alertas`, `notificaciones`, `pausas_activas`, `configuracion`

**2. Web Interface Layer** (`terminal/templates/`)
- Bootstrap-based responsive UI with modular template organization
- Main dashboard (`index.html`) providing access to all system modules
- Specialized interfaces for camera configuration, alert management, and user administration

**3. Route Management** (`terminal/routes/`)
- Modular Flask route configuration with domain-specific modules
- Central orchestration via `configure_all_routes()` function
- Separate modules for: users, authentication, cameras, videos, notifications, alerts, wellness breaks

**4. Video Processing Service** (`terminal/services/video_streamer.py`)
- Real-time video stream processing using MediaPipe
- Concurrent multi-camera support with threading
- Posture analysis with configurable thresholds and alert generation

**5. Authentication System** (`terminal/routes/login.py`, `terminal/routes/usuarios.py`)
- Role-based access control (normal users vs administrators)
- Secure password hashing and session management
- User CRUD operations with profile management

### Main Files and Directories

```
terminal/
├── app.py                          # Flask application entry point
├── database.py                     # Database connection and schema management
├── monitoring.db                   # SQLite database file
├── routes/                         # Modular route definitions
│   ├── __init__.py                # Central route configuration
│   ├── login.py                   # Authentication routes
│   ├── usuarios.py                # User management routes
│   ├── videos.py                  # Video streaming and camera control
│   ├── camaras.py                 # Camera configuration routes
│   ├── alertas.py                 # Alert display and management
│   ├── pausas.py                  # Active breaks management
│   └── notificacion.py            # Notification handling
├── services/                       # Core business logic services
│   ├── video_streamer.py          # Main video processing service
│   └── video_processor.py         # Legacy video processing
├── templates/                      # Jinja2 HTML templates
│   ├── index.html                 # Main dashboard
│   ├── login.html                 # Authentication interface
│   ├── video/                     # Video-related templates
│   ├── pausas_activas/            # Wellness break templates
│   └── alertas/                   # Alert management templates
└── static/                         # Static assets (CSS, JS, images)
    └── uploads/pausas/            # Wellness break instruction images
```

### Main Functions and Classes

**Core Application (`terminal/app.py`)**
- `Flask(__name__)`: Main application instance
- `configure_all_routes(app)`: Central route registration orchestrator

**Database Management (`terminal/database.py`)**
- `get_db_connection()`: Returns configured SQLite connection with row factory
- `init_db()`: Creates all required tables and indices

**Video Processing (`terminal/services/video_streamer.py`)**
- `VideoStreamer`: Main service class for multi-camera video processing
- `_stream_worker()`: Threaded video capture and processing loop
- `_process_frame()`: Individual frame analysis with MediaPipe integration
- `_check_head_posture()`, `_check_shoulders_posture()`: Specific posture analysis functions

**Authentication (`terminal/routes/login.py`)**
- `login_required()`: Decorator for route protection with optional role checking
- `login()`: Credential validation and session establishment

## Glossary of Codebase-Specific Terms

### Core Entities
**`usuarios`** - User management entity table storing authentication and profile data (`terminal/database.py:16-25`)

**`camaras`** - Camera configuration entity with posture analysis parameters (`terminal/database.py:28-43`)

**`alertas`** - Critical alerts generated by posture analysis system (`terminal/database.py:67-75`)

**`notificaciones`** - User-targeted messages from monitoring system (`terminal/database.py:46-56`)

**`pausas_activas`** - Wellness break scheduler with visual instructions (`terminal/database.py:78-86`)

### Video Processing
**`VideoStreamer`** - Main service class managing concurrent camera streams (`terminal/services/video_streamer.py:29`)

**`_stream_worker`** - Threaded function processing individual camera feeds (`terminal/services/video_streamer.py:157`)

**`video_feed`** - MJPEG streaming endpoint for live camera display (`terminal/routes/videos.py:62`)

**`frame_queue`** - Buffer storing processed video frames per camera (`terminal/services/video_streamer.py`)

**`PostureState`** - Enum defining posture quality: GOOD, WARNING, BAD (`terminal/services/video_streamer.py:20`)

### Posture Analysis Parameters
**`angulo_min/angulo_max`** - Head/neck angle thresholds for posture detection (`terminal/database.py:33-34`)

**`hombros_min/hombros_max`** - Shoulder distance parameters for posture analysis (`terminal/database.py:35-36`)

**`manos_min/manos_max`** - Hand position thresholds for ergonomic assessment (`terminal/database.py:37-38`)

**`max_neck_angle`** - Critical neck angle threshold for alert generation (`terminal/services/video_streamer.py`)

### Alert System
**`AlertType`** - Enum categorizing alerts: POSTURE, HANDS, MOVEMENT (`terminal/services/video_streamer.py:32`)

**`AlertLevel`** - Severity classification: INFO, WARNING, CRITICAL (`terminal/services/video_streamer.py:34`)

**`severidad`** - Alert severity field in database (`terminal/routes/alertas.py`)

**`alert_cooldown`** - Spam prevention mechanism for alert generation (`terminal/services/video_streamer.py`)

**`_trigger_alert`** - Function generating and logging posture alerts (`terminal/services/video_streamer.py:399`)

### System Status Fields
**`activa/activo`** - Boolean status indicating if camera/user/break is active (`terminal/database.py`)

**`leida`** - Boolean indicating if notification has been read by user (`terminal/database.py:52`)

**`role`** - User permission level: 1=normal user, 2=admin (`terminal/database.py:21`)

### Wellness System
**`hora_pausa`** - Scheduled time for active break reminders (`terminal/database.py:82`)

**`dias_semana`** - CSV string specifying break days: "Lunes,Miércoles,Viernes" (`terminal/database.py:83`)

**`bad_posture_start`** - Timestamp tracking poor posture duration (`terminal/services/video_streamer.py`)

### Architecture Components
**`configure_all_routes`** - Central function orchestrating modular route registration (`terminal/routes/__init__.py:10`)

**`get_db_connection`** - Utility function returning configured SQLite connection (`terminal/database.py:4`)

**`monitoring.db`** - SQLite database file storing all system data (`terminal/database.py:5`)

**`login_required`** - Authentication decorator with optional role checking (`terminal/routes/login.py:58`)

**`_process_frame`** - Core function analyzing individual video frames (`terminal/services/video_streamer.py:201`)
