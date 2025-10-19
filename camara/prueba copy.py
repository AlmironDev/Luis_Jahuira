import cv2

usuario = "admin"
clave = "Jahuira123456"
ip_publica = "147.79.110.180"  # IP de tu servidor
puertos = [8554, 8555]

for puerto in puertos:
    url = f"rtsp://{usuario}:{clave}@{ip_publica}:{puerto}/cam/realmonitor?channel=1&subtype=0"
    print(f"🔌 Probando cámara en puerto {puerto} ...")
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print(f"❌ No se pudo conectar a la cámara en {puerto}")
        continue

    ret, frame = cap.read()
    if ret:
        print(f"✅ Cámara conectada correctamente en {puerto}")
    else:
        print(f"⚠️ Se conectó pero no recibe video en {puerto}")

    cap.release()
