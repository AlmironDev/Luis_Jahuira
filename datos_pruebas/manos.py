import cv2
import mediapipe as mp
import math

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose

def calculate_angle_3d(a, b, c):
    ba = [a[i] - b[i] for i in range(3)]
    bc = [c[i] - b[i] for i in range(3)]
    dot = sum(ba[i] * bc[i] for i in range(3))
    mag_ba = math.sqrt(sum(x**2 for x in ba))
    mag_bc = math.sqrt(sum(x**2 for x in bc))
    cos_angle = dot / (mag_ba * mag_bc)
    return math.degrees(math.acos(max(min(cos_angle, 1), -1)))


# video_path = "VID-20250127-WA0001.mp4"

video_path = "VID-20250127-WA0004.mp4"

cap = cv2.VideoCapture(video_path)



with mp_hands.Hands(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as hands, mp_pose.Pose(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as pose:
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convertir BGR a RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Procesar la imagen con MediaPipe
        results_hands = hands.process(image)
        results_pose = pose.process(image)

        # Convertir de nuevo a BGR para dibujar
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Verificar la detección de manos
        if results_hands.multi_hand_landmarks and results_pose.pose_landmarks:
            for hand_landmarks in results_hands.multi_hand_landmarks:
                landmarks = hand_landmarks.landmark
                wrist = [landmarks[mp_hands.HandLandmark.WRIST].x, landmarks[mp_hands.HandLandmark.WRIST].y]
                thumb_cmc = [landmarks[mp_hands.HandLandmark.THUMB_CMC].x, landmarks[mp_hands.HandLandmark.THUMB_CMC].y]
                thumb_mcp = [landmarks[mp_hands.HandLandmark.THUMB_MCP].x, landmarks[mp_hands.HandLandmark.THUMB_MCP].y]
                thumb_ip = [landmarks[mp_hands.HandLandmark.THUMB_IP].x, landmarks[mp_hands.HandLandmark.THUMB_IP].y]
                thumb_tip = [landmarks[mp_hands.HandLandmark.THUMB_TIP].x, landmarks[mp_hands.HandLandmark.THUMB_TIP].y]
                index_finger_mcp = [landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP].x, landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP].y]
                index_finger_pip = [landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].x, landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y]
                index_finger_dip = [landmarks[mp_hands.HandLandmark.INDEX_FINGER_DIP].x, landmarks[mp_hands.HandLandmark.INDEX_FINGER_DIP].y]
                index_finger_tip = [landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].x, landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y]
                middle_finger_mcp = [landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].x, landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y]
                middle_finger_pip = [landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].x, landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y]
                middle_finger_dip = [landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].x, landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].y]
                middle_finger_tip = [landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x, landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y]
                ring_finger_mcp = [landmarks[mp_hands.HandLandmark.RING_FINGER_MCP].x, landmarks[mp_hands.HandLandmark.RING_FINGER_MCP].y]
                ring_finger_pip = [landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].x, landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y]
                ring_finger_dip = [landmarks[mp_hands.HandLandmark.RING_FINGER_DIP].x, landmarks[mp_hands.HandLandmark.RING_FINGER_DIP].y]
                ring_finger_tip = [landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].x, landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y]
                pinky_mcp = [landmarks[mp_hands.HandLandmark.PINKY_MCP].x, landmarks[mp_hands.HandLandmark.PINKY_MCP].y]
                pinky_pip = [landmarks[mp_hands.HandLandmark.PINKY_PIP].x, landmarks[mp_hands.HandLandmark.PINKY_PIP].y]
                pinky_dip = [landmarks[mp_hands.HandLandmark.PINKY_DIP].x, landmarks[mp_hands.HandLandmark.PINKY_DIP].y]
                pinky_tip = [landmarks[mp_hands.HandLandmark.PINKY_TIP].x, landmarks[mp_hands.HandLandmark.PINKY_TIP].y]

                # Obtener puntos de los codos
                pose_landmarks = results_pose.pose_landmarks.landmark
                left_elbow = [pose_landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, pose_landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
                right_elbow = [pose_landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x, pose_landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y]

                # Calcular ángulos de los dedos con el codo
                thumb_angle = calculate_angle(wrist, thumb_mcp, thumb_tip)
                index_finger_angle = calculate_angle(wrist, index_finger_mcp, index_finger_tip)
                middle_finger_angle = calculate_angle(wrist, middle_finger_mcp, middle_finger_tip)
                ring_finger_angle = calculate_angle(wrist, ring_finger_mcp, ring_finger_tip)
                pinky_angle = calculate_angle(wrist, pinky_mcp, pinky_tip)

                # Calcular ángulos de los codos
                left_elbow_angle = calculate_angle(left_elbow, wrist, thumb_tip)
                right_elbow_angle = calculate_angle(right_elbow, wrist, thumb_tip)

                # Mostrar los ángulos calculados en la imagen
                # cv2.putText(
                #     image,
                #     f"Pulgar: {int(thumb_angle)}",
                #     (50, 50),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     1,
                #     (0, 255, 0),
                #     2,
                #     cv2.LINE_AA,
                # )
                # cv2.putText(
                #     image,
                #     f"Indice: {int(index_finger_angle)}",
                #     (50, 100),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     1,
                #     (0, 255, 0),
                #     2,
                #     cv2.LINE_AA,
                # )
                # cv2.putText(
                #     image,
                #     f"Medio: {int(middle_finger_angle)}",
                #     (50, 150),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     1,
                #     (0, 255, 0),
                #     2,
                #     cv2.LINE_AA,
                # )
                # cv2.putText(
                #     image,
                #     f"Anular: {int(ring_finger_angle)}",
                #     (50, 200),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     1,
                #     (0, 255, 0),
                #     2,
                #     cv2.LINE_AA,
                # )
                # cv2.putText(
                #     image,
                #     f"Meñique: {int(pinky_angle)}",
                #     (50, 250),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     1,
                #     (0, 255, 0),
                #     2,
                #     cv2.LINE_AA,
                # )
                # cv2.putText(
                #     image,
                #     f"Codo Izq: {int(left_elbow_angle)}",
                #     (50, 300),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     1,
                #     (0, 255, 0),
                #     2,
                #     cv2.LINE_AA,
                # )
                # cv2.putText(
                #     image,
                #     f"Codo Der: {int(right_elbow_angle)}",
                #     (50, 350),
                #     cv2.FONT_HERSHEY_SIMPLEX,
                #     1,
                #     (0, 255, 0),
                #     2,
                #     cv2.LINE_AA,
                # )

                # Dibujar puntos clave de las manos
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                )

                # Dibujar puntos clave del cuerpo
                mp_drawing.draw_landmarks(
                    image,
                    results_pose.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                )

        # Mostrar el resultado
        cv2.imshow("MediaPipe Hands", image)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

        frame_count += 1

cap.release()
cv2.destroyAllWindows()
