import streamlit as st
import plotly.graph_objects as go 
import numpy as np 
import pandas as pd 
import re 

# *** INIZIO MODIFICA: DIZIONARIO CORRETTO ***
# Questi simboli sono validi sia in 2D che in 3D
PLOTLY_SYMBOLS = {
    "Cerchio": "circle",
    "Quadrato": "square",
    "Diamante": "diamond",
    "Croce (+)": "cross",
    "Croce (x)": "x",
    "Cerchio Aperto": "circle-open",
    "Quadrato Aperto": "square-open",
    "Diamante Aperto": "diamond-open"
}
# *** FINE MODIFICA ***

def parse_equation_advanced(eq_str):
    """
    Analizza equazioni lineari o costanti del tipo y=val, x=val, o y=mx+q.
    Restituisce (tipo: 'x_const', 'y_const', 'linear', val1(m/c), val2(q)).
    """
    eq_str = eq_str.strip().lower().replace(' ', '')
    if not eq_str or '=' not in eq_str:
        return None, None, None, None
    
    # 1. Caso Costante (y=val o x=val)
    if eq_str.startswith('y=') or eq_str.startswith('x='):
        try:
            var = eq_str[0]
            val = float(eq_str[2:])
            return f'{var}_const', val, None, None
        except ValueError:
            pass 

    # 2. Caso Lineare (y=mx+q)
    if eq_str.startswith('y='):
        expression = eq_str[2:]
        
        if expression == 'x': return 'linear', 1.0, 0.0, expression
        if expression == '-x': return 'linear', -1.0, 0.0, expression
        
        match = re.match(r'(-?\d*\.?\d*)x([+\-]\d*\.?\d*|)$', expression)
        
        if match:
            m_str = match.group(1)
            if m_str in ('', '+'): m = 1.0
            elif m_str == '-': m = -1.0
            else: m = float(m_str)
            
            q_str = match.group(2)
            q = float(q_str) if q_str else 0.0

            return 'linear', m, q, expression

        try:
            val = float(expression)
            return 'y_const', val, None, None
        except ValueError:
            pass
            
    return None, None, None, None


def show_annotation_controls(is_3d_mode):
    """
    Mostra i controlli nella sidebar per aggiungere punti di annotazione e linee di riferimento.
    """
    if 'custom_points' not in st.session_state:
        st.session_state.custom_points = []
    
    # 1. LOGICA DI RESET STATO
    current_mode = "3D" if is_3d_mode else "2D"
    if 'last_plot_mode' not in st.session_state:
        st.session_state.last_plot_mode = current_mode
    
    if st.session_state.last_plot_mode != current_mode:
        st.session_state.custom_points = []
        st.session_state.last_plot_mode = current_mode
        st.rerun()
        
    st.sidebar.header("5. Punti/Linee di Riferimento")
    
    # --- Gestione Cancellazione Punti ---
    if st.session_state.custom_points:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Gestione Punti Aggiunti")
        
        points_to_remove_options = [f"{p['label']} ({p['x']:.2f}, {p['y']:.2f})" + (f", {p['z']:.2f})" if p.get('z') is not None else "") for p in st.session_state.custom_points]
        
        points_to_remove = st.sidebar.multiselect(
            "Seleziona punti da rimuovere", 
            options=points_to_remove_options,
            key="points_remove"
        )
        
        if st.sidebar.button("Rimuovi Selezionati", key="remove_selected_btn"):
            points_to_keep = []
            for p in st.session_state.custom_points:
                label = f"{p['label']} ({p['x']:.2f}, {p['y']:.2f})" + (f", {p['z']:.2f})" if p.get('z') is not None else "")
                if label not in points_to_remove:
                    points_to_keep.append(p)
            st.session_state.custom_points = points_to_keep
            st.rerun()

    # --- Sezione per l'aggiunta di un punto singolo ---
    is_expanded = len(st.session_state.custom_points) == 0 or is_3d_mode 
    with st.sidebar.expander("Aggiungi Nuovo Punto", expanded=is_expanded):
        
        # *** INIZIO MODIFICA: LOGICA ON_CLICK ***
        
        # 1. Definisci la callback che gestisce TUTTA la logica
        def _add_point_and_reset(is_3d_cb, symbol_key_cb):
            # 1. Ottieni i valori dallo stato (dove i widget li hanno scritti)
            point_x = st.session_state.ann_point_x
            point_y = st.session_state.ann_point_y
            point_z = st.session_state.ann_point_z if is_3d_cb else None
            point_label = st.session_state.ann_point_label
            
            if not point_label: # Default se l'utente cancella l'etichetta
                point_label = "Rif."

            # 2. Logica di aggiunta
            new_point = {
                'x': point_x, 'y': point_y, 'z': point_z,
                'label': point_label, 
                'symbol': PLOTLY_SYMBOLS[symbol_key_cb]
            }
            st.session_state.custom_points.append(new_point)

            # 3. Logica di reset (ora è sicura perché dentro una callback)
            st.session_state.ann_point_x = 0.0
            st.session_state.ann_point_y = 0.0
            st.session_state.ann_point_z = 0.0
            st.session_state.ann_point_label = "Rif."

        # 2. Inizializza i valori nello stato SE non esistono
        if 'ann_point_x' not in st.session_state:
            st.session_state.ann_point_x = 0.0
        if 'ann_point_y' not in st.session_state:
            st.session_state.ann_point_y = 0.0
        if 'ann_point_z' not in st.session_state:
            st.session_state.ann_point_z = 0.0
        if 'ann_point_label' not in st.session_state:
            st.session_state.ann_point_label = "Rif."

        # 3. Disegna i widget, legati ai 'key'
        st.number_input("Coordinata X", key="ann_point_x")
        st.number_input("Coordinata Y", key="ann_point_y")
        
        if is_3d_mode:
            st.number_input("Coordinata Z", key="ann_point_z") 
        
        st.text_input("Etichetta", key="ann_point_label")
        point_symbol_key = st.selectbox("Simbolo", list(PLOTLY_SYMBOLS.keys()), key="ann_point_symbol")
        
        # 4. Lega il bottone alla callback
        st.button(
            "Aggiungi Punto", 
            key="add_point_btn", 
            on_click=_add_point_and_reset, 
            args=(is_3d_mode, point_symbol_key) # Passa i valori necessari
        )
        # *** FINE MODIFICA ***


    # Linea di Riferimento
    st.sidebar.markdown("---")
    st.sidebar.subheader("Linee di Riferimento 2D")
    ref_equation = st.sidebar.text_input("Equazione (es. y=0.5, x=10 o y=2x+1)", key="ref_eq", value="")
    show_points = st.sidebar.checkbox("Visualizza Intersezioni (Punti)", key="show_labels_intersections", value=True)
    show_table = st.sidebar.checkbox("Mostra Tabella Analitica", key="show_log_output")
    
    return {
        'custom_points': st.session_state.custom_points,
        'ref_equation': ref_equation,
        'show_points': show_points,
        'show_table': show_table,
    }

