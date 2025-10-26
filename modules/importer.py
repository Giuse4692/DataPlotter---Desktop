import streamlit as st
import pandas as pd
from io import StringIO
import re # Necessario per le espressioni regolari (regex)

def load_data_flexible():
    """
    Mostra l'interfaccia utente flessibile per il caricamento dei file, 
    con logica di parsing specifica per i file di spettroscopia (.asc).
    Restituisce il DataFrame letto.
    """
    df = None
    
    with st.expander("Pannello di Importazione Dati", expanded=True):
        
        # 1. Widget di Upload (ESTESO A TUTTI I TIPI)
        uploaded_file = st.file_uploader(
            "Trascina qui il tuo file (.csv, .xlsx, .txt, .asc, .raw) o clicca per cercare", 
            type=["csv", "xlsx", "xls", "txt", "asc", "raw"]
        )
        
        st.subheader("Configurazione Parsing (Solo per file di testo)")
        
        # 2. Opzioni di Parsing
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Rimuoviamo il delimitatore per i file .ASC/RAW, ma lo lasciamo per CSV/TXT
            delimiter = st.text_input("Delimitatore CSV/TXT (Opzionale)", ",", help="Lascia vuoto per rilevazione automatica.")
        
        with col2:
            # Per i file ASC, l'opzione skiprows non è necessaria, ma la manteniamo.
            skip_rows = st.number_input("Salta righe all'inizio (solo per file generici)", min_value=0, value=0)
        
        with col3:
            header_option = st.selectbox(
                "La prima riga è l'intestazione?", 
                ("Indovina", "Sì (usa riga 0)", "No (dati da riga 0)"), 
                index=0
            )

        # 3. Logica di Caricamento
        if uploaded_file is not None:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Converte l'opzione header in un argomento valido per Pandas
            header_arg = None
            if header_option == "Sì (usa riga 0)":
                header_arg = 0
            elif header_option == "Indovina":
                header_arg = 'infer'
                
            try:
                if file_extension in ['xlsx', 'xls']:
                    # Logica per Excel
                    df = pd.read_excel(uploaded_file, skiprows=skip_rows, header=header_arg)
                    
                elif file_extension in ['csv', 'txt']:
                    # Logica standard per CSV/TXT generico
                    string_data = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    final_sep = delimiter if delimiter not in ['', ' '] else r'\s*,\s*|\t+|\s+'
                    
                    df = pd.read_csv(
                        string_data,
                        sep=final_sep, 
                        skiprows=skip_rows,
                        header=header_arg,
                        engine='python',
                        skipinitialspace=True
                    )

                elif file_extension in ['asc', 'raw']:
                    # ⚠️ LOGICA SPECIFICA PER FILE ASC/RAW CON INTESTAZIONE A BLOCCHI
                    
                    file_content = uploaded_file.getvalue().decode("utf-8")
                    
                    # 1. Trova l'indice di inizio dei dati ('#DATA')
                    data_start_marker = "#DATA"
                    if data_start_marker not in file_content:
                        raise ValueError("Marcatore #DATA non trovato. Formato ASC non riconosciuto.")
                        
                    # 2. Suddivide il contenuto e prende solo il blocco dati
                    data_block = file_content.split(data_start_marker, 1)[1].strip()
                    
                    # 3. Carica il blocco dati. Si assume che i campi siano separati da TAB.
                    df = pd.read_csv(
                        StringIO(data_block),
                        sep=r'\t+|\s\s+', # Delimitatori: TAB o 2+ spazi consecutivi (molto comune)
                        header=None,      # Non ci sono intestazioni nel blocco dati stesso
                        engine='python',
                        skipinitialspace=True
                    )
                    
                    # 4. Assegna i nomi delle colonne (Wavenumber e Intensity)
                    df.columns = ['Wavenumber', 'Intensity']
                    
                    # 5. Rimuovi le righe NaN (pulizia finale)
                    df = df.dropna(how='all').reset_index(drop=True)


                else:
                    st.error(f"Estensione '{file_extension}' non supportata.")
                    return None
                
                # --- Logica di Pulizia Finale ---
                
                # Rinomina colonne se Pandas ha usato numeri (solo per CSV/TXT standard)
                if file_extension not in ['asc', 'raw'] and (header_arg is None or all(isinstance(col, int) for col in df.columns)):
                    df.columns = [f'Colonna_{i+1}' for i in range(df.shape[1])]

                # Pulisci e normalizza i nomi delle colonne
                df.columns = df.columns.astype(str).str.strip().str.replace(r'[^A-Za-z0-9_]+', '', regex=True)
                
                st.success(f"File '{uploaded_file.name}' caricato con successo! ({df.shape[0]} righe, {df.shape[1]} colonne)")
                
                return df
            
            except ValueError as ve:
                st.error(f"Errore di formato nel file: {ve}")
                st.warning("Verifica se il file è corrotto o se il formato ASC è diverso dal modello standard.")
                return None
            
            except Exception as e:
                st.error(f"Errore generico nel leggere il file: {e}")
                st.warning("Verifica il delimitatore o il numero di righe da saltare per i file non-ASC.")
                return None
    
    return None