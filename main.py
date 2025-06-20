import threading
import webview
import subprocess
import time
import socket
import sys
import os
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """Devuelve la ruta absoluta compatible con PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    full_path = os.path.join(base_path, relative_path)

    if not os.path.exists(full_path):
        logger.warning(f"No encontrado: {full_path}. Probando ruta de desarrollo...")
        dev_path = os.path.join(os.path.abspath("."), relative_path)
        if os.path.exists(dev_path):
            return dev_path

    return full_path

def run_flask():
    try:
        ruta_app = resource_path(os.path.join("backend", "app.py"))
        logger.info(f"Iniciando Flask desde: {ruta_app}")

        if not os.path.exists(ruta_app):
            logger.error(f"Archivo app.py no encontrado: {ruta_app}")
            return False

        # Ejecutar app.py como script
        command = [sys.executable, ruta_app]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )

        # Capturar la salida para log
    except Exception as e:
        logger.error(f"Error al iniciar Flask: {e}")
        return False
# ...existing code...

    def log_output(pipe, log_method, is_stderr=False):
        for line in iter(pipe.readline, b''):
            decoded = line.decode(errors='ignore').strip()
            if is_stderr:
                if "WARNING" in decoded:
                    logger.warning(decoded)
                elif "INFO" in decoded:
                    logger.info(decoded)
                elif "ERROR" in decoded or "Traceback" in decoded:
                    logger.error(decoded)
                else:
                    logger.warning(decoded)
            else:
                log_method(decoded)

    # ...en tu función run_flask, reemplaza los hilos así:
    threading.Thread(target=log_output, args=(process.stdout, logger.info, False), daemon=True).start()
    threading.Thread(target=log_output, args=(process.stderr, logger.error, True), daemon=True).start()
    return process

# ...existing code...

def wait_for_flask(port=5000, timeout=30):
    logger.info("Esperando que Flask se inicie...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                logger.info("Flask activo")
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error al verificar puerto: {e}")
            break
    return False

def show_error_message(message):
    """Ventana emergente de error en HTML simple"""
    try:
        error_window = webview.create_window("Error", html=f"<h1 style='color:red;'>Error</h1><p>{message}</p>", width=400, height=200)
        webview.start()
    except:
        logger.error(f"No se pudo mostrar ventana de error: {message}")

if __name__ == '__main__':
    try:
        logger.info("Iniciando aplicación...")

        if not run_flask():
            show_error_message("No se pudo iniciar el servidor Flask. Verifique app.log")
            sys.exit(1)

        if wait_for_flask(5000):
            logger.info("Cargando ventana principal...")
            window = webview.create_window(
                "Mi Sistema",
                "http://localhost:5000",
                width=1024,
                height=768,
                resizable=True,
                text_select=True
            )
            webview.start()
        else:
            msg = "El servidor Flask no respondió a tiempo. Verifique app.log"
            logger.error(msg)
            show_error_message(msg)

    except Exception as e:
        msg = f"Error inesperado: {str(e)}"
        logger.error(msg)
        show_error_message(msg)

    finally:
        logger.info("Aplicación finalizada.")
