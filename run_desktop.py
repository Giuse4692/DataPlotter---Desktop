import webview
import socket
import time
import sys
import os
import threading
import subprocess
from streamlit.web import bootstrap

def resource_path(relative_path):
    """ Trova il percorso corretto, sia in sviluppo che in .exe """
    try:
        # PyInstaller crea una cartella temp e ci mette il path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se non siamo in un .exe, usiamo il percorso normale
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def start_streamlit_server():
    """
    Questa funzione viene eseguita SOLO dal processo subprocess.
    Avvia il server Streamlit e si blocca qui.
    """
    print("--- Processo 'SERVER' avviato. Avvio di Streamlit... ---")
    app_path = resource_path('app.py')
    
    # Cambiamo directory per far sì che app.py trovi 'modules'
    os.chdir(resource_path('.')) 
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    # --- QUESTA È LA CORREZIONE (v10) ---
    flag_options = {}
    
    # 1. Rispondiamo all'errore: disabilitiamo la modalità sviluppo.
    flag_options['global.developmentMode'] = False
    
    # 2. Ora che la dev mode è 'False', possiamo impostare la porta.
    flag_options['server.port'] = 8501
    # --- FINE CORREZIONE ---
    
    try:
        # Questo processo è "main thread", quindi i segnali funzionano
        bootstrap.load_config_options(flag_options=flag_options)
        
        # --- MODIFICA (v14) ---
        # Abbiamo provato 'run' (-> TypeError str)
        # Abbiamo provato None (-> TypeError NoneType)
        # Abbiamo provato "" (-> TypeError str)
        # L'errore è "...cannot be interpreted as an integer".
        # Un Booleano (True/False) è un intero in Python. Proviamo True.
        bootstrap.run(app_path, True, [], flag_options=flag_options)
        # --- FINE MODIFICA ---
    except Exception as e:
        print(f"ERRORE SUBPROCESS STREAMLIT: {e}")
        with open("subprocess_error.log", "w") as f:
            f.write(str(e))

def start_main_app():
    """
    Questa funzione viene eseguita dall'utente (App Principale).
    Lancia il subprocess e avvia Pywebview.
    """
    print("--- 'APP PRINCIPALE' avviata. ---")

    def run_streamlit_subprocess():
        """ Funzione eseguita in un thread per non bloccare l'App Principale """
        # Imposta la "bandiera" per dire al prossimo .exe di essere il server
        env = os.environ.copy()
        env["AM_I_STREAMLIT_SERVER"] = "true"
        
        # Nasconde la finestra della console per il processo server
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        try:
            print(f"Avvio del processo server: {sys.executable}")
            # Avvia l'exe stesso, che vedrà la "bandiera" ed eseguirà start_streamlit_server()
            subprocess.Popen([sys.executable], env=env, startupinfo=startupinfo)
            print("Processo server avviato.")
        except Exception as e:
            print(f"ERRORE AVVIO SUBPROCESS: {e}")

    def wait_for_server(port, timeout=40):
        """ Attende che la porta 8501 sia attiva """
        start_time = time.time()
        print(f"In attesa del server Streamlit su http://localhost:{port}...")
        while True:
            try:
                with socket.create_connection(("localhost", port), timeout=1):
                    print("Server Streamlit è pronto!")
                    break
            except (OSError, ConnectionRefusedError):
                if time.time() - start_time > timeout:
                    print(f"Server non ha risposto entro {timeout} secondi.")
                    return False
                time.sleep(0.5)
        return True

    # 1. Avvia il thread che avvierà il processo server
    streamlit_thread = threading.Thread(target=run_streamlit_subprocess, daemon=True)
    streamlit_thread.start()

    # 2. Aspetta il server e avvia Pywebview (nel main thread)
    if wait_for_server(8501, timeout=40):
        print("Avvio finestra PyWebview...")
        webview.create_window('DataPlotter', 'http://localhost:8501')
        webview.start(debug=True)
    else:
        print("Impossibile avviare. Server Streamlit non partito.")
        input("Premi Invio per chiudere...")
        sys.exit(1)

# --- PUNTO DI INGRESSO GLOBALE ---
if __name__ == '__main__':
    # Questo controllo previene il loop infinito.
    if os.environ.get("AM_I_STREAMLIT_SERVER") == "true":
        # Se la "bandiera" è presente, esegui SOLO il server.
        start_streamlit_server()
    else:
        # Altrimenti, esegui l'app GUI principale.
        start_main_app()