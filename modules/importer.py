import streamlit as st
import pandas as pd
from io import StringIO
import re # Necessario per le espressioni regolari (regex)

def load_data_flexible():
    """
    Mostra l'interfaccia utente flessibile per il caricamento di FILE MULTIPLI,
    con logica di parsing specifica per i file di spettroscopia (.asc).
    Restituisce un DataFrame unico che concatena tutti i file letti.
    """
    
    with st.expander("Pannello di Importazione Dati", expanded=True):
        
        # *** 1. MODIFICA: ACCETTA FILE MULTIPLI ***
        uploaded_files = st.file_uploader(
            "Trascina qui i tuoi file (.csv, .xlsx, .txt, .asc, .raw) o clicca per cercare", 
            type=["csv", "xlsx", "xls", "txt", "asc", "raw"],
            accept_multiple_files=True  # <-- Modifica Chiave
        )
        
        st.subheader("Configurazione Parsing (Solo per file di testo)")
        
        # 2. Opzioni di Parsing (invariate)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delimiter = st.text_input("Delimitatore CSV/TXT (Opzionale)", ",", help="Lascia vuoto per rilevazione automatica.")
        
        with col2:
            skip_rows = st.number_input("Salta righe all'inizio (solo per file generici)", min_value=0, value=0)
        
        with col3:
            header_option = st.selectbox(
                "La prima riga è l'intestazione?", 
                ("Indovina", "Sì (usa riga 0)", "No (dati da riga 0)"), 
                index=0
            )

        # 3. Logica di Caricamento (modificata per il ciclo)
        
        # Converte l'opzione header in un argomento valido per Pandas
        header_arg = None
        if header_option == "Sì (usa riga 0)":
            header_arg = 0
        elif header_option == "Indovina":
            header_arg = 'infer'
            
        all_dfs = [] # Lista per raccogliere i DataFrame di ogni file
        all_filenames = [] # Lista per i messaggi di successo

        if uploaded_files: # Se la lista non è vuota
            
            # *** INIZIO MODIFICA: CICLO SUI FILE CARICATI ***
            for uploaded_file in uploaded_files:
                df_single = None # Resetta il dataframe per ogni file
                
                try:
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    
                    if file_extension in ['xlsx', 'xls']:
                        df_single = pd.read_excel(uploaded_file, skiprows=skip_rows, header=header_arg)
                        
                    elif file_extension in ['csv', 'txt']:
                        string_data = StringIO(uploaded_file.getvalue().decode("utf-8"))
                        final_sep = delimiter if delimiter not in ['', ' '] else r'\s*,\s*|\t+|\s+'
                        
                        df_single = pd.read_csv(
                            string_data,
                            sep=final_sep, 
                            skiprows=skip_rows,
                            header=header_arg,
                            engine='python',
                            skipinitialspace=True
                        )

                    elif file_extension in ['asc', 'raw']:
                        file_content = uploaded_file.getvalue().decode("utf-8")
                        
                        data_start_marker = "#DATA"
                        if data_start_marker not in file_content:
                            raise ValueError(f"Marcatore #DATA non trovato in '{uploaded_file.name}'. Formato ASC non riconosciuto.")
                            
                        data_block = file_content.split(data_start_marker, 1)[1].strip()
                        
                        df_single = pd.read_csv(
                            StringIO(data_block),
                            sep=r'\t+|\s\s+', 
                            header=None,
                            engine='python',
                            skipinitialspace=True
                        )
                        
                        # Assegna i nomi delle colonne (Wavenumber e Intensity)
                        df_single.columns = ['Wavenumber', 'Intensity']
                        df_single = df_single.dropna(how='all').reset_index(drop=True)

                    else:
                        st.error(f"File '{uploaded_file.name}': Estensione '{file_extension}' non supportata. File saltato.")
                        continue # Salta al prossimo file
                    
                    # --- Logica di Pulizia Finale (per singolo file) ---
                    
                    # Rinomina colonne se Pandas ha usato numeri (solo per CSV/TXT standard)
                    if file_extension not in ['asc', 'raw'] and (header_arg is None or all(isinstance(col, int) for col in df_single.columns)):
                        df_single.columns = [f'Colonna_{i+1}' for i in range(df_single.shape[1])]

                    # Pulisci e normalizza i nomi delle colonne
                    df_single.columns = df_single.columns.astype(str).str.strip().str.replace(r'[^A-Za-z0-9_]+', '', regex=True)
                    
                    # Aggiungi il df alla lista
                    all_dfs.append(df_single)
                    all_filenames.append(uploaded_file.name)
                
                except ValueError as ve:
                    st.error(f"Errore di formato nel file '{uploaded_file.name}': {ve}. File saltato.")
                
                except Exception as e:
                    st.error(f"Errore generico nel leggere il file '{uploaded_file.name}': {e}. File saltato.")
            
            # *** FINE MODIFICA: CICLO COMPLETATO ***
            
            
            # --- 4. Concatena tutti i DataFrame alla fine ---
            if not all_dfs:
                return None # Nessun file è stato letto con successo
            
            try:
                final_df = pd.concat(all_dfs, ignore_index=True)
                
                st.success(f"Caricati e uniti {len(all_dfs)} file: {', '.join(all_filenames)}")
                st.info(f"DataFrame finale: {final_df.shape[0]} righe totali, {final_df.shape[1]} colonne.")
                
                return final_df
                
            except Exception as e:
                st.error(f"Errore durante l'unione dei file: {e}")
                st.warning("Assicurati che i file abbiano strutture compatibili. (Es. stesso numero di colonne o stesse intestazioni)")
                return None
    
    return None # Ritorna None se nessun file è stato caricato