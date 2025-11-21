import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import altair as alt
import re

# -----------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------------------------------------
st.set_page_config(
    page_title="InvestiData - Análisis Forense",
    layout="wide"
)

# -----------------------------------------------------------
# ESTILO PERSONALIZADO
# -----------------------------------------------------------
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        background-color: #F5F7FF;
    }
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    .metric-container {
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 10px;
        background: #FAFAFA;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# TÍTULO PRINCIPAL
# -----------------------------------------------------------
st.title("📱 InvestiData – Plataforma de Análisis Forense Digital")
st.write("Cargue el archivo de extracción UFED y presione **Analizar** para comenzar.")

# -----------------------------------------------------------
# SUBIR ARCHIVO
# -----------------------------------------------------------
uploaded_file = st.file_uploader("📂 Cargar archivo forensic XLSX (UFED)", type=["xlsx"])

iniciar = st.button("🚀 ANALIZAR DATOS")

if not uploaded_file or not iniciar:
    st.info("Sube un archivo y presiona **Analizar**.")
    st.stop()

# -----------------------------------------------------------
# CARGAR EXCEL
# -----------------------------------------------------------
try:
    xls = pd.ExcelFile(uploaded_file)
    st.success("✔ Archivo leído correctamente")
except:
    st.error("❌ No se pudo leer el archivo.")
    st.stop()

# -----------------------------------------------------------
# MAPEO DE HOJAS
# -----------------------------------------------------------
MAPEO_HOJAS = {
    "resumen": ["resumen", "summary", "general"],
    "apps": ["aplicaciones", "applications", "apps"],
    "apps_instaladas": ["instaladas", "installed"],
    "archivos": ["archive", "archivos", "files"],
    "bases_datos": ["database", "db", "bases"],
    "calendario": ["calendar", "calendario"],
    "conectividad": ["conect", "wifi", "network"],
    "config": ["config", "ajustes", "settings"],
    "contactos": ["contact", "contactos"],
    "conversaciones": ["convers", "threads", "chat"],
    "cookies": ["cookie"],
    "cuentas": ["cuenta", "accounts"],
    "dispositivos": ["devices", "dispositivo"],
    "busquedas": ["buscado", "search"],
    "eventos": ["evento", "events"],
    "internet_historial": ["historial", "internet"],
    "info_dispositivo": ["información del dispositivo", "device info"],
    "marcadores": ["marcadores", "bookmark"],
    "mensajes_sms": ["sms", "mms", "mensajes"],
    "mensajes_inst": ["instant", "whatsapp", "telegram", "messenger"],
    "notificaciones": ["notif"],
    "redes_inalambricas": ["wireless", "redes"],
    "llamadas": ["llamadas", "call"],
    "uso_apps": ["uso de aplicaciones", "usage"],
    "autocompletado": ["autofill", "relleno"],
    "texto": ["texto", "notes"],
    "ubicaciones": ["ubicaciones", "locations"],
    "usuarios": ["usuarios", "users"],
    "cronograma": ["cronograma", "timeline"],
    "vista_ubicaciones": ["vista ubicaciones", "map view"],
}

def detectar_hoja(xls, keywords):
    for hoja in xls.sheet_names:
        for k in keywords:
            if k.lower() in hoja.lower():
                return hoja
    return None

hojas_detectadas = {
    categoria: detectar_hoja(xls, claves)
    for categoria, claves in MAPEO_HOJAS.items()
}

# -----------------------------------------------------------
# FUNCIÓN UNIVERSAL DE PANEL
# -----------------------------------------------------------
def mostrar_panel(nombre, df):
    st.subheader(f"📌 {nombre}")
    st.dataframe(df.head(200))

    # Detectar número
    texto = " ".join(df.astype(str).values.flatten())
    numeros = re.findall(r"\b\d{7,15}\b", texto)
    if numeros:
        st.write("### 🔢 Números más frecuentes")
        st.write(pd.DataFrame(Counter(numeros).most_common(10), columns=["Número", "Frecuencia"]))

    # Detectar fechas
    fecha_col = next((c for c in df.columns if "fecha" in c.lower()), None)
    if fecha_col:
        try:
            df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
            chart = alt.Chart(df.dropna(subset=[fecha_col])).mark_line().encode(
                x=fecha_col + ":T",
                y="count()",
                tooltip=[fecha_col]
            )
            st.altair_chart(chart, use_container_width=True)
        except:
            pass

    # Detectar ubicación
    lat = next((c for c in df.columns if "lat" in c.lower()), None)
    lon = next((c for c in df.columns if "lon" in c.lower()), None)
    if lat and lon:
        try:
            map_df = df[[lat, lon]].dropna()
            map_df.columns = ["lat", "lon"]
            map_df["lat"] = map_df["lat"].astype(float)
            map_df["lon"] = map_df["lon"].astype(float)
            st.map(map_df)
        except:
            st.info("⚠ Coordenadas no válidas para mapa.")

# -----------------------------------------------------------
# CREAR TABS
# -----------------------------------------------------------
tabs = st.tabs([
    "📱 Perfil del Dispositivo",
    "📊 Resumen General",
    "💬 Mensajes / Conversaciones",
    "📇 Contactos",
    "📲 Aplicaciones",
    "📍 Ubicaciones",
    "📞 Llamadas",
    "🌐 Internet",
    "🔐 Cuentas y Seguridad",
    "🧩 Otras Hojas"
])

# -----------------------------------------------------------
# PANEL 1: PERFIL DEL DISPOSITIVO
# -----------------------------------------------------------
with tabs[0]:

    hoja_resumen = hojas_detectadas["resumen"]
    hoja_info = hojas_detectadas["info_dispositivo"]

    hoja_final = hoja_info or hoja_resumen

    if hoja_final:
        df = xls.parse(hoja_final)
        st.subheader("📱 Perfil del Dispositivo")

        try:
            marca = df.iloc[0]["Marca"]
            modelo = df.iloc[0]["Modelo"]
            color = df.iloc[0]["Color"]
            imei1 = df.iloc[0]["IMEI1"]
            imei2 = df.iloc[0]["IMEI2"]
            correo = df.iloc[0]["Correo"]
            estado = df.iloc[0]["Estado"]
        except:
            st.warning("⚠ El formato de la hoja no es estándar UFED.")
            st.dataframe(df.head())
        else:
            st.markdown(f"""
            <div style="border:1px solid #1a73e8; padding:12px; border-radius:10px;">
            <b>📱 {marca} – {modelo}</b><br>
            🎨 <b>Color:</b> {color}<br>
            🔢 <b>IMEI:</b><br>• {imei1}<br>• {imei2}<br>
            📧 <b>Correo:</b> {correo}<br>
            🛠 <b>Estado:</b> {estado}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No se detectó una hoja de perfil del dispositivo.")

# -----------------------------------------------------------
# PANEL 2: RESUMEN GENERAL
# -----------------------------------------------------------
with tabs[1]:
    hoja = hojas_detectadas["resumen"]
    if hoja:
        df = xls.parse(hoja)
        mostrar_panel("Resumen General del Caso", df)
    else:
        st.info("No se detectó una hoja de resumen.")

# -----------------------------------------------------------
# PANEL 3: MENSAJES / CONVERSACIONES
# -----------------------------------------------------------
with tabs[2]:
    hoja = hojas_detectadas["conversaciones"] or hojas_detectadas["mensajes_inst"] or hojas_detectadas["mensajes_sms"]
    if hoja:
        df = xls.parse(hoja)
        mostrar_panel("Mensajes / Conversaciones", df)
    else:
        st.info("No hay hoja de mensajes.")

# -----------------------------------------------------------
# PANEL 4: CONTACTOS
# -----------------------------------------------------------
with tabs[3]:
    hoja = hojas_detectadas["contactos"]
    if hoja:
        df = xls.parse(hoja)
        mostrar_panel("Contactos del Dispositivo", df)
    else:
        st.info("No se detectó hoja de contactos.")

# -----------------------------------------------------------
# PANEL 5: APLICACIONES
# -----------------------------------------------------------
with tabs[4]:
    hoja1 = hojas_detectadas["apps"]
    hoja2 = hojas_detectadas["apps_instaladas"]

    if hoja1:
        mostrar_panel("Aplicaciones", xls.parse(hoja1))
    if hoja2:
        mostrar_panel("Aplicaciones Instaladas", xls.parse(hoja2))
    if not (hoja1 or hoja2):
        st.info("No se detectaron hojas relacionadas con aplicaciones.")

# -----------------------------------------------------------
# PANEL 6: UBICACIONES
# -----------------------------------------------------------
with tabs[5]:
    hoja = hojas_detectadas["ubicaciones"] or hojas_detectadas["vista_ubicaciones"]
    if hoja:
        df = xls.parse(hoja)
        mostrar_panel("Ubicaciones GPS", df)
    else:
        st.info("No hay ubicación disponible.")

# -----------------------------------------------------------
# PANEL 7: LLAMADAS
# -----------------------------------------------------------
with tabs[6]:
    hoja = hojas_detectadas["llamadas"]
    if hoja:
        df = xls.parse(hoja)
        mostrar_panel("Registro de Llamadas", df)
    else:
        st.info("No se detectó hoja de llamadas.")

# -----------------------------------------------------------
# PANEL 8: INTERNET
# -----------------------------------------------------------
with tabs[7]:
    hoja = hojas_detectadas["internet_historial"] or hojas_detectadas["marcadores"]
    if hoja:
        df = xls.parse(hoja)
        mostrar_panel("Historial de Internet / Marcadores", df)
    else:
        st.info("No se detectó historial de internet.")

# -----------------------------------------------------------
# PANEL 9: CUENTAS
# -----------------------------------------------------------
with tabs[8]:
    hoja = hojas_detectadas["cuentas"] or hojas_detectadas["autocompletado"]
    if hoja:
        df = xls.parse(hoja)
        mostrar_panel("Cuentas del Propietario", df)
    else:
        st.info("No se detectaron cuentas.")

# -----------------------------------------------------------
# PANEL 10: OTRAS HOJAS
# -----------------------------------------------------------
with tabs[9]:
    st.subheader("📂 Hojas adicionales detectadas")
    for categoria, hoja in hojas_detectadas.items():
        if hoja and categoria not in [
            "resumen","conversaciones","mensajes_sms","mensajes_inst","contactos",
            "apps","apps_instaladas","ubicaciones","llamadas","internet_historial",
            "marcadores","cuentas","autocompletado","info_dispositivo"
        ]:
            st.markdown(f"### 🗂 {categoria.replace('_', ' ').title()}")
            mostrar_panel(categoria, xls.parse(hoja))
