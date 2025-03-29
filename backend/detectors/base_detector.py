from abc import ABC, abstractmethod
import cv2
import mediapipe as mp

class BaseDetector(ABC):
    def __init__(self, config):
        self.config = config
        self._setup_mediapipe()

    def _setup_mediapipe(self):
        """Configuración inicial de MediaPipe"""
        self.mp_drawing = mp.solutions.drawing_utils
        self.results = None

    @abstractmethod
    def process_frame(self, frame):
        """Procesa un frame y devuelve resultados"""
        pass

    @abstractmethod
    def draw_results(self, frame):
        """Dibuja los resultados en el frame"""
        pass

    @abstractmethod
    def check_conditions(self):
        """Verifica condiciones específicas de detección"""
        pass

    def update_config(self, new_config):
        """Actualiza la configuración del detector"""
        self.config.update(new_config)