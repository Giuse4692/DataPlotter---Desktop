import streamlit as st
import pandas as pd
from modules import data_viewer, plotting
# ⚠️ MANTENIAMO L'IMPORTAZIONE ORIGINALE ⚠️
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

# --- 3. Chiamata al Modulo di Caricamento Flessibile (Funzione Rinominata) ---
# La funzione in importer.py ora si chiama load_data_flexible
df = importer.load_data_flexible() 

if df is not None:
    
    # --- 4. LAYOUT CON TAB ---
    tab_plot, tab_data, tab_settings = st.tabs(["Costruttore Grafici", "Anteprima Dati", "Impostazioni"])

    with tab_plot:
        plotting.show_plotting_ui(df) 
        
    with tab_data:
        data_viewer.show_data_table(df)
        
    with tab_settings:
        st.subheader("Opzioni Applicazione")
        st.info("Questa è la sezione che puoi espandere in futuro per opzioni globali.")

else:
    st.info("Per iniziare, carica un file CSV, Excel, TXT, ASC o RAW usando il pannello di importazione.")