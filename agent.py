# agent.py
"""
Agente SMAT para máquinas del laboratorio de computación.
Envía información de procesos no autorizados al servidor central.

Configuración (variables de entorno):
- SMAT_SERVER_URL: URL base del servidor (ej: http://192.168.1.10:8000)
- SMAT_SERVER_HOST: Host del servidor (ej: 192.168.1.10) - alternativa a SERVER_URL
- SMAT_SERVER_PORT: Puerto del servidor (default: 8000)
- SMAT_BATCH_INTERVAL: Segundos entre escaneos (default: 5)
- SMAT_POST_TIMEOUT: Timeout en segundos para requests (default: 5.0)
"""
import psutil
import requests
import time
import socket
import datetime
import os
import sys

# Configuración
def get_server_url():
    """Obtiene la URL del servidor desde variables de entorno."""
    # Opción 1: URL completa directa
    if "SMAT_SERVER_URL" in os.environ:
        return os.environ["SMAT_SERVER_URL"]
    
    # Opción 2: Host + Puerto
    host = os.getenv("SMAT_SERVER_HOST", "192.168.1.10")
    port = os.getenv("SMAT_SERVER_PORT", "8000")
    return f"http://{host}:{port}/events/"

SERVER_URL = get_server_url()
BATCH_INTERVAL = int(os.getenv("SMAT_BATCH_INTERVAL", "5"))
POST_TIMEOUT = float(os.getenv("SMAT_POST_TIMEOUT", "5.0"))

# Whitelist: procesos autorizados (no se envían)
WHITE_LIST_ENV = os.getenv("SMAT_WHITE_LIST", None)
if WHITE_LIST_ENV:
    WHITE_LIST = [p.strip() for p in WHITE_LIST_ENV.split(",") if p.strip()]
else:
    # Whitelist por defecto: procesos del sistema permitidos
    WHITE_LIST = [
        "chrome.exe", 
        "firefox.exe",
        "explorer.exe",
        "notepad.exe",
        "code.exe",
        "python.exe",
        "java.exe",
        "notepad++.exe",
        "vlc.exe"
    ]

def local_ip():
    """Intentar obtener IP local de forma segura."""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        # fallback: abrir socket UDP a un destino público sin enviar datos
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

def send_batch_http(batch):
    """Envía un lote de eventos al servidor."""
    if not batch:
        return
    try:
        res = requests.post(SERVER_URL, json=batch, timeout=POST_TIMEOUT)
        status = "OK" if res.status_code == 200 else "WARN"
        print(f"[{status}] [{datetime.datetime.now().strftime('%H:%M:%S')}] HTTP {res.status_code} - {len(batch)} eventos enviados")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] No se puede conectar a {SERVER_URL}")
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] Timeout conectando a {SERVER_URL}")
    except Exception as e:
        print(f"[ERROR] Error al enviar: {type(e).__name__}: {e}")

def monitoring():
    """Monitorea procesos y envía los no autorizados al servidor."""
    hostname = socket.gethostname()
    ip_addr = local_ip()
    
    print(f"[SMAT] Iniciando monitoreo desde: {hostname} ({ip_addr})")
    print(f"[SMAT] Servidor: {SERVER_URL}")
    print(f"[SMAT] Intervalo de escaneo: {BATCH_INTERVAL}s")
    print(f"[SMAT] Procesos en whitelist: {len(WHITE_LIST)}")
    print("-" * 60)
    
    while True:
        try:
            batch = []
            # Recorremos procesos y añadimos solo los NO whitelist
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info.get('name') or ""
                    pid = proc.info.get('pid')
                    if not name:
                        continue
                    
                    # Normalizar nombre a minúsculas para comparar
                    if name.lower() in (p.lower() for p in WHITE_LIST):
                        # Este proceso está autorizado, no lo enviamos
                        continue
                    
                    # Proceso NO autorizado: agregarlo al lote
                    event = {
                        "proceso": name,
                        "pid": int(pid) if pid is not None else 0,
                        "fecha": datetime.datetime.now().isoformat(),
                        "pc": hostname,
                        "ip": ip_addr
                    }
                    batch.append(event)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    print(f"[WARN] Error procesando {name}: {e}")
            
            # Enviar lote si hay eventos
            if batch:
                send_batch_http(batch)
            
            time.sleep(BATCH_INTERVAL)
        except KeyboardInterrupt:
            print("\n[INFO] Monitoreo detenido por usuario")
            break
        except Exception as e:
            print(f"[ERROR] Error en loop de monitoreo: {e}")
            time.sleep(BATCH_INTERVAL)

if __name__ == "__main__":
    try:
        monitoring()
    except KeyboardInterrupt:
        print("\n[INFO] Agente SMAT finalizado")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error fatal: {e}")
        sys.exit(1)
