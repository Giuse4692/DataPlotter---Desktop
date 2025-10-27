import webview
import subprocess
import threading
import time
import sys
import os
import socket
import atexit
import requests  # Per verificare se Streamlit è pronto

# Se eseguibile PyInstaller, cambia la cartella corrente
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

# --- Configurazione ---
APP_FILE = "app.py"
APP_TITLE = "DataPlotter Desktop"
APP_URL = "http://localhost:8501"
SINGLE_INSTANCE_PORT = 12345
STREAMLIT_PORT = 8501
MAX_WAIT = 15  # Massimo tempo di attesa per Streamlit in secondi

def check_single_instance():
    """Controllo istanza unica tramite porta TCP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', SINGLE_INSTANCE_PORT))
        s.listen(1)
        global app_lock_socket
        app_lock_socket = s
        atexit.register(lambda: s.close())  # Chiude il socket all'uscita
        return True
    except OSError:
        return False

def wait_streamlit_ready(url, timeout=MAX_WAIT):
    """Aspetta che Streamlit sia pronto prima di aprire webview."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url)
            return True
        except:
            time.sleep(0.5)
    return False

def run_streamlit():
    """Avvia Streamlit in background."""
    try:
        subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", APP_FILE,
            "--server.port", str(STREAMLIT_PORT),
            "--server.headless", "true",
            "--global.developmentMode", "false",
            "--server.enableCORS", "false"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except Exception as e:
        print(f"Errore avvio Streamlit: {e}")

if __name__ == "__main__":
    # 1. Controllo istanza singola
    if not check_single_instance():
        sys.exit(0)

    # 2. Avvia Streamlit in thread separato
    t = threading.Thread(target=run_streamlit)
    t.daemon = True
    t.start()

    # 3. Aspetta che Streamlit sia pronto
    if not wait_streamlit_ready(APP_URL):
        print(f"Streamlit non ha risposto su {APP_URL} entro {MAX_WAIT} secondi")
        sys.exit(1)

    # 4. Avvia la finestra desktop
    try:
        window = webview.create_window(APP_TITLE, APP_URL, width=1280, height=800)
        webview.start()
    except Exception as e:
        print(f"Errore pywebview: {e}")
