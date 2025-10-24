import cv2
import threading
import time
import logging
from datetime import datetime
from database import execute_query
from services.video_streamer import video_streamer
from services.posture_analyzer import posture_analyzer

class CameraManager:
    def __init__(self, refresh_interval=15):
        self.cameras = {}
        self.refresh_interval = refresh_interval
        self.lock = threading.Lock()
        self.running = False
        self.monitor_thread = None
        self.alert_callback = None
        self.camera_timeouts = {}  # Track camera connection issues
        self.max_retries = 3
        self.retry_delay = 5
        
        # Configurar logging
        self.logger = logging.getLogger('CameraManager')
        
    def set_alert_callback(self, callback):
        """Configura callback para enviar alertas a usuarios"""
        self.alert_callback = callback

    def start(self):
        """Inicia el monitor de cámaras activas."""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            self.logger.info("🎥 Camera monitor iniciado con análisis de postura")

    def stop(self):
        """Detiene todas las cámaras y el monitor."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        with self.lock:
            for cam_id in list(self.cameras.keys()):
                self._close_camera(cam_id)
            self.cameras.clear()
        self.logger.info("🛑 Camera manager detenido")

    def _monitor(self):
        """Monitorea la base de datos y sincroniza cámaras activas, gestiona alertas"""
        while self.running:
            try:
                active_cameras = execute_query(
                    "SELECT id, url, nombre FROM camaras WHERE activa = true",
                    fetch=True
                )

                if active_cameras is None:
                    self.logger.error("No se pudo obtener cámaras activas de la base de datos")
                    time.sleep(self.refresh_interval)
                    continue

                active_ids = {c["id"] for c in active_cameras}

                with self.lock:
                    # Cerrar cámaras inactivas
                    current_camera_ids = list(self.cameras.keys())
                    for cam_id in current_camera_ids:
                        if cam_id not in active_ids:
                            self._close_camera(cam_id)

                    # Abrir nuevas cámaras activas
                    for cam in active_cameras:
                        if cam["id"] not in self.cameras:
                            self._initialize_camera(cam["id"], cam["url"], cam["nombre"])

                    # Verificar estado de cámaras existentes
                    self._check_camera_status()
                    
                    # Verificar y enviar alertas de postura
                    self._check_posture_alerts()

            except Exception as e:
                self.logger.error(f"Error en monitor de cámaras: {e}")

            time.sleep(self.refresh_interval)

    def _initialize_camera(self, cam_id, url, nombre=None):
        """Inicializa una nueva cámara con verificación de conexión."""
        try:
            # Verificar que la cámara es accesible
            test_cap = cv2.VideoCapture(url)
            if not test_cap.isOpened():
                self.logger.warning(f"No se pudo conectar a cámara {cam_id} con URL: {url}")
                test_cap.release()
                return False
            
            # Probar lectura de frame
            ret, frame = test_cap.read()
            test_cap.release()
            
            if not ret:
                self.logger.warning(f"Cámara {cam_id} conectada pero no devuelve frames")
                return False
            
            # Registrar en tracking interno
            self.cameras[cam_id] = {
                "url": url,
                "nombre": nombre,
                "active": True,
                "last_check": time.time(),
                "connection_attempts": 0,
                "last_success": time.time()
            }
            
            # Resetear contador de timeouts
            if cam_id in self.camera_timeouts:
                del self.camera_timeouts[cam_id]
            
            # Iniciar en VideoStreamer para procesamiento
            video_streamer.start_camera(cam_id, url)
            self.logger.info(f"Cámara {cam_id} ({nombre}) inicializada correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando cámara {cam_id}: {e}")
            return False

    def _close_camera(self, cam_id):
        """Cierra una cámara específica."""
        if cam_id in self.cameras:
            camera_info = self.cameras[cam_id]
            nombre = camera_info.get("nombre", "Sin nombre")
            video_streamer.stop_stream(cam_id)
            self.cameras.pop(cam_id)
            self.logger.info(f"Cámara {cam_id} ({nombre}) cerrada")

    def _check_camera_status(self):
        """Verifica el estado de las cámaras y maneja reconexiones."""
        current_time = time.time()
        
        for cam_id, cam_info in list(self.cameras.items()):
            try:
                is_active = video_streamer.is_camera_active(cam_id)
                
                if not is_active:
                    cam_info["connection_attempts"] += 1
                    self.logger.warning(f"Cámara {cam_id} inactiva. Intento {cam_info['connection_attempts']}/{self.max_retries}")
                    
                    if cam_info["connection_attempts"] >= self.max_retries:
                        self.logger.error(f"Cámara {cam_id} excedió intentos de reconexión")
                        self._close_camera(cam_id)
                        continue
                    
                    # Intentar reconexión
                    self._reconnect_camera(cam_id, cam_info["url"])
                    
                else:
                    # Resetear contadores si está activa
                    cam_info["connection_attempts"] = 0
                    cam_info["last_success"] = current_time
                    
            except Exception as e:
                self.logger.error(f"Error verificando estado cámara {cam_id}: {e}")

    def _reconnect_camera(self, cam_id, url):
        """Intenta reconectar una cámara."""
        try:
            self.logger.info(f"Reconectando cámara {cam_id}...")
            video_streamer.stop_stream(cam_id)
            time.sleep(self.retry_delay)
            video_streamer.start_camera(cam_id, url)
            
            # Verificar si la reconexión fue exitosa
            time.sleep(2)  # Esperar a que se estabilice
            if video_streamer.is_camera_active(cam_id):
                self.logger.info(f"Cámara {cam_id} reconectada exitosamente")
                return True
            else:
                self.logger.warning(f"Reconexión fallida para cámara {cam_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en reconexión cámara {cam_id}: {e}")
            return False

    def _check_posture_alerts(self):
        """Verifica y envía alertas de postura a usuarios."""
        try:
            active_alerts = video_streamer.get_active_alerts()
            current_time = time.time()
            
            for cam_id, alerts_data in active_alerts.items():
                # Verificar si tenemos información de la cámara
                if cam_id not in self.cameras:
                    continue
                
                # Enviar alertas CRITICAL
                for alert in alerts_data.get('critical', []):
                    if self._should_send_alert(cam_id, alert, 'CRITICAL'):
                        self._send_user_alert(cam_id, alert, "CRITICAL")
                
                # Enviar alertas WARNING  
                for alert in alerts_data.get('warning', []):
                    if self._should_send_alert(cam_id, alert, 'WARNING'):
                        self._send_user_alert(cam_id, alert, "WARNING")
                    
        except Exception as e:
            self.logger.error(f"Error verificando alertas de postura: {e}")

    def _should_send_alert(self, camera_id, alert, level):
        """Determina si se debe enviar una alerta (evitar spam)."""
        alert_key = f"{camera_id}_{alert['angle_type']}_{level}"
        current_time = time.time()
        
        # Prevenir envío repetitivo de la misma alerta
        min_interval = 300 if level == 'CRITICAL' else 60  # 5 min para critical, 10 min para warning
        
        if alert_key in self.camera_timeouts:
            last_sent = self.camera_timeouts[alert_key]
            if current_time - last_sent < min_interval:
                return False
        
        self.camera_timeouts[alert_key] = current_time
        return True

    def _send_user_alert(self, camera_id, alert, level):
        """Envía alerta al usuario y la guarda en base de datos."""
        try:
            alert_message = self._format_alert_message(camera_id, alert, level)
            camera_name = self.cameras.get(camera_id, {}).get('nombre', 'Desconocida')
            
            self.logger.warning(f"{level} ALERT - Cámara {camera_id} ({camera_name}): {alert_message}")
            
            # Enviar callback si está configurado
            if self.alert_callback:
                try:
                    self.alert_callback(camera_id, alert_message, level, alert)
                except Exception as e:
                    self.logger.error(f"Error en callback de alerta: {e}")
            
            # Guardar en base de datos
            self._save_alert_to_db(camera_id, alert, level)
            
        except Exception as e:
            self.logger.error(f"Error enviando alerta: {e}")

    def _format_alert_message(self, camera_id, alert, level):
        """Formatea el mensaje de alerta."""
        angle_type_map = {
            'rodilla_izq': 'Rodilla izquierda',
            'rodilla_der': 'Rodilla derecha', 
            'cadera_columna_izq': 'Cadera-columna izquierda',
            'cadera_columna_der': 'Cadera-columna derecha',
            'codo_izq': 'Codo izquierdo',
            'codo_der': 'Codo derecho',
            'cuello_izq': 'Cuello izquierdo',
            'cuello_der': 'Cuello derecho'
        }
        
        angle_name = angle_type_map.get(alert['angle_type'], alert['angle_type'])
        camera_name = self.cameras.get(camera_id, {}).get('nombre', 'Desconocida')
        
        return (f"🚨 {level}: Postura incorrecta detectada\n"
                f"📍 Cámara: {camera_name} (ID: {camera_id})\n"
                f"📐 Ángulo: {angle_name}\n"
                f"📊 Valor: {alert['angle_value']:.1f}° (Objetivo: {alert['target_angle']}°)\n"
                f"⏰ Hora:  {alert['timestamp']}")

    def _save_alert_to_db(self, camera_id, alert, level):
        """Guarda alerta en base de datos."""
        try:
            execute_query(
                '''INSERT INTO alertas 
                (id_camara, tipo_angulo, valor_angulo, angulo_objetivo, nivel_alerta, duracion_segundos, fecha) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (camera_id, alert['angle_type'], alert['angle_value'], 
                alert['target_angle'], level, self._calculate_duration(camera_id, alert),
                alert['timestamp'])  # ← Usar el timestamp de la alerta
            )
            self.logger.debug(f"Alerta guardada en BD: {level} - {alert['angle_type']}")
        except Exception as e:
            self.logger.error(f"Error guardando alerta en BD: {e}")

    def _calculate_duration(self, camera_id, alert):
        """Calcula la duración en segundos de la mala postura."""
        try:
            # Usar el sistema de alertas del posture_analyzer
            alert_key = f"{camera_id}_{alert['angle_type']}"
            if hasattr(posture_analyzer.alert_system, 'alert_start_time'):
                if alert_key in posture_analyzer.alert_system.alert_start_time:
                    return int(time.time() - posture_analyzer.alert_system.alert_start_time[alert_key])
            return None
        except Exception as e:
            self.logger.error(f"Error calculando duración: {e}")
            return None

    def get_frame(self, camera_id):
        """Obtiene un frame procesado de VideoStreamer."""
        try:
            frame, alerts = video_streamer.get_frame_with_alerts(camera_id)
            return frame
        except Exception as e:
            self.logger.error(f"Error obteniendo frame de cámara {camera_id}: {e}")
            return None

    def get_camera_status(self, camera_id):
        """Obtiene estado completo de una cámara."""
        with self.lock:
            if camera_id not in self.cameras:
                return None
            
            cam_info = self.cameras[camera_id]
            video_status = video_streamer.get_camera_status(camera_id)
            alerts = video_streamer.get_active_alerts(camera_id)
            
            return {
                'id': camera_id,
                'nombre': cam_info.get('nombre'),
                'url': cam_info['url'],
                'active': cam_info['active'],
                'connection_attempts': cam_info.get('connection_attempts', 0),
                'last_success': cam_info.get('last_success'),
                'video_status': video_status,
                'active_alerts': alerts,
                'posture_data': video_streamer.get_posture_data(camera_id)
            }

    def get_all_cameras_status(self):
        """Obtiene estado de todas las cámaras."""
        with self.lock:
            status = {}
            for cam_id in self.cameras.keys():
                status[cam_id] = self.get_camera_status(cam_id)
            return status

    def get_active_cameras(self):
        """Retorna lista de cámaras activas."""
        with self.lock:
            return list(self.cameras.keys())

    def is_camera_active(self, camera_id):
        """Verifica si una cámara está activa."""
        with self.lock:
            return (camera_id in self.cameras and 
                    self.cameras[camera_id].get("active", False) and
                    video_streamer.is_camera_active(camera_id))

    def get_alert_statistics(self, camera_id=None):
        """Obtiene estadísticas de alertas."""
        return video_streamer.get_alert_statistics(camera_id)

# Instancia global del CameraManager
camera_manager = CameraManager(refresh_interval=15)