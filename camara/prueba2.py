import socket

base = "192.168.18."
puerto = 554

for i in range(1, 255):
    ip = base + str(i)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    try:
        result = sock.connect_ex((ip, puerto))
        if result == 0:
            print(f"🎥 Posible cámara en {ip}")
    except:
        pass
    finally:
        sock.close()
