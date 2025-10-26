import streamlit as st
from modules import importer, data_viewer, plotting

# --- 1. Configurazione Pagina ---
# st.set_page_config imposta le proprietà della pagina (Titolo, layout)
# Va chiamato come prima cosa nello script.
st.set_page_config(
    page_title="DataPlotter Scientifico",
    layout="wide",  # "wide" usa tutto lo schermo, utile per grafici
    initial_sidebar_state="expanded" # Sidebar aperta di default
)

# --- 2. Gestione dello Stato (Session State) ---
# st.session_state è un "dizionario" che persiste tra i re-run.
# È FONDAMENTALE. Senza, ogni volta che tocchi un widget,
# il file caricato verrebbe perso.

# Inizializziamo il nostro DataFrame (df) a 'None' se non esiste.
if 'df' not in st.session_state:
    st.session_state.df = None

# --- 3. Layout dell'Applicazione ---
st.title("DataPlotter 🔬")
st.write("Carica i tuoi dati e visualizzali in 2D e 3D.")

# --- 4. Chiamata ai Moduli ---

# Modulo 1: Importazione
# Questo modulo mostrerà l'interfaccia di upload.
# Se l'utente carica un file, questo modulo aggiornerà st.session_state.df
importer.show_importer()

# Modulo 2 e 3: Visualizzazione (solo se i dati sono stati caricati)
# Controlliamo se st.session_state.df contiene qualcosa.
if st.session_state.df is not None:
    
    # Passiamo il dataframe (df) ai nostri moduli
    df = st.session_state.df
    
    # Modulo 2: Mostra la tabella (foglio di calcolo)
    data_viewer.show_data_table(df)
    
    # Modulo 3: Mostra l'UI per i grafici
    # Questa è la parte più complessa, che vedremo dopo.
    plotting.show_plotting_ui(df)

else:
    # Messaggio iniziale finché non si carica un file
    st.info("Per iniziare, carica un file CSV o TXT usando il pannello qui sopra.")
