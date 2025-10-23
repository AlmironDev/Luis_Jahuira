# ==================== 
# PARTE 1: CONFIGURACIÓN INICIAL
# ====================
import cv2
import mediapipe as mp
import math
import time
import ctypes

# Inicializar MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# Constantes de configuración
ANGLE_TOLERANCE = 5  # Tolerancia de ±15° alrededor del objetivo
ALERT_DELAY = 5       # Segundos antes de mostrar alerta

# Ángulos objetivo
ANGLE_OBJECTIVES = {
    'knee': 90,        # Ángulo 1: Rodilla
    'hip_spine': 270,   # Ángulo 2: Cadera-Columna  
    'elbow': 260,       # Ángulo 3: Codo
    'neck': 180        # Ángulo 4: Cuello
}

def calculate_angle(a, b, c):
    """Calcula el ángulo entre tres puntos"""
    ang = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    return ang + 360 if ang < 0 else ang

def show_notification(title, message):
    """Muestra una notificación en Windows"""
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1)

# ==================== 
# PARTE 2: ANÁLISIS DE TODOS LOS ÁNGULOS
# ====================
class PostureAnalyzer:
    def __init__(self):
        self.bad_posture_start_time = None
        self.alert_shown = False
        
    def analyze_all_angles(self, landmarks):
        """Analiza los 4 ángulos: piernas, torso y cuello"""
        try:
            # ========== ÁNGULOS 1 Y 2 (PIERNAS) ==========
            # Obtener landmarks para piernas
            left_hip = [landmarks[mp_holistic.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp_holistic.PoseLandmark.LEFT_HIP.value].y]
            left_knee = [landmarks[mp_holistic.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp_holistic.PoseLandmark.LEFT_KNEE.value].y]
            left_ankle = [landmarks[mp_holistic.PoseLandmark.LEFT_ANKLE.value].x,
                         landmarks[mp_holistic.PoseLandmark.LEFT_ANKLE.value].y]
            
            right_hip = [landmarks[mp_holistic.PoseLandmark.RIGHT_HIP.value].x,
                        landmarks[mp_holistic.PoseLandmark.RIGHT_HIP.value].y]
            right_knee = [landmarks[mp_holistic.PoseLandmark.RIGHT_KNEE.value].x,
                         landmarks[mp_holistic.PoseLandmark.RIGHT_KNEE.value].y]
            right_ankle = [landmarks[mp_holistic.PoseLandmark.RIGHT_ANKLE.value].x,
                          landmarks[mp_holistic.PoseLandmark.RIGHT_ANKLE.value].y]
            
            # Puntos para columna
            left_shoulder = [landmarks[mp_holistic.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp_holistic.PoseLandmark.LEFT_SHOULDER.value].y]
            right_shoulder = [landmarks[mp_holistic.PoseLandmark.RIGHT_SHOULDER.value].x,
                             landmarks[mp_holistic.PoseLandmark.RIGHT_SHOULDER.value].y]
            spine = [(left_shoulder[0] + right_shoulder[0]) / 2,
                    (left_shoulder[1] + right_shoulder[1]) / 2]
            
            # ÁNGULO 1: Cadera → Rodilla → Tobillo
            left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
            
            # ÁNGULO 2: Columna → Cadera → Rodilla
            left_hip_angle = calculate_angle(spine, left_hip, left_knee)
            right_hip_angle = calculate_angle(spine, right_hip, right_knee)
            
            # ========== ÁNGULO 3: TORSO - HOMBROS - BRAZOS ==========
            # Obtener landmarks para brazos
            left_elbow = [landmarks[mp_holistic.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp_holistic.PoseLandmark.LEFT_ELBOW.value].y]
            left_wrist = [landmarks[mp_holistic.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp_holistic.PoseLandmark.LEFT_WRIST.value].y]
            
            right_elbow = [landmarks[mp_holistic.PoseLandmark.RIGHT_ELBOW.value].x,
                          landmarks[mp_holistic.PoseLandmark.RIGHT_ELBOW.value].y]
            right_wrist = [landmarks[mp_holistic.PoseLandmark.RIGHT_WRIST.value].x,
                          landmarks[mp_holistic.PoseLandmark.RIGHT_WRIST.value].y]
            
            # ÁNGULO 3: Hombro → Codo → Muñeca
            left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
            
            # ========== ÁNGULO 4: ESPALDA - CUELLO - CABEZA ==========
            # Obtener landmarks para cabeza/cuello
            left_ear = [landmarks[mp_holistic.PoseLandmark.LEFT_EAR.value].x,
                       landmarks[mp_holistic.PoseLandmark.LEFT_EAR.value].y]
            right_ear = [landmarks[mp_holistic.PoseLandmark.RIGHT_EAR.value].x,
                        landmarks[mp_holistic.PoseLandmark.RIGHT_EAR.value].y]
            nose = [landmarks[mp_holistic.PoseLandmark.NOSE.value].x,
                   landmarks[mp_holistic.PoseLandmark.NOSE.value].y]
            
            # Punto medio de orejas (cabeza)
            head = [(left_ear[0] + right_ear[0]) / 2,
                   (left_ear[1] + right_ear[1]) / 2]
            
            # ÁNGULO 4: Cadera → Hombro → Cabeza
            left_neck_angle = calculate_angle(left_hip, left_shoulder, head)
            right_neck_angle = calculate_angle(right_hip, right_shoulder, head)
            
            return {
                # Ángulos de piernas
                'left_knee_angle': left_knee_angle,
                'right_knee_angle': right_knee_angle,
                'left_hip_angle': left_hip_angle,
                'right_hip_angle': right_hip_angle,
                
                # Ángulos de brazos
                'left_elbow_angle': left_elbow_angle,
                'right_elbow_angle': right_elbow_angle,
                
                # Ángulos de cuello
                'left_neck_angle': left_neck_angle,
                'right_neck_angle': right_neck_angle,
                
                # Puntos para dibujar
                'landmarks': {
                    # Piernas
                    'left_hip': left_hip, 'left_knee': left_knee, 'left_ankle': left_ankle,
                    'right_hip': right_hip, 'right_knee': right_knee, 'right_ankle': right_ankle,
                    'spine': spine,
                    # Brazos
                    'left_shoulder': left_shoulder, 'left_elbow': left_elbow, 'left_wrist': left_wrist,
                    'right_shoulder': right_shoulder, 'right_elbow': right_elbow, 'right_wrist': right_wrist,
                    # Cabeza
                    'head': head, 'left_ear': left_ear, 'right_ear': right_ear, 'nose': nose
                }
            }
            
        except Exception as e:
            print(f"Error en análisis de ángulos: {e}")
            return None
    
    def check_all_angles(self, posture_data):
        """Verifica si todos los ángulos están dentro del rango óptimo"""
        if not posture_data:
            return None, (0, 255, 0), ""
        
        # Verificar cada ángulo contra su objetivo
        all_angles_optimal = True
        angle_status = {}
        
        # Verificar ÁNGULO 1 (rodilla)
        angle_status['left_knee'] = self._is_angle_optimal(posture_data['left_knee_angle'], ANGLE_OBJECTIVES['knee'])
        angle_status['right_knee'] = self._is_angle_optimal(posture_data['right_knee_angle'], ANGLE_OBJECTIVES['knee'])
        
        # Verificar ÁNGULO 2 (cadera-columna)
        angle_status['left_hip'] = self._is_angle_optimal(posture_data['left_hip_angle'], ANGLE_OBJECTIVES['hip_spine'])
        angle_status['right_hip'] = self._is_angle_optimal(posture_data['right_hip_angle'], ANGLE_OBJECTIVES['hip_spine'])
        
        # Verificar ÁNGULO 3 (codo)
        angle_status['left_elbow'] = self._is_angle_optimal(posture_data['left_elbow_angle'], ANGLE_OBJECTIVES['elbow'])
        angle_status['right_elbow'] = self._is_angle_optimal(posture_data['right_elbow_angle'], ANGLE_OBJECTIVES['elbow'])
        
        # Verificar ÁNGULO 4 (cuello)
        angle_status['left_neck'] = self._is_angle_optimal(posture_data['left_neck_angle'], ANGLE_OBJECTIVES['neck'])
        angle_status['right_neck'] = self._is_angle_optimal(posture_data['right_neck_angle'], ANGLE_OBJECTIVES['neck'])
        
        # Si alguno está fuera del rango → mala postura
        bad_posture_detected = not all(angle_status.values())
        
        alert_text = ""
        color = (0, 255, 0)  # Verde por defecto
        
        if bad_posture_detected:
            color = (0, 0, 255)  # Rojo para mala postura
            
            if self.bad_posture_start_time is None:
                self.bad_posture_start_time = time.time()
                self.alert_shown = False
            elif time.time() - self.bad_posture_start_time > ALERT_DELAY and not self.alert_shown:
                alert_text = self._generate_alert_message(posture_data, angle_status)
                show_notification("Alerta de Postura Completa", alert_text)
                self.alert_shown = True
        else:
            self.bad_posture_start_time = None
            self.alert_shown = False
        
        return posture_data, color, alert_text
    
    def _is_angle_optimal(self, angle, target):
        """Verifica si un ángulo está dentro del rango óptimo"""
        return (target - ANGLE_TOLERANCE) <= angle <= (target + ANGLE_TOLERANCE)
    
    def _generate_alert_message(self, posture_data, angle_status):
        """Genera mensaje de alerta específico"""
        message = "¡Mala postura detectada!\n\n"
        message += "Ángulos fuera de rango:\n"
        
        if not angle_status['left_knee'] or not angle_status['right_knee']:
            message += f"• Rodillas: I{posture_data['left_knee_angle']:.1f}° D{posture_data['right_knee_angle']:.1f}° (objetivo: 90°)\n"
        
        if not angle_status['left_hip'] or not angle_status['right_hip']:
            message += f"• Cadera-Columna: I{posture_data['left_hip_angle']:.1f}° D{posture_data['right_hip_angle']:.1f}° (objetivo: 90°)\n"
        
        if not angle_status['left_elbow'] or not angle_status['right_elbow']:
            message += f"• Codos: I{posture_data['left_elbow_angle']:.1f}° D{posture_data['right_elbow_angle']:.1f}° (objetivo: 90°)\n"
        
        if not angle_status['left_neck'] or not angle_status['right_neck']:
            message += f"• Cuello: I{posture_data['left_neck_angle']:.1f}° D{posture_data['right_neck_angle']:.1f}° (objetivo: 180°)\n"
        
        message += f"\nTolerancia: ±{ANGLE_TOLERANCE}°"
        return message

