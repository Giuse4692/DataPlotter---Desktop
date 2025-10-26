import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Assicurati che il tuo file export_utils sia nella cartella modules/
import modules.export_utils as export_utils 

def show_plotting_ui(df):
    st.header("Costruttore di Grafici")
    st.info("Usa la **Sidebar a sinistra** per mappare gli assi e personalizzare il grafico.")
    
    column_list = df.columns.tolist()
    
    # --- 1. Selezione Tipo di Grafico ---
    plot_type = st.selectbox(
        "Scegli il tipo di grafico",
        ["Linea 2D", "Scatter 2D", "Scatter 3D", "Linea 3D (Line)", "Superficie 3D (Mesh)"]
    )
    
    # --- 2. Mappatura Assi ---
    st.sidebar.header("2. Mappatura Assi")
    x_axis = st.sidebar.selectbox("Asse X", column_list, index=0, key="x_axis")
    
    # MULTISELECT per le curve 2D
    y_axes = st.sidebar.multiselect(
        "Assi Y (Curve 2D) / Asse Y (Curve 3D)",
        column_list,
        default=[column_list[1]] if len(column_list) > 1 else [column_list[0]],
        key="y_axes"
    )
    
    # Prende la prima Y per i grafici 3D e per il titolo di default
    y_axis_single = y_axes[0] if y_axes else column_list[1] if len(column_list) > 1 else column_list[0]
    
    z_axis = None
    if "3D" in plot_type:
        z_axis = st.sidebar.selectbox("Asse Z", column_list, index=2 if len(column_list) > 2 else 0, key="z_axis")
        
    color_axis = st.sidebar.selectbox("Mappa Colore (opzionale)", [None] + column_list, key="color_axis")
    
    # ----------------------------------------------------
    # NUOVA SEZIONE: SCALE LOGARITMICHE (3. Scale Assi)
    # ----------------------------------------------------
    st.sidebar.header("3. Scale Assi")
    log_x = st.sidebar.checkbox("Scala Logaritmica Asse X", key="log_x")
    log_y = st.sidebar.checkbox("Scala Logaritmica Asse Y", key="log_y")
    
    # --- 4. Personalizzazione (Titoli) ---
    st.sidebar.header("4. Titoli e Legenda")
    
    default_title = f"{', '.join(y_axes)} vs {x_axis}" if len(y_axes) > 1 and "3D" not in plot_type else f"{y_axis_single} vs {x_axis}"
    
    plot_title = st.sidebar.text_input("Titolo Grafico", default_title)
    x_label = st.sidebar.text_input("Etichetta Asse X", x_axis)
    y_label = st.sidebar.text_input("Etichetta Asse Y", ", ".join(y_axes) if len(y_axes) > 1 else y_axis_single)
    z_label = "Z"
    if z_axis:
        z_label = st.sidebar.text_input("Etichetta Asse Z", z_axis)
    show_legend = st.sidebar.checkbox("Mostra Legenda", True)

    # ----------------------------------------------------
    # SEZIONE 5: IMPOSTAZIONI CURVE DINAMICHE
    # ----------------------------------------------------
    curve_settings = {}
    if plot_type in ["Linea 2D", "Scatter 2D"] and y_axes:
        st.sidebar.header("5. Dettagli Curva")
        st.sidebar.info("Colore e Spessore/Dimensione per ogni curva.")
        
        for i, y_col in enumerate(y_axes):
            with st.sidebar.expander(f"Curva: {y_col}", expanded=(i == 0)):
                
                default_color = px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
                color = st.color_picker("Colore", default_color, key=f"color_{y_col}")
                
                # Spessore/Dimensione del punto
                default_width = 2.0 # ⚠️ CORREZIONE: DEVE ESSERE FLOAT
                line_width = st.slider(
                    "Spessore linea / Dimensione punto", 
                    min_value=0.5, 
                    max_value=10.0, 
                    value=default_width, 
                    step=0.5, 
                    key=f"width_{y_col}"
                )
                
                curve_settings[y_col] = {
                    'color': color,
                    'width': line_width
                }
    # ----------------------------------------------------
    
    # --- 6. Generazione Grafico ---
    fig = go.Figure()

    try:
        # ----------------------------------------------------
        # LOGICA 2D: TRACCE MULTIPLE (Linee e Scatter)
        # ----------------------------------------------------
        if plot_type == "Linea 2D" or plot_type == "Scatter 2D":
            mode = 'lines' if plot_type == "Linea 2D" else 'markers'
            
            for y_col in y_axes:
                settings = curve_settings.get(y_col, {}) 
                color = settings.get('color', 'blue') 
                width = settings.get('width', 2.0)
                
                fig.add_trace(go.Scatter(
                    x=df[x_axis],
                    y=df[y_col],
                    mode=mode,
                    name=y_col, 
                    line=dict(color=color, width=width) if mode == 'lines' else None,
                    marker=dict(color=color, size=width) if mode == 'markers' else None
                ))

        # ----------------------------------------------------
        # LOGICA 3D: TRACCE SINGOLE (Linee e Scatter) - INVARIANTI
        # ----------------------------------------------------
        elif plot_type == "Scatter 3D":
            is_numeric = color_axis and df[color_axis].dtype.kind in 'iufc'
            fig = px.scatter_3d(
                df, x=x_axis, y=y_axis_single, z=z_axis, color=color_axis, title=plot_title,
                color_continuous_scale='Viridis' if is_numeric else None,
                color_discrete_sequence=px.colors.qualitative.Plotly if color_axis and not is_numeric else None
            )
            
        elif plot_type == "Linea 3D (Line)":
            fig = px.line_3d(
                df, x=x_axis, y=y_axis_single, z=z_axis, color=color_axis, title=plot_title,
                color_discrete_sequence=px.colors.qualitative.Plotly if color_axis else None
            )

        # ----------------------------------------------------
        # LOGICA Mesh 3D (Funzionante) - INVARIANTE
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
                colorway=px.colors.qualitative.Plotly
            )
            
            # --- Configurazione Colore per Kaleido (Correzione) ---
            if color_axis and "Mesh" not in plot_type:
                fig.update_layout(coloraxis=dict(
                    colorscale=px.colors.sequential.Viridis,
                    colorbar=dict(title=color_axis)
                ))
            
            # --- Configurazione Assi ---
            if "3D" in plot_type:
                fig.update_layout(scene=dict(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    zaxis_title=z_label
                ))
            else:
                # APPLICAZIONE SCALE LOGARITMICHE E TITOLI 2D
                x_type = "log" if log_x else "linear"
                y_type = "log" if log_y else "linear"
                
                fig.update_layout(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    xaxis=dict(type=x_type),
                    yaxis=dict(type=y_type)
                )
            
            # --- Plot e Download ---
            config = {'displaylogo': False, 'modeBarButtonsToRemove': ['toImage']}
            st.plotly_chart(fig, use_container_width=True, config=config)

            # --- CHIAMATA AL MODULO DOWNLOAD (Funziona con Kaleido) ---
            export_utils.show_download_ui(fig, plot_title)

    except IndexError:
        st.warning("Seleziona almeno una colonna per l'Asse Y.")
    except Exception as e:
        st.error(f"Errore durante la creazione del grafico: {e}")