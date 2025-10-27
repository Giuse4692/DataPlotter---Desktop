import webview
import socket
import time
import sys
import os
import threading
import subprocess
import requests  # Per scaricare il file

# --- FIX (v25): Importiamo tkinter per la finestra "Salva con nome" ---
import tkinter as tk
from tkinter.filedialog import asksaveasfilename
# --- FINE FIX ---

from streamlit.web import bootstrap

def resource_path(relative_path):
    """ Trova il percorso corretto, sia in sviluppo che in .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def start_streamlit_server():
    """
    Eseguita dal subprocess. Avvia il server Streamlit.
    """
    print("--- Processo 'SERVER' avviato. Avvio di Streamlit... ---")
    app_path = resource_path('app.py')
    
    os.chdir(resource_path('.')) 
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    flag_options = {}
    flag_options['global.developmentMode'] = False
    flag_options['server.port'] = 8501
    flag_options['server.headless'] = True
    flag_options['server.fileWatcherType'] = 'none' 
    flag_options['browser.serverAddress'] = "localhost" 
    flag_options['browser.gatherUsageStats'] = False 
    
    try:
        bootstrap.load_config_options(flag_options=flag_options)
        bootstrap.run(app_path, True, [], flag_options=flag_options)
    except Exception as e:
        print(f"ERRORE SUBPROCESS STREAMLIT: {e}")
        with open("subprocess_error.log", "w", encoding='utf-8') as f:
            f.write(str(e))

# --- FIX DOWNLOAD (v25): Usiamo Tkinter al posto di window.save_dialog ---

def download_in_thread(download_url):
    """
    Funzione di download da eseguire in un thread.
    Chiede dove salvare (usando Tkinter) e scarica con requests.
    """
    try:
        print(f"Download in background (chiamato da JS) avviato: {download_url}")
        
        # 1. Chiede dove salvare (usando il dialogo nativo di Tkinter)
        suggested_filename = download_url.split('/')[-1].split('?')[0] or "downloaded_file"
        
        # Creiamo una finestra Tkinter "nascosta" per il dialogo
        root = tk.Tk()
        root.withdraw() # Nasconde la finestra principale
        root.attributes("-topmost", True) # La mette in primo piano
        
        filepath = asksaveasfilename(
            title="Salva file",
            initialfile=suggested_filename,
            # Aggiungiamo filtri per i file (opzionale ma carino)
            filetypes=[("File Immagine", "*.png *.jpg *.jpeg"), ("Tutti i file", "*.*")]
        )
        
        root.destroy() # Chiude la finestra nascosta
        
        if not filepath:
            print("Download annullato dall'utente.")
            return

        # 2. Scarica il file
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        print(f"Download completato: {filepath}")
    except Exception as e:
        print(f"ERRORE nel thread di download: {e}")

class Api:
    """
    Classe esposta a JavaScript.
    JS chiamerà pywebview.api.handle_download(url)
    """
    def handle_download(self, url):
        print(f"API Python chiamata da JS: {url}")
        # Avvia il download "professionale" (con Tkinter) in un thread
        threading.Thread(target=download_in_thread, args=(url,), daemon=True).start()

# Flag per assicurarci di iniettare lo script JS solo una volta
js_injected = False

def on_page_loaded():
    """
    Chiamato quando la pagina è caricata.
    Lo usiamo per iniettare il nostro script (solo una volta).
    """
    global js_injected, window
    
    current_url = window.get_current_url()
    print(f"Pagina caricata: {current_url}")

    # Iniettiamo lo script solo la prima volta che la pagina principale carica
    if not js_injected and current_url and "localhost:8501" in current_url:
        print("Iniezione dello script 'Download Interceptor' (v25)...")
        
        js_code = """
            console.log('Interceptor (v25) in esecuzione. Ridefinizione di HTMLAnchorElement.prototype.click...');
            
            const originalAnchorClick = HTMLAnchorElement.prototype.click;

            HTMLAnchorElement.prototype.click = function() {
                console.log('Intercepted <a>.click(). Href:', this.href);
                
                // Controlliamo se 'this.href' esiste e se è un link di download
                if (this.href && this.href.includes('/media/')) {
                    // È un download di Streamlit!
                    console.log('Download Streamlit rilevato, passo a Python.');
                    // Chiama la nostra API Python
                    window.pywebview.api.handle_download(this.href);
                } else {
                    // È un link normale (o un'ancora #), usa la funzione originale
                    originalAnchorClick.apply(this, arguments);
                }
            };
            console.log('HTMLAnchorElement.prototype.click ridefinito.');
        """
        
        window.evaluate_js(js_code)
        js_injected = True
        print("Script iniettato.")

# --- Fine Sezione Download (v25) ---


def start_main_app():
    """
    Questa funzione viene eseguita dall'utente (App Principale).
    Lancia il subprocess e avvia Pywebview.
    """
    print("--- 'APP PRINCIPALE' avviata. ---")

    def run_streamlit_subprocess():
        """ Funzione eseguita in un thread per non bloccare l'App Principale """
        env = os.environ.copy()
        env["AM_I_STREAMLIT_SERVER"] = "true"
        
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        try:
            print(f"Avvio del processo server: {sys.executable}")
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
        
        global window
        api = Api()
        window = webview.create_window(
            'DataPlotter', 
            'http://localhost:8501',
            js_api=api  # Esponiamo la classe Api a JavaScript
        )
        
        window.events.loaded += on_page_loaded
        
        webview.start(debug=True)
    else:
        print("Impossibile avviare. Server Streamlit non partito.")
        input("Premi Invio per chiudere...")
        sys.exit(1)

# --- PUNTO DI INGRESSO GLOBALE ---
if __name__ == '__main__':
    # Questo controllo previene il loop infinito.
    if os.environ.get("AM_I_STREAMLIT_SERVER") == "true":
        start_streamlit_server()
    else:
        start_main_app()