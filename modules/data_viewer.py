import streamlit as st

def show_data_table(df):
    """
    Mostra i dati importati in una tabella (foglio di calcolo).
    """
    with st.expander("Visualizzazione Dati (Tabella)", expanded=False):
        st.info("Questa è un'anteprima dei dati caricati. Le colonne possono essere ordinate cliccando sull'intestazione.")
        # st.dataframe è il "foglio di calcolo" interattivo di Streamlit
        st.dataframe(df)

