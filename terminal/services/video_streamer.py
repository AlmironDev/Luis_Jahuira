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

class VideoStreamer:
    def __init__(self):
        self.streams: Dict[int, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
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
            # Valores fijos para el análisis de postura
            'max_neck_angle': 45,
            'min_leg_angle': 160
        }
        
        # Estado de alertas
        self.alert_states: Dict[int, Dict[str, Any]] = {}

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
        
        # Inicializar VideoCapture (sin context manager)
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
                        self._handle_posture_alerts(camera_id, posture_state)
                
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
            
            # Obtener puntos clave para análisis de postura
            left_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
            right_shoulder = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_SHOULDER)
            nose = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.NOSE)
            
            # Calcular métricas de postura
            if None not in (left_shoulder, right_shoulder, nose):
                neck_angle = self._calculate_angle(left_shoulder, nose, right_shoulder)
                shoulder_distance = self._calculate_distance(left_shoulder, right_shoulder)
                
                # Determinar estado de postura
                if neck_angle > self.posture_config['max_neck_angle']:
                    alerts.append(f"Ángulo de cuello alto: {neck_angle:.1f}°")
                    posture_state = PostureState.BAD
                elif shoulder_distance > self.posture_config['hombros_max']:
                    alerts.append(f"Hombros muy separados: {shoulder_distance:.2f}m")
                    posture_state = max(posture_state, PostureState.WARNING)
                elif shoulder_distance < self.posture_config['hombros_min']:
                    alerts.append(f"Hombros muy juntos: {shoulder_distance:.2f}m")
                    posture_state = max(posture_state, PostureState.WARNING)
                
                # Configurar colores según el estado de postura
                if posture_state == PostureState.BAD:
                    # Rojo para mala postura
                    landmark_color = (50, 50, 255)  # BGR - Rojo
                    connection_color = (0, 0, 255)   # BGR - Rojo más intenso
                elif posture_state == PostureState.WARNING:
                    # Amarillo para advertencia
                    landmark_color = (0, 255, 255)   # BGR - Amarillo
                    connection_color = (0, 200, 200) # BGR - Amarillo menos intenso
                else:
                    # Verde para buena postura
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
        
        # Mostrar alertas si es necesario
        for i, alert in enumerate(alerts):
            cv2.putText(
                image, alert, 
                (50, 50 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 0, 255), 2, cv2.LINE_AA  # Texto en rojo
            )
        
        return image, posture_state

    def _handle_posture_alerts(self, camera_id: int, posture_state: PostureState) -> None:
        """Maneja las alertas de postura"""
        alert_state = self.alert_states[camera_id]
        current_time = time.time()
        
        if posture_state == PostureState.BAD:
            if alert_state['bad_posture_start'] is None:
                alert_state['bad_posture_start'] = current_time
                alert_state['alert_shown'] = False
            elif not alert_state['alert_shown'] and current_time - alert_state['bad_posture_start'] > 5:
                self._trigger_alert(camera_id, "Mala postura detectada")
                alert_state['alert_shown'] = True
        else:
            alert_state['bad_posture_start'] = None
            alert_state['alert_shown'] = False

    def _trigger_alert(self, camera_id: int, message: str) -> None:
        """Dispara una alerta"""
        logger.warning(f"ALERTA cámara {camera_id}: {message}")

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