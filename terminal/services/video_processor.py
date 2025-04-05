import cv2
import mediapipe as mp
import numpy as np
from threading import Thread
from queue import Queue
import time

class VideoProcessor:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.active_streams = {}
        
    def process_stream(self, camera_id, url):
        cap = cv2.VideoCapture(url)
        frame_queue = Queue(maxsize=1)
        self.active_streams[camera_id] = {'queue': frame_queue, 'active': True}
        
        while self.active_streams[camera_id]['active']:
            success, frame = cap.read()
            if not success:
                time.sleep(0.1)
                continue
                
            # Procesamiento con MediaPipe
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = self.pose.process(image)
            
            # Dibujar landmarks
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2))
            
            # Codificar y poner en cola
            _, buffer = cv2.imencode('.jpg', image)
            if not frame_queue.full():
                frame_queue.put(buffer.tobytes())
                
        cap.release()
        del self.active_streams[camera_id]
        
    def stop_stream(self, camera_id):
        if camera_id in self.active_streams:
            self.active_streams[camera_id]['active'] = False

    def get_frame(self, camera_id):
        if camera_id in self.active_streams:
            try:
                return self.active_streams[camera_id]['queue'].get_nowait()
            except:
                return None
        return None