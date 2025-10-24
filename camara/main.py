import socket
import concurrent.futures
import time


# ✅ Puerto RTSP abierto en: 192.168.1.68
# ✅ Puerto RTSP abierto en: 192.168.1.67

def probar_puerto(ip, puerto=554, timeout=1):
    """Prueba si un puerto está abierto usando sockets (más rápido)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            resultado = sock.connect_ex((ip, puerto))
            return resultado == 0
    except:
        return False


def encontrar_camaras():
    """Encuentra cámaras buscando puertos RTSP abiertos."""
    # Rangos de IP locales comunes
    rangos_ip = (
        [f"192.168.1.{i}" for i in range(1, 255)]
        + [f"192.168.0.{i}" for i in range(1, 255)]
        + [f"192.168.18.{i}" for i in range(1, 255)]
    )

    print("🚀 Escaneando puertos RTSP (554)...")
    print(f"🔍 Probando {len(rangos_ip)} IPs...\n")

    inicio = time.time()
    ips_con_puerto_abierto = []

    # Escanear puertos en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        resultados = executor.map(probar_puerto, rangos_ip)

        for ip, puerto_abierto in zip(rangos_ip, resultados):
            if puerto_abierto:
                print(f"✅ Puerto RTSP abierto en: {ip}")
                ips_con_puerto_abierto.append(ip)

    # Probar credenciales solo en IPs con puerto abierto
    print(f"\n🔑 Probando credenciales en {len(ips_con_puerto_abierto)} IPs...")

    camaras_encontradas = probar_credenciales(ips_con_puerto_abierto)

    tiempo_total = time.time() - inicio
    print(f"\n🏁 Escaneo completado en {tiempo_total:.1f}s")
    print(f"📹 Cámaras encontradas: {len(camaras_encontradas)}")

    for camara in camaras_encontradas:
        print(f"   📍 {camara}")


def probar_credenciales(ips):
    """Prueba combinaciones de usuario/contraseña en IPs con puerto abierto."""
    import cv2

    credenciales = [
        ("admin", "admin123"),
    ]

    rutas = [
        "/cam/realmonitor?channel=1&subtype=0",
        "/live/ch0",
        "/h264",
        "/11",
        "/stream1",
        "/video",
    ]

    camaras_validas = []

    for ip in ips:
        for usuario, clave in credenciales:
            for ruta in rutas:
                url = f"rtsp://{usuario}:{clave}@{ip}:554{ruta}"
                try:
                    cap = cv2.VideoCapture(url)
                    # Timeout muy corto para prueba rápida
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 500)
                    ret, frame = cap.read()
                    cap.release()

                    if ret:
                        print(f"🎯 Cámara encontrada: {usuario}:{clave} @ {ip}")
                        camaras_validas.append(f"{ip} - {usuario}:{clave}")
                        return camaras_validas  # Encontró una, continuar
                except:
                    pass

    return camaras_validas


if __name__ == "__main__":
    encontrar_camaras()
