import cv2
import mediapipe as mp

# Inicializar MediaPipe Holistic
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

# Ruta al video (puedes cambiar el nombre según el archivo que quieras analizar)
video_path = "VID-20250110-WA0039.mp4"
cap = cv2.VideoCapture(video_path)

# Configurar Holistic
with mp_holistic.Holistic(static_image_mode=False, model_complexity=2) as holistic:
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

        # Dibujar puntos clave
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS
        )
        mp_drawing.draw_landmarks(
            image, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS
        )
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
