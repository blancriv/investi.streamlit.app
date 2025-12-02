import streamlit as st
import pandas as pd
import altair as alt
import re
from collections import Counter

# -----------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------------------------------------
st.set_page_config(
    page_title="InvestiData – Forensic Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------
# ESTILO VISUAL
# -----------------------------------------------------------
st.markdown("""
<style>
    body { font-family: 'Segoe UI', sans-serif; }
    .stButton>button {
        background: #2b6cb0;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        border: none;
    }
    .metric-card {
        padding: 15px;
        border-radius: 10px;
        background: #eef2ff;
        border: 1px solid #c3d0ff;
        margin-bottom: 10px;
    }
    .panel {
        padding: 15px;
        background: #fafafa;
        border-radius: 8px;
        border: 1px solid #e5e5e5;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------
st.title("🔍 InvestiData – Forensic Intelligence Dashboard")
st.write("Sube el archivo UFED (.xlsx) y obtén un tablero completo de análisis.")

# -----------------------------------------------------------
# SUBIDA DEL ARCHIVO
# -----------------------------------------------------------
uploaded_file = st.file_uploader("📂 Cargar archivo Excel UFED", type=["xlsx"])
procesar = st.button("🚀 ANALIZAR DATOS")

if not uploaded_file or not procesar:
    st.stop()

# -----------------------------------------------------------
# LECTURA DEL ARCHIVO
# -----------------------------------------------------------
try:
    df_all = pd.read_excel(uploaded_file, sheet_name=None)
    st.success("✔ Archivo cargado correctamente")
except Exception as e:
    st.error(f"❌ Error al leer el archivo: {e}")
    st.stop()

# -----------------------------------------------------------
# DETECCIÓN DE HOJAS POR NOMBRE
# -----------------------------------------------------------
def buscar_hoja(posibles_nombres):
    for nombre in df_all.keys():
        for p in posibles_nombres:
            if p.lower() in nombre.lower():
                return nombre
    return None

hoja_resumen = buscar_hoja(["resumen", "summary"])
hoja_mensajes = buscar_hoja(["mensajes", "sms", "chat"])
hoja_contactos = buscar_hoja(["contact"])
hoja_apps = buscar_hoja(["aplicaciones", "apps"])
hoja_ubicaciones = buscar_hoja(["ubicacion", "location"])
hoja_llamadas = buscar_hoja(["llamada", "call"])
hoja_cuentas = buscar_hoja(["cuenta", "account"])

# -----------------------------------------------------------
# FUNCIÓN UNIVERSAL DE ANÁLISIS
# -----------------------------------------------------------
def panel_analisis(df, titulo):
    st.markdown(f"### 🧩 {titulo}")
    st.dataframe(df.head(200))

    flat_text = " ".join(df.astype(str).values.flatten())

    # 🔢 DETECTAR NÚMEROS TELÉFONOS
    numeros = re.findall(r"\b\d{7,15}\b", flat_text)
    if len(numeros) > 0:
        st.subheader("📞 Números más frecuentes")
        top_nums = pd.DataFrame(Counter(numeros).most_common(10), columns=["Número", "Frecuencia"])
        st.dataframe(top_nums)

    # 📅 DETECTAR FECHAS
    fecha_col = next((c for c in df.columns if "fecha" in c.lower()), None)
    if fecha_col:
        try:
            df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
            chart = alt.Chart(df.dropna(subset=[fecha_col])).mark_bar().encode(
                x=alt.X(fecha_col + ":T", title="Fecha"),
                y=alt.Y("count()", title="Eventos"),
                tooltip=[fecha_col]
            )
            st.altair_chart(chart, use_container_width=True)
        except:
            st.info("⚠ No se pudo graficar fechas.")

# -----------------------------------------------------------
# DASHBOARD UNIFICADO
# -----------------------------------------------------------
st.header("📊 Tablero General del Caso")

# -----------------------------------------------------------
# PANEL 1: PERFIL DEL DISPOSITIVO
# -----------------------------------------------------------
st.subheader("📱 Perfil del Dispositivo")
if hoja_resumen:
    df = df_all[hoja_resumen]
    try:
        marca = df.iloc[0].get("Marca", "N/D")
        modelo = df.iloc[0].get("Modelo", "N/D")
        imei1 = df.iloc[0].get("IMEI1", "N/D")
        imei2 = df.iloc[0].get("IMEI2", "N/D")
        correo = df.iloc[0].get("Correo", "N/D")
        color = df.iloc[0].get("Color", "N/D")
    except:
        st.write("⚠ No se encontró formato estándar.")
    else:
        st.markdown(f"""
        <div class="metric-card">
        <b>📱 {marca} – {modelo}</b><br>
        🔢 IMEI1: {imei1}<br>
        🔢 IMEI2: {imei2}<br>
        📧 Correo: {correo}<br>
        🎨 Color: {color}<br>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No existe hoja de resumen.")

# -----------------------------------------------------------
# PANELES DE ANÁLISIS
# -----------------------------------------------------------
if hoja_mensajes:
    panel_analisis(df_all[hoja_mensajes], "Mensajes / Chats")

if hoja_contactos:
    panel_analisis(df_all[hoja_contactos], "Contactos")

if hoja_apps:
    panel_analisis(df_all[hoja_apps], "Aplicaciones Instaladas")

if hoja_ubicaciones:
    panel_analisis(df_all[hoja_ubicaciones], "Ubicaciones GPS")

if hoja_llamadas:
    panel_analisis(df_all[hoja_llamadas], "Registro de Llamadas")

if hoja_cuentas:
    panel_analisis(df_all[hoja_cuentas], "Cuentas y Perfiles")

# -----------------------------------------------------------
# HOJAS RESTANTES
# -----------------------------------------------------------
st.header("📂 Otras Hojas Detectadas")
for nombre, contenido in df_all.items():
    if nombre not in [
        hoja_resumen, hoja_mensajes, hoja_contactos, hoja_apps,
        hoja_ubicaciones, hoja_llamadas, hoja_cuentas
    ]:
        with st.expander(f"📄 {nombre}"):
            panel_analisis(contenido, f"Hoja: {nombre}")