# ==================== 
# PARTE 3: VISUALIZACIÓN MEJORADA
# ====================
def draw_all_angles(image, posture_data, color, alert_text):
    """Dibuja todos los ángulos en la imagen"""
    if not posture_data:
        return
        
    landmarks = posture_data['landmarks']
    h, w, _ = image.shape
    
    def to_pixels(point):
        return int(point[0] * w), int(point[1] * h)
    
    # COLORES PARA DIFERENTES ÁNGULOS
    COLOR_LEGS = (0, 255, 255)     # Amarillo para piernas
    COLOR_HIP_SPINE = (255, 255, 0) # Cian para cadera-columna  
    COLOR_ARMS = (255, 0, 255)     # Magenta para brazos
    COLOR_NECK = (0, 255, 0)       # Verde para cuello
    
    # ========== DIBUJAR ÁNGULOS 1 Y 2 (PIERNAS) ==========
    # Pierna izquierda - Ángulo 1
    cv2.line(image, to_pixels(landmarks['left_hip']), to_pixels(landmarks['left_knee']), COLOR_LEGS, 3)
    cv2.line(image, to_pixels(landmarks['left_knee']), to_pixels(landmarks['left_ankle']), COLOR_LEGS, 3)
    
    # Pierna derecha - Ángulo 1
    cv2.line(image, to_pixels(landmarks['right_hip']), to_pixels(landmarks['right_knee']), COLOR_LEGS, 3)
    cv2.line(image, to_pixels(landmarks['right_knee']), to_pixels(landmarks['right_ankle']), COLOR_LEGS, 3)
    
    # Ángulo 2 izquierdo
    cv2.line(image, to_pixels(landmarks['spine']), to_pixels(landmarks['left_hip']), COLOR_HIP_SPINE, 3)
    cv2.line(image, to_pixels(landmarks['left_hip']), to_pixels(landmarks['left_knee']), COLOR_HIP_SPINE, 3)
    
    # Ángulo 2 derecho
    cv2.line(image, to_pixels(landmarks['spine']), to_pixels(landmarks['right_hip']), COLOR_HIP_SPINE, 3)
    cv2.line(image, to_pixels(landmarks['right_hip']), to_pixels(landmarks['right_knee']), COLOR_HIP_SPINE, 3)
    
    # ========== DIBUJAR ÁNGULO 3 (BRAZOS) ==========
    # Brazo izquierdo
    cv2.line(image, to_pixels(landmarks['left_shoulder']), to_pixels(landmarks['left_elbow']), COLOR_ARMS, 3)
    cv2.line(image, to_pixels(landmarks['left_elbow']), to_pixels(landmarks['left_wrist']), COLOR_ARMS, 3)
    
    # Brazo derecho
    cv2.line(image, to_pixels(landmarks['right_shoulder']), to_pixels(landmarks['right_elbow']), COLOR_ARMS, 3)
    cv2.line(image, to_pixels(landmarks['right_elbow']), to_pixels(landmarks['right_wrist']), COLOR_ARMS, 3)
    
    # ========== DIBUJAR ÁNGULO 4 (CUELLO) ==========
    # Lado izquierdo
    cv2.line(image, to_pixels(landmarks['left_hip']), to_pixels(landmarks['left_shoulder']), COLOR_NECK, 3)
    cv2.line(image, to_pixels(landmarks['left_shoulder']), to_pixels(landmarks['head']), COLOR_NECK, 3)
    
    # Lado derecho
    cv2.line(image, to_pixels(landmarks['right_hip']), to_pixels(landmarks['right_shoulder']), COLOR_NECK, 3)
    cv2.line(image, to_pixels(landmarks['right_shoulder']), to_pixels(landmarks['head']), COLOR_NECK, 3)
    
    # ========== MOSTRAR VALORES NUMÉRICOS ==========
    y_offset = 30
    text_color = (255, 255, 255)
    
    # Grupo 1: Piernas
    cv2.putText(image, "PIERNAS:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_LEGS, 2)
    cv2.putText(image, f"Rodilla I: {posture_data['left_knee_angle']:.1f}°", (20, y_offset + 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    cv2.putText(image, f"Rodilla D: {posture_data['right_knee_angle']:.1f}°", (20, y_offset + 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    cv2.putText(image, f"Cadera I: {posture_data['left_hip_angle']:.1f}°", (20, y_offset + 75), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    cv2.putText(image, f"Cadera D: {posture_data['right_hip_angle']:.1f}°", (20, y_offset + 100), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Grupo 2: Brazos
    cv2.putText(image, "BRAZOS:", (10, y_offset + 135), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_ARMS, 2)
    cv2.putText(image, f"Codo I: {posture_data['left_elbow_angle']:.1f}°", (20, y_offset + 160), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    cv2.putText(image, f"Codo D: {posture_data['right_elbow_angle']:.1f}°", (20, y_offset + 185), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Grupo 3: Cuello
    cv2.putText(image, "CUELLO:", (10, y_offset + 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_NECK, 2)
    cv2.putText(image, f"Cuello I: {posture_data['left_neck_angle']:.1f}°", (20, y_offset + 245), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    cv2.putText(image, f"Cuello D: {posture_data['right_neck_angle']:.1f}°", (20, y_offset + 270), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Mostrar alerta si existe
    if alert_text:
        cv2.putText(image, "ALERTA: Mala postura detectada", (10, h - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(image, "Ver notificación para detalles", (10, h - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

# ==================== 
# PARTE 4: PROGRAMA PRINCIPAL
# ====================
def main():
    video_path = "uyyy.mp4"
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: No se pudo abrir el video")
        return
    
    posture_analyzer = PostureAnalyzer()
    
    with mp_holistic.Holistic(
        min_detection_confidence=0.5, 
        min_tracking_confidence=0.5
    ) as holistic:
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Procesar imagen
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = holistic.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Analizar todos los ángulos si se detectan landmarks
            if results.pose_landmarks:
                posture_data = posture_analyzer.analyze_all_angles(results.pose_landmarks.landmark)
                posture_data, color, alert_text = posture_analyzer.check_all_angles(posture_data)
                draw_all_angles(image, posture_data, color, alert_text)
                
                # Dibujar landmarks de MediaPipe
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_holistic.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
                )
            
            # Mostrar resultado
            cv2.imshow("Analizador de Postura Completa - 4 Ángulos", image)
            
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()