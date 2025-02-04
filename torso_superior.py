import cv2
import mediapipe as mp
import math
# from win10toast import ToastNotifier  # Eliminar ToastNotifier
# from plyer import notification  # Eliminar plyer para notificaciones
import time  # Importar time para manejar el tiempo
import ctypes  # Importar ctypes para notificaciones personalizadas

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic


def calculate_angle(a, b, c):
    ang = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    return ang + 360 if ang < 0 else ang


def calculate_distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


# video_path = "VID-20250114-WA0004.mp4"
video_path = "VID-20250120-WA0011.mp4"
# video_path = "VID-20250120-WA0009.mp4"
# video_path = "VID-20250120-WA0009.mp4"
cap = cv2.VideoCapture(video_path)

frame_count = 0  # Contador de cuadros

# Función para mostrar notificación en Windows
def show_notification(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1)

# Inicializar el notificador de Windows
# toaster = ToastNotifier()  # Eliminar inicialización de ToastNotifier
bad_posture_start_time = None  # Variable para almacenar el tiempo de inicio de mala postura
alert_shown = False  # Variable para controlar si la alerta ya fue mostrada

with mp_holistic.Holistic(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1  # Incrementar contador de cuadros

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
            if left_leg_angle < 307 or right_leg_angle < 307:  # Umbral para mala postura
                color = (0, 0, 255)  # Rojo para mala postura
                if bad_posture_start_time is None:
                    bad_posture_start_time = time.time()  # Iniciar el tiempo de mala postura
                    alert_shown = False  # Reiniciar el estado de la alerta
                elif time.time() - bad_posture_start_time > 8 and not alert_shown:  # Verificar si han pasado 10 segundos y no se ha mostrado la alerta
                    alert_text = "Mala postura detectada!"
                    show_notification("Alerta de Postura", alert_text)  # Mostrar alerta en Windows
                    alert_shown = True  # Marcar que la alerta ya fue mostrada
            else:
                color = (0, 255, 0)  # Verde para buena postura
                bad_posture_start_time = None  # Reiniciar el tiempo de mala postura
                alert_shown = False  # Reiniciar el estado de la alerta
                alert_text = ""

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

            # Mostrar alerta en la pantalla
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

        else:
            color = (0, 255, 0)  # Verde por defecto

        # Dibujar puntos clave
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
        )
        # mp_drawing.draw_landmarks(
        #     image, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS
        # )
        mp_drawing.draw_landmarks(
            image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS
        )
        mp_drawing.draw_landmarks(
            image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS
        )

        # Mostrar el resultado
        cv2.imshow("MediaPipe Holistic", image)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
