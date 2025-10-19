import cv2
import threading
import time
from database import get_db_connection
from services.video_streamer import video_streamer


class CameraManager:
    def __init__(self, refresh_interval=10):
        self.cameras = {}
        self.refresh_interval = refresh_interval
        self.lock = threading.Lock()
        self.running = False
        self.monitor_thread = None

    def start(self):
        """Inicia el monitor de cámaras activas."""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            print("🎥 Camera monitor iniciado")

    def stop(self):
        """Detiene todas las cámaras."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        with self.lock:
            for cam_id in list(self.cameras.keys()):
                self._close_camera(cam_id)
            self.cameras.clear()

    def _monitor(self):
        """Monitorea la base de datos y sincroniza cámaras activas."""
        while self.running:
            try:
                conn = get_db_connection()
                active_cameras = conn.execute(
                    "SELECT id, url FROM camaras WHERE activa = 1"
                ).fetchall()
                conn.close()

                active_ids = {c["id"] for c in active_cameras}

                with self.lock:
                    # Cerrar cámaras inactivas
                    current_camera_ids = list(self.cameras.keys())
                    for cam_id in current_camera_ids:
                        if cam_id not in active_ids:
                            self._close_camera(cam_id)

                    # Abrir nuevas cámaras activas
                    for cam in active_cameras:
                        if cam["id"] not in self.cameras:
                            self._initialize_camera(cam["id"], cam["url"])

                    # Verificar estado de cámaras existentes
                    self._check_camera_status()

            except Exception as e:
                print(f"❌ Error en monitor de cámaras: {e}")

            time.sleep(self.refresh_interval)

    def _initialize_camera(self, cam_id, url):
        """Inicializa una nueva cámara."""
        # Verificar que la cámara es accesible
        test_cap = cv2.VideoCapture(url)
        if not test_cap.isOpened():
            print(f"❌ No se pudo conectar a cámara {cam_id} con URL: {url}")
            test_cap.release()
            return False
        
        test_cap.release()
        
        # Registrar en tracking interno
        self.cameras[cam_id] = {
            "url": url,
            "active": True,
            "last_check": time.time()
        }
        
        # Iniciar en VideoStreamer para procesamiento
        video_streamer.start_camera(cam_id, url)
        print(f"✅ Cámara {cam_id} inicializada correctamente")
        return True

    def _close_camera(self, cam_id):
        """Cierra una cámara específica."""
        if cam_id in self.cameras:
            video_streamer.stop_stream(cam_id)
            self.cameras.pop(cam_id)
            print(f"🛑 Cámara {cam_id} cerrada (inactiva)")

    def _check_camera_status(self):
        """Verifica el estado de las cámaras."""
        for cam_id in list(self.cameras.keys()):
            if not video_streamer.is_camera_active(cam_id):
                print(f"⚠️ Cámara {cam_id} reportada como inactiva, reintentando...")
                url = self.cameras[cam_id]["url"]
                video_streamer.stop_stream(cam_id)
                time.sleep(1)
                video_streamer.start_camera(cam_id, url)
                
                if video_streamer.is_camera_active(cam_id):
                    print(f"✅ Cámara {cam_id} reconectada")
                else:
                    print(f"❌ No se pudo reconectar cámara {cam_id}")

    def get_frame(self, camera_id):
        """Obtiene un frame PROCESADO de VideoStreamer."""
        try:
            # Obtener el frame procesado de VideoStreamer
            with video_streamer.lock:
                cam_data = video_streamer.cameras.get(camera_id)
                if not cam_data:
                    return None
                return cam_data.get("frame")
        except Exception as e:
            print(f"❌ Error obteniendo frame procesado de cámara {camera_id}: {e}")
            return None

    def get_active_cameras(self):
        """Retorna lista de cámaras activas."""
        with self.lock:
            return list(self.cameras.keys())

    def is_camera_active(self, camera_id):
        """Verifica si una cámara está activa."""
        with self.lock:
            return camera_id in self.cameras and self.cameras[camera_id].get("active", False)


camera_manager = CameraManager(refresh_interval=15)