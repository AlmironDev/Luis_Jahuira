from flask import Flask, Response
import cv2

app = Flask(__name__)

def generate_frames():
    video_path = 'VID-20250127-WA0000.mp4'
    while True:
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')  # Agrega esta ruta adicional
def index():
    return """
    <h1>Streaming de Video en Bucle</h1>
    <img src="/video_feed" width="800">
    """
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)