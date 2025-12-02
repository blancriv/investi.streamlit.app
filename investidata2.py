import streamlit as st
import pandas as pd
import altair as alt
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import re

# ================================
# CONFIGURACIÓN GENERAL
# ================================
st.set_page_config(
    page_title="InvestiData – Análisis Forense Digital",
    layout="wide"
)

# ================================
# ESTILOS
# ================================
st.markdown("""
<style>

    .tarjeta {
        border: 1px solid #d1d1d1;
        border-radius: 12px;
        padding: 15px;
        background: #ffffff;
        transition: 0.3s;
    }

    .tarjeta:hover {
        transform: scale(1.02);
        border-color: #1a73e8;
        background: #f8fbff;
    }

    .titulo-tarjeta {
        font-size: 18px;
        font-weight: 600;
        color: #1a73e8;
    }

    .btn {
        background-color:#1a73e8;
        color:white;
        padding:6px 12px;
        border-radius:8px;
        text-align:center;
        text-decoration:none;
        font-size:14px;
    }

</style>
""", unsafe_allow_html=True)

# ================================
# TÍTULO
# ================================
st.title("🔍 InvestiData – Plataforma de Análisis Forense Digital")
st.write("Cargue un archivo UFED XLSX para iniciar el análisis.")

# ================================
# SUBIR ARCHIVO
# ================================
archivo = st.file_uploader("📂 Subir archivo forense (.xlsx)", type=["xlsx"])

if not archivo:
    st.stop()

# ================================
# CARGAR ARCHIVO
# ================================
try:
    xls = pd.ExcelFile(archivo)
    st.success("✔ Archivo cargado correctamente")
except:
    st.error("❌ No se pudo leer el archivo.")
    st.stop()


# ================================
# FUNCIÓN UNIVERSAL PARA MOSTRAR PANELES
# ================================
def analizar_hoja(df, titulo=""):
    st.header(f"📌 {titulo}")

    st.subheader("📄 Vista previa")
    st.dataframe(df.head(200))

    texto = " ".join(df.astype(str).values.flatten())

    # -------------------------
    # NÚMEROS
    # -------------------------
    numeros = re.findall(r"\b\d{7,15}\b", texto)
    if numeros:
        st.subheader("📞 Números más frecuentes")
        st.dataframe(pd.DataFrame(Counter(numeros).most_common(10),
                                  columns=["Número", "Frecuencia"]))

    # -------------------------
    # FECHAS
    # -------------------------
    fecha_col = next((c for c in df.columns if "fecha" in c.lower()), None)
    if fecha_col:
        try:
            df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")

            chart = alt.Chart(df.dropna(subset=[fecha_col])).mark_line().encode(
                x=f"{fecha_col}:T",
                y="count()",
                tooltip=[fecha_col]
            )

            st.subheader("📈 Actividad por fechas")
            st.altair_chart(chart, use_container_width=True)
        except:
            pass

    # -------------------------
    # MAPA
    # -------------------------
    lat = next((c for c in df.columns if "lat" in c.lower()), None)
    lon = next((c for c in df.columns if "lon" in c.lower()), None)

    if lat and lon:
        try:
            gps = df[[lat, lon]].dropna().astype(float)
            gps.columns = ["lat", "lon"]

            st.subheader("📍 Mapa de ubicaciones")
            st.map(gps)
        except:
            pass


# ================================
# PERFIL DEL DISPOSITIVO
# ================================
st.header("📱 Perfil del Dispositivo")

hojas = {h.lower(): h for h in xls.sheet_names}

# detectamos hoja resumen o dispositivo
hoja_resumen = next((hojas[h] for h in hojas if "resumen" in h or "device" in h), None)

if hoja_resumen:
    df_resumen = xls.parse(hoja_resumen)

    try:
        marca = df_resumen.iloc[0]["Marca"]
        modelo = df_resumen.iloc[0]["Modelo"]
        color = df_resumen.iloc[0]["Color"]
        correo = df_resumen.iloc[0]["Correo"]
        imei1 = df_resumen.iloc[0]["IMEI1"]
        imei2 = df_resumen.iloc[0]["IMEI2"]
    except:
        st.warning("El formato del perfil no coincide con UFED estándar.")
        st.dataframe(df_resumen.head())
    else:
        st.markdown(f"""
        <div class="tarjeta">
            <span class="titulo-tarjeta">📱 {marca} – {modelo}</span><br><br>
            <b>Color:</b> {color}<br>
            <b>Correo asociado:</b> {correo}<br><br>
            <b>IMEI:</b><br>
            • {imei1}<br>
            • {imei2}<br>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No se encontró hoja de perfil del dispositivo.")
    
# ================================
# DASHBOARD DE OPCIONES
# ================================
st.header("📊 Panel General de Análisis")

col1, col2, col3 = st.columns(3)

def tarjeta(texto, hoja_nombre, icono):
    if hoja_nombre in xls.sheet_names:
        with st.container():
            st.markdown(f"""
            <div class="tarjeta">
                <div class="titulo-tarjeta">{icono} {texto}</div>
                <p style="font-size:14px;">Hoja detectada: <b>{hoja_nombre}</b></p>
            """,
            unsafe_allow_html=True)

            if st.button(f"🔎 Ver análisis de {texto}", key=texto):
                st.session_state["panel"] = hoja_nombre

            st.markdown("</div>", unsafe_allow_html=True)

# -------- Tarjetas --------
tarjeta("Mensajes y Conversaciones", next((h for h in xls.sheet_names if "convers" in h.lower() or "msg" in h.lower()), None), "💬")
tarjeta("Contactos", next((h for h in xls.sheet_names if "contact" in h.lower()), None), "📇")
tarjeta("Aplicaciones", next((h for h in xls.sheet_names if "aplic" in h.lower() or "app" in h.lower()), None), "📲")
tarjeta("Ubicaciones GPS", next((h for h in xls.sheet_names if "ubic" in h.lower()), None), "📍")
tarjeta("Llamadas", next((h for h in xls.sheet_names if "llama" in h.lower() or "call" in h.lower()), None), "📞")
tarjeta("Historial Web", next((h for h in xls.sheet_names if "hist" in h.lower() or "internet" in h.lower()), None), "🌐")

# ================================
# PANEL DETALLADO
# ================================
if "panel" in st.session_state:
    hoja_sel = st.session_state["panel"]
    df_sel = xls.parse(hoja_sel)
    analizar_hoja(df_sel, titulo=f"Análisis detallado de {hoja_sel}")
