import streamlit as st
import pandas as pd
import numpy as np 
import re 
# from pandas.core.computation.ops import UndefinedVariableError # Rimossa

@st.cache_data
def convert_df_to_csv(df_to_convert):
    """Funzione helper per convertire il DataFrame in CSV per il download."""
    return df_to_convert.to_csv(index=False).encode('utf-8')

def show_data_processor():
    """
    Mostra i controlli di processamento (filtri, duplicati, etc.)
    e la tabella dei dati.
    Questa funzione legge e scrive direttamente in st.session_state.
    """
    
    st.subheader("Processamento Dati")
    st.info("Le modifiche fatte qui si rifletteranno sul 'Costruttore Grafici'.")

    # Controlla che i dati siano caricati prima di mostrare i controlli
    if 'processed_df' not in st.session_state or 'original_df' not in st.session_state:
        st.warning("Per favore, carica prima un file di dati.")
        return
    
    # Inizializza lo stato per la conferma di eliminazione
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = False
    if 'col_pending_deletion' not in st.session_state:
        st.session_state.col_pending_deletion = None

    # --- 1. Controlli Principali (Reset, Duplicati) ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Resetta ai Dati Originali", use_container_width=True):
            st.session_state.processed_df = st.session_state.original_df.copy()
            st.session_state.confirm_delete = False 
            st.rerun()
    with col2:
        if st.button("Rimuovi Righe Duplicate", use_container_width=True):
            st.session_state.processed_df = st.session_state.processed_df.drop_duplicates()
            st.session_state.confirm_delete = False
            st.rerun()

    st.markdown("---")

    # --- 2. Gestione Colonne (Rinomina/Elimina) ---
    st.subheader("Gestione Colonne")
    st.caption("Nota: L'interfaccia di Streamlit non permette di modificare le intestazioni della tabella. Usa i menu qui sotto.")
    
    col_rinomina, col_elimina = st.columns(2)
    
    with col_rinomina:
        st.markdown("**Rinomina Colonna**")
        col_to_rename = st.selectbox(
            "Colonna da rinominare", 
            st.session_state.processed_df.columns,
            key="col_rename_select"
        )
        new_col_name = st.text_input("Nuovo nome", key="new_col_name_input")
        
        if st.button("Rinomina"):
            if new_col_name and col_to_rename:
                if new_col_name in st.session_state.processed_df.columns:
                    st.error(f"Errore: Il nome '{new_col_name}' esiste già.")
                else:
                    st.session_state.processed_df.rename(columns={col_to_rename: new_col_name}, inplace=True)
                    st.rerun()
            else:
                st.warning("Inserisci un nuovo nome valido.")
    
    with col_elimina:
        st.markdown("**Elimina Colonna**")
        col_to_delete = st.selectbox(
            "Colonna da eliminare", 
            st.session_state.processed_df.columns,
            key="col_delete_select"
        )
        
        # Logica di conferma
        if st.session_state.confirm_delete and st.session_state.col_pending_deletion == col_to_delete:
            st.warning(f"Sei sicuro di voler eliminare definitivamente la colonna **'{col_to_delete}'**?")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sì, Elimina", use_container_width=True, type="primary"):
                    st.session_state.processed_df.drop(columns=[col_to_delete], inplace=True)
                    st.session_state.confirm_delete = False
                    st.session_state.col_pending_deletion = None
                    st.rerun()
            with c2:
                if st.button("Annulla", use_container_width=True):
                    st.session_state.confirm_delete = False
                    st.session_state.col_pending_deletion = None
                    st.rerun()
        else:
            if st.button("Elimina", use_container_width=True):
                st.session_state.confirm_delete = True
                st.session_state.col_pending_deletion = col_to_delete
                st.rerun()

    st.markdown("---")

    # --- 3. Calcolatrice ---
    st.subheader("Calcolatrice (Crea Nuova Colonna)")
    
    col_list = st.session_state.processed_df.columns
    st.caption("Colonne disponibili: `" + "`, `".join(col_list) + "`")

    with st.expander("Mostra funzioni e sintassi"):
        st.markdown("""
        - **Sintassi:** `NomeNuovaColonna = Colonna_A * 2 + Colonna_B`
        - **Nomi con spazi:** Se un nome ha spazi, usa gli apici inversi: `` `Mia Colonna` * 2 ``
        - **Operatori:** `+`, `-`, `*`, `/`, `**` (potenza)
        - **Funzioni:** `log(A)`, `log10(A)`, `sin(A)`, `cos(A)`, `tan(A)`, `sqrt(A)`, `abs(A)`
        - **Costanti:** `pi`, `e`
        """)

    # Definisci la callback per gestire il calcolo e il reset
    def _calculate_and_reset():
        formula_str = st.session_state.formula_input_unified # Leggi dallo stato
        if not formula_str or '=' not in formula_str:
            st.error("Formula non valida. Manca '='. Es: `NuovaCol = Colonna_A * 2`")
            return

        try:
            parts = formula_str.split('=', 1)
            new_col_name_raw = parts[0].strip()
            formula_expression = parts[1].strip()

            if not new_col_name_raw or not formula_expression:
                st.error("Formula incompleta. Assicurati di specificare un nome e un'espressione.")
                return

            safe_col_name = new_col_name_raw.replace(" ", "_") # Rendi il nome sicuro
            
            if safe_col_name in st.session_state.processed_df.columns:
                st.error(f"Errore: La colonna '{safe_col_name}' esiste già.")
                return
            
            df = st.session_state.processed_df
            
            df.eval(f"`{safe_col_name}` = {formula_expression}", inplace=True, engine='python')
            st.session_state.processed_df = df
            st.session_state.formula_input_unified = "" # Reset sicuro dello stato

        except SyntaxError as e:
            st.error(f"Errore di sintassi: {e}. Controlla la formula.")
        except Exception as e:
            err_str = str(e)
            if "UndefinedVariableError" in err_str:
                st.error(f"Errore: Nome colonna non trovato: {e}. Controlla maiuscole/minuscole. Se il nome ha spazi, usa `` `Nome Colonna` ``.")
            else:
                st.error(f"Errore nella formula: {e}")

    # Inizializza lo stato per il campo di testo unificato
    if 'formula_input_unified' not in st.session_state:
        st.session_state.formula_input_unified = ""
        
    # Disegna il widget
    formula_str_input = st.text_input(
        "Formula (es. `Nuova_Col = Colonna_A * 2` o `` `Col C` = `Col A` + `Col B` ``)", 
        key="formula_input_unified"
    )

    # Logica per i Suggerimenti ("Autocompilamento")
    suggestions = []
    if formula_str_input and '=' in formula_str_input:
        try:
            expression_part = formula_str_input.split('=', 1)[1]
            last_word_match = re.split(r'[+\-*/\s()]', expression_part)
            
            if last_word_match:
                last_word = last_word_match[-1].replace('`', '') # Pulisci apici
                if last_word:
                    suggestions = [col for col in col_list if col.lower().startswith(last_word.lower()) and col.lower() != last_word.lower()]
        except Exception:
            pass # Ignora errori di parsing live

    if suggestions:
        st.info(f"Suggerimenti: `{'`, `'.join(suggestions)}`")

    # Lega il bottone alla callback
    st.button(
        "Calcola e Aggiungi", 
        key="calc_btn",
        on_click=_calculate_and_reset
    )
    
    st.markdown("---")

    # --- 4. Filtro per Range ---
    st.subheader("Filtra per Range")
    
    col_to_filter = st.selectbox(
        "Seleziona colonna da filtrare", 
        st.session_state.processed_df.columns,
        key="filter_col"
    )
    
    try:
        numeric_col = pd.to_numeric(st.session_state.processed_df[col_to_filter])
        min_default = float(numeric_col.min())
        max_default = float(numeric_col.max())
        
        min_val, max_val = st.slider(
            f"Seleziona range per '{col_to_filter}'",
            min_value=min_default,
            max_value=max_default,
            value=(min_default, max_default)
        )
        
        if st.button("Applica Filtro Range"):
            st.session_state.processed_df = st.session_state.processed_df[
                (numeric_col >= min_val) &
                (numeric_col <= max_val)
            ]
            st.session_state.confirm_delete = False 
            st.rerun()
            
    except ValueError:
        st.warning(f"La colonna '{col_to_filter}' non è numerica e non può essere filtrata con uno slider.")
    except Exception as e:
        st.error(f"Errore durante il filtraggio: {e}")

    st.markdown("---")

    # --- 5. Esportazione CSV ---
    st.subheader("Esporta Dati Processati")
    
    csv_data = convert_df_to_csv(st.session_state.processed_df)
    
    # *** INIZIO MODIFICA: CHIAVE DINAMICA ***
    # Questa è la versione che ti avevo mandato prima.
    # La chiave cambia ogni volta che i dati cambiano.
    st.download_button(
        label="Scarica dati processati (CSV)",
        data=csv_data,
        file_name="dati_processati.csv",
        mime="text/csv",
        key=f"download_csv_data_{len(st.session_state.processed_df)}" 
    )
    # *** FINE MODIFICA ***

    # --- 6. Visualizzazione Tabella ---
    with st.expander("Visualizzazione Dati (Tabella)", expanded=True):
        st.info(f"Visualizzazione di **{len(st.session_state.processed_df)}** righe di dati processati.")
        st.dataframe(st.session_state.processed_df)