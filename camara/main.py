import cv2

usuario = "admin"
clave = "admin123"
ips = ["192.168.18.30", "192.168.18.31"]

caps = []
for ip in ips:
    url = f"rtsp://{usuario}:{clave}@{ip}:554/cam/realmonitor?channel=1&subtype=0"
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        print(f"✅ Cámara conectada: {ip}")
        caps.append((ip, cap))
    else:
        print(f"❌ No se pudo conectar: {ip}")

while True:
    for ip, cap in caps:
        ret, frame = cap.read()
        if ret:
            cv2.imshow(f"Camara {ip}", frame)
    if cv2.waitKey(1) == 27:  # ESC
        break

for _, cap in caps:
    cap.release()
cv2.destroyAllWindows()
