import math
import cv2
from base_detector import BaseDetector
import mediapipe as mp

class PostureDetector(BaseDetector):
    def __init__(self, config):
        super().__init__(config)
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=config['min_detection_confidence'],
            min_tracking_confidence=config['min_tracking_confidence']
        )
        self.bad_posture_start_time = None
        self.alert_shown = False

    def process_frame(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        self.results = self.pose.process(image)
        image.flags.writeable = True
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    def draw_results(self, frame):
        if self.results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, self.results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
            )
        return frame

    def check_conditions(self):
        if not self.results.pose_landmarks:
            return False, None

        landmarks = self.results.pose_landmarks.landmark
        conditions_met = []
        
        # Verificar ángulos de piernas
        left_leg_angle = self._calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP],
            landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE],
            landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE]
        )
        right_leg_angle = self._calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE]
        )
        
        if left_leg_angle < self.config['leg_angle_threshold'] or \
           right_leg_angle < self.config['leg_angle_threshold']:
            conditions_met.append(('leg_angle', 'Mala postura en piernas detectada'))
        
        # Verificar ángulo del cuello
        neck_angle = self._calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER],
            landmarks[self.mp_pose.PoseLandmark.NOSE],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        )
        
        if neck_angle > self.config['neck_angle_threshold']:
            conditions_met.append(('neck_angle', 'Postura del cuello incorrecta'))
        
        return len(conditions_met) > 0, conditions_met

    def _calculate_angle(self, a, b, c):
        ang = math.degrees(
            math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a.y - b.y, a.x - b.x)
        )
        return ang + 360 if ang < 0 else ang