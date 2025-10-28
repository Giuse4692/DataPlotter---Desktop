import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np 
import pandas as pd
import re 
from io import BytesIO

import modules.export_utils as export_utils 
import modules.annotation_utils as au 

# La funzione calculate_and_plot_intersections è necessaria qui in plotting.py
def calculate_and_plot_intersections(fig, df, x_axis_name, ref_type, val1, val2, show_points, show_table):
    
    intersection_results = []
    
    if not show_points and not show_table:
        return 
    
    # --- Gestione Linea Verticale (X = Costante) ---
    if ref_type == 'x_const':
        x_target = val1
        for trace in fig.data:
            if trace.mode in ['lines', 'markers'] and trace.name not in ['Annotazioni', 'Intersezioni']:
                x_data = np.array(trace.x)
                y_data = np.array(trace.y)
                
                if x_target >= x_data.min() and x_target <= x_data.max():
                    y_intersec = np.interp(x_target, x_data, y_data)
                    
                    intersection_results.append({
                        'Curva': trace.name,
                        'X Intersezione': x_target,
                        'Y Intersezione': y_intersec,
                        'Equazione': f"X = {x_target}"
                    })
    
    # --- Gestione Linea Orizzontale (Y = Costante) e Lineare (Y = mX + q) ---
    elif ref_type in ['y_const', 'linear']:
        
        for trace in fig.data:
            if trace.mode in ['lines', 'markers'] and trace.name not in ['Annotazioni', 'Intersezioni']:
                
                x_data = np.array(trace.x)
                y_data = np.array(trace.y)
                
                if ref_type == 'y_const':
                    target_y = val1
                    f_x = y_data - target_y 
                else: # 'linear'
                    m, q = val1, val2
                    f_x = y_data - (m * x_data + q)
                
                f_x_signs = np.sign(f_x)
                sign_change = np.diff(f_x_signs)
                intersection_indices = np.where(sign_change != 0)[0]
                
                for i in intersection_indices:
                    x1, x2 = x_data[i], x_data[i+1]
                    f1, f2 = f_x[i], f_x[i+1]
                    
                    x_intersec = x1 - f1 * (x2 - x1) / (f2 - f1)
                    y_intersec = np.interp(x_intersec, x_data, y_data) 
                    
                    is_new = True
                    for res in intersection_results:
                        if res['Curva'] == trace.name and abs(res['X Intersezione'] - x_intersec) < 1e-6:
                            is_new = False
                            break
                    
                    if is_new:
                        equation_str = f"Y = {val1}X + {val2}" if ref_type == 'linear' else f"Y = {val1}"
                        intersection_results.append({
                            'Curva': trace.name,
                            'X Intersezione': x_intersec,
                            'Y Intersezione': y_intersec,
                            'Equazione': equation_str
                        })

    if intersection_results:
        points_df = pd.DataFrame(intersection_results)
        
        if show_points:
            fig.add_trace(go.Scatter(
                x=points_df['X Intersezione'],
                y=points_df['Y Intersezione'],
                mode='markers',
                name='Intersezioni',
                marker=dict(size=12, color='green', symbol='circle-open', line=dict(width=2))
            ))

        if show_table:
            st.subheader("Tabella Analitica Intersezione")
            st.dataframe(points_df.style.format({'X Intersezione': '{:.4f}', 'Y Intersezione': '{:.4f}'}), use_container_width=True)
            
    return intersection_results


