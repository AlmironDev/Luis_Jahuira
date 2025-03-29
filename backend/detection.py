import cv2
import numpy as np
from typing import Tuple

class MotionDetector:
    def __init__(self, sensitivity: float = 0.5, min_area: int = 500):
        self.sensitivity = max(0.1, min(sensitivity, 1.0))
        self.min_area = max(100, min(min_area, 5000))
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=100, varThreshold=25, detectShadows=False
        )
        self.first_frame = None

    def detect(self, frame) -> Tuple[np.ndarray, bool]:
        """Procesa un frame y detecta movimiento"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Inicializar el primer frame si es necesario
        if self.first_frame is None:
            self.first_frame = gray
            return frame, False

        # Calcular la diferencia absoluta entre el frame actual y el primero
        frame_delta = cv2.absdiff(self.first_frame, gray)
        thresh = cv2.threshold(
            frame_delta, 
            int(25 * self.sensitivity), 
            255, 
            cv2.THRESH_BINARY
        )[1]

        # Dilatar la imagen threshold para llenar los huecos
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(
            thresh.copy(), 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue

            motion_detected = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return frame, motion_detected