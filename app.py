import streamlit as st
import pandas as pd
from modules import data_viewer, plotting
from modules import importer 

# --- 1. Configurazione Pagina ---
st.set_page_config(
    page_title="DataPlotter Scientifico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Layout dell'Applicazione ---
st.title("DataPlotter 🔬")
st.write("Carica i tuoi dati e visualizzali in 2D e 3D.")

# --- 3. Chiamata al Modulo di Caricamento Flessibile ---
df_loaded = importer.load_data_flexible() 

# --- 4. GESTIONE DELLO STATO (MODIFICATA) ---
# Controlliamo se i dati sono stati caricati
if df_loaded is not None:
    
    # Controlla se è un *nuovo* file o il primo caricamento
    # Questo resetta i dati processati solo quando cambi file
    if 'original_df' not in st.session_state or not st.session_state.original_df.equals(df_loaded):
        st.session_state.original_df = df_loaded.copy()
        st.session_state.processed_df = df_loaded.copy()
        
        # Resetta anche i punti di annotazione quando carichi un nuovo file
        if 'custom_points' in st.session_state:
            st.session_state.custom_points = []
        st.toast("Nuovo file caricato! Dati e annotazioni resettati.")

# --- 5. LAYOUT CON TAB (Ora controlla se lo stato esiste) ---
if 'processed_df' in st.session_state:
    
    # I dati processati sono la nostra "fonte di verità" per i grafici
    df_to_plot = st.session_state.processed_df

    tab_plot, tab_data, tab_settings = st.tabs([
        "Costruttore Grafici", 
        "Dati e Processamento", 
        "Impostazioni"
    ])

    with tab_plot:
        # Il plotting legge sempre i dati processati
        plotting.show_plotting_ui(df_to_plot) 
        
    with tab_data:
        # Questa singola funzione ora gestisce TUTTO:
        # i bottoni, i filtri, l'export e la visualizzazione della tabella.
        data_viewer.show_data_processor()
        
    with tab_settings:
        st.subheader("Opzioni Applicazione")
        st.info("Questa è la sezione che puoi espandere in futuro per opzioni globali.")

else:
    st.info("Per iniziare, carica un file CSV, Excel, TXT, ASC o RAW usando il pannello di importazione.")