def show_plotting_ui(df):
    
    st.header("Costruttore di Grafici")
    st.info("Usa la **Sidebar a sinistra** per mappare gli assi e personalizzare il grafico.")
    
    column_list = df.columns.tolist()
    
    # 1. Selezione Tipo di Grafico (Salviamo il tipo per il reset)
    plot_type = st.selectbox(
        "Scegli il tipo di grafico",
        ["Linea 2D", "Scatter 2D", "Scatter 3D", "Linea 3D (Line)", "Superficie 3D (Mesh)"]
    )
    st.session_state.plot_type = plot_type 
    
    # ⚠️ CORREZIONE: Definiamo 'is_3d' immediatamente dopo 'plot_type'
    is_3d = "3D" in plot_type or "Mesh" in plot_type
    
    # Raccoglie le impostazioni di annotazione dalla sidebar
    annotation_settings = au.show_annotation_controls(is_3d_mode=is_3d) # Passiamo il nuovo is_3d
    custom_points = annotation_settings['custom_points']
    ref_equation = annotation_settings['ref_equation']
    show_points = annotation_settings['show_points']
    show_table = annotation_settings['show_table']
    
    
    # 2. Mappatura Assi
    st.sidebar.header("2. Mappatura Assi")
    x_axis = st.sidebar.selectbox("Asse X", column_list, index=0, key="x_axis")
    
    y_axes = st.sidebar.multiselect(
        "Assi Y (Curve 2D) / Asse Y (Curve 3D)",
        column_list,
        default=[column_list[1]] if len(column_list) > 1 else [column_list[0]],
        key="y_axes"
    )
    
    y_axis_single = y_axes[0] if y_axes else column_list[1] if len(column_list) > 1 else column_list[0]
    
    z_axis = None
    
    if is_3d: # ⚠️ Ora 'is_3d' è definito e questo blocco funziona
        z_axis = st.sidebar.selectbox("Asse Z", column_list, index=2 if len(column_list) > 2 else 0, key="z_axis")
        
    color_axis = st.sidebar.selectbox("Mappa Colore (opzionale)", [None] + column_list, key="color_axis")
    
    st.sidebar.header("3. Scale Assi")
    log_x = st.sidebar.checkbox("Scala Logaritmica Asse X", key="log_x")
    log_y = st.sidebar.checkbox("Scala Logaritmica Asse Y", key="log_y")
    
    st.sidebar.header("4. Titoli e Legenda")
    
    default_title = f"{', '.join(y_axes)} vs {x_axis}" if len(y_axes) > 1 and not is_3d else f"{y_axis_single} vs {x_axis}"
    
    plot_title = st.sidebar.text_input("Titolo Grafico", default_title)
    st.markdown(f'<div id="graph-title-id" style="display:none;">{plot_title}</div>', unsafe_allow_html=True)
    x_label = st.sidebar.text_input("Etichetta Asse X", x_axis)
    y_label = st.sidebar.text_input("Etichetta Asse Y", ", ".join(y_axes) if len(y_axes) > 1 and not is_3d else y_axis_single)
    z_label = "Z"
    if z_axis:
        z_label = st.sidebar.text_input("Etichetta Asse Z", z_axis)
    show_legend = st.sidebar.checkbox("Mostra Legenda", True)

    curve_settings = {}
    if plot_type in ["Linea 2D", "Scatter 2D"] and y_axes:
        st.sidebar.header("6. Dettagli Curva")
        st.sidebar.info("Colore e Spessore/Dimensione per ogni curva.")
        
        for i, y_col in enumerate(y_axes):
            with st.sidebar.expander(f"Curva: {y_col}", expanded=(i == 0)):
                
                default_color = px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
                color = st.color_picker("Colore", default_color, key=f"color_{y_col}")
                
                default_width = 2.0
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
    
    fig = None 

    try:
        # ----------------------------------------------------
        # LOGICA 2D: TRACCE MULTIPLE
        # ----------------------------------------------------
        if plot_type in ["Linea 2D", "Scatter 2D"]:
            fig = go.Figure() 
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
            
            # Aggiunta traccia PUNTI DI ANNOTAZIONE 2D
            annotation_trace = au.get_annotations_trace(custom_points, is_3d=False) 
            if annotation_trace:
                fig.add_trace(annotation_trace)
            
            # GESTIONE LINEA DI RIFERIMENTO E INTERSEZIONI
            ref_type, val1, val2, _ = au.parse_equation_advanced(ref_equation)
            
            if ref_type and val1 is not None:
                if ref_type in ['y_const', 'x_const']:
                    au.add_reference_line(fig, ref_type.split('_')[0], val1, df=df) 
                elif ref_type == 'linear':
                    au.add_reference_line(fig, 'linear', val2, slope=val1, df=df) 
                
                calculate_and_plot_intersections(fig, df, x_axis, ref_type, val1, val2, show_points, show_table)


        # ----------------------------------------------------
        # LOGICA 3D: TRACCE MULTIPLE (Scatter e Linea)
        # ----------------------------------------------------
        elif plot_type in ["Scatter 3D", "Linea 3D (Line)"]:
            
            go_trace_type = go.Scatter3d
            mode = 'markers' if plot_type == "Scatter 3D" else 'lines'

            is_numeric = color_axis and df[color_axis].dtype.kind in 'iufc'
            
            if not color_axis or len(y_axes) > 1:
                 fig = px.scatter_3d(
                    df, x=x_axis, y=y_axis_single, z=z_axis, color=color_axis, title=plot_title,
                    color_continuous_scale='Viridis' if is_numeric else None,
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
            else:
                 fig = go.Figure(data=[go_trace_type(
                    x=df[x_axis], y=df[y_axis_single], z=df[z_axis],
                    mode=mode, name=y_axis_single,
                    marker=dict(
                        color=df[color_axis], 
                        colorscale='Viridis' if is_numeric else px.colors.qualitative.Plotly,
                        cmin=df[color_axis].min(), cmax=df[color_axis].max()
                    )
                )])

            # AGGIUNTA PUNTI DI ANNOTAZIONE 3D
            default_z_val = df[z_axis].iloc[0] if not df.empty and z_axis in df.columns else 0.0
            annotation_trace = au.get_annotations_trace(custom_points, is_3d=True)
            
            if annotation_trace:
                fig.add_trace(go_trace_type(
                    x=annotation_trace.x,
                    y=annotation_trace.y,
                    z=[default_z_val] * len(annotation_trace.x), 
                    mode='markers+text',
                    text=annotation_trace.text,
                    name=annotation_trace.name,
                    marker=dict(size=12, color='red', symbol=annotation_trace.marker.symbol)
                ))


        # ----------------------------------------------------
        # LOGICA Mesh 3D (Superficie)
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
            if is_3d:
                fig.update_layout(scene=dict(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    zaxis_title=z_label
                ))
            else:
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

            export_utils.show_download_ui(fig, plot_title)

    except IndexError:
        st.warning("Seleziona almeno una colonna per l'Asse Y.")
    except Exception as e:
        st.error(f"Errore durante la creazione del grafico: {e}")