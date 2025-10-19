import cv2
import mediapipe as mp
import math
import numpy as np

# Inicializar MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Configurar el modelo de pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# Usar el video especificado
cap = cv2.VideoCapture("VID-20250127-WA0000.mp4")

# Función para calcular ángulos
def calculate_angle(a, b, c):
    """
    Calcula el ángulo entre tres puntos (a, b, c)
    donde b es el vértice del ángulo
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    # Calcular vectores
    ba = a - b
    bc = c - b
    
    # Calcular el producto punto
    dot_product = np.dot(ba, bc)
    
    # Calcular magnitudes
    mag_ba = np.linalg.norm(ba)
    mag_bc = np.linalg.norm(bc)
    
    # Calcular el coseno del ángulo
    cosine_angle = dot_product / (mag_ba * mag_bc + 1e-10)
    
    # Asegurar que el valor esté en el rango válido para arcoseno
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    
    # Calcular el ángulo en grados
    angle = np.degrees(np.arccos(cosine_angle))
    
    return angle

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    # Convertir a RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape
    
    # Procesar pose
    pose_results = pose.process(frame_rgb)
    
    # Dibujar landmarks de pose
    if pose_results.pose_landmarks:
        # Dibujar todos los puntos de pose
        mp_drawing.draw_landmarks(
            frame,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        
        # Obtener landmarks
        landmarks = pose_results.pose_landmarks.landmark
        
        # Calcular y mostrar ángulo entre puntos 23-25-27 (cadera-rodilla-tobillo izquierdo)
        if all(landmarks[i].visibility > 0.5 for i in [23, 25, 27]):
            # Obtener coordenadas de los puntos
            point_23 = (landmarks[23].x * w, landmarks[23].y * h)
            point_25 = (landmarks[25].x * w, landmarks[25].y * h)
            point_27 = (landmarks[27].x * w, landmarks[27].y * h)
            
            # Calcular el ángulo
            angle = calculate_angle(point_23, point_25, point_27)
            
            # Dibujar puntos y líneas en ROJO
            cv2.circle(frame, (int(point_23[0]), int(point_23[1])), 8, (0, 0, 255), -1)  # Punto 23
            cv2.circle(frame, (int(point_25[0]), int(point_25[1])), 8, (0, 0, 255), -1)  # Punto 25
            cv2.circle(frame, (int(point_27[0]), int(point_27[1])), 8, (0, 0, 255), -1)  # Punto 27
            
            # Dibujar líneas entre los puntos
            cv2.line(frame, (int(point_23[0]), int(point_23[1])), 
                    (int(point_25[0]), int(point_25[1])), (0, 0, 255), 3)
            cv2.line(frame, (int(point_25[0]), int(point_25[1])), 
                    (int(point_27[0]), int(point_27[1])), (0, 0, 255), 3)
            
            # Mostrar el ángulo en la rodilla (punto 25)
            cv2.putText(frame, f"{int(angle)}°", 
                       (int(point_25[0]) + 15, int(point_25[1])), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Mostrar información sobre los puntos
            cv2.putText(frame, "Punto 23: Cadera izquierda", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, "Punto 25: Rodilla izquierda", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, "Punto 27: Tobillo izquierdo", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, f"Angulo: {int(angle)} grados", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Mostrar números de todos los puntos de pose
        for idx, landmark in enumerate(pose_results.pose_landmarks.landmark):
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            # Resaltar los puntos 23, 25, 27 en rojo
            if idx in [23, 25, 27]:
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, str(idx), (cx+5, cy), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    # Mostrar el frame
    cv2.imshow("Angulo entre puntos 23-25-27 (ROJO)", frame)
    
    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
pose.close()
cv2.destroyAllWindows()