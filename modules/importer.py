import streamlit as st
import pandas as pd
from io import StringIO # Necessario per leggere il file in memoria

def show_importer():
    """
    Mostra l'interfaccia utente per il caricamento e il parsing dei file.
    Aggiorna st.session_state.df se il caricamento ha successo.
    """
    
    # 'st.expander' crea una sezione collassabile.
    with st.expander("Pannello di Importazione", expanded=True):
        
        # 1. Widget di Upload
        uploaded_file = st.file_uploader(
            "Trascina qui il tuo file (.csv o .txt) o clicca per cercare", 
            type=["csv", "txt"]
        )
        
        st.subheader("Configurazione Importazione")
        
        # 2. Opzioni di Parsing (Delimitatore, Salta Righe, Header)
        # Usiamo le colonne per mettere le opzioni una accanto all'altra
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delimiter = st.text_input("Delimitatore", ",", help="Es: ',' o ';' o '\\t' per tabulazione")
        
        with col2:
            skip_rows = st.number_input("Salta righe all'inizio", min_value=0, value=0)
        
        with col3:
            # Pandas 'infer' prova a indovinarlo
            header_option = st.selectbox("La prima riga è l'intestazione?", 
                                         ("Indovina", "Sì (usa riga 0)", "No (dati da riga 0)"), 
                                         index=0)

        # 3. Logica di Caricamento
        if uploaded_file is not None:
            # Se un file è stato caricato, proviamo a leggerlo
            
            # Converti l'opzione header in un argomento valido per Pandas
            if header_option == "Sì (usa riga 0)":
                header_arg = 0
            elif header_option == "No (dati da riga 0)":
                header_arg = None
            else: # "Indovina"
                header_arg = 'infer'

            try:
                # Per leggere un file caricato da Streamlit, va decodificato
                string_data = StringIO(uploaded_file.getvalue().decode("utf-8"))
                
                # Usiamo Pandas per leggere il CSV con le opzioni date
                df = pd.read_csv(
                    string_data,
                    sep=delimiter,
                    skiprows=skip_rows,
                    header=header_arg
                )
                
                # Se la lettura fallisce senza header, prova a rileggerlo 
                # e assegna nomi di colonna generici
                if header_arg is None and df.shape[1] == 1:
                     raise ValueError("Parsing fallito, forse il delimitatore è errato?")
                
                # Se non c'è header, Pandas usa numeri. Rinominiamoli.
                if header_arg is None:
                    df.columns = [f"Colonna_{i+1}" for i in range(df.shape[1])]

                # SUCCESSO! Salviamo il DataFrame nello stato della sessione
                st.session_state.df = df
                st.success(f"File '{uploaded_file.name}' caricato con successo! ({df.shape[0]} righe, {df.shape[1]} colonne)")
            
            except Exception as e:
                # Se qualcosa va male, mostriamo un errore e resettiamo lo stato
                st.error(f"Errore nel leggere il file: {e}")
                st.session_state.df = None