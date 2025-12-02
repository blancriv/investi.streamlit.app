# app.py
import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import altair as alt
import re
import json
import io
import logging
from datetime import datetime

# -----------------------
# Config & Logging
# -----------------------
st.set_page_config(page_title="InvestiData", layout="wide", page_icon="📱")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("investidata")

# -----------------------
# Styles
# -----------------------
st.markdown("""
<style>
/* Page background */
body { background-color: #f7f9fc; }
/* Header */
.header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.kpi {
  border-radius: 10px;
  padding: 12px;
  background: #ffffff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  text-align: left;
}
.small-muted { color: #6b7280; font-size:12px; }
.device-card {
  border-left: 4px solid #1f6feb;
  padding:10px;
  background:#fff;
  border-radius:8px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# Helpers
# -----------------------
def slug_contains(col, keywords):
    return any(k.lower() in col.lower() for k in keywords)

def detect_sheet(xls, keywords):
    for name in xls.sheet_names:
        for k in keywords:
            if k.lower() in name.lower():
                return name
    return None

@st.cache_data(show_spinner=False)
def load_excel(file) -> pd.ExcelFile:
    return pd.ExcelFile(file)

@st.cache_data(show_spinner=False)
def parse_sheet(xls, sheet_name):
    return xls.parse(sheet_name)

def normalize_columns(df: pd.DataFrame):
    # strip and unify spacing
    df.columns = [str(c).strip() for c in df.columns]
    # optionally lowercase? keep original but add helper mapping
    return df

def find_date_column(df):
    for c in df.columns:
        if "fecha" in c.lower() or "date" in c.lower() or "time" in c.lower():
            return c
    return None

def extract_numbers_from_df(df, min_len=7, max_len=15):
    text = " ".join(df.astype(str).values.flatten())
    nums = re.findall(r"\+?\d{7,15}", text)
    return Counter(nums).most_common()

def safe_to_csv_bytes(df: pd.DataFrame):
    return df.to_csv(index=False).encode("utf-8")

# -----------------------
# UI: Header / Sidebar
# -----------------------
with st.container():
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        st.markdown("<div class='header'><h1>📱 InvestiData</h1><div class='small-muted' style='margin-left:8px;'>Analítica forense automatizada</div></div>", unsafe_allow_html=True)
        st.markdown("**Carga archivos UFED (.xlsx)** — detecta hojas, genera KPIs, grafo de contactos, mapa y reportes.")
    with col2:
        st.image("https://raw.githubusercontent.com/blancriv/investidata/main/assets/logo.png" if False else "https://i.imgur.com/7n4wQ9b.png", width=64)

st.sidebar.header("Configuración")
show_dark = st.sidebar.checkbox("Modo oscuro (experimental)", value=False)
top_n = st.sidebar.slider("Top N contactos/números",  value=10, min_value=5, max_value=50)
download_report = st.sidebar.checkbox("Habilitar descarga JSON de metadata", value=True)

# -----------------------
# File uploader
# -----------------------
uploaded_file = st.file_uploader("📂 Cargar archivo UFED (XLSX)", type=["xlsx"], help="Sube el archivo exportado por UFED / Cellebrite")
use_sample = st.checkbox("Usar ejemplo de muestra (demo)", value=False)

if not uploaded_file and not use_sample:
    st.info("Sube un archivo .xlsx o activa 'Usar ejemplo de muestra' para probar la app.")
    st.stop()

# handle sample fallback (optional)
if use_sample and not uploaded_file:
    st.info("Usando archivo de muestra embebido.")
    # provide a small sample DataFrame zipped? for now warn user
    st.warning("Activa la subida real para análisis completo.")

# Load Excel
try:
    xls = load_excel(uploaded_file if uploaded_file else "/mnt/data/202500019_2025-06-26_Informe.xlsx")
    logger.info(f"Sheets detected: {xls.sheet_names}")
except Exception as e:
    st.error(f"No se pudo leer el archivo: {e}")
    st.stop()

# -----------------------
# Sheet mapping (configurable)
# -----------------------
MAPEO_HOJAS = {
    "resumen": ["resumen", "summary", "general", "overview"],
    "apps": ["aplicaciones", "applications", "apps"],
    "apps_instaladas": ["instaladas", "installed"],
    "archivos": ["archive", "archivos", "files"],
    "bases_datos": ["database", "db", "bases"],
    "calendario": ["calendar", "calendario"],
    "conectividad": ["conect", "wifi", "network"],
    "config": ["config", "ajustes", "settings"],
    "contactos": ["contact", "contactos"],
    "conversaciones": ["convers", "threads", "chat", "messages"],
    "cookies": ["cookie"],
    "cuentas": ["cuenta", "accounts"],
    "dispositivos": ["devices", "dispositivo"],
    "busquedas": ["buscado", "search"],
    "eventos": ["evento", "events"],
    "internet_historial": ["historial", "internet", "browser"],
    "info_dispositivo": ["información del dispositivo", "device info", "device"],
    "marcadores": ["marcadores", "bookmark"],
    "mensajes_sms": ["sms", "mms", "mensajes"],
    "mensajes_inst": ["instant", "whatsapp", "telegram", "messenger"],
    "notificaciones": ["notif"],
    "redes_inalambricas": ["wireless", "redes", "wifi"],
    "llamadas": ["llamadas", "call", "calls"],
    "uso_apps": ["uso de aplicaciones", "usage"],
    "autocompletado": ["autofill", "relleno"],
    "texto": ["texto", "notes"],
    "ubicaciones": ["ubicaciones", "locations", "gps"],
    "usuarios": ["usuarios", "users"],
    "cronograma": ["cronograma", "timeline"],
    "vista_ubicaciones": ["vista ubicaciones", "map view"],
}

hojas_detectadas = {cat: detect_sheet(xls, keys) for cat, keys in MAPEO_HOJAS.items()}

# -----------------------
# Small summary + Analyze button
# -----------------------
st.markdown("### 📌 Resumen del archivo")
st.write(f"Hojas detectadas: **{len(xls.sheet_names)}** — {', '.join(xls.sheet_names[:10])}")

analyze = st.button("🚀 Analizar ahora")

if not analyze:
    st.info("Presiona **Analizar ahora** para procesar el archivo y generar el tablero.")
    st.stop()

# -----------------------
# Parse selected sheets into dict
# -----------------------
data = {}
for category, sheet in hojas_detectadas.items():
    if sheet:
        try:
            df = parse_sheet(xls, sheet)
            df = normalize_columns(df)
            data[category] = df
        except Exception as e:
            logger.exception(f"Error parsing {sheet}: {e}")
            st.warning(f"No se pudo leer la hoja {sheet}: {e}")

# -----------------------
# PROFILE CARD (right column)
# -----------------------
left, right = st.columns([3,1])
with right:
    st.markdown("### 🟦 Perfil del dispositivo (autogenerado)")
    if "resumen" in data or "info_dispositivo" in data:
        df_profile = data.get("info_dispositivo", data.get("resumen"))
        try:
            # flexible access - try multiple possible column names
            def getcol(df, candidates):
                for c in df.columns:
                    for k in candidates:
                        if k.lower() in c.lower():
                            return df.iloc[0][c]
                return None

            marca = getcol(df_profile, ["marca", "brand"])
            modelo = getcol(df_profile, ["modelo", "model"])
            imei1 = getcol(df_profile, ["imei1","imei"])
            correo = getcol(df_profile, ["correo","email","mail"])
            sim = getcol(df_profile, ["sim"])
            estado = getcol(df_profile, ["estado","condition"])
            st.markdown(f"""
            <div class="device-card">
            <b>📱 {marca or 'N/D'} – {modelo or 'N/D'}</b><br>
            🔢 <b>IMEI:</b> {imei1 or 'N/D'}<br>
            📧 <b>Correo:</b> {correo or 'N/D'}<br>
            🧩 <b>SIM:</b> {sim or 'N/D'}<br>
            🛠 <b>Estado:</b> {estado or 'N/D'}
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.write("No se pudo extraer perfil automáticamente.")
    else:
        st.info("El perfil se mostrará después de analizar hojas 'Resumen' o 'Device info'.")

# -----------------------
# MAIN TABS (detailed panels)
# -----------------------
tabs = left.tabs([
    "📊 Tablero general",
    "💬 Conversaciones",
    "📇 Contactos",
    "📲 Aplicaciones",
    "📍 Ubicaciones",
    "🔗 Grafo",
    "📥 Exportar"
])

# TAB: Dashboard
with tabs[0]:
    st.header("Tablero general")
    # pick a main df for KPIs (prefer conversaciones then resumen then cualquier)
    main_df = None
    for candidate in ["conversaciones","mensajes_inst","mensajes_sms","resumen"]:
        main_df = data.get(candidate)
        if main_df is not None:
            break

    if main_df is None:
        st.info("No se detectaron hojas con registros para KPIs.")
    else:
        # KPIs
        total_records = len(main_df)
        numbers = extract_numbers_from_df(main_df)
        total_numbers = len(numbers)
        # word counts
        text_all = " ".join(main_df.astype(str).values.flatten()).lower()
        words = re.findall(r"\b[a-záéíóúñ]{3,}\b", text_all)
        wcount = Counter(words)
        top_word, top_word_count = wcount.most_common(1)[0] if wcount else ("N/A", 0)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📁 Registros", f"{total_records:,}")
        k2.metric("📞 Números detectados", f"{total_numbers}")
        k3.metric("🔠 Palabra más frecuente", f"{top_word}", delta=f"{top_word_count}")
        date_col = find_date_column(main_df)
        if date_col:
            try:
                main_df[date_col] = pd.to_datetime(main_df[date_col], errors="coerce")
                busiest = main_df[date_col].value_counts().idxmax()
                k4.metric("📅 Fecha más activa", str(pd.to_datetime(busiest).date()))
            except:
                k4.metric("📅 Fecha más activa", "N/D")
        else:
            k4.metric("📅 Fecha más activa", "No disponible")

        st.markdown("---")
        # Activity chart by date if exists
        if date_col:
            df_d = main_df.dropna(subset=[date_col])
            df_d[date_col] = pd.to_datetime(df_d[date_col], errors="coerce")
            df_group = df_d.groupby(df_d[date_col].dt.date).size().reset_index(name='count')
            chart = alt.Chart(df_group).mark_line(point=True).encode(
                x=alt.X(f"{date_col}:T", title="Fecha"),
                y=alt.Y("count:Q", title="Cantidad")
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        # Top numbers chart
        if numbers:
            df_nums = pd.DataFrame(numbers[:top_n], columns=["Número","Frecuencia"])
            chart2 = alt.Chart(df_nums).mark_bar().encode(
                x=alt.X("Número:N", sort="-y"),
                y="Frecuencia:Q",
                tooltip=["Número","Frecuencia"]
            )
            st.altair_chart(chart2, use_container_width=True)

# TAB: Conversations
with tabs[1]:
    st.header("Mensajes y Conversaciones")
    df_conv = data.get("conversaciones") or data.get("mensajes_inst") or data.get("mensajes_sms")
    if df_conv is None:
        st.info("No se encontró hoja de conversaciones / mensajes.")
    else:
        st.write("Vista previa")
        st.dataframe(df_conv.head(200))
        # filters
        c1, c2 = st.columns([2,1])
        with c1:
            keyword = st.text_input("🔍 Filtrar por palabra clave")
        with c2:
            contact_filter = st.text_input("👤 Filtrar por número/contacto")
        df_filtered = df_conv.copy()
        if keyword:
            df_filtered = df_filtered[df_filtered.astype(str).apply(lambda row: row.str.contains(keyword, case=False).any(), axis=1)]
        if contact_filter:
            df_filtered = df_filtered[df_filtered.astype(str).apply(lambda row: row.str.contains(contact_filter, case=False).any(), axis=1)]
        st.write(f"Mostrando {len(df_filtered):,} registros")
        st.dataframe(df_filtered.head(500))
        # suspicious keywords
        susp_keywords = st.text_input("Palabras sospechosas (coma separadas)", value="arma,pagar,extorsión,droga,amenaza")
        kw_list = [k.strip() for k in susp_keywords.split(",") if k.strip()]
        pattern = "|".join(kw_list)
        df_sus = df_filtered[df_filtered.astype(str).apply(lambda r: r.str.contains(pattern, case=False).any(), axis=1)] if kw_list else pd.DataFrame()
        st.markdown("### 🚨 Registros sospechosos")
        st.dataframe(df_sus.head(200))

# TAB: Contacts
with tabs[2]:
    st.header("Contactos")
    df_ct = data.get("contactos")
    if df_ct is None:
        st.info("No se encontró hoja de contactos")
    else:
        st.dataframe(df_ct.head(300))
        if "Nombre" in df_ct.columns or "name" in [c.lower() for c in df_ct.columns]:
            st.success("Contactos cargados correctamente")

# TAB: Apps
with tabs[3]:
    st.header("Aplicaciones")
    apps_df = data.get("apps") or data.get("apps_instaladas")
    if apps_df is None:
        st.info("No se detectaron hojas de aplicaciones")
    else:
        st.dataframe(apps_df.head(300))
        if any("version" in c.lower() for c in apps_df.columns):
            st.markdown("### Versiones detectadas")
            if "Version" in apps_df.columns:
                st.table(apps_df["Version"].value_counts().head(10))

# TAB: Locations (map)
with tabs[4]:
    st.header("Ubicaciones")
    loc = data.get("ubicaciones") or data.get("vista_ubicaciones")
    if loc is None:
        st.info("No se detectaron ubicaciones (columnas lat/lon).")
    else:
        # try to find lat lon columns
        lat = next((c for c in loc.columns if "lat" in c.lower()), None)
        lon = next((c for c in loc.columns if "lon" in c.lower() or "long" in c.lower()), None)
        if lat and lon:
            try:
                mapdf = loc[[lat, lon]].dropna()
                mapdf.columns = ["lat","lon"]
                mapdf["lat"] = mapdf["lat"].astype(float)
                mapdf["lon"] = mapdf["lon"].astype(float)
                st.map(mapdf)
            except Exception as e:
                st.error("Error renderizando mapa: " + str(e))
        else:
            st.info("No se detectaron columnas claras de latitud/longitud en la hoja.")

# TAB: Graph
with tabs[5]:
    st.header("Grafo de contactos")
    df_g = data.get("conversaciones") or data.get("mensajes_inst") or data.get("mensajes_sms")
    if df_g is None:
        st.info("No hay datos para grafo")
    else:
        # attempt find sender/receiver
        possible_senders = [c for c in df_g.columns if "remit" in c.lower() or "from" in c.lower() or "sender" in c.lower()]
        possible_receivers = [c for c in df_g.columns if "recept" in c.lower() or "to" in c.lower() or "receiver" in c.lower()]
        if not possible_senders or not possible_receivers:
            st.info("No se detectaron columnas sender/receiver de forma clara. Selecciona columnas manualmente:")
            cols = st.multiselect("Selecciona remitente/ receptor", df_g.columns.tolist(), default=df_g.columns[:2].tolist())
            if len(cols) >= 2:
                s_col, r_col = cols[0], cols[1]
            else:
                st.stop()
        else:
            s_col, r_col = possible_senders[0], possible_receivers[0]
        edges = df_g[[s_col, r_col]].dropna().astype(str).values.tolist()
        G = nx.DiGraph()
        G.add_edges_from([(a,b) for a,b in edges if str(a).strip() and str(b).strip()])
        if len(G) == 0:
            st.info("Grafo vacío con las columnas seleccionadas.")
        else:
            central = nx.degree_centrality(G)
            top_nodes = sorted(central.items(), key=lambda x: x[1], reverse=True)[:top_n]
            st.write("Top nodos (grado centralidad)")
            st.write(pd.DataFrame(top_nodes, columns=["Nodo","Centralidad"]))
            fig, ax = plt.subplots(figsize=(8,5))
            pos = nx.spring_layout(G, k=0.5, iterations=20)
            nx.draw_networkx_nodes(G, pos, node_size=30, ax=ax)
            nx.draw_networkx_edges(G, pos, alpha=0.2, ax=ax)
            labels = {n: n for n,_ in top_nodes}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)
            ax.set_title("Grafo de contactos (muestra)")
            ax.axis("off")
            st.pyplot(fig)

# TAB: Export
with tabs[6]:
    st.header("Exportar resultados")
    # Export filtered DF from conversations if exists
    if 'df_filtered' in locals():
        buffer = io.BytesIO()
        st.download_button("⬇️ Descargar CSV (filtrado)", data=safe_to_csv_bytes(df_filtered), file_name="investidata_filtrado.csv", mime="text/csv")
    else:
        st.info("Realiza un filtrado en 'Mensajes' para descargar resultados filtrados.")

    # Full metadata JSON
    if download_report:
        metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "sheets_detected": xls.sheet_names,
            "hojas_mapeadas": hojas_detectadas,
            "top_n": top_n
        }
        st.download_button("⬇️ Descargar metadata (JSON)", data=json.dumps(metadata, indent=2), file_name="investidata_metadata.json", mime="application/json")

st.success("Análisis completado ✅")

