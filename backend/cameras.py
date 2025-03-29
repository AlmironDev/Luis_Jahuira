import cv2
import numpy as np
import threading
import time
from typing import Dict, Optional
from detection import MotionDetector

class CameraManager:
    def __init__(self):
        self.active_cameras: Dict[str, dict] = {}
        self.camera_threads: Dict[str, threading.Thread] = {}
        self.last_frames: Dict[str, bytes] = {}
        self.lock = threading.Lock()

    def get_active_cameras(self) -> dict:
        """Retorna información de las cámaras activas"""
        return {cam_id: {"status": "active"} for cam_id in self.active_cameras.keys()}

    def add_camera(self, camera_id: str, rtsp_url: str, sensitivity: float = 0.5, min_area: int = 500) -> str:
        """Agrega una nueva cámara para monitoreo"""
        if camera_id in self.active_cameras:
            raise ValueError(f"Camera {camera_id} already exists")

        # Configurar el detector de movimiento
        detector = MotionDetector(sensitivity=sensitivity, min_area=min_area)

        # Iniciar el hilo para esta cámara
        thread = threading.Thread(
            target=self._camera_worker,
            args=(camera_id, rtsp_url, detector),
            daemon=True
        )
        
        with self.lock:
            self.active_cameras[camera_id] = {
                "rtsp_url": rtsp_url,
                "detector": detector,
                "running": True
            }
            self.camera_threads[camera_id] = thread
            thread.start()

        return camera_id

    def remove_camera(self, camera_id: str):
        """Detiene y remueve una cámara"""
        if camera_id not in self.active_cameras:
            raise KeyError(f"Camera {camera_id} not found")

        with self.lock:
            self.active_cameras[camera_id]["running"] = False
            del self.active_cameras[camera_id]
            
            if camera_id in self.last_frames:
                del self.last_frames[camera_id]

        # Esperar a que el hilo termine
        if camera_id in self.camera_threads:
            self.camera_threads[camera_id].join(timeout=2)
            del self.camera_threads[camera_id]

    def get_camera_frame(self, camera_id: str) -> Optional[bytes]:
        """Obtiene el último frame procesado de una cámara"""
        return self.last_frames.get(camera_id)

    def _camera_worker(self, camera_id: str, rtsp_url: str, detector: MotionDetector):
        """Hilo worker que procesa los frames de la cámara"""
        cap = cv2.VideoCapture(rtsp_url)
        
        try:
            while self.active_cameras.get(camera_id, {}).get("running", False):
                ret, frame = cap.read()
                if not ret:
                    time.sleep(1)
                    continue

                # Procesar detección de movimiento
                processed_frame, motion_detected = detector.detect(frame)

                # Codificar frame como JPEG
                _, buffer = cv2.imencode('.jpg', processed_frame)
                frame_bytes = buffer.tobytes()

                # Guardar el último frame
                with self.lock:
                    self.last_frames[camera_id] = frame_bytes

                # Pequeña pausa para no saturar
                time.sleep(0.03)
        finally:
            cap.release()