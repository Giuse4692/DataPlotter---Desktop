import webview
import sys
import threading
import time
from streamlit.cli import main as streamlit_main

# -- Configurazione --
APP_FILE = "app.py"  # Il tuo file Streamlit principale
APP_TITLE = "DataPlotter Desktop"
APP_URL = "http://localhost:8501" # Porta fissa per la comunicazione

def run_streamlit():
    """Avvia il server Streamlit in un thread separato."""
    # Imposta gli argomenti per Streamlit
    sys.argv = [
        "streamlit",
        "run",
        APP_FILE,
        "--server.port", "8501",
        "--server.headless", "true",  # Impedisce a Streamlit di aprire un browser
        "--server.enableCORS", "false"
    ]
    streamlit_main()

# --- Avvio App ---
if __name__ == '__main__':
    # 1. Avvia Streamlit in un thread in background
    t = threading.Thread(target=run_streamlit)
    t.daemon = True
    t.start()

    # 2. Aspetta un attimo che Streamlit si avvii
    time.sleep(3) 

    # 3. Crea la finestra desktop (il "pannello")
    window = webview.create_window(APP_TITLE, APP_URL, width=1280, height=800)
    
    # 4. Avvia l'interfaccia grafica
    webview.start()