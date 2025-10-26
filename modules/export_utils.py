import streamlit as st
from io import BytesIO
import plotly.graph_objects as go # Utilizzato per il type hinting

def show_download_ui(fig: go.Figure, plot_title: str):
    """
    Mostra i pulsanti di download per PNG, JPEG, SVG (richiede Kaleido) e HTML.
    """
    st.subheader("Download Grafico")

    # Utilizziamo le colonne per posizionare i pulsanti uno accanto all'altro
    col_png, col_jpeg, col_svg, col_html = st.columns(4)

    # 1. Download PNG (Richiede Kaleido)
    try:
        buf_png = BytesIO()
        fig.write_image(buf_png, format="png", scale=4) 
        buf_png.seek(0)
        with col_png:
            st.download_button(
                label="Scarica PNG",
                data=buf_png,
                file_name=f"{plot_title.replace(' ', '_')}.png",
                mime="image/png",
                key="download_png"
            )
    except Exception:
        with col_png:
            st.button("PNG (Kaleido mancante)", disabled=True)

    # 2. Download JPEG (Richiede Kaleido)
    try:
        buf_jpeg = BytesIO()
        fig.write_image(buf_jpeg, format="jpeg", scale=4) 
        buf_jpeg.seek(0)
        with col_jpeg:
            st.download_button(
                label="Scarica JPEG",
                data=buf_jpeg,
                file_name=f"{plot_title.replace(' ', '_')}.jpeg",
                mime="image/jpeg",
                key="download_jpeg"
            )
    except Exception:
        with col_jpeg:
            st.button("JPEG (Kaleido mancante)", disabled=True)


    # 3. Download SVG (Richiede Kaleido)
    try:
        buf_svg = BytesIO()
        fig.write_image(buf_svg, format="svg")
        buf_svg.seek(0)
        with col_svg:
            st.download_button(
                label="Scarica SVG",
                data=buf_svg,
                file_name=f"{plot_title.replace(' ', '_')}.svg",
                mime="image/svg+xml",
                key="download_svg"
            )
    except Exception:
        with col_svg:
            st.button("SVG (Kaleido mancante)", disabled=True)
        
    # 4. Download HTML Interattivo (Sempre disponibile)
    html_bytes = fig.to_html(full_html=True).encode("utf-8")
    with col_html:
        st.download_button(
            label="Scarica HTML interattivo",
            data=html_bytes,
            file_name=f"{plot_title.replace(' ', '_')}.html",
            mime="text/html",
            key="download_html"
        )
    
    st.caption("ℹ️ HTML è interattivo e funziona sempre. PNG/JPEG/SVG richiedono la libreria `Kaleido`.")