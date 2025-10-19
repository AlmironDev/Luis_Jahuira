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
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        self.lock = threading.RLock()   # <--- asegúrate que exista (evita tu error)
        self.alert_history: Dict[int, List[Dict]] = {}
        self.active_alerts: Dict[int, Dict] = {}
        self.alert_cooldown = 30  # segundos

        # MediaPipe
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_holistic = mp.solutions.holistic
        self.mp_hands = mp.solutions.hands

        # Config por defecto
        self.posture_config = {
            'max_head_tilt': 25,
            'min_neck_angle': 70,
            'hombros_min': 0.2,
            'hombros_max': 0.6,
        }
        self.alert_states: Dict[int, Dict[str, Any]] = {}

    def update_posture_config(self, new_config: Dict[str, Any]):
        with self.lock:
            self.posture_config.update(new_config)

    def start_stream(self, camera_id: int, video_source: str | int) -> bool:
        with self.lock:
            if camera_id in self.streams:
                return False
            frame_queue = queue.Queue(maxsize=1)
            self.streams[camera_id] = {
                'active': True,
                'frame_queue': frame_queue,
                'thread': None,
                'source': video_source
            }
            self.alert_states[camera_id] = {'bad_posture_start': None, 'alert_shown': False}
            t = threading.Thread(target=self._stream_worker, args=(camera_id,), daemon=True)
            self.streams[camera_id]['thread'] = t
            t.start()
            logger.info(f"Stream iniciado para cámara {camera_id}")
            return True

    def stop_stream(self, camera_id: int) -> bool:
        with self.lock:
            if camera_id not in self.streams:
                return False
            self.streams[camera_id]['active'] = False
            # thread se cierra por su bucle; no join obligatorio porque es daemon
            return True

    def get_frame(self, camera_id: int) -> Optional[bytes]:
        with self.lock:
            s = self.streams.get(camera_id)
            if not s:
                return None
            try:
                return s['frame_queue'].get_nowait()
            except queue.Empty:
                return None

    def get_recent_alerts(self, camera_id: int, limit: int = 5) -> List[Dict]:
        with self.lock:
            alerts = self.alert_history.get(camera_id, [])
            if not alerts: return []
            recent = alerts[-limit:]
            self.alert_history[camera_id] = alerts[:-len(recent)] or []
            return recent

    def _stream_worker(self, camera_id: int):
        stream = self.streams[camera_id]
        source = stream['source']
        cap = cv2.VideoCapture(source)

        with self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            refine_face_landmarks=False
        ) as holistic:
            while stream['active']:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"No se pudo leer frame de cámara {camera_id}")
                    time.sleep(1)
                    continue

                # Convertir a RGB para MediaPipe
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(image_rgb)

                # Dibujar resultados en el frame original (BGR)
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_holistic.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0,0,255), thickness=2)
                )

                self.mp_drawing.draw_landmarks(
                    frame,
                    results.left_hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(255,0,0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0,0,255), thickness=2)
                )

                self.mp_drawing.draw_landmarks(
                    frame,
                    results.right_hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0,255,255), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0,0,255), thickness=2)
                )

                # Colocar frame procesado en la cola
                if not stream['frame_queue'].full():
                    stream['frame_queue'].put(frame)

        cap.release()
        logger.info(f"Stream detenido para cámara {camera_id}")


    # -------------------------------------------------
    # Procesamiento (simplificado y robusto)
    # -------------------------------------------------
    def _process_frame(self, frame: np.ndarray, holistic, hands, camera_id: int):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        res_pose = holistic.process(image)
        res_hands = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        posture_state = PostureState.GOOD
        alerts: List[str] = []

        if res_pose.pose_landmarks:
            lms = res_pose.pose_landmarks.landmark
            head_state, head_alerts = self._check_head_posture(lms)
            posture_state = max(posture_state, head_state)
            alerts.extend(head_alerts)

            back_state, back_alerts = self._check_back_posture(lms)
            posture_state = max(posture_state, back_state)
            alerts.extend(back_alerts)

        if res_hands.multi_hand_landmarks and res_pose.pose_landmarks:
            hands_state, hands_alerts = self._check_hands_position(res_hands.multi_hand_landmarks, res_pose.pose_landmarks.landmark)
            posture_state = max(posture_state, hands_state)
            alerts.extend(hands_alerts)

        # Dibujar landmarks (si los hay) con color según estado
        color = (0,255,0) if posture_state == PostureState.GOOD else (0,255,255) if posture_state == PostureState.WARNING else (0,0,255)
        try:
            if res_pose.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    image,
                    res_pose.pose_landmarks,
                    self.mp_holistic.POSE_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=color, thickness=2, circle_radius=2),
                    mp.solutions.drawing_utils.DrawingSpec(color=color, thickness=2)
                )
            if res_hands.multi_hand_landmarks:
                for hand in res_hands.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(image, hand, self.mp_hands.HAND_CONNECTIONS)
        except Exception:
            pass

        image = self._draw_alerts(image, alerts, posture_state)

        if alerts and posture_state == PostureState.BAD:
            for a in alerts:
                self._trigger_alert(camera_id, a, AlertType.POSTURE, AlertLevel.CRITICAL)

        return image, posture_state

    # ---------- chequeos ----------
    def _check_head_posture(self, landmarks):
        alerts = []
        state = PostureState.GOOD
        try:
            nose = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.NOSE)
            le = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_EAR)
            re = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.RIGHT_EAR)
            if None not in (nose, le, re):
                head_angle = self._calculate_angle(le, nose, re)
                if abs(head_angle - 180) > self.posture_config['max_head_tilt']:
                    alerts.append(f"Inclinación anormal de cabeza: {head_angle:.1f}°")
                    state = PostureState.WARNING
        except Exception:
            pass
        return state, alerts

    def _check_back_posture(self, landmarks):
        alerts = []
        state = PostureState.GOOD
        try:
            ls = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
            lh = self._get_landmark_coords(landmarks, self.mp_holistic.PoseLandmark.LEFT_HIP)
            if None not in (ls, lh):
                angle = self._calculate_angle(lh, ls, (ls[0], ls[1] - 0.1))
                if angle < 70:
                    alerts.append("Espalda encorvada")
                    state = PostureState.BAD
        except Exception:
            pass
        return state, alerts

    def _check_hands_position(self, hands_landmarks, pose_landmarks):
        alerts = []
        state = PostureState.GOOD
        left_sh = self._get_landmark_coords(pose_landmarks, self.mp_holistic.PoseLandmark.LEFT_SHOULDER)
        right_sh = self._get_landmark_coords(pose_landmarks, self.mp_holistic.PoseLandmark.RIGHT_SHOULDER)
        if left_sh is None or right_sh is None:
            return state, alerts
        try:
            for hand in hands_landmarks:
                w = hand.landmark[self.mp_hands.HandLandmark.WRIST]
                wrist = (w.x, w.y)
                if wrist[1] < min(left_sh[1], right_sh[1]):
                    alerts.append("Manos por encima de hombros")
                    state = PostureState.WARNING
        except Exception:
            pass
        return state, alerts

    # ---------- util ----------
    def _draw_alerts(self, image, alerts, posture_state):
        y = 30
        for a in alerts:
            col = (0,0,255) if posture_state == PostureState.BAD else (0,255,255)
            cv2.putText(image, a, (20,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2, cv2.LINE_AA)
            y += 25
        status = "BUENA POSTURA" if posture_state==PostureState.GOOD else "ADVERTENCIA" if posture_state==PostureState.WARNING else "MALA POSTURA"
        col = (0,255,0) if posture_state==PostureState.GOOD else (0,255,255) if posture_state==PostureState.WARNING else (0,0,255)
        cv2.putText(image, status, (image.shape[1]-220, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2, cv2.LINE_AA)
        return image

    def _handle_posture_time(self, camera_id, posture_state):
        now = time.time()
        st = self.alert_states.get(camera_id)
        if st is None:
            return
        if posture_state == PostureState.BAD:
            if st['bad_posture_start'] is None:
                st['bad_posture_start'] = now
            elif now - st['bad_posture_start'] > 60 and not st['alert_shown']:
                self._trigger_alert(camera_id, "Mala postura prolongada", AlertType.POSTURE, AlertLevel.WARNING)
                st['alert_shown'] = True
        else:
            st['bad_posture_start'] = None
            st['alert_shown'] = False

    def _trigger_alert(self, camera_id, message, alert_type, severity):
        ts = time.time()
        data = {
            'message': message,
            'type': alert_type.name,
            'severity': severity.name,
            'timestamp': datetime.fromtimestamp(ts).isoformat()
        }
        with self.lock:
            self.alert_history.setdefault(camera_id, []).append(data)
        logger.warning(f"[{severity.name}] Cámara {camera_id}: {message}")

    @staticmethod
    def _get_landmark_coords(landmarks, landmark_type):
        try:
            lm = landmarks[landmark_type.value]
            return (lm.x, lm.y)
        except Exception:
            return None

    @staticmethod
    def _calculate_angle(a, b, c):
        if None in (a, b, c): return 0.0
        ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
        return ang + 360 if ang < 0 else ang

# Singleton instance for import
video_streamer = VideoStreamer()
