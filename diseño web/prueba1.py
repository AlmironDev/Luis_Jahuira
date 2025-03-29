import cv2

# URL del flujo de video
url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=neb5alh7lepmsurojr62s599i7"

# Inicializar la captura de video desde la URL
cap = cv2.VideoCapture(url)

# Verificar si la conexión se estableció correctamente
if not cap.isOpened():
    print("Error: No se pudo conectar a la cámara.")
    exit()

# Crear un objeto VideoWriter para guardar el video (opcional)
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec de video
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))  # Nombre del archivo, codec, fps, resolución

while True:
    # Capturar frame por frame
    ret, frame = cap.read()

    if not ret:
        print("Error: No se pudo capturar el frame.")
        break

    # Escribir el frame en el archivo de video (opcional)
    out.write(frame)

    # Mostrar el frame en una ventana
    cv2.imshow('Cámara en vivo', frame)

    # Salir del bucle si se presiona la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar el archivo de video
cap.release()
out.release()

# Cerrar todas las ventanas de OpenCV
cv2.destroyAllWindows()