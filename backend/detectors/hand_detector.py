from base_detector import BaseDetector
import mediapipe as mp
import math
import cv2
class HandDetector(BaseDetector):
    def __init__(self, config):
        super().__init__(config)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=config['min_detection_confidence'],
            min_tracking_confidence=config['min_tracking_confidence']
        )
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=config['min_detection_confidence'],
            min_tracking_confidence=config['min_tracking_confidence']
        )

    def process_frame(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        self.results_hands = self.hands.process(image)
        self.results_pose = self.pose.process(image)
        image.flags.writeable = True
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    def draw_results(self, frame):
        if self.results_hands.multi_hand_landmarks:
            for hand_landmarks in self.results_hands.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
                )
        
        if self.results_pose.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, self.results_pose.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
            )
        return frame

    def check_conditions(self):
        conditions_met = []
        
        if self.results_hands.multi_hand_landmarks and self.results_pose.pose_landmarks:
            pose_landmarks = self.results_pose.pose_landmarks.landmark
            
            # Calcular distancia entre hombros
            shoulder_distance = self._calculate_distance(
                pose_landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER],
                pose_landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            )
            
            if shoulder_distance > self.config['max_shoulder_distance']:
                conditions_met.append(('shoulder_distance', 'Brazos demasiado abiertos'))
            
            # Verificar posición de codos
            left_elbow_distance = self._calculate_distance(
                pose_landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW],
                pose_landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            )
            right_elbow_distance = self._calculate_distance(
                pose_landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW],
                pose_landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            )
            
            if left_elbow_distance > self.config['max_elbow_distance'] or \
               right_elbow_distance > self.config['max_elbow_distance']:
                conditions_met.append(('elbow_position', 'Codos demasiado alejados del cuerpo'))
        
        return len(conditions_met) > 0, conditions_met

    def _calculate_distance(self, a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)