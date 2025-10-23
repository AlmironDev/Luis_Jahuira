import cv2
import threading
import time
import numpy as np
from flask import Response
from services.posture_analyzer import posture_analyzer

class VideoStreamer:
    def __init__(self):
        self.cameras = {}
        self.lock = threading.Lock()
        self.running_threads = {}
        
        # Eliminada la configuración de Face Mesh
        # Sistema de alertas en tiempo real
        self.active_alerts = {}
        self.alert_history = {}

    def start_camera(self, cam_id, url):
        """Inicia el hilo de streaming para la cámara con análisis de postura"""
        with self.lock:
            if cam_id in self.cameras:
                print(f"⚠️ Cámara {cam_id} ya está en ejecución")
                return
            
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                print(f"❌ No se pudo abrir la cámara {cam_id}")
                return

            # Configuración para bajo latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FPS, 15)
            
            self.cameras[cam_id] = {
                "cap": cap, 
                "frame": None, 
                "active": True,
                "last_update": time.time(),
                "alerts": [],
                "posture_data": None  # Para almacenar datos de postura
            }
            
            # Iniciar hilo de procesamiento
            self.running_threads[cam_id] = True
            t = threading.Thread(target=self._process_camera_feed, args=(cam_id,), daemon=True)
            t.start()
            print(f"✅ VideoStreamer: Cámara {cam_id} iniciada con análisis de postura")

    def _process_camera_feed(self, cam_id):
        """Procesa los frames de la cámara con análisis de postura"""
        cap = self.cameras[cam_id]["cap"]
        frame_count = 0
        process_every_n_frames = 2  # Procesar cada 2 frames para mejor performance
        
        while self.running_threads.get(cam_id, False):
            try:
                ret, frame = cap.read()
                if not ret:
                    print(f"⚠️ VideoStreamer: No se pudo leer frame de cámara {cam_id}")
                    time.sleep(0.1)
                    continue

                frame_count += 1
                
                # Aplicar análisis de postura cada N frames
                if frame_count % process_every_n_frames == 0:
                    processed_frame, alerts = posture_analyzer.analyze_frame(frame, cam_id)
                    
                    # Actualizar alertas activas y datos de postura
                    with self.lock:
                        self.cameras[cam_id]["alerts"] = alerts
                        self.cameras[cam_id]["frame"] = processed_frame
                        self.cameras[cam_id]["last_update"] = time.time()
                        
                        # Almacenar datos de postura para estadísticas
                        if hasattr(posture_analyzer, 'last_posture_data'):
                            self.cameras[cam_id]["posture_data"] = posture_analyzer.last_posture_data
                        
                        # Gestionar alertas críticas/warning
                        self._update_active_alerts(cam_id, alerts)
                        
                else:
                    # Usar el frame anterior procesado para mantener fluidez
                    with self.lock:
                        previous_frame = self.cameras[cam_id].get("frame")
                        if previous_frame is not None:
                            self.cameras[cam_id]["frame"] = previous_frame

            except Exception as e:
                print(f"❌ VideoStreamer: Error en cámara {cam_id}: {e}")
                time.sleep(0.1)

    def _update_active_alerts(self, cam_id, alerts):
        """Actualiza el estado de alertas activas"""
        critical_alerts = [a for a in alerts if a['alert_level'].value == 'CRITICAL']
        warning_alerts = [a for a in alerts if a['alert_level'].value == 'WARNING']
        
        if critical_alerts or warning_alerts:
            self.active_alerts[cam_id] = {
                'critical': critical_alerts,
                'warning': warning_alerts,
                'last_alert': time.time(),
                'total_critical': len(critical_alerts),
                'total_warning': len(warning_alerts)
            }
            
            # Guardar en historial para estadísticas
            self._save_to_alert_history(cam_id, alerts)
        else:
            # Limpiar alertas si no hay ninguna
            if cam_id in self.active_alerts:
                del self.active_alerts[cam_id]

    def _save_to_alert_history(self, cam_id, alerts):
        """Guarda alertas en el historial para análisis temporal"""
        current_time = time.time()
        if cam_id not in self.alert_history:
            self.alert_history[cam_id] = []
        
        # Agregar nuevas alertas al historial
        for alert in alerts:
            if alert['alert_level'].value in ['CRITICAL', 'WARNING']:
                self.alert_history[cam_id].append({
                    'timestamp': current_time,
                    'alert': alert
                })
        
        # Limpiar historial antiguo (mantener solo últimas 24 horas)
        twenty_four_hours_ago = current_time - (24 * 3600)
        self.alert_history[cam_id] = [
            entry for entry in self.alert_history[cam_id] 
            if entry['timestamp'] > twenty_four_hours_ago
        ]

    def get_frame_with_alerts(self, camera_id):
        """Obtiene frame procesado con información de alertas"""
        with self.lock:
            cam_data = self.cameras.get(camera_id)
            if not cam_data:
                return None, []
            
            frame = cam_data.get("frame")
            alerts = cam_data.get("alerts", [])
            return frame, alerts

    def get_posture_data(self, camera_id):
        """Obtiene los datos de postura actuales de una cámara"""
        with self.lock:
            cam_data = self.cameras.get(camera_id)
            if not cam_data:
                return None
            return cam_data.get("posture_data")

    def get_active_alerts(self, camera_id=None):
        """Obtiene alertas activas"""
        with self.lock:
            if camera_id:
                return self.active_alerts.get(camera_id, {})
            else:
                return self.active_alerts

    def get_alert_statistics(self, camera_id=None, hours=24):
        """Obtiene estadísticas de alertas"""
        with self.lock:
            time_threshold = time.time() - (hours * 3600)
            stats = {
                'total_alerts': 0,
                'critical_alerts': 0,
                'warning_alerts': 0,
                'alert_trend': [],
                'most_common_angles': {}
            }
            
            target_history = self.alert_history
            if camera_id and camera_id in self.alert_history:
                target_history = {camera_id: self.alert_history[camera_id]}
            elif camera_id:
                return stats
            
            angle_counts = {}
            
            for cam_id, history in target_history.items():
                for entry in history:
                    if entry['timestamp'] > time_threshold:
                        alert = entry['alert']
                        stats['total_alerts'] += 1
                        
                        if alert['alert_level'].value == 'CRITICAL':
                            stats['critical_alerts'] += 1
                        else:
                            stats['warning_alerts'] += 1
                        
                        # Contar por tipo de ángulo
                        angle_type = alert['angle_type']
                        angle_counts[angle_type] = angle_counts.get(angle_type, 0) + 1
            
            # Ordenar ángulos más comunes
            stats['most_common_angles'] = dict(
                sorted(angle_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            )
            
            return stats
        
    def stop_stream(self, cam_id):
        """Detiene el streaming de una cámara."""
        with self.lock:
            if cam_id in self.running_threads:
                self.running_threads[cam_id] = False
            
            if cam_id in self.cameras:
                cam = self.cameras[cam_id]
                if cam["cap"] and cam["cap"].isOpened():
                    cam["cap"].release()
                del self.cameras[cam_id]
                
                # Limpiar alertas de esta cámara
                if cam_id in self.active_alerts:
                    del self.active_alerts[cam_id]
                
                # Limpiar instancia de MediaPipe
                posture_analyzer.cleanup_camera(cam_id)
                    
                print(f"🛑 VideoStreamer: Cámara {cam_id} detenida")

    def is_camera_active(self, cam_id):
        """Verifica si una cámara está activa en VideoStreamer."""
        with self.lock:
            cam = self.cameras.get(cam_id)
            if not cam:
                return False
            # Considerar inactiva si no ha actualizado en 15 segundos
            return time.time() - cam.get("last_update", 0) < 15

    def get_camera_status(self, cam_id):
        """Obtiene estado completo de una cámara"""
        with self.lock:
            cam_data = self.cameras.get(cam_id)
            if not cam_data:
                return None
            
            alerts = self.active_alerts.get(cam_id, {})
            posture_data = cam_data.get("posture_data", {})
            
            return {
                'active': True,
                'last_update': cam_data['last_update'],
                'alerts': alerts,
                'posture_angles': self._extract_angles(posture_data),
                'frame_available': cam_data['frame'] is not None
            }

    def _extract_angles(self, posture_data):
        """Extrae los ángulos de los datos de postura"""
        if not posture_data:
            return {}
        
        return {
            'left_knee': posture_data.get('left_knee_angle'),
            'right_knee': posture_data.get('right_knee_angle'),
            'left_hip': posture_data.get('left_hip_angle'),
            'right_hip': posture_data.get('right_hip_angle'),
            'left_elbow': posture_data.get('left_elbow_angle'),
            'right_elbow': posture_data.get('right_elbow_angle'),
            'left_neck': posture_data.get('left_neck_angle'),
            'right_neck': posture_data.get('right_neck_angle')
        }

    def get_all_cameras_status(self):
        """Obtiene estado de todas las cámaras"""
        with self.lock:
            status = {}
            for cam_id in self.cameras.keys():
                status[cam_id] = self.get_camera_status(cam_id)
            return status

# Instancia global del VideoStreamer
video_streamer = VideoStreamer()