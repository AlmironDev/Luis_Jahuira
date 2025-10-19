import cv2
import threading
import time
import numpy as np
from flask import Response
import mediapipe as mp


class VideoStreamer:
    def __init__(self):
        self.cameras = {}
        self.lock = threading.Lock()
        self.running_threads = {}
        
        # Configuración de MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def start_camera(self, cam_id, url):
        """Inicia el hilo de streaming para la cámara."""
        with self.lock:
            if cam_id in self.cameras:
                print(f"⚠️ Cámara {cam_id} ya está en ejecución")
                return
            
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                print(f"❌ No se pudo abrir la cámara {cam_id}")
                return

            # Configuración para bajo latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FPS, 15)
            
            self.cameras[cam_id] = {
                "cap": cap, 
                "frame": None, 
                "active": True,
                "last_update": time.time()
            }
            
            # Iniciar hilo de procesamiento
            self.running_threads[cam_id] = True
            t = threading.Thread(target=self._process_camera_feed, args=(cam_id,), daemon=True)
            t.start()
            print(f"✅ VideoStreamer: Cámara {cam_id} iniciada")

    def _process_camera_feed(self, cam_id):
        """Procesa los frames de la cámara con MediaPipe."""
        cap = self.cameras[cam_id]["cap"]
        frame_count = 0
        process_every_n_frames = 2  # Procesar cada 2 frames para mejor performance
        
        while self.running_threads.get(cam_id, False):
            try:
                ret, frame = cap.read()
                if not ret:
                    print(f"⚠️ VideoStreamer: No se pudo leer frame de cámara {cam_id}")
                    time.sleep(0.1)
                    continue

                frame_count += 1
                
                # Procesar con MediaPipe solo cada N frames
                if frame_count % process_every_n_frames == 0:
                    processed_frame = self._apply_mediapipe_processing(frame)
                else:
                    # Usar el frame anterior procesado para mantener fluidez
                    with self.lock:
                        previous_frame = self.cameras[cam_id].get("frame")
                        processed_frame = previous_frame if previous_frame is not None else frame

                # Actualizar frame procesado
                with self.lock:
                    if cam_id in self.cameras:
                        self.cameras[cam_id]["frame"] = processed_frame
                        self.cameras[cam_id]["last_update"] = time.time()

            except Exception as e:
                print(f"❌ VideoStreamer: Error en cámara {cam_id}: {e}")
                time.sleep(0.1)

    def _apply_mediapipe_processing(self, frame):
        """Aplica MediaPipe Face Mesh al frame."""
        try:
            # Voltear el frame para efecto espejo
            # frame = cv2.flip(frame, 1)
            
            # Convertir BGR a RGB para MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            
            # Procesar con MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            # Volver a hacer writeable
            rgb_frame.flags.writeable = True
            processed_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            
            # Dibujar líneas de referencia
            height, width, _ = processed_frame.shape
            cv2.line(processed_frame, (0, height//2), (width, height//2), (255, 0, 0), 2)
            cv2.line(processed_frame, (width//2, 0), (width//2, height), (0, 0, 255), 2)
            
            # Dibujar landmarks si se detectan caras
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Dibujar malla completa
                    self.mp_drawing.draw_landmarks(
                        image=processed_frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_face_mesh_tesselation_style()
                    )
                    
                    # Dibujar contornos
                    self.mp_drawing.draw_landmarks(
                        image=processed_frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_face_mesh_contours_style()
                    )
            
            return processed_frame
            
        except Exception as e:
            print(f"❌ Error en procesamiento MediaPipe: {e}")
            return frame

    def stop_stream(self, cam_id):
        """Detiene el streaming de una cámara."""
        with self.lock:
            if cam_id in self.running_threads:
                self.running_threads[cam_id] = False
            
            if cam_id in self.cameras:
                cam = self.cameras[cam_id]
                if cam["cap"] and cam["cap"].isOpened():
                    cam["cap"].release()
                del self.cameras[cam_id]
                print(f"🛑 VideoStreamer: Cámara {cam_id} detenida")

    def is_camera_active(self, cam_id):
        """Verifica si una cámara está activa en VideoStreamer."""
        with self.lock:
            cam = self.cameras.get(cam_id)
            if not cam:
                return False
            # Considerar inactiva si no ha actualizado en 15 segundos
            return time.time() - cam.get("last_update", 0) < 15


video_streamer = VideoStreamer()