import cv2
import mediapipe as mp
import math

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic


def calculate_angle(a, b, c):
    ang = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    return ang + 360 if ang < 0 else ang

def calculate_height(a, b):
    return abs(a[1] - b[1])

video_path = "VID-20250127-WA0001.mp4"
cap = cv2.VideoCapture(video_path)

with mp_holistic.Holistic(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convertir BGR a RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Procesar la imagen con MediaPipe
        results = holistic.process(image)

        # Convertir de nuevo a BGR para dibujar
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Verificar la postura
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
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

            chair_height = calculate_height(left_hip, left_knee)

            if left_leg_angle < 160 or right_leg_angle < 160:  # Umbral para mala postura
                color = (0, 0, 255)  # Rojo para mala postura
            else:
                color = (0, 255, 0)  # Verde para buena postura

            # Mostrar los ángulos calculados en la imagen
            cv2.putText(
                image,
                f"Angulo Izq: {int(left_leg_angle)}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                image,
                f"Angulo Der: {int(right_leg_angle)}",
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                2,
                cv2.LINE_AA,
            )

            # Mostrar la altura de la silla en la imagen
            cv2.putText(
                image,
                f"Altura Silla: {int(chair_height)}",
                (50, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                2,
                cv2.LINE_AA,
            )
        else:
            color = (0, 255, 0)  # Verde por defecto

        # Dibujar puntos clave solo de las piernas
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
        )

        # Mostrar el resultado
        cv2.imshow("MediaPipe Holistic", image)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
