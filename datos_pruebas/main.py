import cv2
import mediapipe as mp
import math

# Inicializar MediaPipe
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Configurar los modelos
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)


cap = cv2.VideoCapture("VID-20250127-WA0000.mp4")

# Definir conexiones personalizadas para el torso
TORSO_CONNECTIONS = [
    (11, 12),  # Hombros
    (11, 23),  # Hombro izquierdo a cadera izquierda
    (12, 24),  # Hombro derecho a cadera derecha
    (23, 24),  # Caderas
    (11, 13),  # Hombro izquierdo a codo izquierdo
    (12, 14),  # Hombro derecho a codo derecho
]

# Conexiones entre cabeza y torso
HEAD_TORSO_CONNECTIONS = [
    (0, 11),   # Nariz a hombro izquierdo
    (0, 12),   # Nariz a hombro derecho
    (7, 11),   # Oreja izquierda a hombro izquierdo
    (8, 12),   # Oreja derecha a hombro derecho
]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    # Convertir a RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape
    
    # Procesar pose, manos y cara
    pose_results = pose.process(frame_rgb)
    hand_results = hands.process(frame_rgb)
    face_results = face_mesh.process(frame_rgb)
    
    # Dibujar landmarks de pose
    if pose_results.pose_landmarks:
        # Dibujar todos los puntos de pose
        mp_drawing.draw_landmarks(
            frame,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        
        # Dibujar conexiones del torso con un color diferente
        for connection in TORSO_CONNECTIONS:
            start_idx, end_idx = connection
            if (start_idx < len(pose_results.pose_landmarks.landmark) and 
                end_idx < len(pose_results.pose_landmarks.landmark)):
                start_point = pose_results.pose_landmarks.landmark[start_idx]
                end_point = pose_results.pose_landmarks.landmark[end_idx]
                
                # Convertir coordenadas normalizadas a píxeles
                start_x, start_y = int(start_point.x * w), int(start_point.y * h)
                end_x, end_y = int(end_point.x * w), int(end_point.y * h)
                
                # Dibujar línea para el torso
                cv2.line(frame, (start_x, start_y), (end_x, end_y), (0, 255, 255), 3)
        
        # Dibujar conexiones entre cabeza y torso
        for connection in HEAD_TORSO_CONNECTIONS:
            start_idx, end_idx = connection
            if (start_idx < len(pose_results.pose_landmarks.landmark) and 
                end_idx < len(pose_results.pose_landmarks.landmark)):
                start_point = pose_results.pose_landmarks.landmark[start_idx]
                end_point = pose_results.pose_landmarks.landmark[end_idx]
                
                # Convertir coordenadas normalizadas a píxeles
                start_x, start_y = int(start_point.x * w), int(start_point.y * h)
                end_x, end_y = int(end_point.x * w), int(end_point.y * h)
                
                # Dibujar línea para conexión cabeza-torso
                cv2.line(frame, (start_x, start_y), (end_x, end_y), (255, 0, 255), 2)
        
        # Mostrar números de los puntos de pose
        for idx, landmark in enumerate(pose_results.pose_landmarks.landmark):
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            # Resaltar puntos del torso y cabeza
            if idx in [0, 7, 8, 11, 12, 13, 14, 23, 24]:
                cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)  # Puntos amarillos para torso/cabeza
            cv2.putText(frame, str(idx), (cx+5, cy), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    # Dibujar landmarks de manos
    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
            
            # Mostrar números de los puntos de manos
            for idx, landmark in enumerate(hand_landmarks.landmark):
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.putText(frame, str(idx), (cx, cy), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
    
    # Dibujar landmarks de cara
    if face_results.multi_face_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                face_landmarks,
                mp_face_mesh.FACEMESH_TESSELATION,
                None,
                mp_drawing_styles.get_default_face_mesh_tesselation_style())
            
            # Mostrar números de los puntos clave de la cara
            key_face_points = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 33, 61, 91, 263, 291, 234, 454]
            for idx in key_face_points:
                if idx < len(face_landmarks.landmark):
                    landmark = face_landmarks.landmark[idx]
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.putText(frame, str(idx), (cx, cy), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
    
    # Mostrar información sobre los puntos
    cv2.putText(frame, "Puntos de Pose (verde): 33 puntos", (10, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, "Puntos de Manos (azul): 21 puntos cada una", (10, 45), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    cv2.putText(frame, "Puntos de Cara (rojo): 478 puntos", (10, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(frame, "Torso y cabeza (amarillo): conexiones resaltadas", (10, 95), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # Mostrar el frame
    cv2.imshow("Puntos del cuerpo humano - Torso y Cabeza", frame)
    
    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
pose.close()
hands.close()
face_mesh.close()
cv2.destroyAllWindows()