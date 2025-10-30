Documentazione Tecnica DataPlotter (Streamlit Desktop App)

Versione Documento: 2.0 (Analisi Dettagliata dei Moduli)

Questo documento descrive l'architettura, i componenti chiave, le dipendenze e i flussi operativi dell'applicazione desktop DataPlotter. La comprensione di questi concetti è fondamentale per la manutenzione e l'aggiornamento futuri del progetto.

1. Architettura Fondamentale: Il Modello Ibrido

L'applicazione non è un eseguibile Python tradizionale. È un'app ibrida che sfrutta un'architettura Client-Server impacchettata in un unico eseguibile:

Il Server (Processo #1): Una versione "headless" (senza testa) di Streamlit che gira in background. È responsabile di eseguire la logica Python (app.py, modules/), generare l'HTML/CSS/JS e servire i dati sulla porta localhost:8501.

Il Client (Processo #2): Una finestra desktop nativa creata con Pywebview. Questa finestra funge da "browser" leggero che punta esclusivamente a localhost:8501.

L'intero pacchetto (run_desktop.py) è progettato per orchestrare l'avvio e la comunicazione tra questi due processi.

2. Componenti Chiave e Dipendenze

Il successo dell'app dipende dalla stretta interazione di questi file e dalle dipendenze che includiamo nel build.

2.1 Dipendenze Critiche (per il Build)

Libreria

Scopo nel Progetto

Flag di Build Richiesto

streamlit

Core dell'applicazione (logica, UI).

--collect-all=streamlit

pywebview

Crea la finestra desktop nativa (il client).

(Nessuno, importato da run_desktop.py)

pyinstaller

Compilatore che crea l'.exe.

(Il comando stesso)

requests

Usato da run_desktop.py per il download in background.

(Incluso automaticamente)

tkinter

Usato da run_desktop.py per la finestra "Salva con nome...".

(Incluso automaticamente)

tornado

Dipendenza server di Streamlit.

--collect-all=tornado

pandas

Gestione e manipolazione dei dati (DataFrame).

(Incluso automaticamente)

plotly

Creazione dei grafici 2D e 3D interattivi.

(Incluso automaticamente)

kaleido

(Opzionale) Per esportare immagini statiche (PNG/JPEG) da Plotly.

(Incluso automaticamente se installato)

2.2 Ruolo dei File di Progetto (Panoramica)

File

Responsabilità Principale

Interazione Chiave

run_desktop.py (v32)

IL CERVELLO. Gestisce l'avvio, la finestra, l'iniezione JS e il download.

Avvia app.py e ospita la finestra.

app.py

IL CUORE. Punto di ingresso di Streamlit, gestisce il layout a schede (Tabs).

Chiama importer, plotting e data_viewer.

modules/ (cartella)

Contenitore per tutta la logica di business.

Inclusa con --add-data="modules;modules".

3. Analisi Dettagliata dei Moduli

Questa sezione descrive ogni file della logica di business.

3.1 run_desktop.py (Il Cervello)

Scopo: È il file di avvio dell'eseguibile. Gestisce l'orchestrazione dei processi e i "trucchi" per far funzionare i download.

Logica Principale (Avvio):

Implementa il "Doppio Processo" (vedi Sezione 4) per evitare loop infiniti.

start_main_app(): Eseguito dall'utente. Avvia il processo server in background (run_streamlit_subprocess) e poi attende (wait_for_server) che la porta 8501 sia attiva.

start_streamlit_server(): Eseguito solo dal processo server. Avvia Streamlit (bootstrap.run) con flag "headless" (server.headless = True, server.fileWatcherType = 'none', ecc.) per impedire l'apertura del browser.

Logica Principale (Finestra):

Usa webview.create_window per creare la finestra desktop.

CRUCIALE: Espone la Api a JavaScript (js_api=api). Questo è il "ponte" che permette a JS di chiamare Python.

Imposta debug=False per nascondere i DevTools nella versione finale.

Logica di Download (Il "Trucco"):

on_page_loaded(): Evento che scatta al caricamento della pagina. Inietta il js_code.

js_code (Stringa JavaScript):

Monkey-Patching: Ridefinisce HTMLAnchorElement.prototype.click.

Intercettazione: Quando Streamlit (da export_utils.py) chiama .click() su un link di download, questo script lo intercetta.

Lettura Titolo: Esegue document.getElementById('graph-title-id').innerText per leggere il titolo del grafico (es. "Intensity vs Wavenumber") dall'HTML nascosto (creato da plotting.py).

Chiamata Python: Chiama l'API esposta: window.pywebview.api.handle_download(url, nome_titolo).

Api.handle_download(url, filename): Funzione Python chiamata da JS. Avvia download_in_thread per non bloccare la UI.

download_in_thread(url, filename):

Usa tkinter.Tk() e tkinter.asksaveasfilename per aprire la finestra "Salva con nome..." nativa.

Usa initialfile=filename per pre-compilare il nome del file con il titolo del grafico.

Usa requests.get() per scaricare il file in background.

3.2 app.py (Il Cuore)

Scopo: Punto di ingresso di Streamlit. Definisce la struttura principale della pagina.

Logica:

Imposta la configurazione della pagina (st.set_page_config).

Chiama importer.load_data_flexible() per ottenere il DataFrame (df).

Se df esiste, crea il layout a schede: st.tabs(["Costruttore Grafici", "Anteprima Dati", "Impostazioni"]).

Delega la Logica:

Nella scheda "Costruttore Grafici", chiama plotting.show_plotting_ui(df).

Nella scheda "Anteprima Dati", chiama data_viewer.show_data_table(df).

Se df non esiste, mostra un messaggio di benvenuto.

3.3 modules/importer.py

Scopo: Gestire il caricamento e la pre-elaborazione dei dati.

UI (Interfaccia Utente):

Usa st.file_uploader per permettere all'utente di selezionare un file.

Mostra widget (st.selectbox, st.number_input) per configurare le opzioni di importazione (delimitatore, righe da saltare, ecc.).

Logica:

Analizza l'estensione del file (.csv, .txt, .xlsx).

Usa pandas.read_csv o pandas.read_excel per leggere i dati, passando le opzioni della UI.

Gestisce la pulizia dei nomi delle colonne (es. rimuove spazi bianchi).

Restituisce il DataFrame (df) pulito ad app.py.

3.4 modules/data_viewer.py

Scopo: Fornire una vista tabellare interattiva dei dati caricati.

Funzione Principale: show_data_table(df).

Logica:

Riceve il df da app.py.

Usa st.dataframe(df, use_container_width=True) per mostrare la tabella.

(Potrebbe includere filtri o opzioni di visualizzazione aggiuntive).

3.5 modules/plotting.py

Scopo: È il modulo più complesso. Gestisce la creazione e la personalizzazione dei grafici.

Funzione Principale: show_plotting_ui(df).

UI (Sidebar):

Usa st.sidebar.selectbox e st.sidebar.multiselect per mappare le colonne ai vari assi (X, Y, Z, Colore).

Usa st.sidebar.checkbox per le opzioni (es. Scala Logaritmica).

Usa st.sidebar.expander per raggruppare le impostazioni (es. "Dettagli Curva", "Titoli e Leggenda").

Logica "Titoli e Leggenda" (CRUCIALE):

Usa st.sidebar.text_input("Titolo Grafico", ...) per permettere all'utente di definire il titolo. Il valore viene salvato nella variabile plot_title.

MODIFICA CHIAVE: Contiene la riga st.markdown(f'<div id="graph-title-id" style="display:none;">{plot_title}</div>', unsafe_allow_html=True). Questo tag HTML nascosto "espone" il valore di plot_title alla pagina, rendendolo leggibile dallo script JS iniettato da run_desktop.py.

Logica di Rendering:

Crea una figura Plotly (fig = go.Figure()).

Aggiunge le tracce (fig.add_trace(go.Scatter, ...)) in base alle selezioni della UI (Linea 2D, Scatter 3D, Mesh 3D).

Applica le personalizzazioni (colori, spessori) definite nella sidebar.

Interazione con Altri Moduli:

Chiama annotation_utils per aggiungere linee di riferimento e calcolare/disegnare le intersezioni.

Usa st.plotly_chart(fig, ...) per renderizzare il grafico.

CRUCIALE: Chiama export_utils.show_download_ui(fig, plot_title), passando sia la figura (fig) sia il titolo (plot_title) al modulo di esportazione.

3.6 modules/export_utils.py

Scopo: Gestire la UI e la logica di esportazione del grafico.

Funzione Principale: show_download_ui(fig, plot_title).

Logica:

Riceve la figura (fig) e il titolo (plot_title) da plotting.py.

Usa BytesIO e le funzioni di Plotly (fig.write_image, fig.to_html) per convertire la figura in dati binari (PNG, JPEG, SVG, HTML). Questo richiede kaleido per le immagini statiche.

Crea i bottoni di download (es. "Scarica PNG") usando st.columns per allinearli.

INTERAZIONE CRUCIALE (Il "Passaggio di Testimone"):

Chiama st.download_button(...).

Passa il titolo ricevuto al parametro file_name=. Ad esempio: file_name=f"{plot_title.replace(' ', '_')}.png".

Streamlit genera un link <a> con download="Intensity_vs_Wavenumber.png".

Questo file_name è ciò che lo script JS in run_desktop.py leggerà (anche se, nella v31/v32, leggiamo il titolo dall'ID #graph-title-id come fallback più robusto, ma il file_name è comunque essenziale per il funzionamento del bottone).

3.7 modules/annotation_utils.py

Scopo: Libreria di utilità per l'analisi e il disegno sopra il grafico.

Funzioni Principali: show_annotation_controls, add_reference_line, calculate_and_plot_intersections.

Logica:

show_annotation_controls: Mostra i widget nella sidebar (es. st.text_input per un'equazione, st.checkbox per mostrare/nascondere i punti).

add_reference_line: Aggiunge una linea (fig.add_shape o fig.add_trace) alla figura Plotly in base all'equazione.

calculate_and_plot_intersections: Esegue i calcoli (usando numpy.interp o simili) per trovare dove la linea di riferimento interseca le curve dei dati e aggiunge nuovi punti (go.Scatter) alla figura per visualizzarli.

4. Flusso Operativo 1: Avvio dell'Applicazione

(Questa sezione è identica alla v1, poiché descrive il meccanismo di avvio che non è cambiato.)

L'utente fa doppio clic su DataPlotter.exe.

Si avvia run_desktop.py (v32).

Controlla la variabile d'ambiente AM_I_STREAMLIT_SERVER.

Flusso A (App Principale): La variabile non esiste.

Avvia run_streamlit_subprocess in un thread.

Questo thread lancia una seconda copia di DataPlotter.exe (impostando AM_I_STREAMLIT_SERVER="true").

Attende (wait_for_server) che localhost:8501 sia attivo.

Flusso B (Processo Server): Si avvia la seconda copia di DataPlotter.exe.

Vede la variabile d'ambiente ed esegue solo start_streamlit_server().

Avvia Streamlit "headless" sulla porta 8501.

Connessione:

L'App Principale (Flusso A) rileva la porta 8501.

Crea la finestra Pywebview (webview.create_window) e la avvia (webview.start(debug=False)).

5. Flusso Operativo 2: Download del Grafico (Il "Trucco")

(Questa sezione è identica alla v1, poiché descrive il meccanismo di download che non è cambiato.)

Iniezione (Avvio): on_page_loaded (in run_desktop.py) inietta il js_code.

Monkey-Patching (Avvio): Il JS ridefinisce HTMLAnchorElement.prototype.click.

Azione Utente: L'utente clicca su "Scarica PNG" (creato da export_utils.py).

Azione Streamlit: Streamlit crea un link <a> invisibile (con href="/media/..." e download="Intensity_vs_Wavenumber.png") e chiama .click() su di esso.

Intercettazione (JS): Lo script JS (in run_desktop.py) intercetta il .click().

Vede che this.href contiene /media/.

FASE CRUCIALE: Esegue document.getElementById('graph-title-id').innerText per leggere il titolo dall'elemento HTML nascosto (creato da plotting.py).

Blocca il click originale.

Chiama l'API Python: window.pywebview.api.handle_download(this.href, "Intensity_vs_Wavenumber").

Esecuzione (Python):

La classe Api (in run_desktop.py) riceve la chiamata.

Avvia download_in_thread in un thread separato.

download_in_thread usa tkinter.asksaveasfilename per aprire la finestra "Salva con nome", usando initialfile="Intensity_vs_Wavenumber".

requests scarica il file in background.

6. Istruzioni di Build Finale

(Identiche alla v1)

Prerequisiti:

Aver eseguito pip install streamlit pywebview pyinstaller requests pandas plotly kaleido.

Aver aggiunto la riga st.markdown(...) a modules/plotting.py.

Avere il file run_desktop.py (v32) con debug=False.

(Opzionale) Avere un file dataplotter.ico nella cartella principale.

Comando di Build:

# Uccidi processi vecchi
taskkill /F /IM DataPlotter.exe
taskkill /F /IM DataPlotter_Debug.exe
# Pulisci
rmdir /s /q build
rmdir /s /q dist
# Build Finale
pyinstaller --noconfirm --onedir --windowed --name=DataPlotter ^
--icon=dataplotter.ico ^
--add-data="app.py;." ^
--add-data="modules;modules" ^
--collect-all=streamlit ^
--collect-all=tornado ^
run_desktop.py


7. Distribuzione

(Identica alla v1)

Per distribuire l'applicazione, devi zippare l'intera cartella che si trova in dist\DataPlotter e inviare quel file .zip ai tuoi utenti.