def get_annotations_trace(custom_points, is_3d=False):
    """Crea un trace Scatter (2D) o Scatter3D (3D) per i punti di annotazione."""
    if not custom_points:
        return None
    
    points_x = [p['x'] for p in custom_points]
    points_y = [p['y'] for p in custom_points]
    points_text = [p['label'] for p in custom_points]
    points_symbol = [p['symbol'] for p in custom_points]

    if is_3d:
        # Punti Z vengono presi dalla sessione
        points_z = [p.get('z', 0.0) for p in custom_points] 
        TraceType = go.Scatter3d
        
        return TraceType(
            x=points_x, y=points_y, z=points_z,
            mode='markers+text',
            text=points_text,
            name='Annotazioni',
            textposition="top center", # Aggiunto per coerenza
            marker=dict(
                size=12, 
                color='red', 
                symbol=points_symbol,
                line=dict(width=1, color='Black')
            )
        )
    else:
        # Traccia 2D
        return go.Scatter(
            x=points_x,
            y=points_y,
            mode='markers+text',
            text=points_text,
            textposition="top center",
            name='Annotazioni',
            marker=dict(
                size=12, 
                color='red', 
                symbol=points_symbol,
                line=dict(width=1, color='Black')
            )
        )


def add_reference_line(fig, var, val, slope=None, df=None):
    """Aggiunge una linea orizzontale (y=c), verticale (x=c) o lineare (y=mx+q) al grafico."""
    if var == 'y':
        fig.add_shape(type='line', x0=0, y0=val, x1=1, y1=val, xref='paper', yref='y', line=dict(color="Red", width=1, dash="dot"), name=f"Rif. Y={val}")
    elif var == 'x':
        fig.add_shape(type='line', x0=val, y0=0, x1=val, y1=1, xref='x', yref='paper', line=dict(color="Red", width=1, dash="dot"), name=f"Rif. X={val}")
    elif var == 'linear' and df is not None:
        q = val 
        m = slope 
        try:
            # Assumiamo che x_axis sia accessibile da st.session_state
            # NOTA: questo 'x_axis' è quello del grafico principale, non l'input dell'annotazione
            x_col_key = 'x_axis_2d' # Chiave del widget 2D
            if st.session_state.get('plot_type', "2D") in ["Scatter 3D", "Linea 3D (Line)", "Superficie 3D (Mesh)"]:
                 x_col_key = 'x_3d_0' # Chiave del primo widget 3D
            
            x_col = st.session_state.get(x_col_key, df.columns[0])
            
            x_min = df[x_col].min()
            x_max = df[x_col].max()
            x_line = np.linspace(x_min, x_max, 100)
            y_line = m * x_line + q 
            fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', name=f"Rif. Y={m}X+{q}", line=dict(color='orange', width=2, dash='dot')))
        except Exception as e:
            st.warning(f"Impossibile disegnare la linea Y=mX+q. Errore: {e}")