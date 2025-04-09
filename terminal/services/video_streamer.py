import cv2
import mediapipe as mp
import math
import time
import threading
import queue
import logging
from enum import IntEnum, auto
from typing import Optional, Dict, Tuple, List, Any
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VideoStreamer')

class PostureState(IntEnum):
    GOOD = auto()
    WARNING = auto()
    BAD = auto()

class AlertType(IntEnum):
    POSTURE = auto()
    HANDS = auto()
    MOVEMENT = auto()

class AlertLevel(IntEnum):
    INFO = auto()
    WARNING = auto()
    CRITICAL = auto()

class VideoStreamer:
    def __init__(self):
        self.streams: Dict[int, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.alert_history: Dict[int, List[Dict]] = {}  # Historial de alertas por cámara
        self.active_alerts: Dict[int, Dict] = {}       # Alertas activas por cámara
        self.alert_cooldown = 30  # Segundos entre alertas del mismo tipo

        # Configuración de MediaPipe
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_holistic = mp.solutions.holistic
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose

        # Configuración de postura con valores por defecto
        self.posture_config = {
            'angulo_min': 45,
            'angulo_max': 135,
            'hombros_min': 0.5,
            'hombros_max': 1.5,
            'manos_min': 30,
            'manos_max': 150,
            'max_neck_angle': 45,
            'min_leg_angle': 160,
            'max_head_tilt': 20,
            'min_neck_angle': 140
        }
        
        # Estado de alertas
        self.alert_states: Dict[int, Dict[str, Any]] = {}
        self.db_conn = None  # Conexión a base de datos (opcional)

    def update_posture_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración de postura"""
        with self.lock:
            self.posture_config.update(new_config)

    def start_stream(self, camera_id: int, video_source: str) -> bool:
        """Inicia un stream de video"""
        with self.lock:
            if camera_id in self.streams:
                return False
                
            self.streams[camera_id] = {
                'active': True,
                'frame_queue': queue.Queue(maxsize=1),
                'thread': None,
                'source': video_source
            }
            
            self.alert_states[camera_id] = {
                'bad_posture_start': None,
                'alert_shown': False
            }
            
            thread = threading.Thread(
                target=self._stream_worker,
                args=(camera_id,),
                daemon=True
            )
            self.streams[camera_id]['thread'] = thread
            thread.start()
            
            logger.info(f"Stream iniciado para cámara {camera_id}")
            return True

    def stop_stream(self, camera_id: int) -> bool:
        """Detiene un stream de video"""
        with self.lock:
            if camera_id not in self.streams:
                return False
                
            self.streams[camera_id]['active'] = False
            if self.streams[camera_id]['thread']:
                self.streams[camera_id]['thread'].join(timeout=2)
            
            if camera_id in self.alert_states:
                del self.alert_states[camera_id]
            
            del self.streams[camera_id]
            logger.info(f"Stream detenido para cámara {camera_id}")
            return True

    def get_frame(self, camera_id: int) -> Optional[bytes]:
        """Obtiene el último frame procesado"""
        with self.lock:
            if camera_id not in self.streams:
                return None
                
            try:
                return self.streams[camera_id]['frame_queue'].get_nowait()
            except queue.Empty:
                return None

    def get_recent_alerts(self, camera_id: int, limit: int = 5) -> List[Dict]:
        """Obtiene las alertas recientes para una cámara"""
        with self.lock:
            if camera_id not in self.alert_history:
                return []
            return self.alert_history[camera_id][-limit:]

    def _stream_worker(self, camera_id: int) -> None:
        """Procesa el stream de video"""
        stream_info = self.streams[camera_id]
        
        # Inicializar modelos MediaPipe
        holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        hands = self.mp_hands.Hands(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            max_num_hands=2
        )
        
        # Inicializar VideoCapture
        cap = cv2.VideoCapture(stream_info['source'])
        
        if not cap.isOpened():
            logger.error(f"No se pudo abrir el video source para cámara {camera_id}")
            holistic.close()
            hands.close()
            return
        
        try:
            while stream_info['active']:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Error al leer frame de cámara {camera_id}, reintentando...")
                    time.sleep(0.1)
                    continue
                
                try:
                    # Procesar frame
                    processed_frame, posture_state = self._process_frame(frame, holistic, hands, camera_id)
                    _, buffer = cv2.imencode('.jpg', processed_frame)
                    
                    # Actualizar cola de frames
                    with self.lock:
                        if stream_info['frame_queue'].full():
                            try:
                                stream_info['frame_queue'].get_nowait()
                            except queue.Empty:
                                pass
                        
                        stream_info['frame_queue'].put(buffer.tobytes())
                        self._handle_posture_time(camera_id, posture_state)
                
                except Exception as e:
                    logger.error(f"Error procesando frame: {str(e)}")
                    time.sleep(0.1)
        
        finally:
            # Limpieza de recursos
            cap.release()
            holistic.close()
            hands.close()
            logger.info(f"Stream worker terminado para cámara {camera_id}")

    def _process_frame(self, frame: np.ndarray, holistic, hands, camera_id: int) -> Tuple[np.ndarray, PostureState]:
        """Procesa un frame individual con detección de postura"""
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        results = {
            'holistic': holistic.process(image),
            'hands': hands.process(image)
        }
        
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        posture_state = PostureState.GOOD
        alerts = []
        
        if results['holistic'].pose_landmarks:
            landmarks = results['holistic'].pose_landmarks.landmark
            
            # 1. Detección de postura de cabeza/cuello
            head_state, head_alerts = self._check_head_posture(landmarks)
            alerts.extend(head_alerts)
            posture_state = max(posture_state, head_state)
            
            # 2. Detección de postura de hombros
            shoulders_state, shoulders_alerts = self._check_shoulders_posture(landmarks)
            alerts.extend(shoulders_alerts)
            posture_state = max(posture_state, shoulders_state)
            
            # 3. Detección de postura de espalda
            back_state, back_alerts = self._check_back_posture(landmarks)
            alerts.extend(back_alerts)
            posture_state = max(posture_state, back_state)
            
            # 4. Detección de manos (si están en frame)
            if results['hands'].multi_hand_landmarks:
                hands_state, hands_alerts = self._check_hands_position(
                    results['hands'].multi_hand_landmarks,
                    landmarks
                )
                alerts.extend(hands_alerts)
                posture_state = max(posture_state, hands_state)
            
            # Configurar colores según el estado de postura
            if posture_state == PostureState.BAD:
                landmark_color = (50, 50, 255)  # BGR - Rojo
                connection_color = (0, 0, 255)   # BGR - Rojo más intenso
            elif posture_state == PostureState.WARNING:
                landmark_color = (0, 255, 255)   # BGR - Amarillo
                connection_color = (0, 200, 200) # BGR - Amarillo menos intenso
            else:
                landmark_color = (50, 255, 50)  # BGR - Verde
                connection_color = (100, 200, 100) # BGR - Verde menos intenso
            
            # Dibujar landmarks y conexiones con los colores adecuados
            self.mp_drawing.draw_landmarks(
                image, 
                results['holistic'].pose_landmarks, 
                self.mp_holistic.POSE_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(color=landmark_color, thickness=2, circle_radius=2),
                mp.solutions.drawing_utils.DrawingSpec(color=connection_color, thickness=2, circle_radius=1)
            )
        
        # Dibujar landmarks de manos (siempre en color azul)
        if results['hands'].multi_hand_landmarks:
            for hand_landmarks in results['hands'].multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    image, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2),  # Azul
                    mp.solutions.drawing_utils.DrawingSpec(color=(200, 0, 0), thickness=2, circle_radius=1)    # Azul oscuro
                )
        
        # Dibujar alertas en el frame
        image = self._draw_alerts(image, alerts, posture_state)
        
        # Disparar alertas si es necesario
        if alerts and posture_state == PostureState.BAD:
            for alert in alerts:
                self._trigger_alert(
                    camera_id=camera_id,
                    message=alert,
                    alert_type=AlertType.POSTURE,
                    severity=AlertLevel.CRITICAL if posture_state == PostureState.BAD else AlertLevel.WARNING
                )
        
        return image, posture_state

    def _check_head_posture(self, landmarks) -> Tuple[PostureState, List[str]]:
        """Verifica la postura de la cabeza/cuello"""
        nose = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.NOSE)
        left_ear = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_EAR)
        right_ear = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_EAR)
        left_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
        right_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_SHOULDER)
        
        alerts = []
        state = PostureState.GOOD
        
        if None not in (nose, left_ear, right_ear, left_shoulder, right_shoulder):
            # Ángulo de inclinación de la cabeza
            head_angle = self._calculate_angle(left_ear, nose, right_ear)
            if abs(head_angle - 180) > self.posture_config['max_head_tilt']:
                alerts.append(f"Inclinación anormal de cabeza: {head_angle:.1f}°")
                state = PostureState.WARNING
            
            # Distancia cabeza-hombros
            neck_angle_left = self._calculate_angle(left_shoulder, left_ear, nose)
            neck_angle_right = self._calculate_angle(right_shoulder, right_ear, nose)
            
            if neck_angle_left < self.posture_config['min_neck_angle'] or neck_angle_right < self.posture_config['min_neck_angle']:
                alerts.append("Cabeza demasiado adelantada (postura de tortuga)")
                state = PostureState.BAD
        
        return state, alerts

    def _check_shoulders_posture(self, landmarks) -> Tuple[PostureState, List[str]]:
        """Verifica la postura de los hombros"""
        left_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
        right_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_SHOULDER)
        
        alerts = []
        state = PostureState.GOOD
        
        if None not in (left_shoulder, right_shoulder):
            shoulder_distance = self._calculate_distance(left_shoulder, right_shoulder)
            
            if shoulder_distance > self.posture_config['hombros_max']:
                alerts.append(f"Hombros muy separados: {shoulder_distance:.2f}m")
                state = PostureState.WARNING
            elif shoulder_distance < self.posture_config['hombros_min']:
                alerts.append(f"Hombros muy juntos: {shoulder_distance:.2f}m")
                state = PostureState.WARNING
            
            # Verificar si un hombro está más alto que el otro
            y_diff = abs(left_shoulder[1] - right_shoulder[1])
            if y_diff > 0.05:  # Diferencia significativa en altura
                higher = "izquierdo" if left_shoulder[1] < right_shoulder[1] else "derecho"
                alerts.append(f"Hombro {higher} más alto que el otro")
                state = max(state, PostureState.WARNING)
        
        return state, alerts

    def _check_back_posture(self, landmarks) -> Tuple[PostureState, List[str]]:
        """Verifica la postura de la espalda"""
        left_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
        right_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_SHOULDER)
        left_hip = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_HIP)
        right_hip = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_HIP)
        
        alerts = []
        state = PostureState.GOOD
        
        if None not in (left_shoulder, right_shoulder, left_hip, right_hip):
            # Ángulo de inclinación de la espalda
            back_angle_left = self._calculate_angle(left_hip, left_shoulder, (left_shoulder[0], left_shoulder[1] - 0.1))  # Punto imaginario arriba
            back_angle_right = self._calculate_angle(right_hip, right_shoulder, (right_shoulder[0], right_shoulder[1] - 0.1))
            
            if back_angle_left < 70 or back_angle_right < 70:
                alerts.append("Espalda encorvada")
                state = PostureState.BAD
        
        return state, alerts

    def _check_hands_position(self, hand_landmarks_list, pose_landmarks) -> Tuple[PostureState, List[str]]:
        """Verifica la posición de las manos"""
        alerts = []
        state = PostureState.GOOD
        
        left_shoulder = self._get_landmark_coords(pose_landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
        right_shoulder = self._get_landmark_coords(pose_landmarks, self.mp_holistic.PoseLandmark.RIGHT_SHOULDER)
        
        if left_shoulder is None or right_shoulder is None:
            return state, alerts
        
        for hand_landmarks in hand_landmarks_list:
            # Obtener coordenadas de la muñeca (punto de referencia para la mano)
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            wrist_pos = (wrist.x, wrist.y)
            
            # Calcular distancia a los hombros
            dist_left = self._calculate_distance(wrist_pos, left_shoulder)
            dist_right = self._calculate_distance(wrist_pos, right_shoulder)
            
            # Verificar si las manos están demasiado altas (por encima de los hombros)
            if wrist.y < min(left_shoulder[1], right_shoulder[1]):
                alerts.append("Manos levantadas por encima de los hombros")
                state = max(state, PostureState.WARNING)
            
            # Verificar si las manos están demasiado lejos del cuerpo
            min_dist = min(dist_left, dist_right)
            if min_dist > 0.3:  # Valor empírico
                alerts.append("Manos demasiado alejadas del cuerpo")
                state = max(state, PostureState.WARNING)
        
        return state, alerts

    def _draw_alerts(self, image: np.ndarray, alerts: List[str], posture_state: PostureState) -> np.ndarray:
        """Dibuja las alertas en el frame de video"""
        # Fondo para texto
        y_offset = 30
        for alert in alerts:
            text_size = cv2.getTextSize(alert, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(
                image,
                (10, y_offset - 25),
                (20 + text_size[0], y_offset + 5),
                (0, 0, 0), -1  # Fondo negro
            )
            
            # Color según severidad
            color = (0, 0, 255) if posture_state == PostureState.BAD else (0, 255, 255)
            
            cv2.putText(
                image, alert,
                (20, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                color, 2, cv2.LINE_AA
            )
            y_offset += 30
        
        # Indicador de estado en esquina
        status_text = "BUENA POSTURA"
        status_color = (0, 255, 0)
        if posture_state == PostureState.WARNING:
            status_text = "ADVERTENCIA"
            status_color = (0, 255, 255)
        elif posture_state == PostureState.BAD:
            status_text = "MALA POSTURA"
            status_color = (0, 0, 255)
        
        cv2.putText(
            image, status_text,
            (image.shape[1] - 200, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
            status_color, 2, cv2.LINE_AA
        )
        
        return image

    def _handle_posture_time(self, camera_id: int, posture_state: PostureState):
        """Maneja el tiempo acumulado en mala postura"""
        current_time = time.time()
        alert_state = self.alert_states[camera_id]
        
        if posture_state == PostureState.BAD:
            if alert_state['bad_posture_start'] is None:
                alert_state['bad_posture_start'] = current_time
                alert_state['alert_shown'] = False
            else:
                duration = current_time - alert_state['bad_posture_start']
                
                # Alertas progresivas según el tiempo
                if duration > 300 and not alert_state['alert_shown']:  # 5 minutos
                    self._trigger_alert(
                        camera_id=camera_id,
                        message="Mala postura durante más de 5 minutos continuos",
                        alert_type=AlertType.POSTURE,
                        severity=AlertLevel.CRITICAL
                    )
                    alert_state['alert_shown'] = True
                elif duration > 60:  # 1 minuto
                    self._trigger_alert(
                        camera_id=camera_id,
                        message="Mala postura durante más de 1 minuto",
                        alert_type=AlertType.POSTURE,
                        severity=AlertLevel.WARNING
                    )
        else:
            # Resetear temporizador si la postura es buena
            if alert_state['bad_posture_start'] is not None:
                duration = current_time - alert_state['bad_posture_start']
                if duration > 60:
                    logger.info(f"Cámara {camera_id}: Postura corregida después de {duration:.1f} segundos")
                
                alert_state['bad_posture_start'] = None
                alert_state['alert_shown'] = False

    def _trigger_alert(self, camera_id: int, message: str, alert_type: AlertType, 
                      severity: AlertLevel = AlertLevel.WARNING) -> None:
        """Dispara una alerta y la maneja adecuadamente"""
        timestamp = time.time()
        alert_key = f"{alert_type.name}_{severity.name}"
        
        # Verificar si ya hay una alerta similar reciente
        if alert_key in self.active_alerts.get(camera_id, {}):
            last_alert = self.active_alerts[camera_id][alert_key]
            if timestamp - last_alert['timestamp'] < self.alert_cooldown:
                return  # Ignorar alertas muy seguidas del mismo tipo
        
        # Registrar la alerta
        alert_data = {
            'message': message,
            'type': alert_type,
            'severity': severity,
            'timestamp': timestamp,
            'camera_id': camera_id
        }
        
        # Actualizar estructuras de datos
        with self.lock:
            if camera_id not in self.alert_history:
                self.alert_history[camera_id] = []
            self.alert_history[camera_id].append(alert_data)
            
            if camera_id not in self.active_alerts:
                self.active_alerts[camera_id] = {}
            self.active_alerts[camera_id][alert_key] = alert_data
        
        # Loggear la alerta
        logger.warning(f"ALERTA [{severity.name}] cámara {camera_id}: {message}")
        
        # Guardar en la base de datos si hay conexión
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                    INSERT INTO alertas (id_camara, mensaje, tipo, severidad, fecha)
                    VALUES (?, ?, ?, ?, ?)
                ''', (camera_id, message, alert_type.name, severity.name, 
                      time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))))
                self.db_conn.commit()
                logger.info(f"Alerta guardada en BD para cámara {camera_id}")
            except Exception as e:
                logger.error(f"Error al guardar alerta en BD: {str(e)}")

    @staticmethod
    def _get_landmark_coords(landmarks, landmark_type) -> Optional[Tuple[float, float]]:
        """Obtiene coordenadas de un landmark"""
        try:
            landmark = landmarks[landmark_type.value]
            return (landmark.x, landmark.y)
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def _calculate_angle(a: Optional[Tuple[float, float]], 
                        b: Optional[Tuple[float, float]], 
                        c: Optional[Tuple[float, float]]) -> float:
        """Calcula el ángulo entre tres puntos"""
        if None in (a, b, c):
            return 0.0
            
        ang = math.degrees(
            math.atan2(c[1] - b[1], c[0] - b[0]) - 
            math.atan2(a[1] - b[1], a[0] - b[0])
        )
        return ang + 360 if ang < 0 else ang

    @staticmethod
    def _calculate_distance(a: Optional[Tuple[float, float]], 
                          b: Optional[Tuple[float, float]]) -> float:
        """Calcula la distancia entre dos puntos"""
        if None in (a, b):
            return 0.0
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


# Ejemplo de uso
if __name__ == "__main__":
    streamer = VideoStreamer()
    
    # Iniciar stream con la cámara web (id 0)
    streamer.start_stream(0, 0)
    
    try:
        while True:
            # Obtener frame
            frame = streamer.get_frame(0)
            if frame is not None:
                cv2.imshow('Posture Monitor', cv2.imdecode(frame, 1))
            
            # Mostrar alertas recientes
            recent_alerts = streamer.get_recent_alerts(0)
            if recent_alerts:
                print("\nAlertas recientes:")
                for alert in recent_alerts:
                    print(f"[{time.strftime('%H:%M:%S', time.localtime(alert['timestamp']))}] {alert['message']}")
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.1)
    
    finally:
        streamer.stop_stream(0)
        cv2.destroyAllWindows()