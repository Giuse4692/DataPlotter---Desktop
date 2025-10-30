import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np 
import pandas as pd
import re 
from io import BytesIO

import modules.export_utils as export_utils 
import modules.annotation_utils as au 

# Assicurati che la funzione calculate_and_plot_intersections sia definita qui sopra
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
                yaxis='y1', 
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
    
    # 1. Selezione Tipo di Grafico
    plot_type = st.selectbox(
        "Scegli il tipo di grafico",
        ["Linea 2D", "Scatter 2D", "Scatter 3D", "Linea 3D (Line)", "Superficie 3D (Mesh)"]
    )
    st.session_state.plot_type = plot_type 
    
    is_3d = "3D" in plot_type or "Mesh" in plot_type
    is_2d = plot_type in ["Linea 2D", "Scatter 2D"]
    
    # Inizializza lo stato per le curve 3D con colore e spessore
    if 'plot_3d_curves' not in st.session_state:
        st.session_state.plot_3d_curves = [{
            'x': column_list[0],
            'y': column_list[1] if len(column_list) > 1 else column_list[0],
            'z': column_list[2] if len(column_list) > 2 else column_list[0],
            'color': px.colors.qualitative.Plotly[0], 
            'width': 2.0 if plot_type == "Linea 3D (Line)" else 4.0 
        }]

    # Se si passa da 3D a 2D, resetta per sicurezza
    if is_2d and len(st.session_state.plot_3d_curves) > 1:
        st.session_state.plot_3d_curves = [st.session_state.plot_3d_curves[0]]
        
    
    # -----------------------------------------------------------------
    # BLOCCHI SIDEBAR RIORDINATI
    # -----------------------------------------------------------------

    # ===== BLOCCO 1: MAPPATURA ASSI =====
    st.sidebar.header("1. Mappatura Assi")
    
    # Inizializza variabili per 2D
    x_axis = column_list[0]
    y_axes_left = []
    y_axes_right = []
    
    if is_2d:
        x_axis = st.sidebar.selectbox("Asse X", column_list, index=0, key="x_axis_2d")
        
        y_axes_left = st.sidebar.multiselect(
            "Assi Y (Sinistra)",
            column_list,
            default=[column_list[1]] if len(column_list) > 1 else [column_list[0]],
            key="y_axes_left"
        )
        
        available_cols_for_right = [col for col in column_list if col not in y_axes_left]
        y_axes_right = st.sidebar.multiselect(
            "Assi Y (Destra - Opzionale)",
            available_cols_for_right,
            default=[],
            key="y_axes_right"
        )
    
    if is_3d:
        
        # Aggiungi Grafico 3D con colore/spessore di default
        if st.sidebar.button("Aggiungi Grafico 3D"):
            i = len(st.session_state.plot_3d_curves) # Indice per nuovo colore
            default_width = 2.0 if plot_type == "Linea 3D (Line)" else 4.0
            
            st.session_state.plot_3d_curves.append({
                'x': column_list[0],
                'y': column_list[1] if len(column_list) > 1 else column_list[0],
                'z': column_list[2] if len(column_list) > 2 else column_list[0],
                'color': px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)],
                'width': default_width
            })
        
        # Gestione Rimozione (fuori dal ciclo di rendering)
        indices_to_remove = []
        for i in range(len(st.session_state.plot_3d_curves)):
            if f"remove_3d_{i}" in st.session_state and st.session_state[f"remove_3d_{i}"]:
                if len(st.session_state.plot_3d_curves) > 1:
                    indices_to_remove.append(i)
        
        if indices_to_remove:
            st.session_state.plot_3d_curves = [c for i, c in enumerate(st.session_state.plot_3d_curves) if i not in indices_to_remove]
            for i in indices_to_remove:
                st.session_state[f"remove_3d_{i}"] = False
            st.rerun()

        # Rendering dei selettori per ogni curva
        for i, curve_config in enumerate(st.session_state.plot_3d_curves):
            with st.sidebar.expander(f"Grafico 3D #{i+1}", expanded=True):
                
                x_index = column_list.index(curve_config['x']) if curve_config['x'] in column_list else 0
                y_index = column_list.index(curve_config['y']) if curve_config['y'] in column_list else 1
                z_index = column_list.index(curve_config['z']) if curve_config['z'] in column_list else 2

                curve_config['x'] = st.selectbox(f"Asse X (Grafico {i+1})", column_list, index=x_index, key=f"x_3d_{i}")
                curve_config['y'] = st.selectbox(f"Asse Y (Grafico {i+1})", column_list, index=y_index, key=f"y_3d_{i}")
                curve_config['z'] = st.selectbox(f"Asse Z (Grafico {i+1})", column_list, index=z_index, key=f"z_3d_{i}")

                if len(st.session_state.plot_3d_curves) > 1:
                    st.button(f"Rimuovi Grafico #{i+1}", key=f"remove_3d_{i}")
    
    # Asse Colore (comune a 2D e 3D)
    color_axis = st.sidebar.selectbox("Mappa Colore (opzionale)", [None] + column_list, key="color_axis")
    
    
    # ===== BLOCCO 2: TITOLI E LEGENDA =====
    st.sidebar.header("2. Titoli e Legenda")
    
    # Inizializza etichette
    x_label, y_label_left, z_label = "", "", ""
    y_label_right = ""
    
    if is_2d:
        all_y_axes = y_axes_left + y_axes_right
        default_title = f"{', '.join(all_y_axes)} vs {x_axis}" if all_y_axes else "Grafico 2D"
        
        plot_title = st.sidebar.text_input("Titolo Grafico", default_title, key="title_2d")
        x_label = st.sidebar.text_input("Etichetta Asse X", x_axis, key="xlabel_2d")
        
        y_label_left_default = ", ".join(y_axes_left) if y_axes_left else "Asse Y (Sinistra)"
        y_label_left = st.sidebar.text_input("Etichetta Asse Y (Sinistra)", y_label_left_default, key="ylabel_left")
        
        if y_axes_right:
            y_label_right_default = ", ".join(y_axes_right)
            y_label_right = st.sidebar.text_input("Etichetta Asse Y (Destra)", y_label_right_default, key="ylabel_right")

    elif is_3d:
        default_title = f"Grafico 3D ({plot_type})"
        plot_title = st.sidebar.text_input("Titolo Grafico", default_title, key="title_3d")
        
        first_curve_config = st.session_state.plot_3d_curves[0]
        x_label = st.sidebar.text_input("Etichetta Asse X (Generale)", first_curve_config['x'], key="xlabel_3d")
        y_label_left = st.sidebar.text_input("Etichetta Asse Y (Generale)", first_curve_config['y'], key="ylabel_3d") # Riusiamo y_label_left
        z_label = st.sidebar.text_input("Etichetta Asse Z (Generale)", first_curve_config['z'], key="zlabel_3d")

        
    show_legend = st.sidebar.checkbox("Mostra Legenda", True)

    
    # ===== BLOCCO 3: SCALE ASSI E GRIGLIA =====
    st.sidebar.header("3. Scale Assi e Griglia")
    log_x = st.sidebar.checkbox("Scala Logaritmica Asse X", key="log_x")
    log_y_left = st.sidebar.checkbox("Scala Logaritmica Asse Y (Sinistra)", key="log_y_left")
    
    log_y_right = False
    if y_axes_right: # Solo per 2D
        log_y_right = st.sidebar.checkbox("Scala Logaritmica Asse Y (Destra)", key="log_y_right")
    
    st.sidebar.markdown("---") # Separatore

    grid_style_2d = "Griglia Completa (Default)"
    hide_grid_3d = False
    
    if is_2d:
        grid_style_2d = st.sidebar.selectbox(
            "Stile Griglia 2D", 
            ["Griglia Completa (Default)", "Solo Orizzontali", "Solo Verticali", "Nessuna Griglia"], 
            key="grid_style_2d",
            help="Scegli se mostrare la griglia completa, solo le linee orizzontali/verticali, o nasconderla."
        )
    if is_3d:
        hide_grid_3d = st.sidebar.checkbox("Nascondi Griglia 3D", value=False, key="hide_grid_3d")

    
    st.sidebar.markdown("---") # Separatore
    highlight_axes = st.sidebar.checkbox("Evidenzia Assi (Titoli e Linee)", key="highlight_axes")
    
    # *** INIZIO MODIFICA: Rimosso radio button "axis_color_style" ***
    # Non serve più, gli assi 3D evidenziati saranno sempre colorati.
    # *** FINE MODIFICA ***
    

    # ===== BLOCCO 4: DETTAGLI CURVA =====
    curve_settings = {}
    all_y_curves = y_axes_left + y_axes_right 
    
    if is_2d and all_y_curves:
        st.sidebar.header("4. Dettagli Curva 2D")
        st.sidebar.info("Colore e Spessore/Dimensione per ogni curva 2D.")
        
        for i, y_col in enumerate(all_y_curves):
            axis_label = "(Destra)" if y_col in y_axes_right else "(Sinistra)"
            with st.sidebar.expander(f"Curva: {y_col} {axis_label}", expanded=(i == 0)):
                
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
    
    elif is_3d and plot_type in ["Scatter 3D", "Linea 3D (Line)"]:
        st.sidebar.header("4. Dettagli Curva 3D")
        st.sidebar.info(f"Colore e Spessore/Dimensione per ogni curva 3D. Questi verranno ignorati se si imposta una 'Mappa Colore'.")

        for i, curve_config in enumerate(st.session_state.plot_3d_curves):
            with st.sidebar.expander(f"Dettagli Grafico 3D #{i+1}", expanded=True):
                
                default_color = curve_config['color']
                default_width = curve_config['width']
                
                label_width = "Dimensione punto" if plot_type == "Scatter 3D" else "Spessore linea"

                color = st.color_picker(f"Colore #{i+1}", default_color, key=f"color_3d_{i}")
                width = st.slider(
                    f"{label_width} #{i+1}",
                    min_value=0.5, 
                    max_value=20.0, 
                    value=default_width, 
                    step=0.5, 
                    key=f"width_3d_{i}"
                )
                
                curve_config['color'] = color
                curve_config['width'] = width


    
    # ===== BLOCCO 5: LINEE DI RIFERIMENTO E PUNTI =====
    annotation_settings = au.show_annotation_controls(is_3d_mode=is_3d)
    custom_points = annotation_settings['custom_points']
    ref_equation = annotation_settings['ref_equation']
    show_points = annotation_settings['show_points']
    show_table = annotation_settings['show_table']
    
    # -----------------------------------------------------------------
    # FINE BLOCCHI SIDEBAR
    # -----------------------------------------------------------------

    fig = None 

    try:
        # ----------------------------------------------------
        # LOGICA 2D: DOPPIO ASSE
        # ----------------------------------------------------
        if is_2d:
            fig = go.Figure() 
            mode = 'lines' if plot_type == "Linea 2D" else 'markers'
            
            # Loop per ASSE SINISTRO (y1)
            for y_col in y_axes_left:
                settings = curve_settings.get(y_col, {}) 
                color = settings.get('color', 'blue') 
                width = settings.get('width', 2.0)
                
                fig.add_trace(go.Scatter(
                    x=df[x_axis], y=df[y_col], mode=mode,
                    name=y_col, yaxis='y1', 
                    line=dict(color=color, width=width) if mode == 'lines' else None,
                    marker=dict(color=color, size=width) if mode == 'markers' else None
                ))
            
            # Loop per ASSE DESTRO (y2)
            for y_col in y_axes_right:
                settings = curve_settings.get(y_col, {})
                i = all_y_curves.index(y_col)
                default_color = px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
                color = settings.get('color', default_color) 
                width = settings.get('width', 2.0)
                
                fig.add_trace(go.Scatter(
                    x=df[x_axis], y=df[y_col], mode=mode,
                    name=f"{y_col} (Destra)", yaxis='y2', 
                    line=dict(color=color, width=width) if mode == 'lines' else None,
                    marker=dict(color=color, size=width) if mode == 'markers' else None
                ))
            
            # Annotazioni e Intersezioni (solo su y1)
            annotation_trace = au.get_annotations_trace(custom_points, is_3d=False) 
            if annotation_trace:
                fig.add_trace(annotation_trace)
            
            ref_type, val1, val2, _ = au.parse_equation_advanced(ref_equation)
            if ref_type and val1 is not None:
                if ref_type in ['y_const', 'x_const']:
                    au.add_reference_line(fig, ref_type.split('_')[0], val1, df=df) 
                elif ref_type == 'linear':
                    au.add_reference_line(fig, 'linear', val2, slope=val1, df=df) 
                
                calculate_and_plot_intersections(fig, df, x_axis, ref_type, val1, val2, show_points, show_table)


        # ----------------------------------------------------
        # LOGICA 3D (Multi-Traccia con Dettagli Curva)
        # ----------------------------------------------------
        elif is_3d:
            
            fig = go.Figure()
            
            # Determina il tipo di traccia
            if plot_type == "Superficie 3D (Mesh)":
                go_trace_type = go.Mesh3d
            else: # Scatter 3D or Linea 3D
                go_trace_type = go.Scatter3d
                mode = 'markers' if plot_type == "Scatter 3D" else 'lines'
            
            # Itera su ogni configurazione di grafico 3D salvata
            for i, curve_config in enumerate(st.session_state.plot_3d_curves):
                x_col = curve_config['x']
                y_col = curve_config['y']
                z_col = curve_config['z']
                
                if go_trace_type == go.Scatter3d:
                    manual_color = curve_config['color']
                    width = curve_config['width'] 
                    
                    marker_props = dict()
                    line_props = dict()

                    if color_axis:
                        marker_props['color'] = df[color_axis]
                        marker_props['colorscale'] = 'Viridis'
                        marker_props['showscale'] = (i == 0) 
                        if mode == 'markers':
                            marker_props['size'] = width 
                        line_props = None if mode == 'lines' else None 
                    
                    else:
                        marker_props['color'] = manual_color
                        if mode == 'markers':
                            marker_props['size'] = width
                        line_props = dict(color=manual_color, width=width) if mode == 'lines' else None

                    fig.add_trace(go_trace_type(
                        x=df[x_col],
                        y=df[y_col],
                        z=df[z_col],
                        mode=mode,
                        name=f"Grafico #{i+1} ({y_col})",
                        marker=marker_props if mode == 'markers' else None,
                        line=line_props if mode == 'lines' else None
                    ))
                
                elif go_trace_type == go.Mesh3d:
                    intensity_data = df[z_col] 
                    colorscale_choice = 'Blues'
                    if color_axis:
                        try:
                            intensity_data = df[color_axis]
                            colorscale_choice = 'Viridis' 
                        except Exception:
                            st.warning(f"Asse colore '{color_axis}' non valido. Uso '{z_col}'.")
                    
                    min_intensity = intensity_data.min()
                    max_intensity = intensity_data.max()

                    fig.add_trace(go_trace_type(
                        x=df[x_col],
                        y=df[y_col],
                        z=df[z_col],
                        opacity=0.7,
                        name=f"GrafC:\\Users\\giuse\\OneDrive\\Desktop\\DataPlotter---Desktop\\modules\\plotting.pyico #{i+1}",
                        intensity=intensity_data,
                        colorscale=colorscale_choice,
                        showscale=(i == 0), 
                        cmin=min_intensity,
                        cmax=max_intensity
                    ))

            # --- Gestione Annotazioni 3D (generica) ---
            annotation_trace_data = au.get_annotations_trace(custom_points, is_3d=True)
            if annotation_trace_data:
                fig.add_trace(annotation_trace_data)
        
        # ----------------------------------------------------
        # AGGIORNAMENTO LAYOUT
        # ----------------------------------------------------
        if fig: 
            
            # Applica "grassetto" ai titoli se la checkbox è attiva
            if highlight_axes:
                x_label = f"<b>{x_label}</b>"
                y_label_left = f"<b>{y_label_left}</b>"
                if y_label_right:
                    y_label_right = f"<b>{y_label_right}</b>"
                if z_label:
                    z_label = f"<b>{z_label}</b>"
            
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
                # *** INIZIO MODIFICA 3D ***
                show_grid_3d_val = not hide_grid_3d
                
                scene_dict = {
                    'xaxis_title': x_label,
                    'yaxis_title': y_label_left,
                    'zaxis_title': z_label,
                    'xaxis_showgrid': show_grid_3d_val,
                    'yaxis_showgrid': show_grid_3d_val,
                    'zaxis_showgrid': show_grid_3d_val,
                    'annotations': [] # Inizializza la lista di annotazioni
                }
                
                if highlight_axes:
                    # *** MODIFICA: Assi sempre colorati ***
                    x_col_c, y_col_c, z_col_c = 'red', 'green', 'blue'

                    # Calcola i range di tutti i dati plottati
                    all_x_cols = [c['x'] for c in st.session_state.plot_3d_curves]
                    all_y_cols = [c['y'] for c in st.session_state.plot_3d_curves]
                    all_z_cols = [c['z'] for c in st.session_state.plot_3d_curves]
                    
                    min_x = min(df[col].min() for col in all_x_cols)
                    max_x = max(df[col].max() for col in all_x_cols)
                    min_y = min(df[col].min() for col in all_y_cols)
                    max_y = max(df[col].max() for col in all_y_cols)
                    min_z = min(df[col].min() for col in all_z_cols)
                    max_z = max(df[col].max() for col in all_z_cols)
                    
                    # Estendi i range per includere lo zero
                    plot_min_x = min(0, min_x)
                    plot_max_x = max(0, max_x)
                    plot_min_y = min(0, min_y)
                    plot_max_y = max(0, max_y)
                    plot_min_z = min(0, min_z)
                    plot_max_z = max(0, max_z)

                    # Aggiungi le linee degli assi come tracce
                    fig.add_trace(go.Scatter3d(
                        x=[plot_min_x, plot_max_x], y=[0, 0], z=[0, 0],
                        mode='lines', line=dict(color=x_col_c, width=5),
                        name='Asse X', showlegend=False, hoverinfo='skip'
                    ))
                    fig.add_trace(go.Scatter3d(
                        x=[0, 0], y=[plot_min_y, plot_max_y], z=[0, 0],
                        mode='lines', line=dict(color=y_col_c, width=5),
                        name='Asse Y', showlegend=False, hoverinfo='skip'
                    ))
                    fig.add_trace(go.Scatter3d(
                        x=[0, 0], y=[0, 0], z=[plot_min_z, plot_max_z],
                        mode='lines', line=dict(color=z_col_c, width=5),
                        name='Asse Z', showlegend=False, hoverinfo='skip'
                    ))
                    
                    # Aggiungi Etichette (come frecce)
                    scene_dict['annotations'].extend([
                        dict(showarrow=False, x=plot_max_x, y=0, z=0, text="X", xanchor="left", yanchor="middle", font=dict(color=x_col_c, size=16)),
                        dict(showarrow=False, x=0, y=plot_max_y, z=0, text="Y", xanchor="center", yanchor="bottom", font=dict(color=y_col_c, size=16)),
                        dict(showarrow=False, x=0, y=0, z=plot_max_z, text="Z", xanchor="center", yanchor="bottom", font=dict(color=z_col_c, size=16))
                    ])
                    if plot_min_x < 0:
                        scene_dict['annotations'].append(dict(showarrow=False, x=plot_min_x, y=0, z=0, text="-X", xanchor="right", yanchor="middle", font=dict(color=x_col_c, size=16)))
                    if plot_min_y < 0:
                        scene_dict['annotations'].append(dict(showarrow=False, x=0, y=plot_min_y, z=0, text="-Y", xanchor="center", yanchor="top", font=dict(color=y_col_c, size=16)))
                    if plot_min_z < 0:
                        scene_dict['annotations'].append(dict(showarrow=False, x=0, y=0, z=plot_min_z, text="-Z", xanchor="center", yanchor="top", font=dict(color=z_col_c, size=16)))


                fig.update_layout(scene=scene_dict)
                # *** FINE MODIFICA 3D ***

            else: # is_2d
                # *** INIZIO MODIFICA 2D ***
                x_type = "log" if log_x else "linear"
                y_type_left = "log" if log_y_left else "linear"
                
                # Logica Griglia 2D
                show_x_grid = True
                show_y_grid = True
                show_x_zeroline = True 
                show_y_zeroline = True 

                if grid_style_2d == "Solo Orizzontali":
                    show_x_grid = False
                elif grid_style_2d == "Solo Verticali":
                    show_y_grid = False
                elif grid_style_2d == "Nessuna Griglia":
                    show_x_grid = False
                    show_y_grid = False
                    # CORREZIONE BUG: Nascondi anche le zeroline
                    show_x_zeroline = False
                    show_y_zeroline = False
                
                layout_update_dict = {
                    'xaxis_title': x_label,
                    'yaxis_title': y_label_left, 
                    'xaxis': dict(type=x_type, showgrid=show_x_grid, zeroline=show_x_zeroline),
                    'yaxis': dict(type=y_type_left, title=y_label_left, showgrid=show_y_grid, zeroline=show_y_zeroline) 
                }
                
                # Logica per evidenziare assi 2D
                if highlight_axes:
                    layout_update_dict['xaxis'].update({'linecolor': 'black', 'linewidth': 2})
                    layout_update_dict['yaxis'].update({'linecolor': 'black', 'linewidth': 2})
                    if show_x_grid: layout_update_dict['xaxis']['gridcolor'] = '#e0e0e0'
                    if show_y_grid: layout_update_dict['yaxis']['gridcolor'] = '#e0e0e0'


                # Aggiungi asse Y secondario (destro) se necessario
                if y_axes_right:
                    y_type_right = "log" if log_y_right else "linear"
                    layout_update_dict['yaxis2'] = dict(
                        title=y_label_right,
                        type=y_type_right,
                        overlaying='y',
                        side='right',
                        showgrid=show_y_grid, # Applica logica griglia
                        zeroline=show_y_zeroline # Applica logica zeroline
                    )
                    if highlight_axes:
                        layout_update_dict['yaxis2'].update({'linecolor': 'black', 'linewidth': 2})
                        if show_y_grid: layout_update_dict['yaxis2']['gridcolor'] = '#e0e0e0'
                    
                fig.update_layout(layout_update_dict)
                # *** FINE MODIFICA 2D ***
            
            # --- Plot e Download ---
            config = {'displaylogo': False, 'modeBarButtonsToRemove': ['toImage']}
            st.plotly_chart(fig, use_container_width=True, config=config)

            export_utils.show_download_ui(fig, plot_title)

    except IndexError:
        st.warning("Seleziona almeno una colonna per l'Asse Y (Sinistra) o configura un Grafico 3D.")
    except Exception as e:
        st.error(f"Errore durante la creazione del grafico: {e}")