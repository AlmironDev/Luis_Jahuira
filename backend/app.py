import cv2
import time
from config.default_config import DEFAULT_CONFIG
from detectors.posture_detector import PostureDetector
from detectors.hand_detector import HandDetector
from notifications.desktop_notifier import DesktopNotifier

class PostureDetectionApp:
    def __init__(self, config):
        self.config = config
        self.detectors = []
        self.notifier = DesktopNotifier(config['notifications'])
        self._initialize_detectors()
        
    def _initialize_detectors(self):
        if self.config['detectors']['posture']['enabled']:
            self.detectors.append(PostureDetector(self.config['detectors']['posture']))
        
        if self.config['detectors']['hands']['enabled']:
            self.detectors.append(HandDetector(self.config['detectors']['hands']))
    
    def update_config(self, new_config):
        """Actualiza la configuración de la aplicación"""
        for section, values in new_config.items():
            if section in self.config:
                self.config[section].update(values)
        
        # Reiniciar detectores con nueva configuración
        self.detectors = []
        self._initialize_detectors()
        
        if 'notifications' in new_config:
            self.notifier = DesktopNotifier(self.config['notifications'])
    
    def run(self):
        cap = cv2.VideoCapture(self.config['video']['source'])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['video']['width'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['video']['height'])
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                processed_frame = frame.copy()
                all_conditions = []
                
                for detector in self.detectors:
                    processed_frame = detector.process_frame(processed_frame)
                    conditions_met, conditions = detector.check_conditions()
                    
                    if conditions_met:
                        all_conditions.extend(conditions)
                    
                    processed_frame = detector.draw_results(processed_frame)
                
                # Mostrar alertas si hay condiciones detectadas
                if all_conditions and self.config['notifications']['enabled']:
                    for condition_type, message in all_conditions:
                        self.notifier.show_notification("Alerta de Postura", message)
                        self.notifier.log_event(condition_type, message)
                
                cv2.imshow('Posture Detection', processed_frame)
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    # Ejemplo de cómo cambiar la configuración desde el frontend
    custom_config = {
        'detectors': {
            'posture': {
                'leg_angle_threshold': 300,  # Ajustar parámetro
                'neck_angle_threshold': 40
            },
            'hands': {
                'max_elbow_distance': 0.35
            }
        },
        'notifications': {
            'notification_cooldown': 20
        }
    }
    
    app = PostureDetectionApp(DEFAULT_CONFIG)
    
    # Actualizar configuración (esto podría venir de una API desde React)
    app.update_config(custom_config)
    
    app.run()