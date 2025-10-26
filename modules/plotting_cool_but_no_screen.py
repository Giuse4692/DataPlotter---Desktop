import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
# Rimosso import pio e components perché i fix lato server e client sono falliti

def show_plotting_ui(df):
    """
    Mostra l'interfaccia utente per la creazione e personalizzazione dei grafici.
    Prende in input il DataFrame dallo stato della sessione.
    """
    st.header("Costruttore di Grafici")
    st.info("Usa la **Sidebar a sinistra** per mappare gli assi e personalizzare il grafico.")
    
    # Prendiamo la lista delle colonne per i menu a tendina
    column_list = df.columns.tolist()
    
    # --- 1. Selezione Tipo di Grafico (in colonna) ---
    with st.container():
        plot_type = st.selectbox(
            "Scegli il tipo di grafico",
            ["Linea 2D", "Scatter 2D", "Scatter 3D", "Linea 3D (Line)", "Superficie 3D (Mesh)"] # MODIFICATO
        )
    
    # --- 2. Mappatura Assi (in Sidebar) ---
    st.sidebar.header("2. Mappatura Assi")
    
    x_axis = st.sidebar.selectbox("Asse X", column_list, index=0, key="x_axis")
    y_axis = st.sidebar.selectbox("Asse Y", column_list, index=1 if len(column_list) > 1 else 0, key="y_axis")
    
    z_axis = None
    if "3D" in plot_type: # Questa logica funziona per tutte le opzioni 3D
        z_axis = st.sidebar.selectbox("Asse Z", column_list, index=2 if len(column_list) > 2 else 0, key="z_axis")
        
    color_axis = st.sidebar.selectbox("Mappa Colore (opzionale)", [None] + column_list, key="color_axis")

    # --- 3. Personalizzazione (in Sidebar) ---
    st.sidebar.header("3. Personalizzazione")
    
    plot_title = st.sidebar.text_input("Titolo Grafico", f"{y_axis} vs {x_axis}")
    x_label = st.sidebar.text_input("Etichetta Asse X", x_axis)
    y_label = st.sidebar.text_input("Etichetta Asse Y", y_axis)
    z_label = "Z"
    if z_axis:
        z_label = st.sidebar.text_input("Etichetta Asse Z", z_axis)
    
    show_legend = st.sidebar.checkbox("Mostra Legenda", True)

    # --- 4. Generazione Grafico ---
    fig = None

    try:
        if plot_type == "Linea 2D":
            fig = px.line(df, x=x_axis, y=y_axis, color=color_axis, title=plot_title)
        
        elif plot_type == "Scatter 2D":
            fig = px.scatter(df, x=x_axis, y=y_axis, color=color_axis, title=plot_title)
        
        elif plot_type == "Scatter 3D":
            fig = px.scatter_3d(df, x=x_axis, y=y_axis, z=z_axis, color=color_axis, title=plot_title)
        
        # --- OPZIONE ---
        elif plot_type == "Linea 3D (Line)":
            st.info("""
                **Nota:** Questo grafico collega i punti (X, Y, Z) con una linea, 
                seguendo l'ordine in cui appaiono nel file.
            """)
            try:
                fig = px.line_3d(df, x=x_axis, y=y_axis, z=z_axis, color=color_axis, title=plot_title)
            except Exception as e:
                st.error(f"Impossibile creare la Linea 3D: {e}. Assicurati di aver mappato X, Y, e Z.")

        # --- OPZIONE RINOMINATA E CORRETTA ---
        elif plot_type == "Superficie 3D (Mesh)":
            st.info("""
                **Nota:** Per creare una superficie da punti sparsi (come X, Y, Z), 
                stiamo usando la triangolazione 3D (Mesh3d) per "unire i punti".
            """)
            try:
                # Usa Mesh3d per creare una superficie da punti sparsi (X, Y, Z)
                fig = go.Figure(data=[go.Mesh3d(
                    x=df[x_axis],
                    y=df[y_axis],
                    z=df[z_axis],
                    opacity=0.7,
                )])
                
                # Aggiungi anche i punti scatter 3D per vedere i dati originali
                fig.add_trace(go.Scatter3d(
                    x=df[x_axis],
                    y=df[y_axis],
                    z=df[z_axis],
                    mode='markers',
                    marker=dict(size=2, color='red'),
                    name='Dati Originali'
                ))
                
            except Exception as e:
                st.error(f"Impossibile creare la superficie Mesh3d: {e}. Assicurati di aver mappato X, Y, e Z.")

        # --- 5. Applica Personalizzazioni e Mostra Grafico ---
        if fig:
            # Applica etichette e legenda
            fig.update_layout(
                title=plot_title, # Assicura che il titolo venga aggiornato
                xaxis_title=x_label,
                yaxis_title=y_label,
                showlegend=show_legend,
                # Grazie a Plotly, Interattività (Zoom, Pan) è già inclusa
            )
            if "3D" in plot_type:
                fig.update_layout(scene=dict(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    zaxis_title=z_label
                ))
            
            # Mostra il grafico!
            # Questo è l'unico metodo che renderizza 3D, Zoom e Download 📷
            st.plotly_chart(fig, use_container_width=True)

            # --- ISTRUZIONI PER IL DOWNLOAD ---
            st.caption("ℹ️ **Come scaricare:** Passa il mouse sopra il grafico. Apparirà una barra degli strumenti in alto a destra. Clicca l'icona a forma di **fotocamera 📷** per scaricare il grafico come PNG.")

            # --- Sezione Esportazione Rimossa ---
            # Qualsiasi tentativo di esportazione lato server (st.download_button)
            # fallisce su Streamlit Cloud a causa del problema Kaleido/Chromium.
            # L'esportazione lato client 📷 è l'unica affidabile.
            
    except Exception as e:
        # Questo cattura errori nella *creazione* del grafico (es. dati errati)
        st.error(f"Errore during la creazione del grafico: {e}")


