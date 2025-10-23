import cv2
import mediapipe as mp
import math
import time
import threading
from enum import Enum
from datetime import datetime

class AlertLevel(Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class PostureAlert:
    def __init__(self):
        self.alert_start_time = {}
        self.alert_level = {}
        self.last_alert_time = {}
        
    def check_alert_level(self, camera_id, angle_type, is_bad_posture):
        """Gestiona los niveles de alerta basado en el tiempo"""
        current_time = time.time()
        alert_key = f"{camera_id}_{angle_type}"
        
        if is_bad_posture:
            if alert_key not in self.alert_start_time:
                self.alert_start_time[alert_key] = current_time
                self.alert_level[alert_key] = AlertLevel.NORMAL
                return AlertLevel.NORMAL
            
            duration = current_time - self.alert_start_time[alert_key]
            
            if duration > 300:  # 5 minutos
                self.alert_level[alert_key] = AlertLevel.CRITICAL
            elif duration > 60 :  # 3 minutos
                self.alert_level[alert_key] = AlertLevel.WARNING
            else:
                self.alert_level[alert_key] = AlertLevel.NORMAL
                
            return self.alert_level[alert_key]
        else:
            # Resetear si la postura es buena
            if alert_key in self.alert_start_time:
                del self.alert_start_time[alert_key]
                del self.alert_level[alert_key]
            return AlertLevel.NORMAL

class PostureAnalyzer:
    def __init__(self):
        # Configuración MediaPipe
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        
        # Crear instancias separadas de MediaPipe para cada cámara
        self.holistic_instances = {}
        self.instance_lock = threading.Lock()
        
        # Configuración de ángulos
        self.ANGLE_TOLERANCE = 15
        self.ALERT_DELAY = 5
        
        self.ANGLE_OBJECTIVES = {
            'knee': 90,
            'hip_spine': 90,
            'elbow': 90,
            'neck': 180
        }
        
        # Sistema de alertas
        self.alert_system = PostureAlert()
        self.lock = threading.Lock()
        
        # Historial de posturas por cámara
        self.camera_posture_history = {}
        self.last_posture_data = {}

    def _get_holistic_instance(self, camera_id):
        """Obtiene o crea una instancia de MediaPipe Holistic para una cámara específica"""
        with self.instance_lock:
            if camera_id not in self.holistic_instances:
                self.holistic_instances[camera_id] = self.mp_holistic.Holistic(
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                    model_complexity=1  # Reducir complejidad para mejor performance
                )
                print(f"✅ Creada instancia MediaPipe para cámara {camera_id}")
            return self.holistic_instances[camera_id]

    def calculate_angle(self, a, b, c):
        """Calcula el ángulo entre tres puntos"""
        ang = math.degrees(
            math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
        )
        return ang + 360 if ang < 0 else ang

    def analyze_frame(self, frame, camera_id):
        """Analiza la postura en un frame y retorna frame procesado + alertas"""
        try:
            if frame is None:
                return frame, []
            
            # Obtener instancia específica para esta cámara
            holistic = self._get_holistic_instance(camera_id)
            
            # Procesar con MediaPipe
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False
            
            # Usar un timestamp único para evitar conflictos
            current_time = int(time.time() * 1000)
            
            # Procesar el frame
            results = holistic.process(image_rgb)
            
            image_rgb.flags.writeable = True
            processed_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            alerts = []

            if results.pose_landmarks:
                # Analizar ángulos
                posture_data = self._analyze_all_angles(results.pose_landmarks.landmark)
                
                if posture_data:
                    # Guardar datos de postura
                    self.last_posture_data[camera_id] = posture_data
                    
                    # Verificar postura y generar alertas
                    alerts = self._check_posture_and_generate_alerts(posture_data, camera_id)
                    
                    # Dibujar ángulos y alertas en el frame
                    processed_frame = self._draw_posture_analysis(processed_frame, posture_data, alerts)
                
                # Dibujar landmarks de MediaPipe
                self.mp_drawing.draw_landmarks(
                    processed_frame,
                    results.pose_landmarks,
                    self.mp_holistic.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
                )
            
            return processed_frame, alerts

        except Exception as e:
            print(f"❌ Error en análisis de postura para cámara {camera_id}: {e}")
            # En caso de error, retornar frame original sin procesar
            return frame, []

    def _analyze_all_angles(self, landmarks):
        """Analiza los 4 ángulos de postura"""
        try:
            # ========== ÁNGULOS 1 Y 2 (PIERNAS) ==========
            left_hip = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_HIP)
            left_knee = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_KNEE)
            left_ankle = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_ANKLE)
            
            right_hip = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_HIP)
            right_knee = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_KNEE)
            right_ankle = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_ANKLE)
            
            left_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
            right_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_SHOULDER)
            spine = [(left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2]
            
            # Ángulos de rodilla
            left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)
            
            # Ángulos cadera-columna
            left_hip_angle = self.calculate_angle(spine, left_hip, left_knee)
            right_hip_angle = self.calculate_angle(spine, right_hip, right_knee)
            
            # ========== ÁNGULO 3: BRAZOS ==========
            left_elbow = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_ELBOW)
            left_wrist = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_WRIST)
            right_elbow = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_ELBOW)
            right_wrist = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_WRIST)
            
            left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
            
            # ========== ÁNGULO 4: CUELLO ==========
            left_ear = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_EAR)
            right_ear = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_EAR)
            head = [(left_ear[0] + right_ear[0]) / 2, (left_ear[1] + right_ear[1]) / 2]
            
            left_neck_angle = self.calculate_angle(left_hip, left_shoulder, head)
            right_neck_angle = self.calculate_angle(right_hip, right_shoulder, head)
            
            return {
                'left_knee_angle': left_knee_angle,
                'right_knee_angle': right_knee_angle,
                'left_hip_angle': left_hip_angle,
                'right_hip_angle': right_hip_angle,
                'left_elbow_angle': left_elbow_angle,
                'right_elbow_angle': right_elbow_angle,
                'left_neck_angle': left_neck_angle,
                'right_neck_angle': right_neck_angle,
                'landmarks': {
                    'left_hip': left_hip, 'left_knee': left_knee, 'left_ankle': left_ankle,
                    'right_hip': right_hip, 'right_knee': right_knee, 'right_ankle': right_ankle,
                    'spine': spine, 'left_shoulder': left_shoulder, 'right_shoulder': right_shoulder,
                    'left_elbow': left_elbow, 'left_wrist': left_wrist,
                    'right_elbow': right_elbow, 'right_wrist': right_wrist,
                    'head': head
                }
            }
            
        except Exception as e:
            print(f"❌ Error analizando ángulos: {e}")
            return None

    def _get_landmark_coords(self, landmarks, landmark_type):
        """Obtiene coordenadas de un landmark"""
        return [landmarks[landmark_type.value].x, landmarks[landmark_type.value].y]

    def _check_posture_and_generate_alerts(self, posture_data, camera_id):
        """Verifica la postura y genera alertas"""
        alerts = []
        current_time = time.time()
        
        # Verificar cada tipo de ángulo
        angle_checks = [
            ('rodilla_izq', posture_data['left_knee_angle'], self.ANGLE_OBJECTIVES['knee']),
            ('rodilla_der', posture_data['right_knee_angle'], self.ANGLE_OBJECTIVES['knee']),
            ('cadera_columna_izq', posture_data['left_hip_angle'], self.ANGLE_OBJECTIVES['hip_spine']),
            ('cadera_columna_der', posture_data['right_hip_angle'], self.ANGLE_OBJECTIVES['hip_spine']),
            ('codo_izq', posture_data['left_elbow_angle'], self.ANGLE_OBJECTIVES['elbow']),
            ('codo_der', posture_data['right_elbow_angle'], self.ANGLE_OBJECTIVES['elbow']),
            ('cuello_izq', posture_data['left_neck_angle'], self.ANGLE_OBJECTIVES['neck']),
            ('cuello_der', posture_data['right_neck_angle'], self.ANGLE_OBJECTIVES['neck'])
        ]
        
        for angle_type, angle_value, target in angle_checks:
            is_bad_posture = not ((target - self.ANGLE_TOLERANCE) <= angle_value <= (target + self.ANGLE_TOLERANCE))
            alert_level = self.alert_system.check_alert_level(camera_id, angle_type, is_bad_posture)
            
            if alert_level != AlertLevel.NORMAL:
                alerts.append({
                    'camera_id': camera_id,
                    'angle_type': angle_type,
                    'angle_value': angle_value,
                    'target_angle': target,
                    'alert_level': alert_level,
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts

    def _draw_posture_analysis(self, frame, posture_data, alerts):
        """Dibuja el análisis de postura en el frame"""
        try:
            h, w, _ = frame.shape
            landmarks = posture_data['landmarks']
            
            def to_pixels(point):
                return int(point[0] * w), int(point[1] * h)
            
            # Colores para diferentes ángulos
            colors = {
                'legs': (0, 255, 255),      # Amarillo
                'hip_spine': (255, 255, 0), # Cian
                'arms': (255, 0, 255),      # Magenta
                'neck': (0, 255, 0)         # Verde
            }
            
            # Dibujar líneas de ángulos
            # Piernas
            cv2.line(frame, to_pixels(landmarks['left_hip']), to_pixels(landmarks['left_knee']), colors['legs'], 2)
            cv2.line(frame, to_pixels(landmarks['left_knee']), to_pixels(landmarks['left_ankle']), colors['legs'], 2)
            cv2.line(frame, to_pixels(landmarks['right_hip']), to_pixels(landmarks['right_knee']), colors['legs'], 2)
            cv2.line(frame, to_pixels(landmarks['right_knee']), to_pixels(landmarks['right_ankle']), colors['legs'], 2)
            
            # Cadera-columna
            cv2.line(frame, to_pixels(landmarks['spine']), to_pixels(landmarks['left_hip']), colors['hip_spine'], 2)
            cv2.line(frame, to_pixels(landmarks['left_hip']), to_pixels(landmarks['left_knee']), colors['hip_spine'], 2)
            cv2.line(frame, to_pixels(landmarks['spine']), to_pixels(landmarks['right_hip']), colors['hip_spine'], 2)
            cv2.line(frame, to_pixels(landmarks['right_hip']), to_pixels(landmarks['right_knee']), colors['hip_spine'], 2)
            
            # Brazos
            cv2.line(frame, to_pixels(landmarks['left_shoulder']), to_pixels(landmarks['left_elbow']), colors['arms'], 2)
            cv2.line(frame, to_pixels(landmarks['left_elbow']), to_pixels(landmarks['left_wrist']), colors['arms'], 2)
            cv2.line(frame, to_pixels(landmarks['right_shoulder']), to_pixels(landmarks['right_elbow']), colors['arms'], 2)
            cv2.line(frame, to_pixels(landmarks['right_elbow']), to_pixels(landmarks['right_wrist']), colors['arms'], 2)
            
            # Cuello
            cv2.line(frame, to_pixels(landmarks['left_hip']), to_pixels(landmarks['left_shoulder']), colors['neck'], 2)
            cv2.line(frame, to_pixels(landmarks['left_shoulder']), to_pixels(landmarks['head']), colors['neck'], 2)
            cv2.line(frame, to_pixels(landmarks['right_hip']), to_pixels(landmarks['right_shoulder']), colors['neck'], 2)
            cv2.line(frame, to_pixels(landmarks['right_shoulder']), to_pixels(landmarks['head']), colors['neck'], 2)
            
            # Mostrar alertas en pantalla
            y_offset = 30
            for i, alert in enumerate(alerts[:5]):  # Mostrar máximo 5 alertas
                color = (0, 165, 255) if alert['alert_level'] == AlertLevel.WARNING else (0, 0, 255)
                alert_text = f"{alert['alert_level'].value}: {alert['angle_type']} ({alert['angle_value']:.1f}°)"
                cv2.putText(frame, alert_text, (10, y_offset + i*25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            return frame
            
        except Exception as e:
            print(f"❌ Error dibujando análisis: {e}")
            return frame

    def get_alerts_summary(self, camera_id):
        """Obtiene resumen de alertas para una cámara"""
        warnings = 0
        criticals = 0
        
        for key, level in self.alert_system.alert_level.items():
            if key.startswith(f"{camera_id}_"):
                if level == AlertLevel.WARNING:
                    warnings += 1
                elif level == AlertLevel.CRITICAL:
                    criticals += 1
        
        return {
            'warnings': warnings,
            'criticals': criticals,
            'total_alerts': warnings + criticals
        }

    def cleanup_camera(self, camera_id):
        """Limpia los recursos de MediaPipe para una cámara específica"""
        with self.instance_lock:
            if camera_id in self.holistic_instances:
                self.holistic_instances[camera_id].close()
                del self.holistic_instances[camera_id]
                print(f"🛑 Instancia MediaPipe limpiada para cámara {camera_id}")

# Instancia global del analizador de postura
posture_analyzer = PostureAnalyzer()