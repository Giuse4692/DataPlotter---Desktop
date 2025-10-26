import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Import export_utils (assumo che contenga la show_download_ui)
import modules.export_utils as export_utils 

def show_plotting_ui(df):
    st.header("Costruttore di Grafici")
    st.info("Usa la **Sidebar a sinistra** per mappare gli assi e personalizzare il grafico.")
    
    column_list = df.columns.tolist()
    
    # --- 2. Mappatura Assi (MODIFICATA) ---
    st.sidebar.header("2. Mappatura Assi")
    x_axis = st.sidebar.selectbox("Asse X", column_list, index=0, key="x_axis")
    
    # ⚠️ MULTISELECT per le curve 2D
    y_axes = st.sidebar.multiselect(
        "Assi Y (Curve 2D) / Asse Y (Curve 3D)", # Etichetta aggiornata
        column_list,
        default=[column_list[1]] if len(column_list) > 1 else [column_list[0]],
        key="y_axes"
    )
    
    # Prende la prima Y per i grafici 3D, per mantenere la retrocompatibilità
    y_axis_single = y_axes[0] if y_axes else column_list[1] if len(column_list) > 1 else column_list[0]
    
    z_axis = None
    if "3D" in plot_type:
        z_axis = st.sidebar.selectbox("Asse Z", column_list, index=2 if len(column_list) > 2 else 0, key="z_axis")
        
    color_axis = st.sidebar.selectbox("Mappa Colore (opzionale)", [None] + column_list, key="color_axis")
    
    # --- 3. Personalizzazione (INVARIATA) ---
    st.sidebar.header("3. Personalizzazione")
    # Aggiorna il titolo se ci sono curve multiple
    default_title = f"{', '.join(y_axes)} vs {x_axis}" if len(y_axes) > 1 and "3D" not in plot_type else f"{y_axis_single} vs {x_axis}"
    
    plot_title = st.sidebar.text_input("Titolo Grafico", default_title)
    x_label = st.sidebar.text_input("Etichetta Asse X", x_axis)
    y_label = st.sidebar.text_input("Etichetta Asse Y", ", ".join(y_axes) if len(y_axes) > 1 else y_axis_single)
    z_label = "Z"
    if z_axis:
        z_label = st.sidebar.text_input("Etichetta Asse Z", z_axis)
    show_legend = st.sidebar.checkbox("Mostra Legenda", True)

    # --- 4. Generazione Grafico (LOGICA MODIFICATA) ---
    fig = go.Figure() # Iniziamo con un oggetto Figure vuoto, ideale per tracce multiple

    try:
        # ----------------------------------------------------
        # LOGICA 2D: TRACCE MULTIPLE (Linee e Scatter)
        # ----------------------------------------------------
        if plot_type == "Linea 2D" or plot_type == "Scatter 2D":
            mode = 'lines' if plot_type == "Linea 2D" else 'markers'
            
            # Seleziona la sequenza di colori da usare
            color_sequence = px.colors.qualitative.Plotly 
            
            # ⚠️ Cicla su tutti gli assi Y selezionati e aggiunge una curva
            for i, y_col in enumerate(y_axes):
                trace_color = color_sequence[i % len(color_sequence)]
                
                fig.add_trace(go.Scatter(
                    x=df[x_axis],
                    y=df[y_col],
                    mode=mode,
                    name=y_col, 
                    line=dict(color=trace_color) if mode == 'lines' else None,
                    marker=dict(color=trace_color) if mode == 'markers' else None
                ))

            # Se si usa Mappa Colore in 2D, lo ignoriamo qui perché abbiamo disegnato tracce separate.
            
        # ----------------------------------------------------
        # LOGICA 3D: TRACCE SINGOLE (Linee e Scatter)
        # ----------------------------------------------------
        elif plot_type == "Scatter 3D":
            fig = px.scatter_3d(df, x=x_axis, y=y_axis_single, z=z_axis, 
                                color=color_axis, title=plot_title, 
                                color_continuous_scale='Viridis' if color_axis else None)
        elif plot_type == "Linea 3D (Line)":
            fig = px.line_3d(df, x=x_axis, y=y_axis_single, z=z_axis, 
                             color=color_axis, title=plot_title, 
                             color_continuous_scale='Viridis' if color_axis else None)

        # ----------------------------------------------------
        # LOGICA Mesh 3D (Invariata)
        # ----------------------------------------------------
        elif plot_type == "Superficie 3D (Mesh)":
            intensity_data = df[z_axis]
            colorscale_choice = 'Blues'
            if color_axis:
                 intensity_data = df[color_axis]
                 colorscale_choice = 'Viridis' 
            
            min_intensity = intensity_data.min()
            max_intensity = intensity_data.max()

            fig = go.Figure(data=[go.Mesh3d(
                x=df[x_axis], y=df[y_axis_single], z=df[z_axis], opacity=0.7,
                intensity=intensity_data, colorscale=colorscale_choice, showscale=True,
                cmin=min_intensity, cmax=max_intensity
            )])

        if fig:
            # --- Layout (Generale) ---
            fig.update_layout(
                title=plot_title,
                showlegend=show_legend,
                colorway=px.colors.qualitative.Plotly # Forza colorway per Plotly Express
            )
            
            # --- Configurazione Assi ---
            if "3D" in plot_type:
                fig.update_layout(scene=dict(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    zaxis_title=z_label
                ))
            else:
                fig.update_layout(
                    xaxis_title=x_label,
                    yaxis_title=y_label
                )
            
            # --- Plot e Download ---
            config = {'displaylogo': False, 'modeBarButtonsToRemove': ['toImage']}
            st.plotly_chart(fig, use_container_width=True, config=config)

            # --- CHIAMATA CORRETTA AL MODULO DOWNLOAD ---
            export_utils.show_download_ui(fig, plot_title)

    except IndexError:
        st.warning("Seleziona almeno una colonna per l'Asse Y.")
    except Exception as e:
        st.error(f"Errore durante la creazione del grafico: {e}")