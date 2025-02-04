import cv2
import mediapipe as mp
import math
import time
import ctypes



mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    ang = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    return ang + 360 if ang < 0 else ang

def calculate_distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def show_notification(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1)

# Inicializar variables para la detección de mala postura
bad_posture_start_time = None
alert_shown = False

# Ruta del video
video_path = "VID-20250127-WA0000.mp4"
cap = cv2.VideoCapture(video_path)

frame_count = 0

with mp_holistic.Holistic(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as holistic, mp_hands.Hands(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as hands, mp_pose.Pose(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Convertir BGR a RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Procesar la imagen con MediaPipe
        results_holistic = holistic.process(image)
        results_hands = hands.process(image)
        results_pose = pose.process(image)

        # Convertir de nuevo a BGR para dibujar
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Verificar la postura
        if results_holistic.pose_landmarks:
            landmarks = results_holistic.pose_landmarks.landmark
            left_shoulder = [
                landmarks[mp_holistic.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[mp_holistic.PoseLandmark.LEFT_SHOULDER.value].y,
            ]
            left_hip = [
                landmarks[mp_holistic.PoseLandmark.LEFT_HIP.value].x,
                landmarks[mp_holistic.PoseLandmark.LEFT_HIP.value].y,
            ]
            left_knee = [
                landmarks[mp_holistic.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[mp_holistic.PoseLandmark.LEFT_KNEE.value].y,
            ]
            left_ankle = [
                landmarks[mp_holistic.PoseLandmark.LEFT_ANKLE.value].x,
                landmarks[mp_holistic.PoseLandmark.LEFT_ANKLE.value].y,
            ]

            right_shoulder = [
                landmarks[mp_holistic.PoseLandmark.RIGHT_SHOULDER.value].x,
                landmarks[mp_holistic.PoseLandmark.RIGHT_SHOULDER.value].y,
            ]
            right_hip = [
                landmarks[mp_holistic.PoseLandmark.RIGHT_HIP.value].x,
                landmarks[mp_holistic.PoseLandmark.RIGHT_HIP.value].y,
            ]
            right_knee = [
                landmarks[mp_holistic.PoseLandmark.RIGHT_KNEE.value].x,
                landmarks[mp_holistic.PoseLandmark.RIGHT_KNEE.value].y,
            ]
            right_ankle = [
                landmarks[mp_holistic.PoseLandmark.RIGHT_ANKLE.value].x,
                landmarks[mp_holistic.PoseLandmark.RIGHT_ANKLE.value].y,
            ]

            left_leg_angle = calculate_angle(left_hip, left_knee, left_ankle)
            right_leg_angle = calculate_angle(right_hip, right_knee, right_ankle)

            alert_text = ""
            if left_leg_angle < 307 or right_leg_angle < 307:
                color = (0, 0, 255)
                if bad_posture_start_time is None:
                    bad_posture_start_time = time.time()
                    alert_shown = False
                elif time.time() - bad_posture_start_time > 5 and not alert_shown:
                    # 
                    alert_text = "Mala postura detectada! , se recomienda tomar acciones"
                    show_notification("Alerta de Postura", alert_text)
                    alert_shown = True
            else:
                color = (0, 255, 0)
                bad_posture_start_time = None
                alert_shown = False
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

        # Verificar la detección de manos
        if results_hands.multi_hand_landmarks and results_pose.pose_landmarks:
            for hand_landmarks in results_hands.multi_hand_landmarks:
                landmarks = hand_landmarks.landmark
                wrist = [
                    landmarks[mp_hands.HandLandmark.WRIST].x,
                    landmarks[mp_hands.HandLandmark.WRIST].y,
                ]
                thumb_cmc = [
                    landmarks[mp_hands.HandLandmark.THUMB_CMC].x,
                    landmarks[mp_hands.HandLandmark.THUMB_CMC].y,
                ]
                thumb_mcp = [
                    landmarks[mp_hands.HandLandmark.THUMB_MCP].x,
                    landmarks[mp_hands.HandLandmark.THUMB_MCP].y,
                ]
                thumb_ip = [
                    landmarks[mp_hands.HandLandmark.THUMB_IP].x,
                    landmarks[mp_hands.HandLandmark.THUMB_IP].y,
                ]
                thumb_tip = [
                    landmarks[mp_hands.HandLandmark.THUMB_TIP].x,
                    landmarks[mp_hands.HandLandmark.THUMB_TIP].y,
                ]
                index_finger_mcp = [
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP].x,
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP].y,
                ]
                index_finger_pip = [
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].x,
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y,
                ]
                index_finger_dip = [
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_DIP].x,
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_DIP].y,
                ]
                index_finger_tip = [
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].x,
                    landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y,
                ]
                middle_finger_mcp = [
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].x,
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y,
                ]
                middle_finger_pip = [
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].x,
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y,
                ]
                middle_finger_dip = [
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].x,
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].y,
                ]
                middle_finger_tip = [
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x,
                    landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y,
                ]
                ring_finger_mcp = [
                    landmarks[mp_hands.HandLandmark.RING_FINGER_MCP].x,
                    landmarks[mp_hands.HandLandmark.RING_FINGER_MCP].y,
                ]
                ring_finger_pip = [
                    landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].x,
                    landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y,
                ]
                ring_finger_dip = [
                    landmarks[mp_hands.HandLandmark.RING_FINGER_DIP].x,
                    landmarks[mp_hands.HandLandmark.RING_FINGER_DIP].y,
                ]
                ring_finger_tip = [
                    landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].x,
                    landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y,
                ]
                pinky_mcp = [
                    landmarks[mp_hands.HandLandmark.PINKY_MCP].x,
                    landmarks[mp_hands.HandLandmark.PINKY_MCP].y,
                ]
                pinky_pip = [
                    landmarks[mp_hands.HandLandmark.PINKY_PIP].x,
                    landmarks[mp_hands.HandLandmark.PINKY_PIP].y,
                ]
                pinky_dip = [
                    landmarks[mp_hands.HandLandmark.PINKY_DIP].x,
                    landmarks[mp_hands.HandLandmark.PINKY_DIP].y,
                ]
                pinky_tip = [
                    landmarks[mp_hands.HandLandmark.PINKY_TIP].x,
                    landmarks[mp_hands.HandLandmark.PINKY_TIP].y,
                ]

                # Obtener puntos de los codos
                pose_landmarks = results_pose.pose_landmarks.landmark
                left_elbow = [
                    pose_landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x,
                    pose_landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y,
                ]
                right_elbow = [
                    pose_landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x,
                    pose_landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y,
                ]

                # Obtener puntos de los hombros
                left_shoulder = [
                    pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                    pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y,
                ]
                right_shoulder = [
                    pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                    pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y,
                ]
                nose = [
                    pose_landmarks[mp_pose.PoseLandmark.NOSE].x,
                    pose_landmarks[mp_pose.PoseLandmark.NOSE].y,
                ]

                # Calcular ángulo del cuello
                neck_angle = calculate_angle(left_shoulder, nose, right_shoulder)

                # Calcular distancia entre los hombros
                shoulder_distance = math.sqrt(
                    (right_shoulder[0] - left_shoulder[0]) ** 2
                    + (right_shoulder[1] - left_shoulder[1]) ** 2
                )

                # Calcular distancia de los codos hacia el cuerpo
                left_elbow_distance = math.sqrt(
                    (left_elbow[0] - left_shoulder[0]) ** 2
                    + (left_elbow[1] - left_shoulder[1]) ** 2
                )
                right_elbow_distance = math.sqrt(
                    (right_elbow[0] - right_shoulder[0]) ** 2
                    + (right_elbow[1] - right_shoulder[1]) ** 2
                )

                # Calcular distancia entre los codos
                elbow_distance = math.sqrt(
                    (right_elbow[0] - left_elbow[0]) ** 2
                    + (right_elbow[1] - left_elbow[1]) ** 2
                )

                # Calcular ángulos de los dedos con el codo
                thumb_angle = calculate_angle(wrist, thumb_mcp, thumb_tip)
                index_finger_angle = calculate_angle(
                    wrist, index_finger_mcp, index_finger_tip
                )
                middle_finger_angle = calculate_angle(
                    wrist, middle_finger_mcp, middle_finger_tip
                )
                ring_finger_angle = calculate_angle(
                    wrist, ring_finger_mcp, ring_finger_tip
                )
                pinky_angle = calculate_angle(wrist, pinky_mcp, pinky_tip)

                # Calcular ángulos de los codos
                left_elbow_angle = calculate_angle(left_elbow, wrist, thumb_tip)
                right_elbow_angle = calculate_angle(right_elbow, wrist, thumb_tip)

                # Verificar si el cuello se mueve mucho, los brazos están muy abiertos o la distancia entre los codos es mayor que 0.15
                if (
                    neck_angle > 45 or shoulder_distance > 0.5 or left_elbow_distance > 0.3 or right_elbow_distance > 0.3 or elbow_distance > 0.15
                ):
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)

                # Dibujar puntos clave de las manos
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(
                        color=(0, 0, 255), thickness=2, circle_radius=2
                    ),
                    mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=2, circle_radius=2
                    ),
                )

                # Dibujar puntos clave del cuerpo
                mp_drawing.draw_landmarks(
                    image,
                    results_pose.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(
                        color=(0, 0, 255), thickness=2, circle_radius=2
                    ),
                    mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=2, circle_radius=2
                    ),
                )

        # Mostrar el resultado
        cv2.imshow("MediaPipe Holistic", image)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
