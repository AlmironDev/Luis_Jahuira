import cv2
import mediapipe as mp


# ✅ Puerto RTSP abierto en: 192.168.1.68


# ✅ Puerto RTSP abierto en: 192.168.1.67


# Configuración simple de MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Configuración de la cámara
usuario = "admin"
clave = "admin123"
ip = "192.168.1.68"

url = f"rtsp://{usuario}:{clave}@{ip}:554/cam/realmonitor?channel=1&subtype=0"
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print(f"❌ No se pudo conectar: {ip}")
    exit()

print(f"✅ Cámara conectada: {ip}")
print("Presiona ESC para salir...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ No se pudo leer frame")
        break
    
    # Efecto espejo
    frame = cv2.flip(frame, 1)
    
    # Procesar con MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    # Líneas de referencia
    h, w, _ = frame.shape
    cv2.line(frame, (0, h//2), (w, h//2), (255, 0, 0), 2)
    cv2.line(frame, (w//2, 0), (w//2, h), (0, 0, 255), 2)
    
    # Dibujar landmarks si se detecta rostro
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(
                    color=(0, 255, 0), thickness=1, circle_radius=1
                )
            )
        print("✅ Rostro detectado")
    else:
        print("❌ No se detectó rostro")
    
    cv2.imshow("Camara IP - MediaPipe Test", frame)
    
    if cv2.waitKey(1) == 27:
        break

cap.release()
face_mesh.close()
cv2.destroyAllWindows()
