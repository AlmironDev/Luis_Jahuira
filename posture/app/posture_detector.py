import cv2
import mediapipe as mp
import math
import time

class PostureDetector:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.mp_holistic = mp.solutions.holistic
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        
        self.bad_posture_start_time = None
        self.alert_shown = False

    def calculate_angle(self, a, b, c):
        ang = math.degrees(
            math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
        )
        return ang + 360 if ang < 0 else ang

    def calculate_distance(self, a, b):
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def process_frame(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        results_holistic = self.holistic.process(image)
        results_hands = self.hands.process(image)
        results_pose = self.pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results_holistic.pose_landmarks:
            landmarks = results_holistic.pose_landmarks.landmark
            left_shoulder = [
                landmarks[self.mp_holistic.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[self.mp_holistic.PoseLandmark.LEFT_SHOULDER.value].y,
            ]
            left_hip = [
                landmarks[self.mp_holistic.PoseLandmark.LEFT_HIP.value].x,
                landmarks[self.mp_holistic.PoseLandmark.LEFT_HIP.value].y,
            ]
            left_knee = [
                landmarks[self.mp_holistic.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[self.mp_holistic.PoseLandmark.LEFT_KNEE.value].y,
            ]
            left_ankle = [
                landmarks[self.mp_holistic.PoseLandmark.LEFT_ANKLE.value].x,
                landmarks[self.mp_holistic.PoseLandmark.LEFT_ANKLE.value].y,
            ]

            right_shoulder = [
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_SHOULDER.value].x,
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_SHOULDER.value].y,
            ]
            right_hip = [
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_HIP.value].x,
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_HIP.value].y,
            ]
            right_knee = [
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_KNEE.value].x,
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_KNEE.value].y,
            ]
            right_ankle = [
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_ANKLE.value].x,
                landmarks[self.mp_holistic.PoseLandmark.RIGHT_ANKLE.value].y,
            ]

            left_leg_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
            right_leg_angle = self.calculate_angle(right_hip, right_knee, right_ankle)

            alert_text = ""
            if left_leg_angle < 307 or right_leg_angle < 307:
                color = (0, 0, 255)
                if self.bad_posture_start_time is None:
                    self.bad_posture_start_time = time.time()
                    self.alert_shown = False
                elif time.time() - self.bad_posture_start_time > 5 and not self.alert_shown:
                    alert_text = "Mala postura detectada! Se recomienda tomar acciones"
                    self.alert_shown = True
            else:
                color = (0, 255, 0)
                self.bad_posture_start_time = None
                self.alert_shown = False
                alert_text = ""

            if alert_text:
                cv2.putText(
                    image,
                    alert_text,
                    (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA,
                )

            # Dibujar landmarks
            self.mp_drawing.draw_landmarks(
                image,
                results_holistic.pose_landmarks,
                self.mp_holistic.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
            )

        if results_hands.multi_hand_landmarks:
            for hand_landmarks in results_hands.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
                )

        return image

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        processed_frame = self.process_frame(frame)
        return processed_frame

    def __del__(self):
        self.cap.release()