from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

def generate_frames():
    video_path = 'VID-20250127-WA0000.mp4'
    cap = cv2.VideoCapture(video_path)
    
    # Obtener el framerate original del video (FPS)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_delay = 1.0 / fps  # Tiempo que debería durar cada frame en segundos
    
    # Si quieres que vaya más lento, multiplica por un factor (ej. 2 para mitad de velocidad)
    slowdown_factor = 1.0  # 1.0 = velocidad normal, 2.0 = mitad de velocidad, etc.
    frame_delay *= slowdown_factor
    
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reiniciar al inicio del video
        while cap.isOpened():
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret:
                break
                
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Controlar la velocidad
            elapsed = time.time() - start_time
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)
        
        cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return """
    <h1>Streaming de Video en Bucle</h1>
    <img src="/video_feed" width="800">
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)