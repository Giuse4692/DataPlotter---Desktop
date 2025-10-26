import streamlit as st
from io import BytesIO
import plotly.graph_objects as go # Utilizzato per il type hinting

def show_download_ui(fig: go.Figure, plot_title: str):
    """
    Mostra i pulsanti di download per PNG, SVG (richiede Kaleido) e HTML (sempre disponibile).
    """
    st.subheader("Download grafico")

    # Download PNG (Richiede Kaleido)
    try:
        buf_png = BytesIO()
        # Scala aumentata per migliore risoluzione nell'immagine statica
        fig.write_image(buf_png, format="png", scale=6) 
        buf_png.seek(0)
        st.download_button(
            label="Scarica PNG",
            data=buf_png,
            file_name=f"{plot_title.replace(' ', '_')}.png",
            mime="image/png",
            key="download_png"
        )
    except Exception as e:
        st.info("Download PNG fallito. Potrebbe mancare la libreria 'Kaleido' sul server.")
        
    # Download SVG (Richiede Kaleido)
    try:
        buf_svg = BytesIO()
        fig.write_image(buf_svg, format="svg")
        buf_svg.seek(0)
        st.download_button(
            label="Scarica SVG",
            data=buf_svg,
            file_name=f"{plot_title.replace(' ', '_')}.svg",
            mime="image/svg+xml",
            key="download_svg"
        )
    except Exception as e:
        pass 
        
    # Download HTML Interattivo (NON richiede Kaleido, è sempre sicuro)
    html_bytes = fig.to_html(full_html=True).encode("utf-8")
    st.download_button(
        label="Scarica HTML interattivo",
        data=html_bytes,
        file_name=f"{plot_title.replace(' ', '_')}.html",
        mime="text/html",
        key="download_html"
    )
    
    st.caption("ℹ️ Scarica l'immagine (PNG/SVG) o il file interattivo (HTML).")